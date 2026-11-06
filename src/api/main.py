"""API REST de VetCare 24 (FastAPI). Documentación interactiva en /docs."""

import logging
import os
from contextlib import asynccontextmanager
from datetime import timedelta

from fastapi import Depends, FastAPI, Query, Request
from fastapi.responses import JSONResponse

from src.api import schemas as sc
from src.application.event_bus import EventBus
from src.application.services import ClinicaService, ExpedienteService, OperacionService
from src.domain import errors as err
from src.domain.entities import Operacion
from src.domain.reglas_clinicas import Agenda, Cita
from src.infrastructure import models as m
from src.infrastructure.database import make_engine, make_session_factory
from src.infrastructure.repositorios import EventoRepo, RecursoRepo
from src.infrastructure.seed import cargar_datos

log = logging.getLogger("vetcare")

CODIGOS = {
    err.EntidadNoEncontrada: 404,
    err.DatoInvalido: 400,
    err.OperacionNoProcesable: 400,
    err.UrgenciaIncompleta: 400,
    err.TransicionInvalida: 409,
    err.SinDisponibilidad: 409,
    err.PosibleDuplicado: 409,
    err.AlergiaDetectada: 409,
    err.AgendaExcedeCierre: 409,
}


def crear_app(database_url=None, seed=None) -> FastAPI:
    engine = make_engine(database_url)
    factory = make_session_factory(engine)

    @asynccontextmanager
    async def lifespan(app):
        if seed if seed is not None else os.getenv("SEED_ON_START", "true") == "true":
            with factory() as s:
                cargar_datos(s)
        yield
        engine.dispose()

    app = FastAPI(
        title="VetCare 24 API",
        version="1.0.0",
        description="Citas y servicios veterinarios de VetCare 24 (PIA, Equipo 4, UANL FIME).",
        lifespan=lifespan,
    )

    def get_session():
        with factory() as s:
            yield s

    def op_service(s=Depends(get_session)):
        return OperacionService(s, EventBus())

    @app.exception_handler(err.DominioError)
    async def manejar_dominio(_: Request, e: err.DominioError):
        codigo = next((c for t, c in CODIGOS.items() if isinstance(e, t)), 400)
        return JSONResponse(status_code=codigo, content={"detail": str(e)})

    def salida(op: Operacion) -> sc.OperacionOut:
        return sc.OperacionOut(
            id=op.id, actor_id=op.actor.id, estado=op.estado.value,
            fecha_solicitud=op.fecha_solicitud, total_mxn=str(op.total),
            lineas=[sc.LineaOut(recurso_id=l.recurso_id, cantidad=l.cantidad,
                                precio_unitario_mxn=str(l.precio_unitario),
                                subtotal_mxn=str(l.subtotal)) for l in op.lineas])

    @app.get("/health", tags=["Sistema"], summary="¿La API está funcionando?")
    def health():
        return {"estado": "ok"}

    @app.get("/catalogo", tags=["Catálogo"], summary="Servicios y lugares disponibles")
    def catalogo(s=Depends(get_session)):
        return [{"id": r.id, "descripcion": r.descripcion, "precio_mxn": str(r.precio),
                 "lugares_disponibles": r.capacidad, "habilitado": r.habilitado}
                for r in RecursoRepo(s).listar()]

    # --- Citas (operaciones) -------------------------------------------------
    @app.post("/operaciones", response_model=sc.OperacionOut, status_code=201, tags=["Citas"],
              summary="Solicitar una cita")
    def crear_operacion(datos: sc.OperacionIn, svc=Depends(op_service)):
        op = svc.crear(datos.actor_id, [(l.recurso_id, l.cantidad) for l in datos.lineas],
                       datos.promocion_activa, datos.autorizado, datos.referencia,
                       datos.fecha_solicitud)
        return salida(op)

    @app.get("/operaciones", response_model=list[sc.OperacionOut], tags=["Citas"],
             summary="Listar citas")
    def listar(estado: str | None = Query(None, pattern="^(SOLICITADA|CONFIRMADA|REALIZADA|CANCELADA)$"),
               limite: int = Query(50, ge=1, le=200), desde: int = Query(0, ge=0),
               svc=Depends(op_service)):
        return [salida(o) for o in svc.operaciones.listar(estado, limite, desde)]

    @app.get("/operaciones/{op_id}", response_model=sc.OperacionOut, tags=["Citas"],
             summary="Consultar una cita")
    def obtener(op_id: str, svc=Depends(op_service)):
        return salida(svc.operaciones.obtener(op_id))

    @app.post("/operaciones/{op_id}/confirmar", response_model=sc.OperacionOut, tags=["Citas"],
              summary="Confirmar una cita (reserva los lugares)")
    def confirmar(op_id: str, svc=Depends(op_service)):
        return salida(svc.confirmar(op_id))

    @app.post("/operaciones/{op_id}/realizar", response_model=sc.OperacionOut, tags=["Citas"],
              summary="Marcar una cita como realizada")
    def realizar(op_id: str, svc=Depends(op_service)):
        return salida(svc.realizar(op_id))

    @app.post("/operaciones/{op_id}/cancelar", response_model=sc.OperacionOut, tags=["Citas"],
              summary="Cancelar una cita")
    def cancelar(op_id: str, svc=Depends(op_service)):
        return salida(svc.cancelar(op_id))

    @app.get("/operaciones/{op_id}/evaluacion", tags=["Citas"],
             summary="¿Puede procesarse? ¿Aplica beneficio?")
    def evaluacion(op_id: str, svc=Depends(op_service)):
        return svc.evaluar(op_id)

    @app.get("/operaciones/{op_id}/eventos", response_model=list[sc.EventoOut], tags=["Citas"],
             summary="Historial de eventos de la cita")
    def eventos(op_id: str, s=Depends(get_session)):
        return [sc.EventoOut(nombre=e.nombre, ocurrido=e.ocurrido)
                for e in EventoRepo(s).de_operacion(op_id)]

    # --- Tutores (US-13) -----------------------------------------------------
    @app.post("/tutores", response_model=sc.TutorOut, status_code=201, tags=["Expedientes"],
              summary="Registrar tutor (evita expedientes duplicados)")
    def registrar_tutor(d: sc.TutorIn, s=Depends(get_session)):
        a = ExpedienteService(s).registrar_tutor(
            d.nombre, d.telefono, d.correo, d.ciudad, d.confirmar_distinta_persona)
        return sc.TutorOut(id=a.id, nombre=a.nombre, telefono=a.telefono,
                           correo=a.correo, ciudad=a.ciudad)

    # --- Mascotas y recetas (US-11) -----------------------------------------
    @app.post("/mascotas", response_model=sc.MascotaOut, status_code=201, tags=["Clínica"],
              summary="Registrar mascota con sus alergias")
    def registrar_mascota(d: sc.MascotaIn, s=Depends(get_session)):
        f = ClinicaService(s).registrar_mascota(d.nombre, d.propietario_id, d.alergias)
        return sc.MascotaOut(id=f.id, nombre=f.nombre, propietario_id=f.propietario_id,
                             alergias=[a for a in f.alergias.split(",") if a])

    @app.post("/mascotas/{mascota_id}/recetas", response_model=sc.RecetaOut, status_code=201,
              tags=["Clínica"], summary="Recetar un medicamento (bloquea alergias)")
    def recetar(mascota_id: int, d: sc.RecetaIn, s=Depends(get_session)):
        r = ClinicaService(s).prescribir(mascota_id, d.medicamento, d.sustancias,
                                         d.confirmar_conscientemente, d.veterinario)
        return sc.RecetaOut(id=r.id, mascota_id=r.mascota_id, medicamento=r.medicamento,
                            con_alerta=r.con_alerta, autorizada_por=r.autorizada_por)

    # --- Urgencias (US-06) ----------------------------------------------------
    @app.post("/agenda/urgencias", tags=["Clínica"],
              summary="Registrar urgencia: pausa la cita en curso y recorre la agenda")
    def urgencia(d: sc.UrgenciaIn):
        agenda = Agenda([Cita(c.id, c.mascota_id, c.inicio, c.fin) for c in d.citas],
                        d.hora_cierre, timedelta(minutes=d.desplazamiento_minutos))
        motivo = agenda.registrar_urgencia(d.mascota_id, d.motivo, d.ahora)
        return {"motivo": motivo, "etiqueta": "Urgencia",
                "citas": [{"id": c.id, "estado": c.estado, "inicio": c.inicio, "fin": c.fin}
                          for c in agenda.citas]}

    _ = m  # (modelos registrados en la base)
    return app


app = crear_app()
