"""Patrón Specification: reglas de negocio pequeñas que se combinan con
& (AND), | (OR) y ~ (NOT)."""

from decimal import Decimal

from src.domain.value_objects import Dinero


class Specification:
    motivo = "no cumple la regla"

    def es_satisfecha_por(self, candidato) -> bool:
        raise NotImplementedError

    def __and__(self, otra):
        return _And(self, otra)

    def __or__(self, otra):
        return _Or(self, otra)

    def __invert__(self):
        return _Not(self)

    def explicar(self, candidato) -> list[str]:
        """Motivos (en español claro) por los que NO se cumple la regla."""
        return [] if self.es_satisfecha_por(candidato) else [self.motivo]


class _And(Specification):
    def __init__(self, a, b):
        self.a, self.b = a, b

    def es_satisfecha_por(self, c):
        return self.a.es_satisfecha_por(c) and self.b.es_satisfecha_por(c)

    def explicar(self, c):
        return self.a.explicar(c) + self.b.explicar(c)


class _Or(Specification):
    def __init__(self, a, b):
        self.a, self.b = a, b

    def es_satisfecha_por(self, c):
        return self.a.es_satisfecha_por(c) or self.b.es_satisfecha_por(c)

    def explicar(self, c):
        if self.es_satisfecha_por(c):
            return []
        return self.a.explicar(c) + self.b.explicar(c)


class _Not(Specification):
    def __init__(self, a):
        self.a = a
        self.motivo = f"se cumple la condición excluyente ({a.motivo_negado})"

    def es_satisfecha_por(self, c):
        return not self.a.es_satisfecha_por(c)


# --- Specifications del negocio. El candidato es una Operacion. -------------
class ActorActivo(Specification):
    motivo = "el tutor está inactivo"
    motivo_negado = "el tutor está inactivo"

    def es_satisfecha_por(self, op):
        return op.actor.activo


class TieneDetalle(Specification):
    motivo = "la cita no tiene ningún servicio agregado"
    motivo_negado = "la cita tiene servicios"

    def es_satisfecha_por(self, op):
        return len(op.lineas) > 0


class EstaAutorizada(Specification):
    motivo = "la cita no tiene autorización"
    motivo_negado = "la cita está autorizada"

    def es_satisfecha_por(self, op):
        return op.autorizado


class ActorPreferente(Specification):
    motivo = "el tutor no es preferente"
    motivo_negado = "el tutor es preferente"

    def es_satisfecha_por(self, op):
        return op.actor.es_preferente


class TotalMinimo(Specification):
    def __init__(self, minimo=Dinero(Decimal("1500"))):
        self.minimo = minimo
        self.motivo = f"el total es menor a ${minimo} MXN"
        self.motivo_negado = f"el total es de ${minimo} MXN o más"

    def es_satisfecha_por(self, op):
        return op.total >= self.minimo


class PromocionActiva(Specification):
    motivo = "la cita no tiene promoción activa"
    motivo_negado = "la cita ya tiene una promoción activa"

    def es_satisfecha_por(self, op):
        return op.promocion_activa


# Reglas compuestas (BRD: N-02/N-06 y beneficio para clientes preferentes)
puede_procesarse = ActorActivo() & TieneDetalle() & EstaAutorizada()
beneficio_referencia = ActorPreferente() & TotalMinimo() & ~PromocionActiva()
