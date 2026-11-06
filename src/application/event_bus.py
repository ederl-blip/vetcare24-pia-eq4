"""Bus de eventos en memoria: quien se suscribe reacciona a los eventos de dominio."""

from collections import defaultdict


class EventBus:
    def __init__(self):
        self._handlers = defaultdict(list)

    def suscribir(self, tipo_evento, handler):
        self._handlers[tipo_evento].append(handler)

    def publicar(self, evento):
        for handler in self._handlers[type(evento)]:
            handler(evento)
