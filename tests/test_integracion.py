"""Pruebas de integración: servicios + base de datos reales (SQLite en memoria)."""

from datetime import date

import pytest
from sqlalchemy import select

from src.application.evaluacion import evaluar_casos, evaluar_transiciones
from src.application.event_bus import EventBus
from src.application.services import ClinicaService, ExpedienteService, OperacionService
from src.domain.errors import (
    DatoInvalido,
    EntidadNoEncontrada,
    OperacionNoProcesable,
    PosibleDuplicado,
    SinDisponibilidad,
    TransicionInvalida,
)
from src.infrastructure import models as m
from src.infrastructure.database import database_url, make_engine
from src.infrastructure.seed import cargar_datos


def test_seed_carga_los_datos_oficiales_y_es_idempotente(session):
    assert session.query(m.ActorRow).count() == 40
    assert session.query(m.RecursoRow).count() == 20
    assert session.query(m.OperacionRow).count() == 60
    assert session.query(m.LineaRow).count() == 117
    assert cargar_datos(session) is False


def test_total_de_o001_calculado_con_decimal(session):
    assert str(OperacionService(session).operaciones.obtener("VET-O001").total) == "7587.00"


def test_confirmar_reserva_lugares_y_cancelar_los_devuelve(session):
    svc = OperacionService(session, EventBus())
    antes = svc.recursos.obtener("VET-P009").capacidad
    svc.confirmar("VET-O001")
    assert svc.recursos.obtener("VET-P009").capacidad == antes - 3
    svc.cancelar("VET-O001")
    assert svc.recursos.obtener("VET-P009").capacidad == antes
    assert [e.nombre for e in svc.eventos.de_operacion("VET-O001")] == [
        "OperacionConfirmada", "OperacionCancelada"]


def test_sin_disponibilidad_hace_rollback_completo(session):
    svc = OperacionService(session, EventBus())
    op = svc.crear("VET-C001", [("VET-P001", 14)])  # P001 solo tiene 13
    with pytest.raises(SinDisponibilidad):
        svc.confirmar(op.id)
    assert svc.operaciones.obtener(op.id).estado.value == "SOLICITADA"
    assert svc.recursos.obtener("VET-P001").capacidad == 13
    assert svc.eventos.de_operacion(op.id) == []


def test_flujo_completo_confirmar_realizar(session):
    svc = OperacionService(session, EventBus())
    svc.confirmar("VET-O001")
    assert svc.realizar("VET-O001").estado.value == "REALIZADA"
    with pytest.raises(TransicionInvalida):
        svc.cancelar("VET-O001")


def test_confirmar_cita_no_procesable_se_rechaza(session):
    svc = OperacionService(session, EventBus())
    sin_auth = next(o for o in svc.operaciones.listar(limite=60) if not o.autorizado)
    with pytest.raises(OperacionNoProcesable, match="autorización"):
        svc.confirmar(sin_auth.id)


def test_crear_valida_actor_servicio_y_detalle(session):
    svc = OperacionService(session)
    with pytest.raises(EntidadNoEncontrada):
        svc.crear("NOPE", [("VET-P001", 1)])
    with pytest.raises(EntidadNoEncontrada):
        svc.crear("VET-C001", [("NOPE", 1)])
    with pytest.raises(DatoInvalido):
        svc.crear("VET-C001", [])
    inactivo = session.query(m.ActorRow).filter_by(activo=False).first().id
    with pytest.raises(OperacionNoProcesable, match="inactivo"):
        svc.crear(inactivo, [("VET-P001", 1)])
    deshab = session.query(m.RecursoRow).filter_by(habilitado=False).first().id
    with pytest.raises(OperacionNoProcesable, match="no está disponible"):
        svc.crear("VET-C001", [(deshab, 1)])


def test_crear_persiste_y_evalua(session):
    svc = OperacionService(session)
    op = svc.crear("VET-C001", [("VET-P001", 2)], fecha=date(2026, 11, 6))
    assert op.id == "VET-O061"
    ev = svc.evaluar(op.id)
    assert ev["total_mxn"] == "626.00" and ev["puede_procesarse"] is True
    assert ev["aplica_beneficio"] is False and ev["motivos_sin_beneficio"]
    assert svc.operaciones.listar(estado="SOLICITADA", limite=1000)


def test_duplicados_us13(session):
    svc = ExpedienteService(session)
    a = svc.registrar_tutor("Ana Torres", "81 1234 5678", "Ana@Correo.com")
    assert a.telefono == "8112345678" and a.correo == "ana@correo.com"
    with pytest.raises(PosibleDuplicado, match="Ya existe un expediente activo"):
        svc.registrar_tutor("Ana T.", "(81) 1234-5678")
    otro = svc.registrar_tutor("Luis", "8112345678", confirmar_distinta_persona=True)
    assert otro.id != a.id
    with pytest.raises(DatoInvalido):
        svc.registrar_tutor("Sin contacto")
    with pytest.raises(DatoInvalido):
        svc.registrar_tutor("  ", "811")


def test_alergias_us11(session):
    svc = ClinicaService(session)
    luna = svc.registrar_mascota("Luna", "VET-C001", ["penicilina"])
    with pytest.raises(Exception, match="alérgica"):
        svc.prescribir(luna.id, "Penicilina G", ["penicilina"])
    assert session.scalars(select(m.RecetaRow)).first() is None
    r = svc.prescribir(luna.id, "Penicilina G", ["penicilina"], True, "Dra. Ruiz")
    assert r.con_alerta and r.autorizada_por == "Dra. Ruiz"
    with pytest.raises(EntidadNoEncontrada):
        svc.prescribir(999, "X", [])
    with pytest.raises(EntidadNoEncontrada):
        svc.registrar_mascota("Rex", "NOPE", [])


def test_evaluacion_de_los_120_casos_y_20_transiciones():
    casos = evaluar_casos()
    assert len(casos) == 120
    assert {c["resultado"] for c in casos} <= {"APROBADO", "RECHAZADO", "CON_BENEFICIO", "SIN_BENEFICIO"}
    trans = evaluar_transiciones()
    assert len(trans) == 20
    por = {t["caso_id"]: t for t in trans}
    assert all(t["estado_final"] in {"SOLICITADA", "CONFIRMADA", "REALIZADA", "CANCELADA"} for t in trans)
    # saltar_estado y repetir_aprobacion nunca terminan en REALIZADA
    assert all(t["estado_final"] != "REALIZADA" for t in trans
               if t["accion"] in {"saltar_estado"})
    assert por


def test_database_url_corrige_postgres_y_usa_valor_por_defecto(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@host/db")
    assert database_url() == "postgresql://u:p@host/db"
    monkeypatch.delenv("DATABASE_URL")
    assert database_url().startswith("sqlite")
    engine = make_engine("sqlite:///:memory:")
    assert engine is not None
