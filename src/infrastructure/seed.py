"""Carga de los datos oficiales del paquete (CSV) a la base de datos."""

import csv
from datetime import date
from decimal import Decimal
from pathlib import Path

from sqlalchemy import func, select

from src.infrastructure import models as m

DATA = Path(__file__).resolve().parents[2] / "data"


def _leer(nombre):
    with open(DATA / nombre, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def cargar_datos(session) -> bool:
    """Carga los CSV solo si la base está vacía. Devuelve True si cargó."""
    if session.scalar(select(func.count()).select_from(m.ActorRow)):
        return False
    for r in _leer("actores.csv"):
        session.add(m.ActorRow(id=r["actor_id"], nombre=r["nombre"], ciudad=r["ciudad"],
                               es_preferente=r["es_preferente"] == "1", activo=r["activo"] == "1"))
    precios = {}
    for r in _leer("catalogo.csv"):
        precios[r["recurso_id"]] = Decimal(r["precio_mxn"])
        session.add(m.RecursoRow(id=r["recurso_id"], descripcion=r["descripcion"],
                                 precio=precios[r["recurso_id"]],
                                 capacidad=int(r["capacidad_o_stock"]),
                                 habilitado=r["habilitado"] == "1"))
    lineas = {}
    for r in _leer("detalle_operaciones.csv"):
        lineas.setdefault(r["operacion_id"], []).append(
            m.LineaRow(recurso_id=r["recurso_id"], cantidad=int(r["cantidad"]),
                       precio_unitario=precios[r["recurso_id"]]))
    for r in _leer("operaciones.csv"):
        session.add(m.OperacionRow(
            id=r["operacion_id"], actor_id=r["actor_id"], estado=r["estado_inicial"],
            fecha_solicitud=date.fromisoformat(r["fecha_solicitud"]),
            promocion_activa=r["promocion_activa"] == "1", autorizado=r["autorizado"] == "1",
            referencia=r["referencia"], lineas=lineas.get(r["operacion_id"], [])))
    session.commit()
    return True
