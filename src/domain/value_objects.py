"""Objetos de valor: inmutables y comparables por su contenido."""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum

from src.domain.errors import DatoInvalido

CENTAVO = Decimal("0.01")


@dataclass(frozen=True)
class Dinero:
    """Importe en MXN. Siempre Decimal, nunca float."""

    monto: Decimal

    def __post_init__(self):
        monto = Decimal(str(self.monto)).quantize(CENTAVO, rounding=ROUND_HALF_UP)
        if monto < 0:
            raise DatoInvalido("El importe no puede ser negativo")
        object.__setattr__(self, "monto", monto)

    @classmethod
    def cero(cls):
        return cls(Decimal("0"))

    def __add__(self, otro):
        return Dinero(self.monto + otro.monto)

    def por(self, cantidad: int):
        return Dinero(self.monto * cantidad)

    def __ge__(self, otro):
        return self.monto >= otro.monto

    def __str__(self):
        return f"{self.monto:.2f}"


class Estado(str, Enum):
    SOLICITADA = "SOLICITADA"
    CONFIRMADA = "CONFIRMADA"
    REALIZADA = "REALIZADA"
    CANCELADA = "CANCELADA"
