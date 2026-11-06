# Matriz de trazabilidad

| Necesidad (BRD) | Historia | Regla / Componente de dominio | Código | Prueba |
|---|---|---|---|---|
| N-02 Gestión de agenda | US-03 | `Operacion`, `Linea`, `Recurso` | `src/domain/entities.py`, `OperacionService.crear` | `test_201_crear_cita`, `test_crear_valida_actor_servicio_y_detalle` |
| N-02 | US-03 | Máquina de estados | `src/domain/state_machine.py` | `test_transiciones_invalidas`, `test_409_transicion_invalida_con_mensaje_claro` |
| N-02 | US-03 | Disponibilidad de lugares | `Recurso.reservar`, `_confirmar` | `test_sin_disponibilidad_hace_rollback_completo` |
| N-02 | US-03 | Specification `puede_procesarse` | `src/domain/specifications.py` | `test_puede_procesarse_explica_por_que_no` |
| N-02 | — | Specification `beneficio_referencia` | `src/domain/specifications.py` | `test_limite_exacto_de_1500_si_aplica_y_un_centavo_menos_no` |
| N-02 | — | Domain Events | `src/domain/events.py`, `EventBus` | `test_flujo_completo_y_eventos`, `test_flujo_confirmar_realizar_con_eventos` |
| N-03 Urgencias | US-06 | `Agenda.registrar_urgencia` | `src/domain/reglas_clinicas.py` | `test_urgencia_limite_de_cierre`, `test_us06_urgencia` |
| N-01 Alergias | US-10, US-11 | `verificar_alergias` | `ClinicaService.prescribir` | `test_alergia_bloquea_y_confirma_con_veterinario`, `test_us11_alergia_bloquea_con_409_y_permite_confirmar` |
| N-06 Duplicados | US-13 | `ExpedienteService` | `src/application/services.py` | `test_duplicados_us13`, `test_us13_tutor_duplicado_409_y_201` |
| Datos oficiales | — | Carga y evaluación de 120 casos + 20 transiciones | `seed.py`, `evaluacion.py` | `test_evaluacion_de_los_120_casos_y_20_transiciones` |
| CON-04 / 12-Factor | — | Configuración por variables de entorno | `database.py`, `.env.example` | `test_database_url_corrige_postgres_y_usa_valor_por_defecto` |
