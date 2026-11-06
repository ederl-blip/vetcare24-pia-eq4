"""Casos de uso. La capa de aplicación orquesta; las reglas viven en el dominio."""

from datetime import date

from src.domain import events
from src.domain.entities import Actor, Linea, Operacion
from src.domain.errors import DatoInvalido, OperacionNoProcesable, PosibleDuplicado
from src.domain.reglas_clinicas import normalizar, solo_digitos, verificar_alergias
from src.domain.specifications import beneficio_referencia, puede_procesarse
from src.domain.value_objects import Dinero
from src.infrastructure import models as m
from src.infrastructure.repositorios import (
    ActorRepo,
    EventoRepo,
    OperacionRepo,
    RecursoRepo,
)


class OperacionService:
    def __init__(self, session, bus=None):
        self.s = session
        self.actores, self.recursos = ActorRepo(session), RecursoRepo(session)
        self.operaciones, self.eventos = OperacionRepo(session), EventoRepo(session)
        self.bus = bus
        if bus:
            for tipo in (events.OperacionConfirmada, events.OperacionRealizada,
                         events.OperacionCancelada):
                bus.suscribir(tipo, self.eventos.registrar)

    # -- crear --------------------------------------------------------------
    def crear(self, actor_id, lineas, promocion_activa=False, autorizado=True,
              referencia="", fecha=None):
        actor = self.actores.obtener(actor_id)
        if not actor.activo:
            raise OperacionNoProcesable("El tutor está inactivo y no puede solicitar citas")
        if not lineas:
            raise DatoInvalido("La cita debe incluir al menos un servicio")
        lineas_dom = []
        for recurso_id, cantidad in lineas:
            recurso = self.recursos.obtener(recurso_id)
            if not recurso.habilitado:
                raise OperacionNoProcesable(f"El servicio «{recurso.descripcion}» no está disponible")
            lineas_dom.append(Linea(recurso_id, cantidad, recurso.precio))
        op = Operacion(self.operaciones.siguiente_id(), actor, fecha or date.today(),
                       lineas_dom, promocion_activa=promocion_activa,
                       autorizado=autorizado, referencia=referencia)
        self.operaciones.agregar(op)
        self.s.commit()
        return op

    # -- transiciones -------------------------------------------------------
    def _publicar(self, op):
        for e in op.eventos:
            if self.bus:
                self.bus.publicar(e)
        op.eventos.clear()

    def _ejecutar(self, op_id, accion):
        try:
            op = self.operaciones.obtener(op_id)
            if accion == "confirmar":
                self._confirmar(op)
            elif accion == "realizar":
                op.realizar()
            else:
                self._cancelar(op)
            self.operaciones.guardar_estado(op)
            self._publicar(op)
            self.s.commit()
            return op
        except Exception:
            self.s.rollback()
            raise

    def _confirmar(self, op):
        motivos = puede_procesarse.explicar(op)
        if motivos:
            raise OperacionNoProcesable("No se puede confirmar la cita: " + "; ".join(motivos))
        op.confirmar()  # valida la transición antes de tocar el inventario
        por_recurso = {}
        for l in op.lineas:
            por_recurso[l.recurso_id] = por_recurso.get(l.recurso_id, 0) + l.cantidad
        reservados = [(self.recursos.obtener(r), c) for r, c in por_recurso.items()]
        for recurso, cantidad in reservados:
            recurso.reservar(cantidad)  # lanza SinDisponibilidad
        for recurso, _ in reservados:
            self.recursos.guardar(recurso)

    def _cancelar(self, op):
        estaba_confirmada = op.estado.value == "CONFIRMADA"
        op.cancelar()
        if estaba_confirmada:  # devuelve los lugares reservados
            for l in op.lineas:
                r = self.recursos.obtener(l.recurso_id)
                r.liberar(l.cantidad)
                self.recursos.guardar(r)

    def confirmar(self, op_id):
        return self._ejecutar(op_id, "confirmar")

    def realizar(self, op_id):
        return self._ejecutar(op_id, "realizar")

    def cancelar(self, op_id):
        return self._ejecutar(op_id, "cancelar")

    # -- consultas ----------------------------------------------------------
    def evaluar(self, op_id):
        op = self.operaciones.obtener(op_id)
        return {
            "operacion_id": op.id,
            "total_mxn": str(op.total),
            "puede_procesarse": puede_procesarse.es_satisfecha_por(op),
            "motivos_rechazo": puede_procesarse.explicar(op),
            "aplica_beneficio": beneficio_referencia.es_satisfecha_por(op),
            "motivos_sin_beneficio": beneficio_referencia.explicar(op),
        }


class ExpedienteService:
    """US-13: prevención de expedientes duplicados."""

    def __init__(self, session):
        self.s = session
        self.actores = ActorRepo(session)

    def registrar_tutor(self, nombre, telefono="", correo=None, ciudad="",
                        confirmar_distinta_persona=False):
        if not nombre.strip():
            raise DatoInvalido("El nombre del tutor es obligatorio")
        telefono = solo_digitos(telefono)
        correo = normalizar(correo) if correo else None
        if not telefono and not correo:
            raise DatoInvalido("Debe indicarse al menos un teléfono o un correo")
        existente = self.actores.buscar_activo_por_contacto(telefono, correo)
        if existente and not confirmar_distinta_persona:
            raise PosibleDuplicado(
                "Ya existe un expediente activo con ese teléfono o correo: "
                f"{existente.nombre} ({existente.id}). Revise si es la misma "
                "persona antes de crear uno nuevo"
            )
        nuevo = Actor(self.actores.siguiente_id(), nombre.strip(), ciudad=ciudad,
                      telefono=telefono, correo=correo)
        self.actores.agregar(nuevo)
        self.s.commit()
        return nuevo


class ClinicaService:
    """US-11: bloqueo farmacológico por alergias."""

    def __init__(self, session):
        self.s = session
        self.actores = ActorRepo(session)

    def registrar_mascota(self, nombre, propietario_id, alergias):
        self.actores.obtener(propietario_id)
        fila = m.MascotaRow(nombre=nombre.strip(), propietario_id=propietario_id,
                            alergias=",".join(a.strip() for a in alergias if a.strip()))
        self.s.add(fila)
        self.s.commit()
        return fila

    def prescribir(self, mascota_id, medicamento, sustancias, confirmar=False,
                   veterinario=None):
        from src.domain.errors import EntidadNoEncontrada

        mascota = self.s.get(m.MascotaRow, mascota_id)
        if not mascota:
            raise EntidadNoEncontrada(f"No existe la mascota {mascota_id}")
        alergias = [a for a in mascota.alergias.split(",") if a]
        con_alerta, autorizada = verificar_alergias(
            mascota.nombre, alergias, sustancias, medicamento, confirmar, veterinario)
        receta = m.RecetaRow(mascota_id=mascota_id, medicamento=medicamento,
                             con_alerta=con_alerta, autorizada_por=autorizada)
        self.s.add(receta)
        self.s.commit()
        return receta


__all__ = ["OperacionService", "ExpedienteService", "ClinicaService", "Dinero"]
