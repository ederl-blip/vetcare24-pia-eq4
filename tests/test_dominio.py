"""Pruebas unitarias del dominio (sin base de datos ni API)."""

from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest

from src.domain import events
from src.domain.entities import Actor, Linea, Operacion, Recurso
from src.domain.errors import (
    AgendaExcedeCierre,
    AlergiaDetectada,
    DatoInvalido,
    SinDisponibilidad,
    TransicionInvalida,
    UrgenciaIncompleta,
)
from src.domain.reglas_clinicas import Agenda, Cita, solo_digitos, verificar_alergias
from src.domain.specifications import (
    ActorActivo,
    ActorPreferente,
    PromocionActiva,
    TieneDetalle,
    TotalMinimo,
    beneficio_referencia,
    puede_procesarse,
)
from src.domain.state_machine import siguiente_estado
from src.domain.value_objects import Dinero, Estado


def _op(preferente=True, activo=True, autorizado=True, promo=False, lineas=None):
    actor = Actor("A1", "Tutor", es_preferente=preferente, activo=activo)
    if lineas is None:
        lineas = [Linea("R1", 3, Dinero(Decimal("500.00")))]
    return Operacion("O1", actor, date(2026, 11, 6), lineas, promocion_activa=promo,
                     autorizado=autorizado)


# ---- Dinero / total con Decimal ---------------------------------------------
def test_total_usa_decimal_sin_error_de_float():
    op = _op(lineas=[Linea("R1", 3, Dinero(Decimal("0.10"))), Linea("R2", 1, Dinero(Decimal("0.20")))])
    assert op.total.monto == Decimal("0.50")


def test_dinero_redondea_y_rechaza_negativos():
    assert str(Dinero("10.005")) == "10.01"
    with pytest.raises(DatoInvalido):
        Dinero("-1")


def test_linea_exige_cantidad_positiva():
    with pytest.raises(DatoInvalido, match="mayor a cero"):
        Linea("R1", 0, Dinero(1))


# ---- Specifications ---------------------------------------------------------
def test_puede_procesarse_cumple_las_tres_condiciones():
    assert puede_procesarse.es_satisfecha_por(_op())


@pytest.mark.parametrize(("kw", "texto"), [
    ({"activo": False}, "inactivo"),
    ({"autorizado": False}, "autorización"),
    ({"lineas": []}, "ningún servicio"),
])
def test_puede_procesarse_explica_por_que_no(kw, texto):
    op = _op(**kw)
    assert not puede_procesarse.es_satisfecha_por(op)
    assert any(texto in m for m in puede_procesarse.explicar(op))


def test_beneficio_exige_preferente_total_y_sin_promocion():
    assert beneficio_referencia.es_satisfecha_por(_op())  # total 1500 exacto
    assert not beneficio_referencia.es_satisfecha_por(_op(preferente=False))
    assert not beneficio_referencia.es_satisfecha_por(_op(promo=True))
    assert not beneficio_referencia.es_satisfecha_por(
        _op(lineas=[Linea("R1", 1, Dinero(Decimal("1499.99")))]))


def test_limite_exacto_de_1500_si_aplica_y_un_centavo_menos_no():
    assert TotalMinimo().es_satisfecha_por(_op(lineas=[Linea("R", 1, Dinero(Decimal("1500.00")))]))
    assert not TotalMinimo().es_satisfecha_por(_op(lineas=[Linea("R", 1, Dinero(Decimal("1499.99")))]))


def test_combinaciones_or_y_not():
    op = _op(preferente=False)
    assert (ActorPreferente() | TieneDetalle()).es_satisfecha_por(op)
    assert not (ActorPreferente() | PromocionActiva()).es_satisfecha_por(op)
    assert (~PromocionActiva()).es_satisfecha_por(op)
    assert (ActorActivo() & ~PromocionActiva()).explicar(op) == []
    assert "excluyente" in (~TieneDetalle()).explicar(op)[0]
    assert len((ActorPreferente() | PromocionActiva()).explicar(op)) == 2


# ---- Máquina de estados -----------------------------------------------------
def test_flujo_completo_y_eventos():
    op = _op()
    op.confirmar()
    op.realizar()
    assert op.estado == Estado.REALIZADA
    assert [type(e) for e in op.eventos] == [events.OperacionConfirmada, events.OperacionRealizada]
    assert op.eventos[0].nombre == "OperacionConfirmada"


@pytest.mark.parametrize(("estado", "accion"), [
    (Estado.SOLICITADA, "realizar"), (Estado.CONFIRMADA, "confirmar"),
    (Estado.REALIZADA, "cancelar"), (Estado.CANCELADA, "confirmar"),
    (Estado.CANCELADA, "cancelar"), (Estado.REALIZADA, "realizar"),
])
def test_transiciones_invalidas(estado, accion):
    with pytest.raises(TransicionInvalida):
        siguiente_estado(estado, accion)


def test_cancelar_desde_solicitada_y_confirmada():
    a = _op(); a.cancelar()
    b = _op(); b.confirmar(); b.cancelar()
    assert a.estado == b.estado == Estado.CANCELADA


def test_transicion_invalida_no_cambia_estado_ni_emite_evento():
    op = _op()
    with pytest.raises(TransicionInvalida, match="SOLICITADA"):
        op.realizar()
    assert op.estado == Estado.SOLICITADA and op.eventos == []


# ---- Recurso (capacidad) ----------------------------------------------------
def test_recurso_reserva_y_libera():
    r = Recurso("R", "Consulta", Dinero(100), 5)
    r.reservar(5)
    assert r.capacidad == 0
    with pytest.raises(SinDisponibilidad, match="Consulta"):
        r.reservar(1)
    r.liberar(2)
    assert r.capacidad == 2


# ---- US-11 alergias ---------------------------------------------------------
def test_alergia_bloquea_y_confirma_con_veterinario():
    assert verificar_alergias("Luna", ["x"], ["y"], "M") == (False, None)
    with pytest.raises(AlergiaDetectada, match="alérgica a penicilina"):
        verificar_alergias("Luna", ["Penicilina"], ["penicilina"], "Penicilina G")
    assert verificar_alergias("Luna", ["penicilina"], ["PENICILINA "], "P", True, "Dra. Ruiz") == (True, "Dra. Ruiz")
    with pytest.raises(DatoInvalido, match="veterinario"):
        verificar_alergias("Luna", ["penicilina"], ["penicilina"], "P", True)


# ---- US-06 urgencias --------------------------------------------------------
CIERRE = datetime(2026, 11, 6, 20, 0)
AHORA = datetime(2026, 11, 6, 10, 10)


def _agenda(fin=datetime(2026, 11, 6, 11, 30), des=timedelta(minutes=20)):
    return Agenda([
        Cita(1, 1, datetime(2026, 11, 6, 10, 0), datetime(2026, 11, 6, 10, 30)),
        Cita(2, 2, datetime(2026, 11, 6, 10, 30), datetime(2026, 11, 6, 11, 0)),
        Cita(3, 3, datetime(2026, 11, 6, 11, 0), fin)], CIERRE, des)


def test_urgencia_pausa_y_recorre():
    a = _agenda()
    assert a.registrar_urgencia(9, " Atropello ", AHORA) == "Atropello"
    assert a.citas[0].estado == "PAUSADA"
    assert a.citas[1].inicio == datetime(2026, 11, 6, 10, 50)


@pytest.mark.parametrize(("mid", "motivo"), [(None, "x"), (9, "  ")])
def test_urgencia_incompleta(mid, motivo):
    with pytest.raises(UrgenciaIncompleta):
        _agenda().registrar_urgencia(mid, motivo, AHORA)


def test_urgencia_limite_de_cierre():
    _agenda(fin=datetime(2026, 11, 6, 19, 40)).registrar_urgencia(9, "x", AHORA)
    with pytest.raises(AgendaExcedeCierre, match="20:01"):
        _agenda(fin=datetime(2026, 11, 6, 19, 41)).registrar_urgencia(9, "x", AHORA)


def test_solo_digitos():
    assert solo_digitos("(81) 1234-5678") == "8112345678"
    assert solo_digitos(None) == ""
