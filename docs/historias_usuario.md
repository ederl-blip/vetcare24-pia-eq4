# Historias de usuario (equipo) y estado en este PIA

| ID | Rol | Historia (resumen) | Estado en el código |
|---|---|---|---|
| US-01 | Recepción | Registrar mascota con datos esenciales | Parcial: se registra mascota con alergias (`POST /mascotas`) |
| US-02 | Recepción | Vincular varias mascotas a un propietario | Parcial: cada mascota guarda su propietario |
| US-03 | Propietario | Agendar cita por tipo de servicio | **Implementada** (`POST /operaciones`, servicios con precio y lugares) |
| US-04 | Veterinario | Crear nota médica | Diseñada (U3), no implementada |
| US-05 | Personal clínico | Alerta de vacunas por vencer | Diseñada; regla de 3 días probada en Unidad 5 |
| US-06 | Recepción | Atender urgencia sin cita | **Implementada** (`POST /agenda/urgencias`) |
| US-07 | Veterinario | Orden de hospitalización | Diseñada, no implementada |
| US-08 | Veterinario | Consultar historial clínico | Diseñada, no implementada |
| US-09 | Recepción | Reagendar cita | Diseñada, no implementada |
| US-10 | Veterinario | Indicar fármacos y dosis | **Implementada** junto con US-11 (`POST /mascotas/{id}/recetas`) |
| US-11 | Veterinario | Advertencia de alergia al recetar | **Implementada** (bloqueo 409 + confirmación con constancia) |
| US-12 | Veterinario | Solicitar estudios clínicos | Diseñada, no implementada |
| US-13 | Recepción | Verificar duplicados antes del alta | **Implementada** (`POST /tutores`, 409 y confirmación) |
| US-14 | Propietario | Recordatorio de refuerzo | Diseñada; regla probada en Unidad 5 |
| US-15 | Administrativo | Reportes operativos | Diseñada, no implementada |

## Gherkin de las historias implementadas
```gherkin
Escenario: US-03 Reserva con tiempo y precio del servicio
  Given el tutor está activo y el servicio está habilitado
  When solicita una cita con uno o más servicios
  Then el sistema crea la cita en estado SOLICITADA con el total calculado

Escenario: US-06 Urgencia recorre la agenda
  Given hay una cita en curso y citas posteriores
  When Recepción registra una urgencia con mascota y motivo
  Then la cita en curso queda PAUSADA y las siguientes se recorren 20 minutos

Escenario: US-06 La agenda excedería el cierre
  Given la última cita terminaría después del cierre al recorrerla
  When Recepción registra la urgencia
  Then el sistema rechaza el recorrido y no modifica la agenda

Escenario: US-11 Alergia detectada
  Given la mascota es alérgica a una sustancia del medicamento
  When el veterinario intenta recetarlo sin confirmar
  Then el sistema bloquea la receta con un mensaje claro

Escenario: US-11 Confirmación consciente
  Given se mostró la alerta de alergia
  When el veterinario confirma indicando su nombre
  Then la receta se guarda con constancia de quién la autorizó

Escenario: US-13 Duplicado detectado
  Given existe un expediente activo con el mismo teléfono o correo
  When Recepción intenta registrar al tutor
  Then el sistema lo detiene y muestra el expediente existente

Escenario: US-13 Distinta persona confirmada
  Given el sistema avisó de una posible coincidencia
  When Recepción confirma que es otra persona
  Then se crea un expediente independiente
```
