"""Máquina de estados de la operación (cita/servicio veterinario).

SOLICITADA --confirmar--> CONFIRMADA --realizar--> REALIZADA
SOLICITADA/CONFIRMADA --cancelar--> CANCELADA
Cualquier otra combinación es una transición inválida.
"""

from src.domain.errors import TransicionInvalida
from src.domain.value_objects import Estado

TRANSICIONES = {
    (Estado.SOLICITADA, "confirmar"): Estado.CONFIRMADA,
    (Estado.CONFIRMADA, "realizar"): Estado.REALIZADA,
    (Estado.SOLICITADA, "cancelar"): Estado.CANCELADA,
    (Estado.CONFIRMADA, "cancelar"): Estado.CANCELADA,
}

_VERBO = {"confirmar": "confirmar", "realizar": "marcar como realizada", "cancelar": "cancelar"}


def siguiente_estado(actual: Estado, accion: str) -> Estado:
    try:
        return TRANSICIONES[(actual, accion)]
    except KeyError:
        raise TransicionInvalida(
            f"No se puede {_VERBO.get(accion, accion)} una cita que está "
            f"en estado {actual.value}"
        ) from None
