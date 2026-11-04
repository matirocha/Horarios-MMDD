# Prototipo 2 — Visualizador web de horarios MMDD (2026 y 2027)

Página web interactiva para revisar dos horarios del colegio:

| Año | Origen |
| :--- | :--- |
| **2026** | Horario **oficial**, leído tal cual de `data/Data 2026/HORARIO CURSOS 2026.xlsx`. |
| **2027** | Horario **generado** por `notebooks/generador_horarios.py` (semilla por defecto: 3). |

Funciona abriendo `index.html` directamente en el navegador, sin instalar nada ni levantar un servidor.

## Cómo abrirla

1. Abre `index.html` con doble clic (Chrome, Edge o Firefox).
2. En el **menú de inicio** elige el año: cada tarjeta muestra la semana de 3° Medio A, los totales
   y el resultado de la auditoría. Al entrar, el año queda en la dirección (`index.html?anio=2027`),
   así que al recargar se vuelve directo a ese horario.
3. Para cambiar de año, usa el botón `2026 · Oficial` / `2027 · Generado` de la barra superior: vuelve
   al menú y, al elegir el otro año, se abre la misma vista (por ejemplo, el mismo curso).

Para regenerar los datos y recargar la página:

```bash
python "Prototipos/Prototipo 2/exportar_datos.py"
```

```bash
python "Prototipos/Prototipo 2/exportar_datos.py" --anio 2027 --seed 7
```

```bash
python "Prototipos/Prototipo 2/exportar_datos.py" --anio 2026
```

Sin `--anio` se exportan los dos años. El script escribe `datos/horarios_<año>.js` (el horario
completo), `datos/resumen_<año>.js` (lo que muestra la tarjeta del menú) y `assets/escudo.png`
(el escudo se toma del Excel oficial 2026).

### Cómo se lee el horario oficial 2026

- La asignatura de cada bloque sale de la grilla de cada curso (se corrigen erratas como `LENGAUJE`).
- *English skills* se reconoce por la sala ELECTIVO 1 de la hoja `SALAS ELECTIVOS` o por el relleno amarillo.
- Las franjas de electivos de 3° y 4° medio, por sus etiquetas (`CHP 3AB`, `LE-QU-EC S. 1`, …).
- El recinto de Ed. Física, por la hoja `GIMNASIOS`.
- El Excel no indica qué docente dicta cada clase: se asignan según la distribución horaria 2026 del
  motor. Por eso la auditoría 2026 muestra choques de docentes donde esa distribución no calza con la grilla.

## Vistas

| Vista | Qué muestra |
| :--- | :--- |
| **Cursos** | Vista simple de la semana de un curso: se elige con el botón *Horario de*, que abre los cursos ordenados por ciclo (un botón A/B por nivel), cada clase muestra la asignatura y sus docentes, cada día indica su hora de salida y los recreos y la colación aparecen rotulados con su horario en los días que corresponden. Los electivos de 3° y 4° medio aparecen con nombres comunes; párvulos muestra sus 2 clases de Ed. Física. El plan de estudios queda plegado al final. |
| **Docentes** | Grilla de los 37 docentes con sus ventanas, carga por día y distribución horaria. |
| **Salas y gimnasios** | Ocupación de los 3 recintos deportivos y las 12 salas, incluidos los bloqueos de pastoral. |
| **Por bloque** | Todo el colegio en un momento de la semana: qué tiene cada curso, docentes sin clase y salas en uso. El botón *Recorrer la semana* avanza bloque a bloque. |
| **Auditoría** | Estado de las restricciones duras, indicadores (bloques asignados y ventanas docentes), horas por docente y mapa de docentes en clase. |

## Uso rápido

- En el menú de inicio, `←` `→` eligen la tarjeta y `Enter` la abre (también `1` = 2026, `2` = 2027); `Esc` vuelve al horario.
- Toca cualquier clase para ver docente(s), sala, horario y las otras sesiones de esa asignatura en la semana; en Cursos esas otras sesiones quedan marcadas en la grilla.
- En Docentes y Salas, pasa el cursor (o toca) un elemento de la leyenda para destacarlo en la grilla.
- La página recuerda el último curso visto.
- Busca cursos, docentes o salas con la barra superior (atajos `/` o `Ctrl + K`).
- Recorre cursos, docentes o salas con las flechas `←` `→` del teclado; `Esc` cierra el detalle.
- En el menú de cursos las flechas mueven la selección, `Enter` abre el curso y `Esc` cierra el menú.
- En el celular la grilla muestra un día a la vez; el detalle aparece desde abajo.
- Botón de tema claro/oscuro.
- En Cursos, Docentes y Salas, **Imprimir** deja el horario de la semana en una sola hoja horizontal
  (con membrete, en tema claro y sin las marcas de "hoy"), y el botón de descarga, junto a él, guarda esa
  misma hoja como PDF de una plana (carta horizontal). El PDF usa html2canvas-pro y jsPDF, que se descargan
  de la CDN al pedir el primero: sin conexión, usa Imprimir y elige *Guardar como PDF*.
- Si el equipo está en horario de clases se marcan el día de hoy y el bloque en curso.

## Modo desarrollador

El botón `</>` de la barra superior activa el modo desarrollador para los dos horarios (se recuerda
entre visitas). Con el modo activo:

- **Auditoría** suma la sección *Función objetivo del horario*: f(x) = 1000 · H(x) calculada sobre la
  grilla con la misma definición que el motor (choques de docentes, asignatura repetida en el día,
  sala English skills y gimnasios), con el desglose por tipo y la lista de violaciones. El horario
  oficial 2026 da f(x) = 33.000 (30 choques de docentes y 3 repeticiones); el 2027, f(x) = 0.
- En **Cursos** y **Docentes**, las clases con conflictos quedan marcadas en rojo y su detalle explica
  qué violación las afecta.
- Aparece la pestaña **Edición**:

| Sección | Qué permite |
| :--- | :--- |
| **Docentes** | Agregar, renombrar, cambiar de departamento y quitar docentes. Al quitar uno se elige quién se queda con sus clases, jefaturas y electivos. Muestra la carga en grilla de cada docente frente a los 42 bloques de la semana. |
| **Asignación** | Por curso, quién dicta cada asignatura (dos docentes en la co-docencia) y el profesor/a jefe; la Orientación sigue a la jefatura. Las horas y jornadas no se editan. |
| **Electivos** | Nombre, sección, docente y sala de cada electivo de las 3 franjas de 3° y 4° medio; agregar o quitar electivos. Avisa si un docente queda en dos electivos de la misma franja o si una sala se repite o tiene bloqueo de pastoral. |
| **Resolver** | Resuelve la instancia editada con el método elegido: construcción voraz, Min-Conflicts, búsqueda tabú, búsqueda local iterada, Min-Conflicts + tabú (con sus parámetros) o el modelo matemático (CP-SAT, HiGHS, SCIP o CBC). Muestra f(x) inicial y final, tiempos por fase, convergencia y la auditoría, y permite **ver el resultado en el visualizador** (solo en esa pestaña del navegador) o descargarlo con el formato de `datos/horarios_<año>.js`. |
| **Comparar** | Ejecuta los métodos elegidos con varias semillas y el mismo presupuesto (el modelo se repite tantas veces como semillas) y compara factibilidad, f(x) inicial y final, tiempo de ejecución (mediana, media ± desviación, hasta factible), pasos, ventanas y % de bloques dobles. Incluye gráficos de tiempos, función objetivo y convergencia, y descarga en CSV. |

La instancia editada se guarda en el navegador (se puede exportar e importar como JSON y volver a la
original con *Restablecer*). Editar no cambia los archivos de `datos/` ni los de `notebooks/`.

### Servidor local del solver

Resolver y Comparar ejecutan el motor Python de `notebooks/horarios` (y OR-Tools para el modelo), así
que necesitan el servidor local. Desde la carpeta del repositorio:

```bash
python "Prototipos/Prototipo 2/servidor.py" --abrir
```

Abre `http://localhost:8765` con la pestaña Edición. También funciona con la página abierta con doble
clic, siempre que el servidor esté corriendo (si el navegador bloquea la conexión, usa la dirección
del servidor). `--puerto 9000` cambia el puerto. El servidor solo acepta conexiones del propio equipo,
aplica la instancia editada sobre `DatosColegio` mientras dura cada resolución y la valida antes
(docentes existentes, co-docencia con dos docentes distintos, un docente por electivo en cada franja).
GUROBI no se ofrece: en algunos equipos OR-Tools cierra el proceso al intentar crearlo.

## Archivos

```text
Prototipo 2/
├── index.html               # Estructura de la página (menú de inicio + plataforma)
├── css/estilos.css          # Diseño (tema claro y oscuro, responsivo, impresión)
├── js/menu.js               # Menú de inicio: elige el año y carga sus datos y app.js
├── js/app.js                # Lógica de las vistas y animaciones
├── js/desarrollador.js      # Modo desarrollador: pestaña Edición, solver, comparación y diagnóstico de f(x)
├── datos/horarios_2026.js   # Horario oficial 2026 (generado, no editar a mano)
├── datos/horarios_2027.js   # Horario generado 2027 (generado, no editar a mano)
├── datos/resumen_<año>.js   # Resumen de cada año para las tarjetas del menú
├── assets/escudo.png        # Escudo del colegio
├── exportar_datos.py        # Lee el Excel 2026, ejecuta el motor (2027) y exporta los datos
└── servidor.py              # Servidor local del modo desarrollador (página + API del solver)
```

Las animaciones usan [GSAP](https://gsap.com) desde cdnjs. Sin conexión a internet la página
funciona igual, pero sin animaciones y con tipografías del sistema en lugar de Archivo y
Atkinson Hyperlegible.
