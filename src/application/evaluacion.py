"""Ejecuta los 120 casos y las 20 transiciones del paquete de datos y
devuelve el resultado de cada uno (evidencia del PIA)."""

import csv

from src.application.event_bus import EventBus
from src.application.services import OperacionService
from src.domain.errors import DominioError
from src.domain.specifications import beneficio_referencia, puede_procesarse
from src.infrastructure.database import make_engine, make_session_factory
from src.infrastructure.repositorios import EventoRepo
from src.infrastructure.seed import DATA, cargar_datos


def _csv(nombre):
    with open(DATA / nombre, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def _sesion_nueva():
    engine = make_engine("sqlite:///:memory:")
    s = make_session_factory(engine)()
    cargar_datos(s)
    s.info["engine"] = engine
    return s


def _cerrar(s):
    engine = s.info["engine"]
    s.close()
    engine.dispose()


def evaluar_casos():
    s = _sesion_nueva()
    svc = OperacionService(s)
    filas = []
    for c in _csv("casos_prueba.csv"):
        op = svc.operaciones.obtener(c["operacion_id"])
        if c["tipo_prueba"] == "validar_operacion":
            ok = puede_procesarse.es_satisfecha_por(op)
            res, det = ("APROBADO" if ok else "RECHAZADO"), "; ".join(puede_procesarse.explicar(op))
        else:
            ok = beneficio_referencia.es_satisfecha_por(op)
            res, det = ("CON_BENEFICIO" if ok else "SIN_BENEFICIO"), "; ".join(beneficio_referencia.explicar(op))
        filas.append({"caso_id": c["caso_id"], "operacion_id": op.id, "tipo_prueba": c["tipo_prueba"],
                      "total_mxn": str(op.total), "resultado": res, "detalle": det})
    _cerrar(s)
    return filas


def evaluar_transiciones():
    filas = []
    for t in _csv("transiciones_prueba.csv"):
        s = _sesion_nueva()  # base limpia por caso: no se contaminan entre sí
        bus = EventBus()
        svc = OperacionService(s, bus)
        accion = t["accion_sugerida"]
        pasos = {"aprobar": ["confirmar"], "completar": ["realizar"], "cancelar": ["cancelar"],
                 "repetir_aprobacion": ["confirmar", "confirmar"],
                 "saltar_estado": ["realizar"]}[accion]
        resultado, detalle = "OK", ""
        try:
            for p in pasos:
                getattr(svc, p)(t["operacion_id"])
        except DominioError as e:
            resultado, detalle = f"RECHAZADA ({type(e).__name__})", str(e)
        estado = svc.operaciones.obtener(t["operacion_id"]).estado.value
        eventos = ",".join(e.nombre for e in EventoRepo(s).de_operacion(t["operacion_id"]))
        filas.append({"caso_id": t["caso_id"], "operacion_id": t["operacion_id"], "accion": accion,
                      "estado_inicial": t["estado_inicial"], "estado_final": estado,
                      "resultado": resultado, "evento": eventos, "detalle": detalle})
        _cerrar(s)
    return filas


def guardar(filas, ruta):
    with open(ruta, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
