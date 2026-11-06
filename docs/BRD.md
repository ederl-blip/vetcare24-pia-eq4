# BRD — VetCare 24

**Equipo 4 (UANL FIME):** López Guzmán Eder Abihú (2116464), Rodríguez Lara Alexia Guadalupe (2117441), Lepe Rodríguez Ángel Uriel (2115842).
Fuente: entregable Fundamental 2 (04/09/2026). Este archivo resume el BRD del equipo.

## Contexto
VetCare 24 es una clínica veterinaria con consultas, vacunación, cirugías, laboratorio y hospitalización.
Relación 1:N: un propietario puede tener varias mascotas, cada una con historial independiente.

## Problemas (ISS)
| ID | Problema | Impacto |
|---|---|---|
| ISS-01 | Historial clínico parcialmente en papel | Retrasos y riesgo de perder antecedentes |
| ISS-02 | Recordatorios de vacuna deficientes | Refuerzos no aplicados y pérdida de ingresos |
| ISS-03 | Expedientes duplicados | Información dispersa |
| ISS-04 | Difícil consultar antecedentes | Atención lenta |
| ISS-05 | Riesgo en control de peso y alergias | Reacciones adversas |

## Stakeholders
Propietario, Mascota (paciente), Recepción, Veterinario, Personal clínico.

## Alcance
Expedientes y perfiles; control de citas y urgencias; módulo clínico (notas, recetas, estudios, vacunas);
hospitalización; notificaciones automáticas.
**Implementado en este PIA:** citas con servicios y ciclo de vida (N-02), urgencias (N-03), alergias (N-01),
duplicados (N-06). Ver `trazabilidad.md` para lo que queda fuera.

## Necesidades
| ID | Necesidad | Prioridad |
|---|---|---|
| N-01 | Unificación de historiales (alergias, peso) | Alta |
| N-02 | Gestión de agenda por tipo de servicio | Alta |
| N-03 | Atención de urgencias (pausar/recorrer agenda) | Muy alta |
| N-04 | Seguimiento automatizado de vacunas | Media |
| N-05 | Control de hospitalización | Alta |
| N-06 | Validación de identidad (evitar duplicados) | Alta |

## Restricciones
| ID | Restricción |
|---|---|
| CON-01 | Registro en recepción en menos de 2 minutos |
| CON-02 | Expediente carga en menos de 10 s en una emergencia |
| CON-03 | Solo el Veterinario crea, edita o firma notas y diagnósticos |
| CON-04 | Datos protegidos según normativa de datos personales |
| CON-05 | Operar con internet comercial estándar |

## Supuestos
ASM-01 conexión estable y equipos; ASM-02 propietarios con celular activo; ASM-03 el personal acepta el sistema.

## Reglas de negocio del levantamiento
Tolerancia de 10 min; cancelar o modificar con mínimo 3 h de anticipación; urgencias recorren la agenda 15–20 min;
recordatorio de refuerzo 3 días antes; más de 15 días vencido reinicia el esquema; duplicados se buscan por teléfono o correo.

## Criterios de éxito
SCR-01 0 % de duplicados; SCR-02 +30 % de asistencia a refuerzos; SCR-03 expediente en menos de 10 s;
SCR-04 −25 % de espera en sala.
