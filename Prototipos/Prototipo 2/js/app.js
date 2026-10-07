/* =============================================================================
   HORARIOS MMDD 2026 — Prototipo 2
   Visualizador de los horarios generados por notebooks/generador_horarios.py.
   Lee window.HORARIOS_MMDD (datos/horarios.js) y dibuja cinco vistas:
   cursos, docentes, salas y gimnasios, colegio por bloque y auditoría.
   Las animaciones usan GSAP cuando está disponible; sin él la página funciona igual.
   ========================================================================== */
(() => {
  'use strict';

  const $ = (sel, raiz = document) => raiz.querySelector(sel);
  const $$ = (sel, raiz = document) => [...raiz.querySelectorAll(sel)];

  const DATOS = window.HORARIOS_MMDD;
  if (!DATOS) {
    $('main').innerHTML = `
      <div class="aviso-datos">
        <h1>Faltan los datos del horario</h1>
        <p class="nota">No se encontró <code>datos/horarios.js</code>. Ejecuta
        <code>python exportar_datos.py</code> dentro de la carpeta <code>Prototipo 2</code> y recarga la página.</p>
      </div>`;
    return;
  }

  // ===========================================================================
  // 1. CATÁLOGOS E ÍNDICES
  // ===========================================================================
  const DIAS = DATOS.dias;
  const DIA_CORTO = { 'Lunes': 'Lun', 'Martes': 'Mar', 'Miércoles': 'Mié', 'Jueves': 'Jue', 'Viernes': 'Vie' };
  const BLOQUE = Object.fromEntries(DATOS.bloques.map(b => [b.numero, b]));
  const PAUSA = Object.fromEntries(DATOS.pausas.map(p => [p.despues, p]));
  const MAX_BLOQUE = DATOS.bloques.length;
  const CURSOS = DATOS.cursos;
  const DOCENTES = DATOS.docentes;
  const ESPACIOS = DATOS.espacios;
  const CICLO = Object.fromEntries(DATOS.ciclos.map(c => [c.id, c.nombre]));

  const clave = (dia, b) => `${dia}|${b}`;
  const cursoPorId = new Map(CURSOS.map(c => [c.id, c]));
  const docentePorNombre = new Map(DOCENTES.map(d => [d.nombre, d]));
  const espacioPorNombre = new Map(ESPACIOS.map(e => [e.nombre, e]));
  const clasesCurso = new Map(CURSOS.map(c => [c.id, new Map(c.clases.map(k => [clave(k.dia, k.bloque), k]))]));
  const clasesDocente = new Map(DOCENTES.map(d => [d.nombre, new Map(d.clases.map(k => [clave(k.dia, k.bloque), k]))]));
  const usosEspacio = new Map(ESPACIOS.map(e => [e.nombre, new Map(e.usos.map(u => [clave(u.dia, u.bloque), u]))]));
  const pastoralEspacio = new Map(ESPACIOS.map(e => [e.nombre, new Set(e.pastoral.map(p => clave(p.dia, p.bloque)))]));

  // Recinto deportivo que usa cada curso en cada bloque de Ed. Física
  const recintoDe = new Map();
  ESPACIOS.filter(e => e.tipo === 'recinto').forEach(e =>
    e.usos.forEach(u => u.items.forEach(it => recintoDe.set(`${it.curso}|${u.dia}|${u.bloque}`, e.nombre))));

  // Nombre visible y familia de color de cada asignatura de la malla
  const ASIGNATURAS = {
    'Lenguaje y Comunicación': ['Lenguaje', 'lenguaje'],
    'Educación Matemática': ['Matemática', 'matematica'],
    'Idioma Extranjero Inglés': ['Inglés', 'ingles'],
    'English Skills': ['English skills', 'ingles'],
    'Ciencias Sociales': ['C. Sociales', 'humanidades'],
    'Historia, Geografía y CC.SS.': ['Historia', 'humanidades'],
    'Educación Ciudadana': ['Ed. Ciudadana', 'humanidades'],
    'Filosofía': ['Filosofía', 'humanidades'],
    'Ciencias Naturales': ['C. Naturales', 'ciencias'],
    'Biología': ['Biología', 'ciencias'],
    'Química': ['Química', 'ciencias'],
    'Física': ['Física', 'ciencias'],
    'Ciencias para la Ciudadanía': ['CC. Ciudadanía', 'ciencias'],
    'Educación Tecnológica': ['Tecnología', 'tecnologia'],
    'Orientación / Tecnología': ['Orientación / Tec.', 'tecnologia'],
    'Artes Visuales': ['Artes', 'artes'],
    'Educación Musical': ['Música', 'artes'],
    'Artes Visuales / Música': ['Artes / Música', 'artes'],
    'Educación Física y Salud': ['Ed. Física', 'edfisica'],
    'Orientación': ['Orientación', 'formacion'],
    'Religión': ['Religión', 'formacion'],
  };

  const DEPARTAMENTOS = {
    'LENGUAJE': 'Lenguaje y Filosofía',
    'MATEMÁTICA': 'Matemática',
    'INGLÉS': 'Inglés',
    'HISTORIA, GEOGRAFÍA Y C. SOCIALES': 'Historia y Ciencias Sociales',
    'CIENCIAS NATURALES': 'Ciencias y Religión',
    'ARTES VISUALES': 'Artes, Tecnología y Música',
    'EDUCACIÓN FÍSICA': 'Educación Física',
    'EDUCACIÓN GENERAL BÁSICA': 'Educación General Básica',
  };

  // Nombre común de cada electivo en la grilla de Cursos (el detalle muestra el nombre oficial)
  const ELECTIVO_CORTO = {
    'COMPRENSIÓN HISTÓRICA DEL PRESENTE': 'Historia del presente',
    'LECTURA Y ESCRITURA ESPECIALIZADA': 'Lectura y escritura',
    'QUÍMICA FORMACIÓN DIFERENCIADA': 'Química',
    'ECONOMÍA Y SOCIEDAD': 'Economía',
    'PROBABILIDADES Y ESTADÍSTICA DESCRIPTIVA': 'Probabilidades',
    'BIOLOGÍA CELULAR Y MOLECULAR': 'Biología celular',
    'DISEÑO Y ARQUITECTURA': 'Diseño y arquitectura',
    'LÍMITES, DERIVADAS E INTEGRALES': 'Cálculo',
    'PARTICIPACIÓN Y ARGUMENTACIÓN EN DEMOCRACIA': 'Argumentación',
    'GEOGRAFÍA, TERRITORIO Y PROBLEMAS SOCIOAMBIENTALES': 'Geografía',
    'BIOLOGÍA DE LOS ECOSISTEMAS': 'Ecosistemas',
    'CIENCIAS PARA LA SALUD': 'Ciencias para la salud',
  };

  const VISTAS = ['cursos', 'docentes', 'salas', 'bloque', 'auditoria'];

  // ===========================================================================
  // 2. UTILIDADES
  // ===========================================================================
  const esc = s => String(s ?? '').replace(/[&<>"']/g, ch =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
  const normalizar = s => String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/°/g, '').toLowerCase();
  const capitalizar = s => s ? s.charAt(0).toUpperCase() + s.slice(1).toLowerCase() : s;
  // Códigos de electivos del Excel ("LECT ESP. S.1", "BIO. ECOS. 4A") en tipo título
  const etiquetaLegible = s => s.toLowerCase()
    .replace(/(^|[\s.(-])(\p{L})/gu, (m, p, c) => p + c.toUpperCase())
    .replace(/\b(\d)(ab|a|b)\b/gi, (m, d, x) => d + x.toUpperCase());
  const numero = n => (n % 1 ? String(n).replace('.', ',') : String(n));
  const minutos = hhmm => { const [h, m] = hhmm.split(':').map(Number); return h * 60 + m; };
  const rango = (b1, b2) => `${BLOQUE[b1].inicio}–${BLOQUE[b2].fin}`;
  const textoBloques = (b1, b2) => (b1 === b2 ? `Bloque ${b1}` : `Bloques ${b1}–${b2}`);
  const departamento = d => DEPARTAMENTOS[d.departamento] || capitalizar(d.departamento);

  function nombreEspacio(n) {
    return n.toLowerCase()
      .replace(/(^|\s)(\S)/g, (m, p, c) => p + c.toUpperCase())
      .replace(/ De /g, ' de ')
      .replace(/(\d°)([ab])$/, (m, a, b) => a + b.toUpperCase());
  }

  function nombreNivel(nivel) {
    if (nivel === 'PREKINDER') return 'Prekínder';
    if (nivel === 'KINDER') return 'Kínder';
    return nivel.replace('BÁSICO', 'Básico').replace('MEDIO', 'Medio');
  }

  function infoAsig(asignatura) {
    if (asignatura.startsWith('Formación Diferenciada')) {
      const k = asignatura.split(' ').pop();
      return { nombre: `Franja ${k} · Electivos`, cat: 'electivo' };
    }
    const a = ASIGNATURAS[asignatura];
    return a ? { nombre: a[0], cat: a[1] } : { nombre: asignatura, cat: 'electivo' };
  }

  // Enlaza los nombres de docentes dentro de un texto "Lenguaje 1 (S.1) / Lenguaje 4 (S.3)"
  const NOMBRES_DOCENTES = DOCENTES.map(d => d.nombre).sort((a, b) => b.length - a.length);
  function enlazarDocentes(texto) {
    if (!texto) return '—';
    return texto.split(' / ').map(parte => {
      const n = NOMBRES_DOCENTES.find(nombre => parte.startsWith(nombre));
      return n
        ? `<button type="button" class="enlace" data-docente="${esc(n)}">${esc(n)}</button>${esc(parte.slice(n.length))}`
        : esc(parte);
    }).join(', ');
  }
  const enlaceDocente = n => `<button type="button" class="enlace" data-docente="${esc(n)}">${esc(n)}</button>`;
  const enlaceCurso = id => `<button type="button" class="enlace" data-curso="${esc(id)}">${esc(cursoPorId.get(id)?.nombre || id)}</button>`;
  const enlaceEspacio = n => (espacioPorNombre.has(n)
    ? `<button type="button" class="enlace" data-espacio="${esc(n)}">${esc(nombreEspacio(n))}</button>`
    : esc(nombreEspacio(n)));

  // Día y bloque en curso según el reloj del equipo (null fuera de la semana escolar)
  function momentoActual() {
    const ahora = new Date();
    const d = ahora.getDay();
    if (d < 1 || d > 5) return null;
    const t = ahora.getHours() * 60 + ahora.getMinutes();
    const bloque = DATOS.bloques.find(b => t >= minutos(b.inicio) && t < minutos(b.fin));
    return { dia: DIAS[d - 1], bloque: bloque ? bloque.numero : null };
  }

  const guardar = (k, v) => { try { localStorage.setItem(k, v); } catch (e) { /* almacenamiento no disponible */ } };
  const leer = k => { try { return localStorage.getItem(k); } catch (e) { return null; } };

  // ===========================================================================
  // 3. ANIMACIONES (GSAP)
  // ===========================================================================
  const movimientoReducido = window.matchMedia('(prefers-reduced-motion: reduce)');
  const G = () => (window.gsap && !movimientoReducido.matches ? window.gsap : null);

  const animar = {
    grilla(grilla) {
      const g = G();
      if (!g || !grilla) return;
      const celdas = $$('.sesion, .vacia', grilla);
      g.fromTo(celdas, { opacity: 0, y: 14, scale: 0.94 }, {
        opacity: 1, y: 0, scale: 1, duration: 0.5, ease: 'back.out(1.5)',
        stagger: (i, el) => (Number(el.dataset.col) - 2) * 0.055 + Number(el.dataset.fila || 0) * 0.02,
        clearProps: 'opacity,transform',
      });
    },
    titulo(raiz) {
      const g = G();
      if (!g || !raiz) return;
      const tl = g.timeline();
      tl.fromTo($$('.cabecera-titulo > *', raiz), { opacity: 0, y: 18 },
        { opacity: 1, y: 0, duration: 0.5, ease: 'power3.out', stagger: 0.06, clearProps: 'opacity,transform' });
      tl.fromTo($$('.leyenda-chip, .estadistica', raiz), { opacity: 0, y: 8 },
        { opacity: 1, y: 0, duration: 0.35, ease: 'power2.out', stagger: 0.025, clearProps: 'opacity,transform' }, 0.15);
    },
    vista(el) {
      const g = G();
      if (!g || !el) return;
      g.fromTo(el, { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.4, ease: 'power2.out', clearProps: 'opacity,transform' });
    },
    detalle(el) {
      const g = G();
      if (!g) return;
      g.fromTo(el.children, { opacity: 0, x: 18 },
        { opacity: 1, x: 0, duration: 0.4, ease: 'power3.out', stagger: 0.05, delay: 0.08, clearProps: 'opacity,transform' });
    },
    contar(el, hasta, sufijo = '') {
      const g = G();
      if (!g || !el) return;
      const o = { v: 0 };
      const decimales = hasta % 1 ? 1 : 0;
      g.to(o, {
        v: hasta, duration: 1.2, ease: 'power2.out',
        onUpdate: () => { el.textContent = o.v.toFixed(decimales).replace('.', ',') + sufijo; },
      });
    },
    barras(els, eje = 'x') {
      const g = G();
      if (!g || !els.length) return;
      const prop = eje === 'x' ? 'scaleX' : 'scaleY';
      g.fromTo(els, { [prop]: 0 }, { [prop]: 1, duration: 0.8, ease: 'power3.out', stagger: 0.012, clearProps: 'transform' });
    },
    aparecer(els, opciones = {}) {
      const g = G();
      if (!g || !els.length) return;
      g.fromTo(els, { opacity: 0, y: opciones.y ?? 10, scale: opciones.scale ?? 1 }, {
        opacity: 1, y: 0, scale: 1, duration: opciones.duracion ?? 0.4, ease: 'power2.out',
        stagger: opciones.stagger ?? 0.02, clearProps: 'opacity,transform',
      });
    },
    intro() {
      const g = G();
      if (!g) return;
      const tl = g.timeline({ defaults: { ease: 'power3.out' } });
      const paso = (sel, desde, hasta, pos) => {
        const els = $$(sel);
        if (els.length) tl.fromTo(els, desde, { clearProps: 'opacity,transform', ...hasta }, pos);
      };
      paso('.marca', { opacity: 0, x: -16 }, { opacity: 1, x: 0, duration: 0.6 }, 0);
      paso('.escudo', { rotate: -12, scale: 0.7 }, { rotate: 0, scale: 1, duration: 0.8, ease: 'back.out(2)' }, 0);
      paso('.buscador, #tema', { opacity: 0, y: -8 }, { opacity: 1, y: 0, duration: 0.5, stagger: 0.08 }, 0.1);
      paso('.pestana', { opacity: 0, y: 8 }, { opacity: 1, y: 0, duration: 0.45, stagger: 0.05 }, 0.15);
      paso('.vista:not([hidden]) .sel-grupo', { opacity: 0, x: -12 }, { opacity: 1, x: 0, duration: 0.4, stagger: 0.04 }, 0.2);
    },
  };

  // ===========================================================================
  // 4. ESTADO Y NAVEGACIÓN
  // ===========================================================================
  const ahoraInicial = momentoActual();
  const estado = {
    vista: 'cursos',
    curso: '3° MEDIO A',
    docente: DOCENTES[0].nombre,
    espacio: ESPACIOS[0].nombre,
    dia: ahoraInicial?.bloque ? ahoraInicial.dia : 'Lunes',
    bloque: ahoraInicial?.bloque || 1,
    diaMovil: ahoraInicial ? ahoraInicial.dia : 'Lunes',
    seleccion: null,       // { dia, inicio } de la celda abierta en el detalle
    resaltado: null,       // clave fijada desde la leyenda
    planAbierto: false,    // plan de estudios desplegado en Cursos
  };

  function hashActual() {
    const e = encodeURIComponent;
    switch (estado.vista) {
      case 'cursos': return `#/cursos/${e(estado.curso)}`;
      case 'docentes': return `#/docentes/${e(estado.docente)}`;
      case 'salas': return `#/salas/${e(estado.espacio)}`;
      case 'bloque': return `#/bloque/${e(estado.dia)}/${estado.bloque}`;
      default: return '#/auditoria';
    }
  }

  function leerHash() {
    const [vista, a, b] = location.hash.replace(/^#\/?/, '').split('/').map(p => { try { return decodeURIComponent(p); } catch (e) { return p; } });
    if (!VISTAS.includes(vista)) return false;
    estado.vista = vista;
    if (vista === 'cursos' && cursoPorId.has(a)) estado.curso = a;
    if (vista === 'docentes' && docentePorNombre.has(a)) estado.docente = a;
    if (vista === 'salas' && espacioPorNombre.has(a)) estado.espacio = a;
    if (vista === 'bloque' && DIAS.includes(a)) {
      estado.dia = a;
      const n = Number(b);
      if (n >= 1 && n <= MAX_BLOQUE) estado.bloque = n;
    }
    return true;
  }

  function escribirHash(reemplazar = false) {
    const h = hashActual();
    if (location.hash === h) return;
    try {
      history[reemplazar ? 'replaceState' : 'pushState'](null, '', h);
    } catch (e) {
      location.replace(h);
    }
  }

  function ir(vista, cambios = {}, opciones = {}) {
    const vistaNueva = vista !== estado.vista;
    Object.assign(estado, cambios, { vista });
    estado.resaltado = null;
    cerrarDetalle();
    if (vista !== 'bloque') detenerReproduccion();
    render({ vistaNueva, animar: opciones.animar !== false });
    escribirHash();
    cerrarSelectores();
    if (opciones.subir !== false) {
      const panel = $(`#vista-${vista}`);
      if (panel && panel.getBoundingClientRect().top < 0) window.scrollTo({ top: 0, behavior: movimientoReducido.matches ? 'auto' : 'smooth' });
    }
  }

  // ===========================================================================
  // 5. GRILLA SEMANAL (componente común a cursos, docentes y salas)
  // ===========================================================================
  /**
   * opciones:
   *   maxBloque           último bloque que se dibuja (8 o 10)
   *   obtener(dia, b)     {tipo:'sesion', ...} | {tipo:'fuera'|'ventana'|'parvulo'|'pastoral'} | null
   *   igual(a, b)         si dos bloques de un par forman una sola sesión doble
   *   celda(pieza, ctx)   HTML de una sesión
   *   subDia(dia)         texto bajo el nombre del día
   *   pausaDia(dia, b)    contenido opcional de la pausa que sigue al bloque b en ese día
   *   simple              vista Cursos: un rótulo por periodo doble y las pausas rotuladas día a día
   *   diaConPausa(dia, b) (vista simple) si ese día muestra la pausa que sigue al bloque b
   */
  function segmentar(dia, op) {
    const piezas = [];
    let b = 1;
    while (b <= op.maxBloque) {
      const v = op.obtener(dia, b);
      if (v && v.tipo === 'sesion' && b % 2 === 1 && b + 1 <= op.maxBloque) {
        const w = op.obtener(dia, b + 1);
        if (w && w.tipo === 'sesion' && op.igual(v, w)) {
          piezas.push({ dia, inicio: b, fin: b + 1, v, v2: w });
          b += 2;
          continue;
        }
      }
      if (v && v.tipo !== 'sesion') {
        // Une celdas vacías contiguas del mismo tipo, sin cruzar un recreo
        let fin = b;
        while (fin + 1 <= op.maxBloque && !PAUSA[fin]) {
          const w = op.obtener(dia, fin + 1);
          if (!w || w.tipo !== v.tipo) break;
          fin += 1;
        }
        piezas.push({ dia, inicio: b, fin, v });
        b = fin + 1;
        continue;
      }
      piezas.push({ dia, inicio: b, fin: b, v });
      b += 1;
    }
    return piezas;
  }

  function grillaHTML(op) {
    const filaBloque = {};
    const filaPausa = {};
    const plantilla = ['auto'];
    let fila = 2;
    for (let b = 1; b <= op.maxBloque; b++) {
      filaBloque[b] = fila++;
      plantilla.push('minmax(3.55rem, auto)');
      if (PAUSA[b] && b < op.maxBloque) {
        filaPausa[b] = fila++;
        // Vista simple (Cursos): la fila crece si el rótulo no cabe en una línea
        plantilla.push(op.simple ? `minmax(${PAUSA[b].nombre === 'COLACIÓN' ? '1.9rem' : '1.5rem'}, auto)` : '1.4rem');
      }
    }
    const hoy = momentoActual();
    const partes = [];

    if (hoy) {
      const c = DIAS.indexOf(hoy.dia) + 2;
      partes.push(`<div class="g-columna-hoy" style="grid-area:1/${c}/${fila}/${c + 1}"></div>`);
    }
    partes.push('<div class="g-esquina" data-col="1"></div>');
    DIAS.forEach((dia, i) => {
      partes.push(`<div class="g-dia${hoy && hoy.dia === dia ? ' es-hoy' : ''}" data-col="${i + 2}" style="grid-area:1/${i + 2}">
        <span class="g-dia-nombre">${dia}</span><span class="g-dia-sub">${esc(op.subDia ? op.subDia(dia) : '')}</span></div>`);
    });

    for (let b = 1; b <= op.maxBloque; b++) {
      if (!op.simple) {
        partes.push(`<div class="g-hora" data-col="1" style="grid-area:${filaBloque[b]}/1">
        <span class="g-hora-num">${b}</span><span class="g-hora-rango">${BLOQUE[b].inicio}–${BLOQUE[b].fin}</span></div>`);
      } else if (b % 2 === 1) {
        // Una etiqueta por periodo doble (los pares nunca cruzan un recreo): inicio arriba, término abajo
        const f = Math.min(b + 1, op.maxBloque);
        partes.push(`<div class="g-hora g-periodo" data-col="1" style="grid-area:${filaBloque[b]}/1/${filaBloque[f] + 1}/2">
        <span>${BLOQUE[b].inicio}</span><span>${BLOQUE[f].fin}</span></div>`);
      }
      if (!filaPausa[b]) continue;
      const p = PAUSA[b];
      const r = filaPausa[b];
      const texto = p.rango.replace(' - ', '–');
      const nombre = p.nombre === 'COLACIÓN' ? 'Colación' : 'Recreo';
      if (op.simple) {
        // Vista simple (Cursos): cada día que sigue con clases rotula su pausa; los días seguidos comparten banda
        const conPausa = DIAS.map(d => (op.diaConPausa ? op.diaConPausa(d, b) : true));
        for (let i = 0; i < DIAS.length; i++) {
          if (!conPausa[i]) continue;
          let j = i;
          while (j + 1 < DIAS.length && conPausa[j + 1]) j++;
          partes.push(`<div class="g-pausa${p.nombre === 'COLACIÓN' ? ' colacion' : ''}" data-col="${i + 2}" data-hasta="${j + 2}" style="grid-area:${r}/${i + 2}/${r + 1}/${j + 3}">
            <span class="g-pausa-texto"><b>${nombre}</b> ${texto}</span></div>`);
          i = j;
        }
        continue;
      }
      partes.push(`<div class="g-pausa-etiqueta" data-col="1" style="grid-area:${r}/1">${nombre}</div>`);
      const porDia = op.pausaDia ? DIAS.map(d => op.pausaDia(d, b)) : [];
      if (porDia.some(Boolean)) {
        DIAS.forEach((d, i) => partes.push(porDia[i]
          ? `<div class="g-pausa-celda vacia pastoral" data-col="${i + 2}" style="grid-area:${r}/${i + 2}">${esc(porDia[i])}</div>`
          : `<div class="g-pausa" data-col="${i + 2}" style="grid-area:${r}/${i + 2}"></div>`));
      } else {
        partes.push(`<div class="g-pausa" data-col="band" style="grid-area:${r}/2/${r + 1}/7">${texto}</div>`);
      }
    }

    DIAS.forEach((dia, i) => {
      const col = i + 2;
      for (const pz of segmentar(dia, op)) {
        const ctx = {
          col,
          fila: filaBloque[pz.inicio],
          area: `${filaBloque[pz.inicio]}/${col}/${filaBloque[pz.fin] + 1}/${col + 1}`,
          ahora: Boolean(hoy && hoy.dia === dia && hoy.bloque && hoy.bloque >= pz.inicio && hoy.bloque <= pz.fin),
        };
        partes.push(pz.v && pz.v.tipo === 'sesion' ? op.celda(pz, ctx) : celdaVacia(pz, ctx, op));
      }
    });

    const diasMovil = DIAS.map(d => `<button type="button" data-dia-movil="${d}" aria-pressed="${d === estado.diaMovil}">${DIA_CORTO[d]}</button>`).join('');
    return `
      <div class="grilla-marco">
        <div class="segmentado dias-movil" role="group" aria-label="Día que se muestra">${diasMovil}</div>
        <div class="grilla" style="grid-template-rows:${plantilla.join(' ')}">${partes.join('')}</div>
      </div>`;
  }

  function celdaVacia(pz, ctx, op) {
    const v = pz.v;
    const base = `data-col="${ctx.col}" data-fila="${ctx.fila}" style="grid-area:${ctx.area}"`;
    if (!v) return `<div class="vacia" ${base}></div>`;
    const texto = op.textoVacio ? op.textoVacio(pz) : '';
    const clases = { fuera: 'fuera', ventana: 'ventana', parvulo: 'parvulo', pastoral: 'pastoral' };
    return `<div class="vacia ${clases[v.tipo] || ''}" ${base}>${esc(texto)}</div>`;
  }

  function sesionHTML({ pz, ctx, cat, titulo, sub, claveResaltado, etiquetaAria, marca, hora }) {
    const doble = pz.fin > pz.inicio;
    // 'hora' permite a Cursos mostrar el horario solo en los bloques sueltos; sin él, igual que siempre
    const textoHora = hora !== undefined ? hora : (doble ? rango(pz.inicio, pz.fin) : '');
    const pie = (textoHora ? `<span class="sesion-hora">${textoHora}</span>` : '')
      + (marca ? `<span class="sesion-marca">${esc(marca)}</span>` : '');
    return `<button type="button" class="sesion cat-${cat}${ctx.ahora ? ' es-ahora' : ''}"
        data-sesion data-dia="${pz.dia}" data-inicio="${pz.inicio}" data-fin="${pz.fin}"
        data-col="${ctx.col}" data-fila="${ctx.fila}" data-clave="${esc(claveResaltado)}"
        style="grid-area:${ctx.area}" aria-label="${esc(etiquetaAria)}">
        <span class="sesion-titulo">${esc(titulo)}</span>
        ${sub ? `<span class="sesion-sub">${esc(sub)}</span>` : ''}
        ${pie ? `<span class="sesion-pie">${pie}</span>` : ''}
      </button>`;
  }

  function prepararGrilla(raiz) {
    const grilla = $('.grilla', raiz);
    if (!grilla) return null;
    aplicarDiaMovil(raiz);
    if (estado.seleccion) {
      const el = $(`.sesion[data-dia="${estado.seleccion.dia}"][data-inicio="${estado.seleccion.inicio}"]`, grilla);
      if (el) el.classList.add('seleccionada');
    }
    if (estado.resaltado) resaltar(raiz, estado.resaltado, true);
    return grilla;
  }

  function aplicarDiaMovil(raiz) {
    const col = DIAS.indexOf(estado.diaMovil) + 2;
    $$('.grilla > [data-col]', raiz).forEach(el => {
      const c = el.dataset.col;
      // data-hasta: banda que abarca varios días seguidos (pausas de la vista Cursos)
      const enDia = Number(c) <= col && col <= Number(el.dataset.hasta || c);
      el.classList.toggle('fuera-dia', c !== '1' && c !== 'band' && !enDia);
    });
    $$('[data-dia-movil]', raiz).forEach(b => b.setAttribute('aria-pressed', String(b.dataset.diaMovil === estado.diaMovil)));
  }

  // Leyenda: destaca en la grilla las sesiones con la misma clave
  function resaltar(raiz, claveR, activo) {
    if (!raiz) return;
    const grilla = $('.grilla', raiz);
    if (!grilla) return;
    grilla.classList.toggle('resaltando', Boolean(activo && claveR));
    $$('.sesion', grilla).forEach(el => el.classList.toggle('coincide', Boolean(activo) && el.dataset.clave === claveR));
    $$('.leyenda-chip', raiz).forEach(ch => ch.setAttribute('aria-pressed', String(estado.resaltado === ch.dataset.clave)));
  }

  function leyendaHTML(items, nota) {
    return `<div class="leyenda" aria-label="Leyenda: pasa el cursor o toca para destacar">${items.map(it => `
      <button type="button" class="leyenda-chip cat-${it.cat}" data-clave="${esc(it.clave)}" aria-pressed="false">
        <span class="punto"></span>${esc(it.nombre)}${it.horas != null ? ` <b>${numero(it.horas)} h</b>` : ''}
      </button>`).join('')}</div>${nota ? `<p class="leyenda-nota">${esc(nota)}</p>` : ''}`;
  }

  // ===========================================================================
  // 6. VISTA CURSOS
  // ===========================================================================
  // Menú "Horario de [curso ⌄]": un bloque por ciclo, una fila por nivel y un botón por sección
  function renderSelectorCursos() {
    const secciones = [...new Set(CURSOS.map(c => c.seccion))].sort();
    $('#curso-menu-grupos').innerHTML = DATOS.ciclos.map(ciclo => {
      const cursos = CURSOS.filter(c => c.ciclo === ciclo.id);
      const filas = [...new Set(cursos.map(c => c.nivel))].map(nivel => `
        <div class="curso-menu-fila">
          <span class="curso-menu-nivel">${esc(nombreNivel(nivel))}</span>
          ${secciones.map(s => {
            const c = cursos.find(k => k.nivel === nivel && k.seccion === s);
            return c
              ? `<button type="button" class="chip-curso" data-elegir-curso="${esc(c.id)}" aria-label="${esc(c.nombre)}" tabindex="-1">${esc(s)}</button>`
              : '<span class="chip-vacio" aria-hidden="true"></span>';
          }).join('')}
        </div>`).join('');
      return `
        <div class="curso-menu-grupo" role="group" aria-labelledby="menu-${ciclo.id}">
          <span class="eyebrow" id="menu-${ciclo.id}">${esc(ciclo.nombre)}</span>${filas}
        </div>`;
    }).join('');
  }

  // Opciones de una franja de electivos para un curso, con nombre común y sin repetir
  function opcionesFranja(curso, n) {
    const franja = (DATOS.franjas[curso.nivel] || [])[n - 1];
    if (!franja) return [];
    const grupos = franja.grupos.filter(g => !(/^\d[AB]$/.test(g.seccion) && g.seccion.slice(-1) !== curso.seccion));
    return [...new Set(grupos.map(g => ELECTIVO_CORTO[g.asignatura] || capitalizar(g.asignatura)))];
  }

  function opcionesGrillaCurso(curso) {
    const idx = clasesCurso.get(curso.id);
    const maxBloque = curso.parvulo ? 6 : Math.max(...curso.jornada);
    return {
      maxBloque,
      simple: true,
      obtener(dia, b) {
        const k = idx.get(clave(dia, b));
        if (k) return { tipo: 'sesion', ...k };
        const jornada = curso.jornada[DIAS.indexOf(dia)];
        if (b > jornada) return { tipo: 'fuera' };
        return curso.parvulo ? { tipo: 'parvulo' } : null;
      },
      igual: (a, b) => a.asignatura === b.asignatura,
      subDia(dia) {
        return `Salida ${BLOQUE[curso.jornada[DIAS.indexOf(dia)]].fin}`;
      },
      // El recreo o la colación solo se muestran si ese día quedan clases después
      diaConPausa: (dia, b) => b < curso.jornada[DIAS.indexOf(dia)],
      textoVacio(pz) {
        if (pz.v.tipo === 'fuera') return pz.inicio === curso.jornada[DIAS.indexOf(pz.dia)] + 1 ? 'Fin de jornada' : '';
        if (pz.v.tipo === 'parvulo') return 'Jornada parvularia';
        return '';
      },
      celda(pz, ctx) {
        const v = pz.v;
        const info = infoAsig(v.asignatura);
        const titulo = v.franja ? 'Electivos' : info.nombre;
        const sub = v.franja ? opcionesFranja(curso, v.franja).join(' · ') : v.docentes.join(' · ');
        return sesionHTML({
          pz, ctx, cat: info.cat, titulo, sub,
          hora: pz.fin === pz.inicio ? rango(pz.inicio, pz.fin) : '',
          claveResaltado: v.asignatura,
          etiquetaAria: v.franja
            ? `Electivos, franja ${v.franja}: ${sub}, ${pz.dia}, ${rango(pz.inicio, pz.fin)}`
            : `${info.nombre}, ${pz.dia}, ${rango(pz.inicio, pz.fin)}, con ${v.docentes.join(', ')}`,
        });
      },
    };
  }

  // "Ed. Física: martes y jueves · Gimnasio B"
  function textoEdFisica(curso) {
    const dias = DIAS.filter(d => curso.clases.some(k => k.dia === d && k.asignatura === 'Educación Física y Salud'))
      .map(d => d.toLowerCase());
    if (!dias.length) return '';
    const lista = dias.length > 1 ? `${dias.slice(0, -1).join(', ')} y ${dias[dias.length - 1]}` : dias[0];
    return `<span>Ed. Física: ${lista}${curso.gimnasio ? ` · ${enlaceEspacio(curso.gimnasio)}` : ''}</span>`;
  }

  // Párvulos: solo 2 clases de Ed. Física, como tarjetas en vez de una grilla casi vacía
  function clasesParvuloHTML(curso) {
    const op = opcionesGrillaCurso(curso);
    const hoy = momentoActual();
    const piezas = DIAS.flatMap(d => segmentar(d, op).filter(pz => pz.v && pz.v.tipo === 'sesion'));
    const tarjetas = piezas.map(pz => {
      const info = infoAsig(pz.v.asignatura);
      const esHoy = Boolean(hoy && hoy.dia === pz.dia);
      const ahora = esHoy && hoy.bloque >= pz.inicio && hoy.bloque <= pz.fin;
      const lugar = lugaresClase(curso, pz.v.espacio, pz.dia, pz.inicio)
        .map(l => (l.espacio ? nombreEspacio(l.espacio) : l.texto)).join(' · ');
      return `<li><button type="button" class="sesion cat-${info.cat}${ahora ? ' es-ahora' : ''}"
          data-sesion data-dia="${pz.dia}" data-inicio="${pz.inicio}" data-fin="${pz.fin}" data-clave="${esc(pz.v.asignatura)}"
          aria-label="${esc(`${info.nombre}, ${pz.dia}, ${rango(pz.inicio, pz.fin)}, con ${pz.v.docentes.join(', ')}, en ${lugar}`)}">
          <span class="sesion-titulo">${pz.dia}${esHoy ? ' · hoy' : ''}</span>
          <span class="sesion-hora">${rango(pz.inicio, pz.fin)}</span>
          <span class="sesion-sub">${esc(pz.v.docentes.join(' · '))} · ${esc(lugar)}</span>
        </button></li>`;
    }).join('');
    return `
      <section class="parvulo-clases">
        <h2 class="eyebrow">Educación Física · ${piezas.length} clases por semana</h2>
        <ul>${tarjetas}</ul>
      </section>`;
  }

  // Plan de estudios plegado (sale de curso.tabla, fiel al Excel oficial)
  function planCurso(curso, abierto) {
    let cuerpo = '';
    let total = curso.horas;
    curso.tabla.forEach((f, i) => {
      if (f.tipo === 'encabezado' && i === 0) return;
      if (f.tipo === 'encabezado' || f.tipo === 'subtitulo') {
        const rotulo = /DIFERENCIADA/.test(f.asignatura) ? 'Electivos (formación diferenciada)' : capitalizar(f.asignatura.replace(/:$/, ''));
        cuerpo += `<tr class="grupo-fila"><th colspan="3">${esc(rotulo)}</th></tr>`;
      } else if (f.tipo === 'total') {
        total = f.horas;
      } else {
        const horas = f.horas == null ? '<span class="etiqueta">compartidas</span>' : numero(f.horas);
        cuerpo += `<tr><td>${esc(capitalizar(f.asignatura))}</td><td class="num">${horas}</td><td>${enlazarDocentes(f.profesor)}</td></tr>`;
      }
    });
    return `
      <details class="plan-curso"${abierto ? ' open' : ''}>
        <summary>Plan de estudios · ${numero(total)} horas semanales</summary>
        <div class="tabla-marco"><table class="tabla">
          <thead><tr><th>Asignatura</th><th class="num">Horas</th><th>Profesor/a</th></tr></thead>
          <tbody>${cuerpo}</tbody>
        </table></div>
      </details>`;
  }

  function renderCursos(animarEntrada) {
    const curso = cursoPorId.get(estado.curso);
    const panel = $('#panel-curso');
    // El estado del plan se guarda fuera del DOM: los párvulos no tienen plan y no deben cerrarlo
    const planPrevio = $('.plan-curso', panel);
    if (planPrevio) estado.planAbierto = planPrevio.open;
    $('#curso-actual').textContent = curso.nombre;
    $$('#curso-menu [data-elegir-curso]').forEach(b => b.setAttribute('aria-current', String(b.dataset.elegirCurso === curso.id)));
    guardar('mmdd-curso', curso.id);
    document.title = `${curso.nombre} · Horarios MMDD ${DATOS.meta.anio}`;

    const meta = curso.parvulo
      ? 'En Educación Parvularia este horario solo programa Educación Física.'
      : [curso.jefe ? `<span>Profesor/a jefe: ${enlaceDocente(curso.jefe)}</span>` : '', textoEdFisica(curso)].join('');

    panel.innerHTML = `
      <h1 class="visualmente-oculto curso-titulo">Horario de ${esc(curso.nombre)}</h1>
      <p class="curso-meta">${meta}</p>
      ${curso.parvulo ? clasesParvuloHTML(curso) : grillaHTML(opcionesGrillaCurso(curso))}
      <p class="curso-pista">Toca una clase para ver la sala, los docentes y sus otras horas de la semana.</p>
      ${curso.parvulo ? '' : planCurso(curso, estado.planAbierto)}`;

    prepararGrilla(panel);
    const marco = $('.grilla-marco', panel);
    if (marco) marco.classList.toggle('jornada-larga', Math.max(...curso.jornada) > 8);   // para ajustar la impresión
    // Fundido del contenedor (no de cada tarjeta: .sesion tiene su propia transición de opacidad)
    if (animarEntrada) animar.aparecer($$('.grilla-marco, .parvulo-clases', panel), { y: 6, stagger: 0, duracion: 0.25 });
  }

  function accionesCabecera(tipo) {
    const flecha = d => `<svg class="icono" viewBox="0 0 24 24" aria-hidden="true"><path d="${d}"/></svg>`;
    return `
      <div class="cabecera-acciones">
        <button type="button" class="boton-icono" data-paso="-1" aria-label="${tipo === 'curso' ? 'Curso' : tipo === 'docente' ? 'Docente' : 'Sala'} anterior">${flecha('m15 6-6 6 6 6')}</button>
        <button type="button" class="boton-icono" data-paso="1" aria-label="${tipo === 'curso' ? 'Curso' : tipo === 'docente' ? 'Docente' : 'Sala'} siguiente">${flecha('m9 6 6 6-6 6')}</button>
        <button type="button" class="boton" data-imprimir>
          <svg class="icono" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 9V3h10v6M7 17H5a2 2 0 0 1-2-2v-4a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2h-2M7 14h10v7H7z"/></svg>
          Imprimir
        </button>
      </div>`;
  }

  function lugaresClase(curso, espacio, dia, b, docente) {
    switch (espacio) {
      case 'Aula': return [{ texto: `Sala de ${curso.nombre}` }];
      case 'Gimnasio': {
        const r = recintoDe.get(`${curso.id}|${dia}|${b}`) || curso.gimnasio;
        return [{ espacio: r }];
      }
      case 'Sala English skills': return [{ espacio: 'ELECTIVO 1' }];
      case 'Sala de Artes y Música':
        if (docente) return [{ espacio: docente === 'Música' ? 'SALA DE MÚSICA' : 'SALA DE ARTES' }];
        return [{ espacio: 'SALA DE ARTES' }, { espacio: 'SALA DE MÚSICA' }];
      case 'Sala de Música': return [{ espacio: 'SALA DE MÚSICA' }];
      case 'Salas electivos': return [{ texto: 'Salas de electivos (ver grupos)' }];
      default: return [{ texto: espacio }];
    }
  }
  const lugaresHTML = lista => lista.map(l => (l.espacio ? enlaceEspacio(l.espacio) : esc(l.texto))).join(' · ');

  function gruposFranja(nivel, numeroFranja, seccion) {
    const franja = (DATOS.franjas[nivel] || [])[numeroFranja - 1];
    if (!franja) return '';
    const grupos = franja.grupos.filter(g => !(/^\d[AB]$/.test(g.seccion) && seccion && g.seccion.slice(-1) !== seccion));
    return `
      <div>
        <h3>Electivos en paralelo</h3>
        <ul class="grupos-electivo">${grupos.map(g => `
          <li><b>${esc(capitalizar(g.asignatura))}</b>
            <span class="meta"><span>Sección ${esc(g.seccion)}</span>${enlaceDocente(g.docente)}${enlaceEspacio(g.sala)}</span></li>`).join('')}
        </ul>
      </div>
      <div>
        <h3>Periodos de la franja ${numeroFranja}</h3>
        <div class="otras">${franja.periodos.map(p => `<button type="button" data-momento="${p.dia}|${p.bloque}">${DIA_CORTO[p.dia]} · ${rango(p.bloque, p.bloque + 1)}</button>`).join('')}</div>
      </div>`;
  }

  function otrasSesiones(grillaOp, claveFn, valorClave, actual) {
    const otras = [];
    DIAS.forEach(dia => segmentar(dia, grillaOp).forEach(pz => {
      if (pz.v && pz.v.tipo === 'sesion' && claveFn(pz.v) === valorClave && !(dia === actual.dia && pz.inicio === actual.inicio)) otras.push(pz);
    }));
    if (!otras.length) return '';
    return `<div><h3>Otras sesiones en la semana</h3><div class="otras">${otras.map(pz =>
      `<button type="button" data-ir-celda="${pz.dia}|${pz.inicio}">${DIA_CORTO[pz.dia]} · ${rango(pz.inicio, pz.fin)}</button>`).join('')}</div></div>`;
  }

  function detalleCurso(dia, inicio) {
    const curso = cursoPorId.get(estado.curso);
    const op = opcionesGrillaCurso(curso);
    const pz = segmentar(dia, op).find(p => p.inicio === inicio);
    if (!pz || !pz.v) return null;
    const v = pz.v;
    const info = infoAsig(v.asignatura);
    const minutosClase = (pz.fin - pz.inicio + 1) * 45;
    let extra = '';
    if (v.franja) extra = gruposFranja(curso.nivel, v.franja, curso.seccion);
    if (v.asignatura === 'English Skills') extra = '<p class="nota">Inglés con dos docentes en el mismo bloque, en la sala Electivo 1 (un curso por bloque).</p>';
    if (v.asignatura === 'Artes Visuales / Música') extra = `<p class="nota">El curso se divide: Artes con ${esc(v.docentes[0])} y Música con ${esc(v.docentes[1])}, en simultáneo.</p>`;
    const docentes = v.franja ? `${v.docentes.length} docentes (ver grupos)` : v.docentes.map(enlaceDocente).join('');
    return {
      eyebrow: curso.nombre,
      html: `
        <div class="detalle-muestra cat-${info.cat}">
          <h2>${esc(info.nombre)}</h2>
          <p>${dia} · ${textoBloques(pz.inicio, pz.fin)} · ${rango(pz.inicio, pz.fin)} · ${minutosClase} min</p>
        </div>
        <dl class="datos">
          <dt>Asignatura</dt><dd>${esc(v.franja ? `Formación diferenciada, franja ${v.franja}` : v.asignatura)}</dd>
          <dt>${v.docentes.length > 1 ? 'Docentes' : 'Docente'}</dt><dd>${docentes}</dd>
          <dt>Lugar</dt><dd>${lugaresHTML(lugaresClase(curso, v.espacio, dia, pz.inicio))}</dd>
          <dt>Momento</dt><dd><button type="button" class="enlace" data-momento="${dia}|${pz.inicio}">Ver todo el colegio en este bloque</button></dd>
        </dl>
        ${extra}
        ${otrasSesiones(op, x => x.asignatura, v.asignatura, pz)}`,
    };
  }

  // ===========================================================================
  // 7. VISTA DOCENTES
  // ===========================================================================
  const MAX_HORAS_DOCENTE = Math.max(...DOCENTES.map(d => d.horasGrilla));

  function renderSelectorDocentes() {
    const filtro = normalizar($('#filtro-docentes').value.trim());
    const grupos = [];
    const porDepto = new Map();
    DOCENTES.forEach(d => {
      const depto = departamento(d);
      if (filtro && !normalizar(`${d.nombre} ${depto}`).includes(filtro)) return;
      if (!porDepto.has(depto)) porDepto.set(depto, []);
      porDepto.get(depto).push(d);
    });
    porDepto.forEach((lista, depto) => {
      grupos.push(`<div class="sel-grupo"><span class="eyebrow">${esc(depto)}</span>${lista.map(d => `
        <button type="button" class="item-lista" data-docente="${esc(d.nombre)}" aria-current="${d.nombre === estado.docente}">
          <span class="item-lista-nombre">${esc(d.nombre)}</span>
          <span class="item-lista-valor">${d.horasGrilla} h</span>
          <span class="item-lista-barra" aria-hidden="true"><span style="width:${(d.horasGrilla / MAX_HORAS_DOCENTE) * 100}%"></span></span>
        </button>`).join('')}</div>`);
    });
    $('#selector-docentes').innerHTML = grupos.join('') || '<p class="nota">Ningún docente coincide con el filtro.</p>';
  }

  function maxBloqueDocente(doc) {
    return doc.clases.some(k => k.bloque > 8) ? 10 : 8;
  }

  function ventanasDocente(doc) {
    const idx = clasesDocente.get(doc.nombre);
    const porDia = {};
    let total = 0;
    DIAS.forEach(dia => {
      const bloques = doc.clases.filter(k => k.dia === dia).map(k => k.bloque);
      porDia[dia] = new Set();
      if (bloques.length < 2) return;
      for (let b = Math.min(...bloques) + 1; b < Math.max(...bloques); b++) {
        if (!idx.has(clave(dia, b))) { porDia[dia].add(b); total += 1; }
      }
    });
    return { porDia, total };
  }

  function opcionesGrillaDocente(doc) {
    const idx = clasesDocente.get(doc.nombre);
    const ventanas = ventanasDocente(doc).porDia;
    return {
      maxBloque: maxBloqueDocente(doc),
      obtener(dia, b) {
        const k = idx.get(clave(dia, b));
        if (k) return { tipo: 'sesion', ...k };
        return ventanas[dia].has(b) ? { tipo: 'ventana' } : null;
      },
      igual: (a, b) => a.grupo === b.grupo && a.asignatura === b.asignatura,
      subDia: dia => {
        const n = doc.clases.filter(k => k.dia === dia).length;
        return n ? `${n} ${n === 1 ? 'hora' : 'horas'}` : 'Sin clases';
      },
      textoVacio: pz => (pz.v.tipo === 'ventana' ? 'Ventana' : ''),
      celda(pz, ctx) {
        const v = pz.v;
        const info = infoAsig(v.asignatura);
        const sub = v.electivo ? capitalizar(v.asignatura) : info.nombre;
        const marca = v.codocentes.length ? 'co-docencia' : '';
        return sesionHTML({
          pz, ctx, cat: info.cat, titulo: v.grupo, sub, marca, claveResaltado: v.grupo,
          etiquetaAria: `${v.grupo}, ${sub}, ${pz.dia}, ${textoBloques(pz.inicio, pz.fin)}, ${rango(pz.inicio, pz.fin)}`,
        });
      },
    };
  }

  function tablaDistribucion(doc) {
    const tipos = { jefatura: 'Jefatura', skills: 'English skills', orientec: 'Orientación/Tec.', electivo: 'Electivo', no_lectiva: 'Fuera de grilla' };
    const filas = doc.distribucion.map(f => {
      const curso = cursoPorId.has(f.curso) ? enlaceCurso(f.curso) : esc(f.curso);
      return `<tr><td>${curso}</td><td>${esc(f.asignatura)} ${tipos[f.tipo] ? `<span class="etiqueta">${tipos[f.tipo]}</span>` : ''}</td><td class="num">${f.horas}</td></tr>`;
    }).join('');
    return `
      <section class="seccion">
        <div class="seccion-titulo"><h2>Distribución horaria</h2><p>Calculada desde el horario generado</p></div>
        <div class="tabla-marco"><table class="tabla">
          <thead><tr><th>Curso</th><th>Asignatura</th><th class="num">Horas</th></tr></thead>
          <tbody>${filas}</tbody>
          <tfoot><tr><td colspan="2">Horas lectivas</td><td class="num">${doc.horasTotales}</td></tr></tfoot>
        </table></div>
      </section>`;
  }

  function cargaPorDiaHTML(doc) {
    const valores = DIAS.map(dia => doc.clases.filter(k => k.dia === dia).length);
    const max = Math.max(10, ...valores);
    return `
      <section class="seccion">
        <div class="seccion-titulo"><h2>Carga por día</h2><p>Bloques de clase de 45 minutos</p></div>
        <div class="carga-dias" role="img" aria-label="${DIAS.map((d, i) => `${d}: ${valores[i]} horas`).join(', ')}">
          ${valores.map((v, i) => `
            <div class="carga-dia">
              <span class="carga-dia-valor">${v}</span>
              <span class="carga-dia-barra" style="height:${(v / max) * 100}%"></span>
              <span class="carga-dia-nombre">${DIA_CORTO[DIAS[i]]}</span>
            </div>`).join('')}
        </div>
      </section>`;
  }

  function renderDocentes(animarEntrada) {
    const doc = docentePorNombre.get(estado.docente);
    $$('#selector-docentes .item-lista').forEach(b => b.setAttribute('aria-current', String(b.dataset.docente === doc.nombre)));
    $('#vista-docentes .selector-toggle span').textContent = `Docente: ${doc.nombre} · cambiar`;

    const grupos = new Map();
    doc.clases.forEach(k => {
      if (!grupos.has(k.grupo)) grupos.set(k.grupo, { clave: k.grupo, nombre: k.grupo, cat: infoAsig(k.asignatura).cat, horas: 0 });
      grupos.get(k.grupo).horas += 1;
    });
    const dias = DIAS.filter(dia => doc.clases.some(k => k.dia === dia)).length;
    const ventanas = ventanasDocente(doc).total;
    const jefatura = doc.jefatura ? `<span>Profesor/a jefe de ${enlaceCurso(doc.jefatura)}</span>` : '';
    const fueraGrilla = doc.horasTotales - doc.horasGrilla;

    $('#panel-docente').innerHTML = `
      <div class="cabecera">
        <div class="cabecera-titulo">
          <span class="eyebrow">${esc(departamento(doc))}</span>
          <h1>${esc(doc.nombre)}</h1>
          <div class="cabecera-meta">${jefatura}<span><b>${doc.horasTotales}</b> horas lectivas${fueraGrilla ? ` (${fueraGrilla} fuera de grilla)` : ''}</span></div>
        </div>
        ${accionesCabecera('docente')}
      </div>
      <div class="columnas">
        <div class="seccion">
          <div class="estadisticas">
            <div class="estadistica"><span class="estadistica-valor" data-contar="${doc.horasGrilla}">${doc.horasGrilla}</span><span class="estadistica-etiqueta">horas en la grilla</span></div>
            <div class="estadistica"><span class="estadistica-valor" data-contar="${grupos.size}">${grupos.size}</span><span class="estadistica-etiqueta">cursos o grupos</span></div>
            <div class="estadistica"><span class="estadistica-valor" data-contar="${dias}">${dias}</span><span class="estadistica-etiqueta">días con clases</span></div>
            <div class="estadistica"><span class="estadistica-valor" data-contar="${ventanas}">${ventanas}</span><span class="estadistica-etiqueta">bloques de ventana</span></div>
          </div>
          ${leyendaHTML([...grupos.values()], 'Pasa el cursor por un curso para ver sus bloques. Las ventanas son bloques libres entre dos clases del mismo día.')}
        </div>
        ${cargaPorDiaHTML(doc)}
      </div>
      ${grillaHTML(opcionesGrillaDocente(doc))}
      ${tablaDistribucion(doc)}`;

    const panel = $('#panel-docente');
    const grilla = prepararGrilla(panel);
    if (animarEntrada) {
      animar.titulo(panel);
      animar.grilla(grilla);
      $$('[data-contar]', panel).forEach(el => animar.contar(el, Number(el.dataset.contar)));
      animar.barras($$('.carga-dia-barra', panel), 'y');
    }
  }

  function detalleDocente(dia, inicio) {
    const doc = docentePorNombre.get(estado.docente);
    const op = opcionesGrillaDocente(doc);
    const pz = segmentar(dia, op).find(p => p.inicio === inicio);
    if (!pz || !pz.v) return null;
    const v = pz.v;
    const info = infoAsig(v.asignatura);
    let grupo;
    let lugar;
    let extra = '';
    if (v.electivo) {
      grupo = ['A', 'B'].map(s => enlaceCurso(`${v.nivel} ${s}`)).join('');
      lugar = enlaceEspacio(v.sala);
      extra = gruposFranja(v.nivel, v.franja, null);
    } else {
      const curso = cursoPorId.get(v.curso);
      grupo = enlaceCurso(v.curso);
      lugar = lugaresHTML(lugaresClase(curso, v.sala, dia, pz.inicio, doc.nombre));
    }
    return {
      eyebrow: doc.nombre,
      html: `
        <div class="detalle-muestra cat-${info.cat}">
          <h2>${esc(v.electivo ? capitalizar(v.asignatura) : info.nombre)}</h2>
          <p>${dia} · ${textoBloques(pz.inicio, pz.fin)} · ${rango(pz.inicio, pz.fin)} · ${(pz.fin - pz.inicio + 1) * 45} min</p>
        </div>
        <dl class="datos">
          <dt>${v.electivo ? 'Cursos' : 'Curso'}</dt><dd>${grupo}</dd>
          ${v.codocentes.length ? `<dt>Comparte con</dt><dd>${v.codocentes.map(enlaceDocente).join('')}</dd>` : ''}
          <dt>Lugar</dt><dd>${lugar}</dd>
          <dt>Momento</dt><dd><button type="button" class="enlace" data-momento="${dia}|${pz.inicio}">Ver todo el colegio en este bloque</button></dd>
        </dl>
        ${extra}
        ${otrasSesiones(op, x => `${x.grupo}|${x.asignatura}`, `${v.grupo}|${v.asignatura}`, pz)}`,
    };
  }

  // ===========================================================================
  // 8. VISTA SALAS Y GIMNASIOS
  // ===========================================================================
  function maxBloqueEspacio(e) {
    const tarde = e.usos.some(u => u.bloque > 8) || e.pastoral.some(p => p.bloque === 'C' || p.bloque > 8);
    return tarde ? 10 : 8;
  }
  const capacidadEspacio = e => maxBloqueEspacio(e) * DIAS.length;

  function catEspacio(nombre) {
    if (nombre.startsWith('GIMNASIO') || nombre.startsWith('PATIO')) return 'edfisica';
    if (nombre === 'ELECTIVO 1') return 'ingles';
    if (nombre === 'SALA DE ARTES' || nombre === 'SALA DE MÚSICA') return 'artes';
    return 'electivo';
  }

  function textoItem(espacio, it) {
    if (!it.curso) return { titulo: etiquetaLegible(it.texto), sub: it.docente || '' };
    const curso = cursoPorId.get(it.curso);
    const actividad = { edfisica: 'Ed. Física', ingles: 'English skills' }[catEspacio(espacio)]
      || (it.texto.endsWith('Artes') ? 'Artes' : 'Música');
    return { titulo: curso.nombre, sub: actividad };
  }

  function renderSelectorSalas() {
    const grupos = [
      ['Recintos deportivos', ESPACIOS.filter(e => e.tipo === 'recinto')],
      ['Salas de especialidad', ESPACIOS.filter(e => e.tipo === 'sala' && e.descripcion !== 'Sala pastoral')],
      ['Salas pastorales', ESPACIOS.filter(e => e.descripcion === 'Sala pastoral')],
    ];
    $('#selector-salas').innerHTML = grupos.map(([titulo, lista]) => `
      <div class="sel-grupo"><span class="eyebrow">${titulo}</span>${lista.map(e => `
        <button type="button" class="item-lista" data-espacio="${esc(e.nombre)}" aria-current="${e.nombre === estado.espacio}">
          <span class="item-lista-nombre">${esc(nombreEspacio(e.nombre))}</span>
          <span class="item-lista-valor">${e.usos.length}</span>
          <span class="item-lista-barra" aria-hidden="true"><span style="width:${(e.usos.length / capacidadEspacio(e)) * 100}%"></span></span>
        </button>`).join('')}</div>`).join('');
  }

  function opcionesGrillaEspacio(e) {
    const usos = usosEspacio.get(e.nombre);
    const pastoral = pastoralEspacio.get(e.nombre);
    const cat = catEspacio(e.nombre);
    return {
      maxBloque: maxBloqueEspacio(e),
      obtener(dia, b) {
        if (pastoral.has(clave(dia, b))) return { tipo: 'pastoral' };
        const u = usos.get(clave(dia, b));
        return u ? { tipo: 'sesion', items: u.items } : null;
      },
      igual: (a, b) => a.items.map(i => i.texto).join() === b.items.map(i => i.texto).join(),
      pausaDia: (dia, b) => (b === 8 && pastoral.has(clave(dia, 'C')) ? 'Pastoral' : null),
      subDia: dia => {
        const n = e.usos.filter(u => u.dia === dia).length;
        return `${n} ${n === 1 ? 'bloque' : 'bloques'} en uso`;
      },
      textoVacio: pz => (pz.v.tipo === 'pastoral' ? 'Pastoral' : ''),
      celda(pz, ctx) {
        const textos = pz.v.items.map(it => textoItem(e.nombre, it));
        return sesionHTML({
          pz, ctx, cat,
          titulo: textos.map(t => t.titulo).join(' + '),
          sub: textos.map(t => t.sub).filter(Boolean).join(' · '),
          claveResaltado: textos[0].titulo,
          etiquetaAria: `${textos.map(t => `${t.titulo} ${t.sub}`).join(', ')}, ${pz.dia}, ${rango(pz.inicio, pz.fin)}`,
        });
      },
    };
  }

  function renderSalas(animarEntrada) {
    const e = espacioPorNombre.get(estado.espacio);
    $$('#selector-salas .item-lista').forEach(b => b.setAttribute('aria-current', String(b.dataset.espacio === e.nombre)));
    $('#vista-salas .selector-toggle span').textContent = `Sala: ${nombreEspacio(e.nombre)} · cambiar`;
    const capacidad = capacidadEspacio(e);
    const ocupacion = Math.round((e.usos.length / capacidad) * 100);
    const cursos = new Set(e.usos.flatMap(u => u.items.map(i => i.curso || i.texto)));
    const vacio = !e.usos.length
      ? `<p class="nota">${e.nombre === 'PATIO SANTO DOMINGO'
        ? 'El horario generado no necesita el Patio Santo Domingo: toda la Educación Física cabe en los gimnasios.'
        : 'Esta sala no tiene clases programadas en el modelo; solo se muestran sus bloqueos de pastoral.'}</p>`
      : '';

    $('#panel-sala').innerHTML = `
      <div class="cabecera">
        <div class="cabecera-titulo">
          <span class="eyebrow">${e.tipo === 'recinto' ? 'Recinto deportivo' : 'Sala'}</span>
          <h1>${esc(nombreEspacio(e.nombre))}</h1>
          <div class="cabecera-meta"><span>${esc(e.descripcion)}</span></div>
        </div>
        ${accionesCabecera('sala')}
      </div>
      <div class="estadisticas">
        <div class="estadistica"><span class="estadistica-valor" data-contar="${e.usos.length}">${e.usos.length}</span><span class="estadistica-etiqueta">bloques en uso de ${capacidad}</span></div>
        <div class="estadistica"><span class="estadistica-valor" data-contar="${ocupacion}" data-sufijo="%">${ocupacion}%</span><span class="estadistica-etiqueta">ocupación semanal</span></div>
        <div class="estadistica"><span class="estadistica-valor" data-contar="${cursos.size}">${cursos.size}</span><span class="estadistica-etiqueta">cursos o grupos distintos</span></div>
        <div class="estadistica"><span class="estadistica-valor" data-contar="${e.pastoral.length}">${e.pastoral.length}</span><span class="estadistica-etiqueta">bloqueos de pastoral</span></div>
      </div>
      ${vacio}
      ${grillaHTML(opcionesGrillaEspacio(e))}`;

    const panel = $('#panel-sala');
    const grilla = prepararGrilla(panel);
    if (animarEntrada) {
      animar.titulo(panel);
      animar.grilla(grilla);
      $$('[data-contar]', panel).forEach(el => animar.contar(el, Number(el.dataset.contar), el.dataset.sufijo || ''));
    }
  }

  function detalleSala(dia, inicio) {
    const e = espacioPorNombre.get(estado.espacio);
    const op = opcionesGrillaEspacio(e);
    const pz = segmentar(dia, op).find(p => p.inicio === inicio);
    if (!pz || !pz.v) return null;
    const cat = catEspacio(e.nombre);
    const items = pz.v.items.map(it => {
      const t = textoItem(e.nombre, it);
      if (it.curso) return `<li><b>${esc(t.titulo)}</b><span class="meta"><span>${esc(t.sub)}</span>${enlaceCurso(it.curso)}</span></li>`;
      return `<li><b>${esc(capitalizar(it.asignatura || it.texto))}</b><span class="meta"><span>${esc(nombreNivel(it.nivel))} · sección ${esc(it.seccion || '')}</span>${enlaceDocente(it.docente)}</span></li>`;
    }).join('');
    return {
      eyebrow: nombreEspacio(e.nombre),
      html: `
        <div class="detalle-muestra cat-${cat}">
          <h2>${esc(nombreEspacio(e.nombre))}</h2>
          <p>${dia} · ${textoBloques(pz.inicio, pz.fin)} · ${rango(pz.inicio, pz.fin)}</p>
        </div>
        <div><h3>Ocupada por</h3><ul class="grupos-electivo">${items}</ul></div>
        <dl class="datos"><dt>Momento</dt><dd><button type="button" class="enlace" data-momento="${dia}|${pz.inicio}">Ver todo el colegio en este bloque</button></dd></dl>`,
    };
  }

  // ===========================================================================
  // 9. VISTA POR BLOQUE (todo el colegio en un momento de la semana)
  // ===========================================================================
  let temporizador = null;

  function estadoTarjeta(curso, dia, b) {
    const k = clasesCurso.get(curso.id).get(clave(dia, b));
    if (k) {
      const info = infoAsig(k.asignatura);
      return {
        clase: `sesion tarjeta cat-${info.cat}`,
        titulo: k.franja ? `Electivos · Franja ${k.franja}` : info.nombre,
        sub: k.franja ? etiquetaLegible(k.etiqueta) : k.docentes.join(' · '),
        activa: true,
      };
    }
    const jornada = curso.jornada[DIAS.indexOf(dia)];
    if (curso.parvulo && b <= jornada) return { clase: 'tarjeta vacia parvulo', titulo: 'Jornada parvularia', sub: '', activa: false };
    return { clase: 'tarjeta vacia fuera', titulo: b > jornada ? 'Terminó su jornada' : 'Sin clase', sub: '', activa: false };
  }

  function tarjetaHTML(curso, dia, b) {
    const t = estadoTarjeta(curso, dia, b);
    return `<button type="button" class="${t.clase}" data-tarjeta="${esc(curso.id)}">
      <span class="sesion-curso">${esc(curso.nombre)}</span>
      <span class="sesion-titulo">${esc(t.titulo)}</span>
      <span class="sesion-sub">${esc(t.sub)}</span>
    </button>`;
  }

  function resumenBloque(dia, b) {
    const enClase = CURSOS.filter(c => clasesCurso.get(c.id).has(clave(dia, b)));
    const ocupados = DOCENTES.filter(d => clasesDocente.get(d.nombre).has(clave(dia, b)));
    const libres = DOCENTES.filter(d => !clasesDocente.get(d.nombre).has(clave(dia, b)));
    const espacios = [];
    ESPACIOS.forEach(e => {
      if (pastoralEspacio.get(e.nombre).has(clave(dia, b))) espacios.push({ e, texto: 'Pastoral' });
      const u = usosEspacio.get(e.nombre).get(clave(dia, b));
      if (u) espacios.push({ e, texto: u.items.map(it => textoItem(e.nombre, it).titulo).join(' + ') });
    });
    return { enClase, ocupados, libres, espacios };
  }

  function contenidoBloqueHTML() {
    const { dia, bloque: b } = estado;
    const r = resumenBloque(dia, b);
    const regulares = r.enClase.filter(c => !c.parvulo).length;
    const grupos = DATOS.ciclos.map(ciclo => `
      <div class="momento-grupo">
        <span class="eyebrow">${esc(ciclo.nombre)}</span>
        <div class="tarjetas">${CURSOS.filter(c => c.ciclo === ciclo.id).map(c => tarjetaHTML(c, dia, b)).join('')}</div>
      </div>`).join('');
    return `
      <div class="momento-resumen" id="momento-resumen">
        <h1>${dia} · Bloque ${b}</h1>
        <p class="cabecera-meta"><span><b>${BLOQUE[b].inicio}–${BLOQUE[b].fin}</b></span>
          <span><b data-resumen="cursos">${regulares}</b> de 24 cursos en clase</span>
          <span><b data-resumen="docentes">${r.ocupados.length}</b> de ${DOCENTES.length} docentes ocupados</span></p>
      </div>
      <div class="momento-grupos">${grupos}</div>
      <div class="columnas">
        <section class="seccion">
          <div class="seccion-titulo"><h2>Docentes sin clase</h2><p>${r.libres.length} disponibles en este bloque</p></div>
          <div class="libres" id="momento-libres">${r.libres.map(d => `<button type="button" class="leyenda-chip" data-docente="${esc(d.nombre)}">${esc(d.nombre)}</button>`).join('') || '<p class="nota">Todos los docentes tienen clase.</p>'}</div>
        </section>
        <section class="seccion">
          <div class="seccion-titulo"><h2>Salas y recintos en uso</h2><p>${r.espacios.length} de ${ESPACIOS.length}</p></div>
          <div class="libres" id="momento-espacios">${r.espacios.map(x => `<button type="button" class="leyenda-chip cat-${x.texto === 'Pastoral' ? 'formacion' : catEspacio(x.e.nombre)}" data-espacio="${esc(x.e.nombre)}"><span class="punto"></span>${esc(nombreEspacio(x.e.nombre))}: ${esc(x.texto)}</button>`).join('') || '<p class="nota">Ninguna sala de especialidad en uso.</p>'}</div>
        </section>
      </div>`;
  }

  function controlesBloqueHTML() {
    const dias = DIAS.map(d => `<button type="button" data-bloque-dia="${d}" aria-pressed="${d === estado.dia}" aria-label="${d}">
      <span class="solo-escritorio">${d}</span><span class="solo-movil" aria-hidden="true">${DIA_CORTO[d]}</span></button>`).join('');
    const linea = [];
    for (let b = 1; b <= MAX_BLOQUE; b++) {
      linea.push(`<button type="button" class="lt-bloque" data-bloque-num="${b}" aria-pressed="${b === estado.bloque}">
        <span class="lt-num">${b}</span><span class="lt-hora">${BLOQUE[b].inicio}</span></button>`);
      if (PAUSA[b] && b < MAX_BLOQUE) linea.push(`<span class="lt-pausa" aria-hidden="true"><span>${PAUSA[b].nombre === 'COLACIÓN' ? 'Colación' : 'Recreo'}</span></span>`);
    }
    const ahora = momentoActual();
    return `
      <div class="momento-controles">
        <div class="momento-fila">
          <div class="segmentado" role="group" aria-label="Día">${dias}</div>
          <button type="button" class="boton" id="reproducir" aria-pressed="false">
            <svg class="icono" viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg>
            <span>Recorrer la semana</span>
          </button>
          ${ahora && ahora.bloque ? '<button type="button" class="boton" id="ir-ahora">Ir a ahora</button>' : ''}
        </div>
        <div class="linea-tiempo" role="group" aria-label="Bloque">${linea.join('')}</div>
      </div>`;
  }

  function renderBloque(animarEntrada) {
    const panel = $('#panel-bloque');
    panel.innerHTML = `${controlesBloqueHTML()}<div id="momento-contenido">${contenidoBloqueHTML()}</div>`;
    centrarBloqueActivo(false);
    if (animarEntrada) {
      animar.aparecer($$('.lt-bloque', panel), { stagger: 0.03 });
      animar.aparecer($$('.tarjeta', panel), { y: 12, scale: 0.96, stagger: 0.012 });
    }
  }

  // Desplaza solo la línea de tiempo (no la página) para dejar visible el bloque elegido
  function centrarBloqueActivo(suave) {
    const linea = $('#panel-bloque .linea-tiempo');
    const activo = linea && $('[aria-pressed="true"]', linea);
    if (!activo || linea.scrollWidth <= linea.clientWidth) return;
    const destino = activo.offsetLeft - (linea.clientWidth - activo.offsetWidth) / 2;
    linea.scrollTo({ left: destino, behavior: suave && !movimientoReducido.matches ? 'smooth' : 'auto' });
  }

  // Cambia de bloque sin redibujar las tarjetas: los colores se transforman con CSS
  function actualizarBloque() {
    const panel = $('#panel-bloque');
    if (!$('.tarjetas', panel)) { renderBloque(true); return; }
    const { dia, bloque: b } = estado;
    $$('[data-bloque-dia]', panel).forEach(x => x.setAttribute('aria-pressed', String(x.dataset.bloqueDia === dia)));
    $$('[data-bloque-num]', panel).forEach(x => x.setAttribute('aria-pressed', String(Number(x.dataset.bloqueNum) === b)));
    centrarBloqueActivo(true);

    const cambiadas = [];
    $$('[data-tarjeta]', panel).forEach(el => {
      const curso = cursoPorId.get(el.dataset.tarjeta);
      const t = estadoTarjeta(curso, dia, b);
      const titulo = $('.sesion-titulo', el);
      const sub = $('.sesion-sub', el);
      if (el.className !== t.clase || titulo.textContent !== t.titulo || sub.textContent !== t.sub) {
        el.className = t.clase;
        titulo.textContent = t.titulo;
        sub.textContent = t.sub;
        cambiadas.push(titulo, sub);
      }
    });
    animar.aparecer(cambiadas, { y: 8, stagger: 0.006, duracion: 0.35 });

    const r = resumenBloque(dia, b);
    const resumen = $('#momento-resumen', panel);
    $('h1', resumen).textContent = `${dia} · Bloque ${b}`;
    $('.cabecera-meta b', resumen).textContent = `${BLOQUE[b].inicio}–${BLOQUE[b].fin}`;
    $('[data-resumen="cursos"]', resumen).textContent = r.enClase.filter(c => !c.parvulo).length;
    $('[data-resumen="docentes"]', resumen).textContent = r.ocupados.length;
    const g = G();
    if (g) g.fromTo($('h1', resumen), { opacity: 0.2, x: -10 }, { opacity: 1, x: 0, duration: 0.35, ease: 'power2.out', clearProps: 'opacity,transform' });

    $('#momento-libres', panel).innerHTML = r.libres.map(d => `<button type="button" class="leyenda-chip" data-docente="${esc(d.nombre)}">${esc(d.nombre)}</button>`).join('') || '<p class="nota">Todos los docentes tienen clase.</p>';
    $('#momento-libres', panel).closest('.seccion').querySelector('.seccion-titulo p').textContent = `${r.libres.length} disponibles en este bloque`;
    $('#momento-espacios', panel).innerHTML = r.espacios.map(x => `<button type="button" class="leyenda-chip cat-${x.texto === 'Pastoral' ? 'formacion' : catEspacio(x.e.nombre)}" data-espacio="${esc(x.e.nombre)}"><span class="punto"></span>${esc(nombreEspacio(x.e.nombre))}: ${esc(x.texto)}</button>`).join('') || '<p class="nota">Ninguna sala de especialidad en uso.</p>';
    $('#momento-espacios', panel).closest('.seccion').querySelector('.seccion-titulo p').textContent = `${r.espacios.length} de ${ESPACIOS.length}`;
    escribirHash(true);
  }

  function moverBloque(paso) {
    let i = DIAS.indexOf(estado.dia) * MAX_BLOQUE + (estado.bloque - 1) + paso;
    const total = DIAS.length * MAX_BLOQUE;
    i = (i + total) % total;
    estado.dia = DIAS[Math.floor(i / MAX_BLOQUE)];
    estado.bloque = (i % MAX_BLOQUE) + 1;
    actualizarBloque();
  }

  function alternarReproduccion() {
    if (temporizador) { detenerReproduccion(); return; }
    const boton = $('#reproducir');
    temporizador = setInterval(() => moverBloque(1), 1500);
    if (boton) {
      boton.classList.add('reproduciendo');
      boton.setAttribute('aria-pressed', 'true');
      $('span', boton).textContent = 'Pausar';
      $('svg', boton).innerHTML = '<path d="M8 5h3v14H8zM13 5h3v14h-3z"/>';
    }
  }

  function detenerReproduccion() {
    if (!temporizador) return;
    clearInterval(temporizador);
    temporizador = null;
    const boton = $('#reproducir');
    if (boton) {
      boton.classList.remove('reproduciendo');
      boton.setAttribute('aria-pressed', 'false');
      $('span', boton).textContent = 'Recorrer la semana';
      $('svg', boton).innerHTML = '<path d="M8 5v14l11-7z"/>';
    }
  }

  // ===========================================================================
  // 10. VISTA AUDITORÍA
  // ===========================================================================
  const ICONO_OK = '<svg class="icono" viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12.5 4.5 4.5L19 7.5"/></svg>';
  const ICONO_MAL = '<svg class="icono" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg>';

  function renderAuditoria(animarEntrada) {
    const a = DATOS.auditoria;
    const m = a.metricas;
    const fecha = DATOS.meta.generado.split(' ');
    const [anio, mes, dia] = fecha[0].split('-');

    const criterios = a.criterios.map(c => `
      <li class="criterio">
        <span class="criterio-nombre">${esc(c.criterio)}</span>
        <span class="criterio-valor">${esc(c.valor)}</span>
        <span class="estado${c.errores ? ' mal' : ''}">${c.errores ? ICONO_MAL : ICONO_OK}${c.errores ? 'No cumple' : 'Cumple'}</span>
      </li>`).join('');

    // Horas en grilla por docente, agrupadas por departamento
    const tope = Math.ceil(MAX_HORAS_DOCENTE / 10) * 10;
    const porDepto = new Map();
    DOCENTES.forEach(d => {
      const k = departamento(d);
      if (!porDepto.has(k)) porDepto.set(k, []);
      porDepto.get(k).push(d);
    });
    const barras = [...porDepto].map(([depto, lista]) => `
      <div class="barras-grupo"><span class="eyebrow">${esc(depto)}</span>${lista.map(d => `
        <button type="button" class="barra-fila" data-docente="${esc(d.nombre)}" data-tip="<b>${esc(d.nombre)}</b><br>${d.horasGrilla} horas en la grilla${d.horasTotales > d.horasGrilla ? `<br>${d.horasTotales - d.horasGrilla} horas fuera de grilla` : ''}">
          <span class="barra-nombre">${esc(d.nombre)}</span>
          <span class="barra-pista"><span class="barra-valor-marca" style="width:${(d.horasGrilla / tope) * 100}%"></span></span>
          <span class="barra-num">${d.horasGrilla}</span>
        </button>`).join('')}</div>`).join('');
    const ticks = [0, 0.25, 0.5, 0.75, 1].map(f => `<span style="left:${f * 100}%">${Math.round(tope * f)}</span>`).join('');
    const promedio = DOCENTES.reduce((s, d) => s + d.horasGrilla, 0) / DOCENTES.length;

    // Docentes en clase por día y bloque
    let calor = '<div></div>' + DIAS.map(d => `<div class="calor-cab">${DIA_CORTO[d]}</div>`).join('');
    for (let b = 1; b <= MAX_BLOQUE; b++) {
      calor += `<div class="calor-hora"><b>${b}</b>${BLOQUE[b].inicio}</div>`;
      DIAS.forEach(dia => {
        const ocupados = DOCENTES.filter(d => clasesDocente.get(d.nombre).has(clave(dia, b))).length;
        const cursos = CURSOS.filter(c => clasesCurso.get(c.id).has(clave(dia, b))).length;
        if (!cursos) {
          calor += `<button type="button" class="calor-celda nulo" data-momento="${dia}|${b}" data-tip="<b>${dia}, bloque ${b}</b><br>Sin clases programadas">—</button>`;
          return;
        }
        const t = ocupados / DOCENTES.length;
        calor += `<button type="button" class="calor-celda${t > 0.55 ? ' alto' : ''}" style="--t:${t.toFixed(3)}" data-momento="${dia}|${b}"
          data-tip="<b>${dia}, bloque ${b}</b> · ${BLOQUE[b].inicio}–${BLOQUE[b].fin}<br>${ocupados} de ${DOCENTES.length} docentes en clase<br>${cursos} cursos con clase">${ocupados}</button>`;
      });
    }

    const errores = a.totalErrores
      ? `<section class="seccion"><div class="seccion-titulo"><h2>Detalle de errores</h2><p>${a.totalErrores} en total</p></div>
         <ul class="errores">${a.errores.map(e => `<li>${esc(e)}</li>`).join('')}</ul></section>` : '';
    const advertencias = a.advertencias.length
      ? `<ul class="errores">${a.advertencias.map(e => `<li>${esc(e)}</li>`).join('')}</ul>` : '';

    $('#panel-auditoria').innerHTML = `
      <div class="veredicto">
        <div class="veredicto-sello${a.valido ? '' : ' mal'}">${a.valido ? ICONO_OK : ICONO_MAL}</div>
        <div>
          <span class="eyebrow">Auditoría de restricciones · semilla ${DATOS.meta.semilla}</span>
          <h1>${a.valido ? 'Horario factible' : 'Horario con conflictos'}</h1>
          <p>${a.valido
            ? `Cumple las ${a.criterios.length} restricciones duras auditadas en ${m.cursos_auditados} cursos y ${m.docentes_auditados} docentes.`
            : `Se encontraron ${a.totalErrores} incumplimientos de restricciones duras.`}
            Generado el ${dia}-${mes}-${anio} a las ${fecha[1]}.</p>
          ${advertencias}
        </div>
      </div>

      <div class="kpis">
        <div class="kpi"><span class="kpi-valor"><span data-contar="${m.total_bloques_asignados}">${m.total_bloques_asignados}</span><small>/ ${m.total_bloques_esperados}</small></span><span class="kpi-etiqueta">bloques asignados</span></div>
        <div class="kpi"><span class="kpi-valor"><span data-contar="${m.porcentaje_bloques_dobles}" data-sufijo="%">${numero(m.porcentaje_bloques_dobles)}%</span></span><span class="kpi-etiqueta">de las horas en bloques dobles de 90 minutos</span></div>
        <div class="kpi"><span class="kpi-valor"><span data-contar="${m.total_ventanas_docentes}">${m.total_ventanas_docentes}</span></span><span class="kpi-etiqueta">bloques de ventana docente (a minimizar)</span></div>
        <div class="kpi"><span class="kpi-valor"><span data-contar="${m.uso_patio}">${m.uso_patio}</span></span><span class="kpi-etiqueta">bloques en el Patio Santo Domingo</span></div>
      </div>

      <section class="seccion">
        <div class="seccion-titulo"><h2>Restricciones duras</h2><p>Verificadas de forma independiente por el validador</p></div>
        <ul class="criterios">${criterios}</ul>
      </section>
      ${errores}

      <div class="columnas">
        <section class="seccion">
          <div class="seccion-titulo"><h2>Horas en grilla por docente</h2><p>Promedio ${numero(Math.round(promedio * 10) / 10)} h · toca una barra para ver su horario</p></div>
          <div class="barras">${barras}</div>
          <div class="eje" aria-hidden="true"><span></span><span class="eje-escala">${ticks}</span><span></span></div>
        </section>
        <section class="seccion">
          <div class="seccion-titulo"><h2>Docentes en clase</h2><p>Por día y bloque · toca una celda para ver ese momento</p></div>
          <div class="tabla-marco"><div class="calor">${calor}</div></div>
          <div class="calor-escala"><span>0</span><span class="calor-escala-barra"></span><span>${DOCENTES.length} docentes</span></div>
        </section>
      </div>
      <p class="nota">Para revisar otro horario, ejecuta <code>python exportar_datos.py --seed N</code> en la carpeta del prototipo y recarga la página.</p>`;

    const panel = $('#panel-auditoria');
    if (animarEntrada) {
      const g = G();
      if (g) {
        g.fromTo($$('.veredicto-sello', panel), { scale: 0, rotate: -40 }, { scale: 1, rotate: 0, duration: 0.7, ease: 'back.out(2.2)', clearProps: 'transform' });
        g.fromTo($$('.veredicto-sello path', panel), { strokeDasharray: 30, strokeDashoffset: 30 }, { strokeDashoffset: 0, duration: 0.6, delay: 0.35, ease: 'power2.out' });
      }
      $$('[data-contar]', panel).forEach(el => animar.contar(el, Number(el.dataset.contar), el.dataset.sufijo || ''));
      animar.aparecer($$('.criterio', panel), { stagger: 0.04 });
      animar.barras($$('.barra-valor-marca', panel), 'x');
      if (g) g.fromTo($$('.calor-celda', panel), { opacity: 0, scale: 0.5 }, { opacity: 1, scale: 1, duration: 0.35, ease: 'power2.out', stagger: { grid: [MAX_BLOQUE, DIAS.length], from: 'start', amount: 0.7 }, clearProps: 'opacity,transform' });
    }
  }

  // ===========================================================================
  // 11. DETALLE LATERAL
  // ===========================================================================
  const detalle = $('#detalle');

  function abrirDetalle(dia, inicio) {
    const fn = { cursos: detalleCurso, docentes: detalleDocente, salas: detalleSala }[estado.vista];
    const contenido = fn && fn(dia, inicio);
    if (!contenido) return;
    estado.seleccion = { dia, inicio };
    const panel = $(`#vista-${estado.vista}`);
    $$('.sesion.seleccionada', panel).forEach(el => el.classList.remove('seleccionada'));
    const celda = $(`.sesion[data-dia="${dia}"][data-inicio="${inicio}"]`, panel);
    if (celda) celda.classList.add('seleccionada');
    // En Cursos se marcan las otras sesiones de la misma asignatura (reemplaza a la leyenda)
    $$('.sesion.misma-asig').forEach(el => el.classList.remove('misma-asig'));
    if (estado.vista === 'cursos' && celda) {
      $$('.sesion', panel).forEach(el => { if (el !== celda && el.dataset.clave === celda.dataset.clave) el.classList.add('misma-asig'); });
    }
    $('#detalle-eyebrow').textContent = contenido.eyebrow;
    $('#detalle-cuerpo').innerHTML = contenido.html;
    detalle.classList.add('abierto');
    detalle.removeAttribute('inert');
    detalle.setAttribute('aria-hidden', 'false');
    $('#detalle-cuerpo').scrollTop = 0;
    animar.detalle($('#detalle-cuerpo'));
  }

  function cerrarDetalle() {
    estado.seleccion = null;
    $$('.sesion.seleccionada').forEach(el => el.classList.remove('seleccionada'));
    $$('.sesion.misma-asig').forEach(el => el.classList.remove('misma-asig'));
    if (!detalle.classList.contains('abierto')) return;
    if (detalle.contains(document.activeElement)) document.activeElement.blur();
    detalle.classList.remove('abierto');
    detalle.setAttribute('inert', '');
    detalle.setAttribute('aria-hidden', 'true');
  }

  // ===========================================================================
  // 12. RENDER GENERAL, PESTAÑAS Y TEMA
  // ===========================================================================
  function moverIndicador() {
    const activa = $(`.pestana[data-vista="${estado.vista}"]`);
    const ind = $('.pestanas-indicador');
    if (!activa || !ind) return;
    ind.style.width = `${activa.offsetWidth}px`;
    ind.style.transform = `translateX(${activa.offsetLeft}px)`;
  }

  function render({ vistaNueva = false, animar: conAnimacion = true } = {}) {
    if (estado.vista !== 'cursos') document.title = `Horarios MMDD ${DATOS.meta.anio}`;
    VISTAS.forEach(v => { $(`#vista-${v}`).hidden = v !== estado.vista; });
    $$('.pestana').forEach(t => {
      const activa = t.dataset.vista === estado.vista;
      t.setAttribute('aria-selected', String(activa));
      t.tabIndex = activa ? 0 : -1;
    });
    moverIndicador();
    switch (estado.vista) {
      case 'cursos': renderCursos(conAnimacion); break;
      case 'docentes': renderDocentes(conAnimacion); break;
      case 'salas': renderSalas(conAnimacion); break;
      case 'bloque': renderBloque(conAnimacion); break;
      default: renderAuditoria(conAnimacion);
    }
    if (vistaNueva && conAnimacion) animar.vista($(`#vista-${estado.vista}`));
  }

  function temaOscuro() {
    const t = document.documentElement.dataset.theme;
    if (t) return t === 'dark';
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  }

  function cambiarTema() {
    const nuevo = temaOscuro() ? 'light' : 'dark';
    document.documentElement.dataset.theme = nuevo;
    guardar('mmdd-tema', nuevo);
    const g = G();
    if (g) g.fromTo('#tema .icono', { rotate: -90, scale: 0.4 }, { rotate: 0, scale: 1, duration: 0.5, ease: 'back.out(2)', clearProps: 'transform' });
  }

  function cerrarSelectores() {
    $$('.selector.abierto').forEach(s => {
      s.classList.remove('abierto');
      $('.selector-toggle', s).setAttribute('aria-expanded', 'false');
    });
    cerrarMenuCursos();
  }

  const menuCursos = $('#curso-menu');
  const botonCursos = $('#curso-boton');

  function abrirMenuCursos() {
    menuCursos.hidden = false;
    botonCursos.setAttribute('aria-expanded', 'true');
    // Cada vez que se abre, el foco parte en el curso que se está viendo
    $$('[data-elegir-curso]', menuCursos).forEach(b => { b.tabIndex = b.getAttribute('aria-current') === 'true' ? 0 : -1; });
    $('[aria-current="true"]', menuCursos).focus();
    animar.aparecer([menuCursos], { y: -6, duracion: 0.2 });
  }

  function cerrarMenuCursos(devolverFoco = false) {
    if (menuCursos.hidden) return;
    menuCursos.hidden = true;
    botonCursos.setAttribute('aria-expanded', 'false');
    if (devolverFoco) botonCursos.focus();
  }

  // Botón vecino en la dirección de la flecha, por su posición en pantalla (vale para 4 o 2 columnas)
  function chipVecino(actual, tecla) {
    const centro = el => { const r = el.getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; };
    const c0 = centro(actual);
    const horizontal = tecla === 'ArrowLeft' || tecla === 'ArrowRight';
    const signo = tecla === 'ArrowRight' || tecla === 'ArrowDown' ? 1 : -1;
    let mejor = null;
    let menor = Infinity;
    $$('[data-elegir-curso]', menuCursos).forEach(el => {
      const c = centro(el);
      const avance = signo * (horizontal ? c.x - c0.x : c.y - c0.y);
      const desvio = Math.abs(horizontal ? c.y - c0.y : c.x - c0.x);
      if (avance > 1 && desvio < 8 && avance < menor) { menor = avance; mejor = el; }
    });
    return mejor;
  }

  function paso(delta) {
    if (estado.vista === 'bloque') { moverBloque(delta); return; }
    const listas = {
      cursos: [CURSOS.map(c => c.id), 'curso'],
      docentes: [DOCENTES.map(d => d.nombre), 'docente'],
      salas: [ESPACIOS.map(e => e.nombre), 'espacio'],
    };
    const par = listas[estado.vista];
    if (!par) return;
    const [lista, campo] = par;
    const i = (lista.indexOf(estado[campo]) + delta + lista.length) % lista.length;
    ir(estado.vista, { [campo]: lista[i] }, { subir: false });
  }

  // ===========================================================================
  // 13. BUSCADOR
  // ===========================================================================
  const indiceBusqueda = [
    ...CURSOS.map(c => ({ tipo: 'Curso', texto: c.nombre, extra: `${CICLO[c.ciclo]} ${c.codigo}`, ir: () => ir('cursos', { curso: c.id }) })),
    ...DOCENTES.map(d => ({ tipo: 'Docente', texto: d.nombre, extra: departamento(d), ir: () => ir('docentes', { docente: d.nombre }) })),
    ...ESPACIOS.map(e => ({ tipo: e.tipo === 'recinto' ? 'Recinto' : 'Sala', texto: nombreEspacio(e.nombre), extra: e.descripcion, ir: () => ir('salas', { espacio: e.nombre }) })),
  ].map(r => ({ ...r, clave: normalizar(`${r.texto} ${r.extra} ${r.tipo}`) }));

  const buscador = $('#buscar');
  const resultados = $('#resultados');
  let encontrados = [];
  let indiceActivo = 0;

  function buscar() {
    const q = normalizar(buscador.value.trim());
    if (!q) { cerrarResultados(); return; }
    const terminos = q.split(/\s+/);
    encontrados = indiceBusqueda
      .filter(r => terminos.every(t => r.clave.includes(t)))
      .sort((a, b) => Number(!normalizar(a.texto).startsWith(terminos[0])) - Number(!normalizar(b.texto).startsWith(terminos[0])))
      .slice(0, 8);
    indiceActivo = 0;
    resultados.innerHTML = encontrados.length
      ? encontrados.map((r, i) => `<li role="option" id="res-${i}" data-i="${i}" aria-selected="${i === 0}">${esc(r.texto)}<span class="tipo">${r.tipo}</span></li>`).join('')
      : '<li class="vacio" role="option" aria-disabled="true">Sin resultados. Prueba con "3 medio", "Inglés 2" o "gimnasio".</li>';
    resultados.hidden = false;
    buscador.setAttribute('aria-expanded', 'true');
  }

  function marcarActivo() {
    $$('li[data-i]', resultados).forEach(li => li.setAttribute('aria-selected', String(Number(li.dataset.i) === indiceActivo)));
    buscador.setAttribute('aria-activedescendant', `res-${indiceActivo}`);
  }

  function elegir(i) {
    const r = encontrados[i];
    if (!r) return;
    buscador.value = '';
    cerrarResultados();
    buscador.blur();
    r.ir();
  }

  function cerrarResultados() {
    resultados.hidden = true;
    buscador.setAttribute('aria-expanded', 'false');
    buscador.removeAttribute('aria-activedescendant');
  }

  buscador.addEventListener('input', buscar);
  buscador.addEventListener('focus', () => { if (buscador.value.trim()) buscar(); });
  buscador.addEventListener('keydown', ev => {
    if (ev.key === 'ArrowDown' && encontrados.length) { ev.preventDefault(); indiceActivo = (indiceActivo + 1) % encontrados.length; marcarActivo(); }
    if (ev.key === 'ArrowUp' && encontrados.length) { ev.preventDefault(); indiceActivo = (indiceActivo - 1 + encontrados.length) % encontrados.length; marcarActivo(); }
    if (ev.key === 'Enter') { ev.preventDefault(); elegir(indiceActivo); }
    if (ev.key === 'Escape') { buscador.value = ''; cerrarResultados(); buscador.blur(); }
  });
  resultados.addEventListener('mousedown', ev => {
    const li = ev.target.closest('li[data-i]');
    if (li) { ev.preventDefault(); elegir(Number(li.dataset.i)); }
  });
  buscador.addEventListener('blur', () => setTimeout(cerrarResultados, 120));

  // ===========================================================================
  // 14. EVENTOS
  // ===========================================================================
  document.addEventListener('click', ev => {
    const t = ev.target.closest('button, [data-tarjeta]');
    if (!t) return;

    if (t.matches('.pestana')) { ir(t.dataset.vista); return; }
    if (t.id === 'tema') { cambiarTema(); return; }
    if (t.id === 'detalle-cerrar') { cerrarDetalle(); return; }
    if (t.matches('.selector-toggle')) {
      const s = t.closest('.selector');
      const abierto = s.classList.toggle('abierto');
      t.setAttribute('aria-expanded', String(abierto));
      if (abierto) animar.aparecer($$('.sel-grupo', s), { y: 8, stagger: 0.03 });
      return;
    }
    if (t === botonCursos) { if (menuCursos.hidden) abrirMenuCursos(); else cerrarMenuCursos(); return; }
    if (t.matches('[data-cerrar-cursos]')) { cerrarMenuCursos(true); return; }
    if (t.matches('[data-elegir-curso]')) {
      cerrarMenuCursos(true);
      ir('cursos', { curso: t.dataset.elegirCurso }, { subir: false });
      return;
    }
    if (t.matches('[data-imprimir]')) { window.print(); return; }
    if (t.matches('[data-paso]')) { paso(Number(t.dataset.paso)); return; }

    if (t.matches('[data-sesion]')) {
      const dia = t.dataset.dia;
      const inicio = Number(t.dataset.inicio);
      if (estado.seleccion && estado.seleccion.dia === dia && estado.seleccion.inicio === inicio && detalle.classList.contains('abierto')) cerrarDetalle();
      else abrirDetalle(dia, inicio);
      return;
    }
    if (t.matches('[data-ir-celda]')) {
      const [dia, b] = t.dataset.irCelda.split('|');
      if (window.matchMedia('(max-width: 719px)').matches) {
        estado.diaMovil = dia;
        aplicarDiaMovil($(`#vista-${estado.vista}`));
      }
      abrirDetalle(dia, Number(b));
      return;
    }
    if (t.matches('[data-dia-movil]')) {
      estado.diaMovil = t.dataset.diaMovil;
      const raiz = t.closest('.panel');
      aplicarDiaMovil(raiz);
      if (estado.vista === 'cursos') animar.aparecer($$('.grilla', raiz), { y: 6, stagger: 0, duracion: 0.25 });
      else animar.grilla($$('.grilla', raiz)[0]);
      return;
    }
    if (t.matches('[data-tarjeta]')) {
      const id = t.dataset.tarjeta;
      const k = clasesCurso.get(id).get(clave(estado.dia, estado.bloque));
      const dia = estado.dia;
      ir('cursos', { curso: id, diaMovil: dia });
      if (k) {
        const pz = segmentar(dia, opcionesGrillaCurso(cursoPorId.get(id))).find(p => p.inicio <= estado.bloque && p.fin >= estado.bloque);
        if (pz) abrirDetalle(dia, pz.inicio);
      }
      return;
    }
    if (t.matches('[data-bloque-dia]')) { estado.dia = t.dataset.bloqueDia; actualizarBloque(); return; }
    if (t.matches('[data-bloque-num]')) { estado.bloque = Number(t.dataset.bloqueNum); actualizarBloque(); return; }
    if (t.id === 'reproducir') { alternarReproduccion(); return; }
    if (t.id === 'ir-ahora') {
      const a = momentoActual();
      if (a && a.bloque) { estado.dia = a.dia; estado.bloque = a.bloque; actualizarBloque(); }
      return;
    }
    if (t.matches('[data-momento]')) {
      const [dia, b] = t.dataset.momento.split('|');
      ir('bloque', { dia, bloque: Number(b) });
      return;
    }
    if (t.matches('[data-curso]')) { ir('cursos', { curso: t.dataset.curso }); return; }
    if (t.matches('[data-docente]')) { ir('docentes', { docente: t.dataset.docente }); return; }
    if (t.matches('[data-espacio]')) { ir('salas', { espacio: t.dataset.espacio }); return; }
    if (t.matches('.leyenda-chip[data-clave]')) {
      const panel = t.closest('.panel');
      estado.resaltado = estado.resaltado === t.dataset.clave ? null : t.dataset.clave;
      resaltar(panel, estado.resaltado, Boolean(estado.resaltado));
    }
  });

  // Resaltado al pasar el cursor por la leyenda (solo con mouse)
  document.addEventListener('pointerover', ev => {
    if (ev.pointerType !== 'mouse') return;
    const chip = ev.target.closest('.leyenda-chip[data-clave]');
    if (chip) resaltar(chip.closest('.panel'), chip.dataset.clave, true);
  });
  document.addEventListener('pointerout', ev => {
    if (ev.pointerType !== 'mouse') return;
    const chip = ev.target.closest('.leyenda-chip[data-clave]');
    if (!chip || chip.contains(ev.relatedTarget)) return;
    const panel = chip.closest('.panel');
    if (estado.resaltado) resaltar(panel, estado.resaltado, true);
    else resaltar(panel, null, false);
  });

  // Tooltip de los gráficos de la auditoría
  const tooltip = $('#tooltip');
  document.addEventListener('pointermove', ev => {
    const el = ev.target.closest('[data-tip]');
    if (!el) { tooltip.hidden = true; return; }
    tooltip.innerHTML = el.dataset.tip;
    tooltip.hidden = false;
    const r = tooltip.getBoundingClientRect();
    const x = Math.min(ev.clientX + 14, window.innerWidth - r.width - 8);
    const y = ev.clientY + 16 + r.height > window.innerHeight ? ev.clientY - r.height - 12 : ev.clientY + 16;
    tooltip.style.left = `${x}px`;
    tooltip.style.top = `${y}px`;
  });
  document.addEventListener('pointerleave', () => { tooltip.hidden = true; });
  window.addEventListener('scroll', () => { tooltip.hidden = true; }, { passive: true });

  $('#filtro-docentes').addEventListener('input', renderSelectorDocentes);
  // Menú de cursos: se cierra al tocar fuera o al salir con Tab; dentro, las flechas recorren los botones
  const elegirCurso = $('.curso-elegir');
  document.addEventListener('pointerdown', ev => {
    if (!menuCursos.hidden && !elegirCurso.contains(ev.target)) cerrarMenuCursos();
  });
  elegirCurso.addEventListener('focusout', ev => {
    if (ev.relatedTarget && !elegirCurso.contains(ev.relatedTarget)) cerrarMenuCursos();
  });
  elegirCurso.addEventListener('keydown', ev => {
    if (ev.key === 'Escape' && !menuCursos.hidden) { ev.stopPropagation(); cerrarMenuCursos(true); return; }
    if (ev.target === botonCursos && ev.key === 'ArrowDown') { ev.preventDefault(); ev.stopPropagation(); abrirMenuCursos(); return; }
    if (!ev.target.matches('[data-elegir-curso]')) return;
    const chips = $$('[data-elegir-curso]', menuCursos);
    let destino;
    if (ev.key === 'Home') destino = chips[0];
    else if (ev.key === 'End') destino = chips[chips.length - 1];
    else if (ev.key.startsWith('Arrow')) destino = chipVecino(ev.target, ev.key);
    else return;
    ev.preventDefault();
    ev.stopPropagation();
    if (destino) { ev.target.tabIndex = -1; destino.tabIndex = 0; destino.focus(); }
  });

  document.addEventListener('keydown', ev => {
    const escribiendo = ev.target.matches('input, textarea');
    if ((ev.key === '/' && !escribiendo) || (ev.key.toLowerCase() === 'k' && (ev.ctrlKey || ev.metaKey))) {
      ev.preventDefault();
      buscador.focus();
      return;
    }
    if (ev.key === 'Escape') {
      if (detalle.classList.contains('abierto')) cerrarDetalle();
      else if (estado.resaltado) { estado.resaltado = null; resaltar($(`#vista-${estado.vista} .panel`), null, false); }
      return;
    }
    if (escribiendo || ev.altKey || ev.ctrlKey || ev.metaKey) return;
    if (ev.target.matches('.pestana') && (ev.key === 'ArrowLeft' || ev.key === 'ArrowRight')) {
      const i = VISTAS.indexOf(estado.vista) + (ev.key === 'ArrowRight' ? 1 : -1);
      const v = VISTAS[(i + VISTAS.length) % VISTAS.length];
      ir(v);
      $(`.pestana[data-vista="${v}"]`).focus();
      return;
    }
    if (ev.key === 'ArrowLeft' || ev.key === 'ArrowRight') {
      ev.preventDefault();
      paso(ev.key === 'ArrowRight' ? 1 : -1);
    }
    if (ev.key === ' ' && estado.vista === 'bloque' && !ev.target.matches('button')) {
      ev.preventDefault();
      alternarReproduccion();
    }
  });

  window.addEventListener('popstate', () => { if (leerHash()) { cerrarDetalle(); render({ vistaNueva: true }); } });
  window.addEventListener('hashchange', () => {
    if (location.hash !== hashActual() && leerHash()) { cerrarDetalle(); render({ vistaNueva: true }); }
  });
  window.addEventListener('resize', moverIndicador);

  // Mantiene al día los marcadores "Hoy" y "Ahora" sin redibujar si nada cambió
  let ultimoMomento = JSON.stringify(momentoActual());
  setInterval(() => {
    const m = JSON.stringify(momentoActual());
    if (m === ultimoMomento) return;
    ultimoMomento = m;
    if (estado.vista !== 'bloque') {
      const seleccion = estado.seleccion;
      render({ animar: false });
      if (seleccion) abrirDetalle(seleccion.dia, seleccion.inicio);
    }
  }, 30000);

  // ===========================================================================
  // 15. INICIO
  // ===========================================================================
  $('#marca-anio').textContent = DATOS.meta.anio;
  $('#pie-datos').textContent = `Horario generado con la semilla ${DATOS.meta.semilla} · ${DATOS.meta.generado} · `
    + `${DATOS.auditoria.metricas.total_bloques_asignados}/${DATOS.auditoria.metricas.total_bloques_esperados} bloques asignados`;

  renderSelectorCursos();
  renderSelectorDocentes();
  renderSelectorSalas();
  // Vuelve al último curso visto (la URL, si trae curso, manda)
  const ultimoCurso = leer('mmdd-curso');
  if (cursoPorId.has(ultimoCurso)) estado.curso = ultimoCurso;
  leerHash();
  render({ animar: true });
  escribirHash(true);
  animar.intro();
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(moverIndicador);
})();
