# Glosario (lenguaje ubicuo)

Los 28 términos del equipo (Propietario, Mascota/Paciente, Expediente clínico, Cita, Nota clínica, Diagnóstico, Vacuna,
Refuerzo, Hospitalización, Seguimiento clínico, Emergencia, Estudio clínico, Medicamento indicado, Alergia, Recepción,
Veterinario, Personal clínico, Peso corporal, Historial médico, Alta médica, Requerimiento, Stakeholder, User Story,
Criterio de aceptación, BRD, BPM/BPMN, Validación y trazabilidad, Modelo de dominio) se mantienen. Correspondencia con el código:

| Término del negocio | Paquete de datos | Clase en el código |
|---|---|---|
| Propietario / tutor | `actores.csv` | `Actor` |
| Servicio veterinario (consulta, vacuna, cirugía…) | `catalogo.csv` | `Recurso` |
| Cita (con servicios) | `operaciones.csv` + `detalle_operaciones.csv` | `Operacion` + `Linea` |
| Estado de la cita | `estado_inicial` | `Estado` + máquina de estados |
| Alergia / receta | — | `verificar_alergias`, `RecetaRow` |
| Emergencia | — | `Agenda.registrar_urgencia` |
| Posible duplicado | — | `ExpedienteService`, `PosibleDuplicado` |
