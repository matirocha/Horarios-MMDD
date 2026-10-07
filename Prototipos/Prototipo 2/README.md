# Prototipo 2 — Visualizador web de horarios MMDD 2026

Página web interactiva para revisar los horarios que genera `notebooks/generador_horarios.py`
(semilla por defecto: 3). Funciona abriendo `index.html` directamente en el navegador, sin
instalar nada ni levantar un servidor.

## Cómo abrirla

1. Abre `index.html` con doble clic (Chrome, Edge o Firefox).
2. Para cargar un horario nuevo, regenera los datos y recarga la página:

```bash
python "Prototipos/Prototipo 2/exportar_datos.py"
```

```bash
python "Prototipos/Prototipo 2/exportar_datos.py" --seed 7
```

El script ejecuta el motor, audita el resultado y escribe `datos/horarios.js` y `assets/escudo.png`
(el escudo se toma del Excel oficial 2026).

## Vistas

| Vista | Qué muestra |
| :--- | :--- |
| **Cursos** | Vista simple de la semana de un curso: se elige con el botón *Horario de*, que abre los cursos ordenados por ciclo (un botón A/B por nivel), cada clase muestra la asignatura y sus docentes, cada día indica su hora de salida y los recreos y la colación aparecen rotulados con su horario en los días que corresponden. Los electivos de 3° y 4° medio aparecen con nombres comunes; párvulos muestra sus 2 clases de Ed. Física. El plan de estudios queda plegado al final. |
| **Docentes** | Grilla de los 37 docentes con sus ventanas, carga por día y distribución horaria. |
| **Salas y gimnasios** | Ocupación de los 3 recintos deportivos y las 12 salas, incluidos los bloqueos de pastoral. |
| **Por bloque** | Todo el colegio en un momento de la semana: qué tiene cada curso, docentes sin clase y salas en uso. El botón *Recorrer la semana* avanza bloque a bloque. |
| **Auditoría** | Estado de las restricciones duras, indicadores (bloques dobles, ventanas, uso del patio), horas por docente y mapa de docentes en clase. |

## Uso rápido

- Toca cualquier clase para ver docente(s), sala, horario y las otras sesiones de esa asignatura en la semana; en Cursos esas otras sesiones quedan marcadas en la grilla.
- En Docentes y Salas, pasa el cursor (o toca) un elemento de la leyenda para destacarlo en la grilla.
- La página recuerda el último curso visto.
- Busca cursos, docentes o salas con la barra superior (atajos `/` o `Ctrl + K`).
- Recorre cursos, docentes o salas con las flechas `←` `→` del teclado; `Esc` cierra el detalle.
- En el menú de cursos las flechas mueven la selección, `Enter` abre el curso y `Esc` cierra el menú.
- En el celular la grilla muestra un día a la vez; el detalle aparece desde abajo.
- Botón de tema claro/oscuro e impresión de la grilla en horizontal.
- Si el equipo está en horario de clases se marcan el día de hoy y el bloque en curso.

## Archivos

```text
Prototipo 2/
├── index.html          # Estructura de la página
├── css/estilos.css     # Diseño (tema claro y oscuro, responsivo, impresión)
├── js/app.js           # Lógica de las vistas y animaciones
├── datos/horarios.js   # Datos generados (no editar a mano)
├── assets/escudo.png   # Escudo del colegio
└── exportar_datos.py   # Ejecuta el motor y exporta los datos para la web
```

Las animaciones usan [GSAP](https://gsap.com) desde cdnjs. Sin conexión a internet la página
funciona igual, pero sin animaciones y con tipografías del sistema en lugar de Archivo y
Atkinson Hyperlegible.
