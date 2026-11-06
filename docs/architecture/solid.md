# Revisión SOLID

| Principio | Evidencia en el código |
|---|---|
| S | `Operacion` solo protege su estado; `OperacionService` solo orquesta; los repositorios solo persisten |
| O | Se agrega una regla nueva con otra `Specification` sin editar las anteriores |
| L | Cualquier `Specification` puede usarse donde se espera una (`&`, `\|`, `~` devuelven `Specification`) |
| I | Un repositorio por agregado (`ActorRepo`, `RecursoRepo`, `OperacionRepo`, `EventoRepo`) |
| D | El dominio no depende de SQLAlchemy ni FastAPI; los servicios reciben la sesión y el bus desde afuera |
