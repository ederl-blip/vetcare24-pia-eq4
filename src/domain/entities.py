"""Entidades y agregado Operacion (cita/servicio veterinario)."""

from dataclasses import dataclass, field
from datetime import date

from src.domain import events
from src.domain.errors import DatoInvalido, SinDisponibilidad
from src.domain.state_machine import siguiente_estado
from src.domain.value_objects import Dinero, Estado


@dataclass
class Actor:
    """Tutor (propietario). Identidad: actor_id."""

    id: str
    nombre: str
    es_preferente: bool = False
    activo: bool = True
    ciudad: str = ""
    telefono: str = ""
    correo: str | None = None


@dataclass
class Recurso:
    """Servicio del catálogo con capacidad limitada."""

    id: str
    descripcion: str
    precio: Dinero
    capacidad: int
    habilitado: bool = True

    def reservar(self, cantidad: int):
        if cantidad > self.capacidad:
            raise SinDisponibilidad(
                f"No hay lugares suficientes para «{self.descripcion}»: "
                f"se piden {cantidad} y quedan {self.capacidad}"
            )
        self.capacidad -= cantidad

    def liberar(self, cantidad: int):
        self.capacidad += cantidad


@dataclass(frozen=True)
class Linea:
    recurso_id: str
    cantidad: int
    precio_unitario: Dinero

    def __post_init__(self):
        if self.cantidad <= 0:
            raise DatoInvalido("La cantidad de cada servicio debe ser mayor a cero")

    @property
    def subtotal(self):
        return self.precio_unitario.por(self.cantidad)


@dataclass
class Operacion:
    """Raíz del agregado: protege sus invariantes y emite eventos."""

    id: str
    actor: Actor
    fecha_solicitud: date
    lineas: list[Linea] = field(default_factory=list)
    estado: Estado = Estado.SOLICITADA
    promocion_activa: bool = False
    autorizado: bool = True
    referencia: str = ""
    eventos: list = field(default_factory=list)

    @property
    def total(self) -> Dinero:
        resultado = Dinero.cero()
        for linea in self.lineas:
            resultado = resultado + linea.subtotal
        return resultado

    def _transitar(self, accion, evento):
        self.estado = siguiente_estado(self.estado, accion)
        self.eventos.append(evento(self.id))

    def confirmar(self):
        self._transitar("confirmar", events.OperacionConfirmada)

    def realizar(self):
        self._transitar("realizar", events.OperacionRealizada)

    def cancelar(self):
        self._transitar("cancelar", events.OperacionCancelada)
