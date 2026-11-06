"""Eventos de dominio: hechos del negocio que ya ocurrieron."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class EventoDominio:
    operacion_id: str
    ocurrido: datetime = field(default_factory=datetime.now)

    @property
    def nombre(self):
        return type(self).__name__


@dataclass(frozen=True)
class OperacionConfirmada(EventoDominio):
    pass


@dataclass(frozen=True)
class OperacionRealizada(EventoDominio):
    pass


@dataclass(frozen=True)
class OperacionCancelada(EventoDominio):
    pass
