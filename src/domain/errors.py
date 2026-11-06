"""Errores de negocio. Cada uno se traduce a un código HTTP en la capa API."""


class DominioError(Exception):
    """Base de los errores de negocio."""


class EntidadNoEncontrada(DominioError):  # 404
    pass


class DatoInvalido(DominioError):  # 400
    pass


class OperacionNoProcesable(DominioError):  # 400
    pass


class TransicionInvalida(DominioError):  # 409
    pass


class SinDisponibilidad(DominioError):  # 409
    pass


class PosibleDuplicado(DominioError):  # 409 (US-13)
    pass


class AlergiaDetectada(DominioError):  # 409 (US-11)
    pass


class UrgenciaIncompleta(DominioError):  # 400 (US-06)
    pass


class AgendaExcedeCierre(DominioError):  # 409 (US-06)
    pass
