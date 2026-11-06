# Mapa DDD de la implementación

| Elemento | Tipo | Clase |
|---|---|---|
| Operacion (cita con servicios) | Agregado raíz | `src/domain/entities.py` |
| Linea | Entidad interna | `Linea` |
| Actor (tutor) | Entidad | `Actor` |
| Recurso (servicio del catálogo) | Entidad | `Recurso` |
| Dinero, Estado | Value Objects | `src/domain/value_objects.py` |
| ActorActivo, TieneDetalle, EstaAutorizada, ActorPreferente, TotalMinimo, PromocionActiva | Specifications | `src/domain/specifications.py` |
| OperacionConfirmada / Realizada / Cancelada | Domain Events | `src/domain/events.py` |
| Agenda, Cita | Servicio de dominio | `src/domain/reglas_clinicas.py` |
| OperacionService, ExpedienteService, ClinicaService | Servicios de aplicación | `src/application/services.py` |
| Repositorios | Infraestructura | `src/infrastructure/repositorios.py` |
| Rutas FastAPI | API | `src/api/main.py` |

Dependencias: `api → application → domain`; `infrastructure → domain`. El dominio no importa SQLAlchemy ni FastAPI.
