"""Repositorios: traducen entre filas SQL y objetos de dominio."""

from sqlalchemy import func, or_, select

from src.domain.entities import Actor, Linea, Operacion, Recurso
from src.domain.errors import EntidadNoEncontrada
from src.domain.value_objects import Dinero, Estado
from src.infrastructure import models as m


def _actor(r):
    return Actor(r.id, r.nombre, r.es_preferente, r.activo, r.ciudad, r.telefono, r.correo)


def _recurso(r):
    return Recurso(r.id, r.descripcion, Dinero(r.precio), r.capacidad, r.habilitado)


class ActorRepo:
    def __init__(self, s):
        self.s = s

    def obtener(self, actor_id) -> Actor:
        fila = self.s.get(m.ActorRow, actor_id)
        if not fila:
            raise EntidadNoEncontrada(f"No existe el tutor {actor_id}")
        return _actor(fila)

    def buscar_activo_por_contacto(self, telefono, correo):
        cond = []
        if telefono:
            cond.append(m.ActorRow.telefono == telefono)
        if correo:
            cond.append(m.ActorRow.correo == correo)
        if not cond:
            return None
        fila = self.s.scalars(
            select(m.ActorRow).where(m.ActorRow.activo.is_(True), or_(*cond))
        ).first()
        return _actor(fila) if fila else None

    def siguiente_id(self):
        n = self.s.scalar(select(func.count()).select_from(m.ActorRow)) + 1
        while self.s.get(m.ActorRow, f"VET-C{n:03d}"):
            n += 1
        return f"VET-C{n:03d}"

    def agregar(self, a: Actor):
        self.s.add(m.ActorRow(id=a.id, nombre=a.nombre, es_preferente=a.es_preferente,
                              activo=a.activo, ciudad=a.ciudad, telefono=a.telefono,
                              correo=a.correo))
        self.s.flush()


class RecursoRepo:
    def __init__(self, s):
        self.s = s

    def obtener(self, recurso_id) -> Recurso:
        fila = self.s.get(m.RecursoRow, recurso_id)
        if not fila:
            raise EntidadNoEncontrada(f"No existe el servicio {recurso_id}")
        return _recurso(fila)

    def listar(self):
        return [_recurso(r) for r in self.s.scalars(select(m.RecursoRow).order_by(m.RecursoRow.id))]

    def guardar(self, r: Recurso):
        fila = self.s.get(m.RecursoRow, r.id)
        fila.capacidad = r.capacidad
        self.s.flush()


class OperacionRepo:
    def __init__(self, s):
        self.s = s

    def _dominio(self, f) -> Operacion:
        actor = _actor(self.s.get(m.ActorRow, f.actor_id))
        lineas = [Linea(l.recurso_id, l.cantidad, Dinero(l.precio_unitario)) for l in f.lineas]
        return Operacion(f.id, actor, f.fecha_solicitud, lineas, Estado(f.estado),
                         f.promocion_activa, f.autorizado, f.referencia)

    def obtener(self, op_id) -> Operacion:
        fila = self.s.get(m.OperacionRow, op_id)
        if not fila:
            raise EntidadNoEncontrada(f"No existe la cita {op_id}")
        return self._dominio(fila)

    def listar(self, estado=None, limite=100, desplazamiento=0):
        q = select(m.OperacionRow).order_by(m.OperacionRow.id)
        if estado:
            q = q.where(m.OperacionRow.estado == estado)
        filas = self.s.scalars(q.limit(limite).offset(desplazamiento))
        return [self._dominio(f) for f in filas]

    def siguiente_id(self):
        n = self.s.scalar(select(func.count()).select_from(m.OperacionRow)) + 1
        while self.s.get(m.OperacionRow, f"VET-O{n:03d}"):
            n += 1
        return f"VET-O{n:03d}"

    def agregar(self, op: Operacion):
        self.s.add(m.OperacionRow(
            id=op.id, actor_id=op.actor.id, estado=op.estado.value,
            fecha_solicitud=op.fecha_solicitud, promocion_activa=op.promocion_activa,
            autorizado=op.autorizado, referencia=op.referencia,
            lineas=[m.LineaRow(recurso_id=l.recurso_id, cantidad=l.cantidad,
                               precio_unitario=l.precio_unitario.monto) for l in op.lineas]))
        self.s.flush()

    def guardar_estado(self, op: Operacion):
        self.s.get(m.OperacionRow, op.id).estado = op.estado.value
        self.s.flush()


class EventoRepo:
    def __init__(self, s):
        self.s = s

    def registrar(self, e):
        self.s.add(m.EventoRow(nombre=e.nombre, operacion_id=e.operacion_id, ocurrido=e.ocurrido))
        self.s.flush()

    def de_operacion(self, op_id):
        q = select(m.EventoRow).where(m.EventoRow.operacion_id == op_id).order_by(m.EventoRow.id)
        return list(self.s.scalars(q))
