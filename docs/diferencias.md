# Diferencias entre el paquete de datos y los requerimientos del equipo

El paquete de datos propone un modelo de pruebas (no vinculante). Estas son las diferencias y cómo se resolvieron.

| Tema | Paquete de datos | Requerimiento del equipo | Decisión |
|---|---|---|---|
| Estados | SOLICITADA→CONFIRMADA→REALIZADA→CANCELADA | Cita PROGRAMADA/PAUSADA (U3), cancelación hasta 3 h antes | Se usan los 4 estados del paquete para las citas; PAUSADA se usa en la agenda de urgencias |
| Cancelar una cita REALIZADA | Aparece en el flujo de referencia | Un servicio ya prestado no se cancela | **No se permite** (409): REALIZADA es final |
| Cancelar desde CONFIRMADA | No está claro | Permitido con anticipación | Se permite y se devuelven los lugares reservados |
| Anticipación de 3 h y tolerancia de 10 min | No hay hora de cita en los datos | BRD, preguntas 2 | **No implementado**: los datos solo traen fecha, sin hora |
| Reglas | `puede_procesarse`, `beneficio_referencia` | Alergias (US-11), urgencias (US-06), duplicados (US-13) | Se implementan **ambos** conjuntos de reglas |
| Importes | MXN | Sin precios en el BRD | Se usa `Decimal` y los precios del catálogo |
| Hospitalización, vacunas, notas | No hay datos | US-04, 05, 07, 08, 12, 14, 15 | Quedan diseñadas (U3) pero fuera del código de este PIA |
