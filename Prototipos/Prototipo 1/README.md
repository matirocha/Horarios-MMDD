# Prototipo 1 — Visualizador web de horarios

Página web para consultar los horarios que genera `notebooks/generador_horarios.py`.
Funciona abriendo `index.html` con doble clic: no necesita servidor ni librerías.

## Cómo usarla

1. Generar los datos desde esta carpeta:

   ```bash
   python exportar_datos.py                 # semilla 3 (la misma que usa el generador por defecto)
   python exportar_datos.py --seed 7        # otra semilla
   python exportar_datos.py --seed 7 --salida horario_semilla7.js
   ```

   El script ejecuta el motor, audita el resultado y escribe `datos_horarios.js`.
2. Abrir `index.html` en el navegador. Para ver otra corrida sin reemplazar la principal,
   usar el botón **Abrir horario** y elegir el `.js` generado con `--salida`.

Cada vez que cambie el generador, hay que volver a ejecutar `exportar_datos.py`.

## Vistas

| Vista | Qué muestra |
| :--- | :--- |
| **Cursos** | Horario semanal de cada curso (incluye párvulos, que solo tienen Ed. Física), profesor jefe y carga por asignatura. Las franjas de electivos de 3° y 4° medio detallan cada electivo, su docente y su sala. |
| **Docentes** | Horario de cada docente, agrupado por departamento, con horas en la grilla, cursos, ventanas, co-docencias y horas fuera de la grilla. |
| **Vista por día** | Los 27 cursos en una sola tabla para el día elegido. Al pasar el cursor sobre una clase se resalta la jornada de ese docente. |
| **Recintos deportivos** | Uso de Gimnasio A, Gimnasio B y Patio Santo Domingo en cada bloque. |
| **Auditoría** | Resultado de `ValidadorRestricciones`: estado de cada restricción dura, métricas y ventanas por docente. |

## Detalles de uso

- Los bloques dobles (90 min) se muestran unidos, y los bloques fuera de la jornada del curso aparecen rayados.
- Al pasar el cursor sobre una asignatura de la leyenda, se ubican sus bloques en el horario.
- Los nombres de docentes y cursos son enlaces: llevan a su horario.
- Las flechas ← → del teclado recorren los cursos o docentes.
- La dirección de la página (por ejemplo `index.html#/curso/3°%20MEDIO%20A`) apunta a esa vista.
- **Imprimir** genera una hoja horizontal con el horario de la vista actual.
- Tema claro u oscuro, y diseño adaptado a celulares (lista por día).

## Archivos

| Archivo | Descripción |
| :--- | :--- |
| `index.html` | Estructura de la página. |
| `estilos.css` | Estilos (colores del colegio, tema claro/oscuro, celular e impresión). |
| `app.js` | Lógica de las vistas. |
| `exportar_datos.py` | Ejecuta el generador y exporta `datos_horarios.js`. |
| `datos_horarios.js` | Datos del horario generado (no editar a mano). |
