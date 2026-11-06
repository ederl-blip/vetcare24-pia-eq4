"""Tablas SQLAlchemy (persistencia). El dominio no conoce estas clases."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database import Base


class ActorRow(Base):
    __tablename__ = "actores"
    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    es_preferente: Mapped[bool] = mapped_column(Boolean, default=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    ciudad: Mapped[str] = mapped_column(String(60), default="")
    telefono: Mapped[str] = mapped_column(String(20), default="", index=True)
    correo: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)


class RecursoRow(Base):
    __tablename__ = "recursos"
    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    descripcion: Mapped[str] = mapped_column(String(120))
    precio: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    capacidad: Mapped[int]
    habilitado: Mapped[bool] = mapped_column(Boolean, default=True)


class OperacionRow(Base):
    __tablename__ = "operaciones"
    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    actor_id: Mapped[str] = mapped_column(ForeignKey("actores.id"), index=True)
    estado: Mapped[str] = mapped_column(String(20), index=True)
    fecha_solicitud: Mapped[date] = mapped_column(Date)
    promocion_activa: Mapped[bool] = mapped_column(Boolean, default=False)
    autorizado: Mapped[bool] = mapped_column(Boolean, default=True)
    referencia: Mapped[str] = mapped_column(String(40), default="")
    lineas: Mapped[list["LineaRow"]] = relationship(
        cascade="all, delete-orphan", order_by="LineaRow.id", lazy="selectin"
    )


class LineaRow(Base):
    __tablename__ = "lineas_operacion"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    operacion_id: Mapped[str] = mapped_column(ForeignKey("operaciones.id"), index=True)
    recurso_id: Mapped[str] = mapped_column(ForeignKey("recursos.id"))
    cantidad: Mapped[int]
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2))


class EventoRow(Base):
    __tablename__ = "eventos_dominio"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(60))
    operacion_id: Mapped[str] = mapped_column(String(20), index=True)
    ocurrido: Mapped[datetime] = mapped_column(DateTime)


class MascotaRow(Base):
    __tablename__ = "mascotas"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(80))
    propietario_id: Mapped[str] = mapped_column(ForeignKey("actores.id"))
    alergias: Mapped[str] = mapped_column(Text, default="")  # separadas por coma


class RecetaRow(Base):
    __tablename__ = "recetas"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    mascota_id: Mapped[int] = mapped_column(ForeignKey("mascotas.id"))
    medicamento: Mapped[str] = mapped_column(String(120))
    con_alerta: Mapped[bool] = mapped_column(Boolean, default=False)
    autorizada_por: Mapped[str | None] = mapped_column(String(120), nullable=True)
