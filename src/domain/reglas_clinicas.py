"""Reglas clínicas del equipo (BRD/US): alergias (US-11), urgencias (US-06)
y duplicados (US-13)."""

from dataclasses import dataclass
from datetime import datetime, timedelta

from src.domain.errors import (
    AgendaExcedeCierre,
    AlergiaDetectada,
    DatoInvalido,
    UrgenciaIncompleta,
)


def normalizar(texto: str) -> str:
    return texto.strip().casefold()


def solo_digitos(texto) -> str:
    return "".join(ch for ch in (texto or "") if ch.isdigit())


# --- US-11: bloqueo farmacológico por alergias -----------------------------
def verificar_alergias(mascota_nombre, alergias, sustancias, medicamento,
                       confirmar=False, veterinario=None):
    """Devuelve (con_alerta, autorizada_por) o lanza AlergiaDetectada."""
    conflicto = {normalizar(a) for a in alergias} & {normalizar(s) for s in sustancias}
    if not conflicto:
        return False, None
    if not confirmar:
        raise AlergiaDetectada(
            f"{mascota_nombre} es alérgica a {', '.join(sorted(conflicto))}. "
            f"No se puede guardar la receta de {medicamento} sin la "
            "confirmación del veterinario"
        )
    if not veterinario:
        raise DatoInvalido(
            "Para confirmar la receta debe indicarse el veterinario que la autoriza"
        )
    return True, veterinario


# --- US-06: urgencia pausa la cita en curso y recorre la agenda ------------
@dataclass
class Cita:
    id: int
    mascota_id: int
    inicio: datetime
    fin: datetime
    estado: str = "PROGRAMADA"


class Agenda:
    def __init__(self, citas, hora_cierre, desplazamiento=timedelta(minutes=20)):
        self.citas = citas
        self.hora_cierre = hora_cierre
        self.desplazamiento = desplazamiento

    def registrar_urgencia(self, mascota_id, motivo, ahora):
        faltantes = []
        if not mascota_id:
            faltantes.append("el identificador de la mascota")
        if not (motivo or "").strip():
            faltantes.append("el motivo de consulta")
        if faltantes:
            raise UrgenciaIncompleta(
                "No se puede activar el modo Urgencia: falta " + " y ".join(faltantes)
            )
        en_curso = [c for c in self.citas if c.inicio <= ahora < c.fin]
        por_mover = [c for c in self.citas if c.inicio > ahora]
        if por_mover:
            ultimo = max(c.fin for c in por_mover) + self.desplazamiento
            if ultimo > self.hora_cierre:
                raise AgendaExcedeCierre(
                    "No se puede recorrer la agenda: la última cita terminaría "
                    f"a las {ultimo:%H:%M}, después del cierre de la clínica "
                    f"({self.hora_cierre:%H:%M})"
                )
        for cita in en_curso:
            cita.estado = "PAUSADA"
        for cita in por_mover:
            cita.inicio += self.desplazamiento
            cita.fin += self.desplazamiento
        return motivo.strip()
