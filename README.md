# VetCare 24 — PIA Componentes de Lógica de Negocio

API REST para citas y servicios veterinarios de **VetCare 24** (Equipo 4, UANL FIME, prof. Miguel Ángel Gómez Marroquín).

- **Repositorio:** https://github.com/ederl-blip/vetcare24-pia-eq4
- **API en línea (Swagger):** _pendiente: pegar aquí la URL de Render + `/docs`_

## Qué incluye
DDD (agregado `Operacion`, Value Objects `Dinero` y `Estado`), patrón **Specification** (6 reglas combinables con AND/OR/NOT),
**máquina de estados**, **Domain Events**, API **FastAPI** con OpenAPI, base de datos (SQLite local / PostgreSQL),
pruebas con **99 % de cobertura**, **Docker Compose** (DB + App + Tests) y **CI** en GitHub Actions.

## Ejecutar en local (sin Docker)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
copy .env.example .env
python -m uvicorn src.api.main:app --reload
```
Abrir http://127.0.0.1:8000/docs (Swagger). Al iniciar, la base se llena con los CSV oficiales de `data/`.

## Pruebas
```powershell
python -m pytest -v --cov=src --cov-report=term-missing --cov-fail-under=80
python -m ruff check src tests scripts
python scripts/run_evaluacion.py     # resultados de 120 casos y 20 transiciones en docs/evidencia/
```

## Docker Compose
```powershell
docker compose up --build              # PostgreSQL + API en http://localhost:8000/docs
docker compose --profile tests run --rm tests   # pruebas con cobertura
```

## Variables de entorno (ver `.env.example`)
`DATABASE_URL`, `SEED_ON_START`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`. No se guardan secretos en el repositorio.

## Endpoints principales
| Método | Ruta | Descripción | Códigos |
|---|---|---|---|
| POST | `/operaciones` | Solicitar cita | 201, 400, 404, 422 |
| GET | `/operaciones/{id}` | Consultar cita | 200, 404 |
| POST | `/operaciones/{id}/confirmar` | Confirmar (reserva lugares) | 200, 400, 404, 409 |
| POST | `/operaciones/{id}/realizar` | Marcar realizada | 200, 404, 409 |
| POST | `/operaciones/{id}/cancelar` | Cancelar | 200, 404, 409 |
| GET | `/operaciones/{id}/evaluacion` | ¿Puede procesarse? ¿beneficio? | 200, 404 |
| POST | `/tutores` | Registrar tutor (US-13) | 201, 400, 409, 422 |
| POST | `/mascotas/{id}/recetas` | Recetar con bloqueo de alergias (US-11) | 201, 404, 409 |
| POST | `/agenda/urgencias` | Urgencia: pausa y recorre agenda (US-06) | 200, 400, 409 |

## Estructura
```
docs/        BRD.md, historias_usuario.md, glosario.md, trazabilidad.md, diferencias.md,
             architecture/ (ADR, DDD, SOLID, diagramas), api/openapi.json, evidencia/
src/         domain/ application/ infrastructure/ api/
tests/       dominio, integración y API
data/        CSV oficiales del paquete
.github/workflows/ci.yml · docker-compose.yml · Dockerfile · render.yaml · .env.example
```

## Despliegue en Render
1. Crear cuenta en render.com con GitHub.
2. New → Blueprint → elegir este repositorio (usa `render.yaml`).
3. Esperar el despliegue y abrir `https://<tu-servicio>.onrender.com/docs`.

## Alcance y límites
Ver `docs/historias_usuario.md` (historias implementadas) y `docs/diferencias.md` (diferencias con el paquete de datos).
La anticipación de 3 h y la tolerancia de 10 min no se implementaron porque los datos no traen hora de cita.

## Uso de IA
Se usó Claude como apoyo para borradores de código, pruebas y documentación; todo se verificó ejecutando pruebas, Ruff y el CI.
