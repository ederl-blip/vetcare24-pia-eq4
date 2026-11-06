# Architecture Decision Records

| ADR | Decisión | Alternativas descartadas | Consecuencia |
|---|---|---|---|
| 001 | **Domain Model** como patrón de lógica de negocio (U3) | Transaction Script (duplica reglas), Table Module (acopla a tablas) | Reglas dentro de entidades; más esfuerzo inicial |
| 002 | **Agregados separados** (Operación, Mascota, Agenda) que se referencian por identificador (U3) | Un agregado gigante | Menos bloqueos y consistencia por agregado |
| 003 | **Alergia: bloqueo estricto** con confirmación consciente del veterinario y constancia (U3 ADR-001) | Solo advertir | Se protege la salud; queda registro de quién autorizó |
| 004 | **Duplicados: advertencia no bloqueante**; con confirmación se crea el expediente (U3, BRD) | Bloqueo total | Familiares con el mismo teléfono pueden registrarse |
| 005 | **Patrón Specification** (AND/OR/NOT) para reglas combinables | `if` anidados | Reglas reutilizables y con motivos legibles para el cliente |
| 006 | **FastAPI + SQLAlchemy**; SQLite local, PostgreSQL en Docker/Render | Django, SQL a mano | OpenAPI automático; mismo código en ambas bases |
| 007 | **Decimal** para todo importe | `float` | Sin errores de redondeo en totales |
| 008 | **Errores de dominio → códigos HTTP** en un solo lugar (404/400/409/422) y mensajes en español claro | Mensajes técnicos | El cliente entiende el rechazo (lección de la Actividad 4) |
