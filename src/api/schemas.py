"""Esquemas de entrada/salida de la API (aparecen en Swagger)."""

from datetime import date, datetime

from pydantic import BaseModel, Field


class LineaIn(BaseModel):
    recurso_id: str = Field(examples=["VET-P001"])
    cantidad: int = Field(gt=0, examples=[2], description="Debe ser mayor a cero")


class OperacionIn(BaseModel):
    actor_id: str = Field(examples=["VET-C001"])
    lineas: list[LineaIn] = Field(min_length=1)
    promocion_activa: bool = False
    autorizado: bool = True
    referencia: str = ""
    fecha_solicitud: date | None = None


class LineaOut(BaseModel):
    recurso_id: str
    cantidad: int
    precio_unitario_mxn: str
    subtotal_mxn: str


class OperacionOut(BaseModel):
    id: str
    actor_id: str
    estado: str
    fecha_solicitud: date
    total_mxn: str
    lineas: list[LineaOut]


class TutorIn(BaseModel):
    nombre: str = Field(min_length=1, examples=["Ana Torres"])
    telefono: str = Field(default="", examples=["81 1234 5678"])
    correo: str | None = Field(default=None, examples=["ana@correo.com"])
    ciudad: str = ""
    confirmar_distinta_persona: bool = False


class TutorOut(BaseModel):
    id: str
    nombre: str
    telefono: str
    correo: str | None
    ciudad: str


class MascotaIn(BaseModel):
    nombre: str = Field(min_length=1, examples=["Luna"])
    propietario_id: str = Field(examples=["VET-C001"])
    alergias: list[str] = Field(default_factory=list, examples=[["penicilina"]])


class MascotaOut(BaseModel):
    id: int
    nombre: str
    propietario_id: str
    alergias: list[str]


class RecetaIn(BaseModel):
    medicamento: str = Field(examples=["Penicilina G"])
    sustancias: list[str] = Field(examples=[["penicilina"]])
    confirmar_conscientemente: bool = False
    veterinario: str | None = None


class RecetaOut(BaseModel):
    id: int
    mascota_id: int
    medicamento: str
    con_alerta: bool
    autorizada_por: str | None


class CitaIn(BaseModel):
    id: int
    mascota_id: int
    inicio: datetime
    fin: datetime


class UrgenciaIn(BaseModel):
    mascota_id: int | None = None
    motivo: str = ""
    ahora: datetime
    hora_cierre: datetime
    desplazamiento_minutos: int = Field(default=20, ge=15, le=20)
    citas: list[CitaIn] = Field(default_factory=list)


class EventoOut(BaseModel):
    nombre: str
    ocurrido: datetime
