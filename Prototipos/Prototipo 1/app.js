/* =============================================================================
   Visualizador de horarios - Prototipo 1
   Colegio Madres Dominicas (MMDD) - TGOP, Ingeniería Civil Industrial UdeC

   Lee window.DATOS_HORARIOS (generado por exportar_datos.py) y muestra:
   horario por curso, por docente, vista general por día, recintos deportivos
   y la auditoría de restricciones del generador.
   ============================================================================= */
(function () {
  'use strict';

  // ---------------------------------------------------------------- Catálogos

  const COLORES = {
    'Lenguaje y Comunicación': '#2563EB',
    'Educación Matemática': '#DC2626',
    'Idioma Extranjero Inglés': '#7C3AED',
    'English Skills': '#9333EA',
    'Ciencias Sociales': '#D97706',
    'Historia, Geografía y CC.SS.': '#D97706',
    'Ciencias Naturales': '#059669',
    'Biología': '#16A34A',
    'Química': '#0D9488',
    'Física': '#0891B2',
    'Ciencias para la Ciudadanía': '#65A30D',
    'Educación Física y Salud': '#EA580C',
    'Artes Visuales': '#DB2777',
    'Educación Musical': '#C026D3',
    'Artes Visuales / Música': '#BE185D',
    'Educación Tecnológica': '#64748B',
    'Orientación': '#0284C7',
    'Orientación / Tecnología': '#0284C7',
    'Religión': '#92400E',
    'Filosofía': '#4F46E5',
    'Educación Ciudadana': '#CA8A04',
  };
  const COLORES_FRANJA = ['#57534E', '#78716C', '#9A938B'];

  const CORTOS = {
    'Lenguaje y Comunicación': 'Lenguaje',
    'Educación Matemática': 'Matemática',
    'Idioma Extranjero Inglés': 'Inglés',
    'Historia, Geografía y CC.SS.': 'Historia',
    'Ciencias Sociales': 'C. Sociales',
    'Ciencias Naturales': 'C. Naturales',
    'Ciencias para la Ciudadanía': 'C. Ciudadanía',
    'Educación Física y Salud': 'Ed. Física',
    'Educación Musical': 'Música',
    'Educación Tecnológica': 'Tecnología',
    'Educación Ciudadana': 'Ed. Ciudadana',
    'Artes Visuales': 'Artes',
    'Artes Visuales / Música': 'Artes / Música',
    'Orientación / Tecnología': 'Orient. / Tec.',
  };

  const VISTAS = [
    { id: 'curso', nombre: 'Cursos' },
    { id: 'docente', nombre: 'Docentes' },
    { id: 'dia', nombre: 'Vista por día' },
    { id: 'recintos', nombre: 'Recintos deportivos' },
    { id: 'auditoria', nombre: 'Auditoría' },
  ];

  const DIAS_SEMANA = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'];
  const PISTA_DIA = 'Pasa el cursor sobre una clase para resaltar la jornada de su docente; haz clic para abrir su horario.';

  const svg = d => `<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${d}</svg>`;
  const ICONOS = {
    izq: svg('<path d="m15 18-6-6 6-6"/>'),
    der: svg('<path d="m9 18 6-6-6-6"/>'),
    ok: svg('<path d="M20 6 9 17l-5-5"/>'),
    error: svg('<path d="M18 6 6 18M6 6l12 12"/>'),
    alerta: svg('<path d="M12 9v4M12 17h.01"/><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/>'),
  };

  // ---------------------------------------------------------------- Utilidades

  const $ = (sel, raiz = document) => raiz.querySelector(sel);
  const $$ = (sel, raiz = document) => [...raiz.querySelectorAll(sel)];
  const esc = s => String(s ?? '').replace(/[&<>"']/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
  const natural = (a, b) => a.localeCompare(b, 'es', { numeric: true });
  const sinTildes = s => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const ruta = (vista, valor) => '#/' + vista + (valor ? '/' + encodeURIComponent(valor) : '');
  const aMinutos = hhmm => { const [h, m] = hhmm.split(':').map(Number); return h * 60 + m; };
  const num = n => Number(n).toLocaleString('es-CL');
  const plural = (n, uno, varios) => `${num(n)} ${n === 1 ? uno : varios}`;
  const unir = lista => lista.length > 1 ? `${lista.slice(0, -1).join(', ')} y ${lista[lista.length - 1]}` : (lista[0] || '');

  const esFranja = asig => /^Formación Diferenciada/.test(asig);
  const numeroFranja = asig => Number((asig.match(/(\d+)\s*$/) || [0, 1])[1]);

  function colorDe(asig) {
    if (esFranja(asig)) return COLORES_FRANJA[(numeroFranja(asig) - 1) % COLORES_FRANJA.length];
    return COLORES[asig] || '#64748B';
  }

  function corto(asig) {
    if (esFranja(asig)) return `Electivos F${numeroFranja(asig)}`;
    return CORTOS[asig] || asig;
  }

  const nombreCurso = id => (I && I.cursos.has(id) ? I.cursos.get(id).nombre : id);

  function diaDeHoy() {
    const d = DIAS_SEMANA[new Date().getDay()];
    return D && D.dias.includes(d) ? d : null;
  }

  function bloqueActual() {
    if (!diaDeHoy()) return null;
    const ahora = new Date();
    const m = ahora.getHours() * 60 + ahora.getMinutes();
    for (const [b, [ini, fin]] of Object.entries(D.bloques)) {
      if (m >= aMinutos(ini) && m < aMinutos(fin)) return Number(b);
    }
    return null;
  }

  function textoRecreo(b) {
    const r = D.recreos[b];
    return r ? `${r.nombre} · ${r.horario}` : '';
  }

  function enlaceDocente(nombre) {
    if (I.docentes.has(nombre)) {
      return `<a class="ref" href="${ruta('docente', nombre)}" title="Ver horario de ${esc(nombre)}">${esc(nombre)}</a>`;
    }
    return `<span>${esc(nombre)}</span>`;
  }

  const enlacesDocentes = lista => lista.map(enlaceDocente).join(' · ');

  function enlaceCurso(id, texto, clase = 'ref') {
    return I.cursos.has(id) ? `<a class="${clase}" href="${ruta('curso', id)}">${esc(texto || nombreCurso(id))}</a>` : `<span class="${clase}">${esc(texto || id)}</span>`;
  }

  function aviso(texto) {
    const el = $('#aviso');
    el.textContent = texto;
    el.classList.add('visible');
    clearTimeout(aviso.t);
    aviso.t = setTimeout(() => el.classList.remove('visible'), 3500);
  }

  // ---------------------------------------------------------------- Estado e índices

  let D = null;   // datos tal como vienen del exportador
  let I = null;   // índices derivados
  const estado = { vista: 'curso', curso: null, docente: null, dia: null, diaMovil: null, busqueda: '', ant: null, sig: null };

  function indexar(datos) {
    const cursos = new Map(datos.cursos.map(c => [c.id, c]));
    const docentes = new Map();

    for (const original of datos.docentes) {
      const d = { ...original, horas: 0, ventanas: 0, diasConClase: 0, huecos: {}, grupos: new Set() };
      for (const dia of datos.dias) {
        const clases = d.clases[dia] || {};
        const bs = Object.keys(clases).map(Number);
        d.horas += bs.length;
        if (!bs.length) continue;
        d.diasConClase++;
        Object.values(clases).forEach(x => d.grupos.add(x.grupo));
        for (let b = Math.min(...bs); b <= Math.max(...bs); b++) {
          if (!bs.includes(b)) {
            d.ventanas++;
            (d.huecos[dia] ||= new Set()).add(b);
          }
        }
      }
      d.jefaturas = datos.cursos.filter(c => c.jefe === d.id).map(c => c.id);
      docentes.set(d.id, d);
    }

    const listaDocentes = [...docentes.values()].sort((a, b) => natural(a.id, b.id));
    return { cursos, docentes, listaDocentes };
  }

  function leerRuta() {
    let h = '';
    try { h = decodeURIComponent(location.hash.replace(/^#\/?/, '')); } catch (e) { h = ''; }
    const i = h.indexOf('/');
    let vista = i < 0 ? h : h.slice(0, i);
    const valor = i < 0 ? '' : h.slice(i + 1);
    if (!VISTAS.some(v => v.id === vista)) vista = 'curso';
    estado.vista = vista;

    if (vista === 'curso') {
      estado.curso = I.cursos.has(valor) ? valor : (I.cursos.has(estado.curso) ? estado.curso : D.cursos[0].id);
    } else if (vista === 'docente') {
      estado.docente = I.docentes.has(valor) ? valor : (I.docentes.has(estado.docente) ? estado.docente : I.listaDocentes[0].id);
    } else if (vista === 'dia') {
      estado.dia = D.dias.includes(valor) ? valor : (estado.dia || diaDeHoy() || D.dias[0]);
    }
  }

  // ---------------------------------------------------------------- Bloques combinados

  // Une bloques consecutivos con la misma clave (un bloque doble de 90 min),
  // sin cruzar nunca un recreo.
  function segmentos(dia, maxB, celda) {
    const out = [];
    for (let b = 1; b <= maxB; b++) {
      const c = celda(dia, b);
      const prev = out[out.length - 1];
      if (prev && c.clave && prev.celda.clave === c.clave && prev.hasta === b - 1 && !D.recreos[b - 1]) {
        prev.hasta = b;
      } else {
        out.push({ desde: b, hasta: b, celda: c });
      }
    }
    return out;
  }

  const rangoHorario = s => `${D.bloques[s.desde][0]}–${D.bloques[s.hasta][1]}`;

  function celdaTabla(s) {
    const c = s.celda;
    const n = s.hasta - s.desde + 1;
    const rs = n > 1 ? ` rowspan="${n}"` : '';
    if (c.tipo === 'off') return `<td class="slot off"${rs} title="Fuera de la jornada del curso"></td>`;
    if (c.tipo === 'vacio') return `<td class="slot vacio"${rs}></td>`;
    if (c.tipo === 'ventana') return `<td class="slot ventana"${rs} title="Bloque libre entre dos clases">Ventana</td>`;
    const titulo = `${c.titulo} · ${rangoHorario(s)}${n > 1 ? ' (bloque doble)' : ''}`;
    return `<td class="slot" style="--c:${c.color}" data-k="${esc(c.k)}"${rs} title="${esc(titulo)}"><div class="slot-in">${c.html}</div></td>`;
  }

  function tablaSemanal(maxB, celda) {
    const hoy = diaDeHoy();
    const ahora = bloqueActual();
    const porDia = {};
    for (const dia of D.dias) porDia[dia] = new Map(segmentos(dia, maxB, celda).map(s => [s.desde, s]));

    let html = `<table class="tt resaltable"><colgroup><col class="col-hora">${D.dias.map(() => '<col>').join('')}</colgroup>`;
    html += `<thead><tr><th scope="col">Bloque</th>${D.dias.map(d =>
      `<th scope="col" class="${d === hoy ? 'hoy' : ''}">${d}${d === hoy ? '<span class="etiqueta-hoy">HOY</span>' : ''}</th>`).join('')}</tr></thead><tbody>`;

    for (let b = 1; b <= maxB; b++) {
      const [ini, fin] = D.bloques[b];
      html += `<tr><th scope="row" class="hora${b === ahora ? ' ahora' : ''}"><b>Bloque ${b}</b><span>${ini}–${fin}</span></th>`;
      for (const dia of D.dias) {
        const s = porDia[dia].get(b);
        if (s) html += celdaTabla(s);   // si no hay, el bloque está cubierto por un rowspan
      }
      html += '</tr>';
      if (D.recreos[b] && b < maxB) html += `<tr class="recreo"><td colspan="${D.dias.length + 1}">${esc(textoRecreo(b))}</td></tr>`;
    }
    return html + '</tbody></table>';
  }

  function listaDelDia(maxB, celda) {
    const segs = segmentos(estado.diaMovil, maxB, celda);
    const ultimoUtil = Math.max(0, ...segs.filter(s => s.celda.tipo !== 'off').map(s => s.hasta));
    let html = '';
    for (const s of segs) {
      const c = s.celda;
      if (c.tipo === 'off') continue;
      const etiqueta = s.hasta > s.desde ? `Bloques ${s.desde}–${s.hasta}` : `Bloque ${s.desde}`;
      const hora = `<div class="item-hora"><b>${etiqueta}</b><span>${rangoHorario(s)}</span></div>`;
      if (c.tipo === 'clase') {
        html += `<div class="item" style="--c:${c.color}">${hora}<div class="slot-in">${c.html}</div></div>`;
      } else if (c.tipo === 'ventana') {
        html += `<div class="item ventana">${hora}<div>Ventana</div></div>`;
      } else {
        html += `<div class="item vacio">${hora}<div class="libre">Libre</div></div>`;
      }
      if (D.recreos[s.hasta] && s.hasta < ultimoUtil) html += `<p class="item-recreo">${esc(textoRecreo(s.hasta))}</p>`;
    }
    return html || '<p class="item-nada">Sin clases este día.</p>';
  }

  function horarioSemanal(maxB, celda) {
    if (!D.dias.includes(estado.diaMovil)) estado.diaMovil = diaDeHoy() || D.dias[0];
    const botones = D.dias.map(d =>
      `<button type="button" data-dia-movil="${esc(d)}" aria-pressed="${d === estado.diaMovil}">${esc(d.slice(0, 3))}</button>`).join('');
    return `<div class="tt-wrap">${tablaSemanal(maxB, celda)}</div>
      <div class="dia-lista resaltable"><div class="segmentado" role="group" aria-label="Día">${botones}</div>${listaDelDia(maxB, celda)}</div>`;
  }

  // ---------------------------------------------------------------- Piezas comunes

  function cabeceraVista({ eyebrow, titulo, meta = [], paginador = null, extra = '' }) {
    let pag = '';
    if (paginador) {
      estado.ant = paginador.ant.href;
      estado.sig = paginador.sig.href;
      pag = `<div class="paginador no-print">
        <a class="btn btn-icono" href="${paginador.ant.href}" title="Anterior: ${esc(paginador.ant.nombre)} (tecla ←)" aria-label="Anterior: ${esc(paginador.ant.nombre)}">${ICONOS.izq}</a>
        ${paginador.selector}
        <a class="btn btn-icono" href="${paginador.sig.href}" title="Siguiente: ${esc(paginador.sig.nombre)} (tecla →)" aria-label="Siguiente: ${esc(paginador.sig.nombre)}">${ICONOS.der}</a>
      </div>`;
    }
    return `<header class="vista-cab">
      <div>
        <p class="eyebrow">${eyebrow}</p>
        <h2>${titulo}</h2>
        ${meta.length ? `<p class="vista-meta">${meta.join('<span class="sep">·</span>')}</p>` : ''}
      </div>
      ${pag}${extra}
    </header>`;
  }

  function indicador(etiqueta, valor, contexto = '', tono = '') {
    const icono = tono === 'ok' ? ICONOS.ok : tono === 'bad' ? ICONOS.alerta : '';
    return `<div class="indicador"><p class="ind-etiqueta">${etiqueta}</p><p class="ind-valor">${valor}</p>
      ${contexto ? `<p class="ind-contexto ${tono}">${icono}${contexto}</p>` : ''}</div>`;
  }

  function agrupar(lista, clave, orden = []) {
    const grupos = new Map(orden.map(g => [g, []]));
    for (const x of lista) {
      const g = clave(x);
      if (!grupos.has(g)) grupos.set(g, []);
      grupos.get(g).push(x);
    }
    return [...grupos].filter(([, xs]) => xs.length);
  }

  const cursosPorCiclo = () => agrupar(D.cursos, c => c.ciclo);
  const docentesPorDepartamento = () => agrupar(I.listaDocentes, d => d.departamento, D.departamentos || []);

  function selectorCursos() {
    const grupos = cursosPorCiclo().map(([ciclo, cs]) =>
      `<optgroup label="${esc(ciclo)}">${cs.map(c =>
        `<option value="${esc(ruta('curso', c.id))}"${c.id === estado.curso ? ' selected' : ''}>${esc(c.nombre)}</option>`).join('')}</optgroup>`).join('');
    return `<select class="selector solo-movil" data-navegar aria-label="Elegir curso">${grupos}</select>`;
  }

  function selectorDocentes() {
    const grupos = docentesPorDepartamento().map(([g, ds]) =>
      `<optgroup label="${esc(g)}">${ds.map(d =>
        `<option value="${esc(ruta('docente', d.id))}"${d.id === estado.docente ? ' selected' : ''}>${esc(d.id)}</option>`).join('')}</optgroup>`).join('');
    return `<select class="selector solo-movil" data-navegar aria-label="Elegir docente">${grupos}</select>`;
  }

  function vecinos(lista, actual, href, nombre) {
    const n = lista.length;
    const pos = lista.indexOf(actual);
    const ant = lista[(pos - 1 + n) % n];
    const sig = lista[(pos + 1) % n];
    return { ant: { href: href(ant), nombre: nombre(ant) }, sig: { href: href(sig), nombre: nombre(sig) } };
  }

  // ---------------------------------------------------------------- Vista: curso

  // Electivos de una franja que corresponden a un curso ('4A' solo a 4° Medio A; 'S.1' o '4AB' a ambos)
  function gruposFranja(curso, nombreFranja) {
    const nivel = curso.id.slice(0, -2);
    const franja = ((D.franjas || {})[nivel] || []).find(f => f.nombre === nombreFranja);
    if (!franja) return [];
    const propia = nivel[0] + curso.seccion;
    return franja.grupos.filter(g => !/^\d[AB]$/.test(g.seccion) || g.seccion === propia);
  }

  function vistaCurso() {
    const c = I.cursos.get(estado.curso);
    const asig = D.asignaciones[c.id];
    const maxB = Math.max(...D.dias.flatMap(d => c.bloquesPermitidos[d]));

    const celda = (dia, b) => {
      if (!c.bloquesPermitidos[dia].includes(b)) return { tipo: 'off', clave: 'off' };
      const it = asig[dia][b];
      if (!it) return { tipo: 'vacio', clave: null };
      const clave = it.asignatura + '::' + it.docentes.join('|');
      if (esFranja(it.asignatura)) {
        const pareja = asig[dia][b % 2 ? b + 1 : b - 1];
        const etiquetas = [...new Set([it.etiqueta, pareja && pareja.asignatura === it.asignatura ? pareja.etiqueta : null].filter(Boolean))];
        return {
          tipo: 'clase', clave, k: it.asignatura, color: colorDe(it.asignatura),
          titulo: `${it.asignatura}: ${etiquetas.join(' · ')}`,
          html: `<span class="slot-titulo">${esc(corto(it.asignatura))}</span><span class="slot-sub">${esc(etiquetas.join(' · '))}</span>`,
        };
      }
      const lugar = it.recinto || (it.espacio !== 'Aula' ? it.espacio : '');
      return {
        tipo: 'clase', clave, k: it.asignatura, color: colorDe(it.asignatura),
        titulo: `${it.asignatura} — ${unir(it.docentes)}${lugar ? ' — ' + lugar : ''}`,
        html: `<span class="slot-titulo">${esc(corto(it.asignatura))}</span><span class="slot-sub">${enlacesDocentes(it.docentes)}</span>${lugar ? `<span class="slot-tag">${esc(lugar)}</span>` : ''}`,
      };
    };

    const horas = {};
    for (const dia of D.dias) for (const it of Object.values(asig[dia])) horas[it.asignatura] = (horas[it.asignatura] || 0) + 1;
    const asignadas = Object.values(horas).reduce((a, b) => a + b, 0);

    const filas = c.malla.map(m => {
      const h = horas[m.asignatura] || 0;
      const ok = h === m.horas;
      let detalle;
      if (esFranja(m.asignatura)) {
        const grupos = gruposFranja(c, m.asignatura);
        detalle = grupos.length
          ? `<ul class="ley-electivos">${grupos.map(g => `<li>${esc(g.asignatura)} <span class="seccion">${esc(g.seccion)}</span><br>${enlaceDocente(g.docente)} · ${esc(g.sala)}</li>`).join('')}</ul>`
          : `<span class="ley-sub">${enlacesDocentes(m.docentes)}</span>`;
      } else {
        detalle = `<span class="ley-sub">${enlacesDocentes(m.docentes)}${m.espacio !== 'Aula' ? ' · ' + esc(m.espacio) : ''}</span>`;
      }
      return `<li class="ley-fila" data-resalta="${esc(m.asignatura)}" tabindex="0">
        <span class="ley-color" style="--c:${colorDe(m.asignatura)}"></span>
        <span><span class="ley-nombre">${esc(esFranja(m.asignatura) ? m.asignatura.replace('Formación Diferenciada', 'Formación diferenciada') : m.asignatura)}</span>${detalle}</span>
        <span class="ley-horas${ok ? '' : ' mal'}" title="${ok ? 'Horas asignadas según el plan' : `Asignadas ${h} de ${m.horas} exigidas`}">${ok ? `${h} h` : `${h}/${m.horas} h`}</span>
      </li>`;
    }).join('');

    const meta = [];
    if (c.jefe) meta.push(`Profesor(a) jefe: ${I.docentes.has(c.jefe) ? `<a class="enlace" href="${ruta('docente', c.jefe)}">${esc(c.jefe)}</a>` : esc(c.jefe)}`);
    meta.push(c.parvulo ? 'Solo se programa Educación Física (comparte docente y gimnasio con básica)' : `${c.carga} horas pedagógicas semanales`);

    const head = cabeceraVista({
      eyebrow: `Curso · ${esc(c.ciclo)}`,
      titulo: esc(c.nombre),
      meta,
      paginador: { ...vecinos(D.cursos, c, x => ruta('curso', x.id), x => x.nombre), selector: selectorCursos() },
    });

    return `${head}
      <div class="contenido">
        <section class="tarjeta" aria-label="Horario semanal">${horarioSemanal(maxB, celda)}</section>
        <aside class="tarjeta">
          <div class="tarjeta-cab"><h3>Carga por asignatura</h3><span class="nota">${asignadas} / ${c.carga} h</span></div>
          <ul class="leyenda">${filas}</ul>
          <p class="ley-pie no-print">Pasa el cursor sobre una asignatura para ubicarla en el horario. Haz clic en un docente para ver su horario.</p>
        </aside>
      </div>`;
  }

  // ---------------------------------------------------------------- Vista: docente

  function vistaDocente() {
    const d = I.docentes.get(estado.docente);
    const tieneTarde = D.dias.some(dia => Object.keys(d.clases[dia] || {}).some(b => Number(b) > 8));
    const maxB = tieneTarde ? 10 : 8;

    const celda = (dia, b) => {
      const it = (d.clases[dia] || {})[b];
      if (it) {
        const co = it.coDocentes && it.coDocentes.length ? `<span class="slot-sub">con ${it.coDocentes.map(enlaceDocente).join(' y ')}</span>` : '';
        const sala = it.sala ? `<span class="slot-tag">${esc(it.sala)}</span>` : '';
        const titulo = it.cursos.length ? enlaceCurso(it.cursos[0], it.grupoNombre, 'slot-titulo') : `<span class="slot-titulo">${esc(it.grupoNombre)}</span>`;
        return {
          tipo: 'clase',
          clave: it.grupo + '::' + it.asignatura,
          k: it.grupo + '::' + it.asignatura,
          color: colorDe(it.base),
          titulo: `${it.grupoNombre} — ${it.asignatura}${it.sala ? ' — ' + it.sala : ''}`,
          html: `${titulo}<span class="slot-sub" title="${esc(it.asignatura)}">${esc(corto(it.asignatura))}</span>${co}${sala}`,
        };
      }
      if (d.huecos[dia] && d.huecos[dia].has(b)) return { tipo: 'ventana', clave: 'ventana' };
      return { tipo: 'vacio', clave: 'vacio' };
    };

    // Resumen por grupo (curso o electivo compartido) y asignatura
    const porGrupo = new Map();
    for (const dia of D.dias) {
      for (const it of Object.values(d.clases[dia] || {})) {
        if (!porGrupo.has(it.grupo)) porGrupo.set(it.grupo, { info: it, asignaturas: new Map() });
        const g = porGrupo.get(it.grupo).asignaturas;
        if (!g.has(it.asignatura)) g.set(it.asignatura, { horas: 0, base: it.base, sala: it.sala });
        g.get(it.asignatura).horas++;
      }
    }
    const ordenCurso = id => { const i = D.cursos.findIndex(c => c.id === id); return i < 0 ? 999 : i; };
    const grupos = [...porGrupo.values()].sort((a, b) => ordenCurso(a.info.cursos[0]) - ordenCurso(b.info.cursos[0]) || natural(a.info.grupo, b.info.grupo));
    const filas = grupos.map(({ info, asignaturas }) => {
      const total = [...asignaturas.values()].reduce((s, x) => s + x.horas, 0);
      const cab = info.cursos.length ? enlaceCurso(info.cursos[0], info.grupoNombre, 'enlace') : esc(info.grupoNombre);
      const filasGrupo = [...asignaturas].map(([a, x]) => `<li class="ley-fila" data-resalta="${esc(info.grupo + '::' + a)}" tabindex="0">
          <span class="ley-color" style="--c:${colorDe(x.base)}"></span>
          <span><span class="ley-nombre">${esc(a)}</span>${x.sala ? `<span class="ley-sub">${esc(x.sala)}</span>` : ''}</span>
          <span class="ley-horas">${x.horas} h</span></li>`).join('');
      return `<li class="ley-bloque"><div class="ley-grupo">${cab}<span>${total} h</span></div><ul class="ley-lista">${filasGrupo}</ul></li>`;
    }).join('');

    const otras = (d.horasNoLectivas || []).length
      ? `<div class="ley-pie"><b>Horas fuera de la grilla</b><ul class="ley-electivos">${d.horasNoLectivas.map(x =>
          `<li>${esc(x.actividad)}${x.cursos ? ` <span class="seccion">${esc(x.cursos)}</span>` : ''} · ${x.horas} h</li>`).join('')}</ul></div>` : '';

    const meta = [`${plural(d.horas, 'hora', 'horas')} en la grilla semanal`];
    if (d.jefaturas.length) meta.push(`Profesor(a) jefe de ${unir(d.jefaturas.map(id => `<a class="enlace" href="${ruta('curso', id)}">${esc(nombreCurso(id))}</a>`))}`);

    const head = cabeceraVista({
      eyebrow: `Docente · ${esc(d.departamento)}`,
      titulo: esc(d.id),
      meta,
      paginador: { ...vecinos(I.listaDocentes, d, x => ruta('docente', x.id), x => x.id), selector: selectorDocentes() },
    });

    const indicadores = `<div class="indicadores">
      ${indicador('Horas en la grilla', num(d.horas), 'bloques pedagógicos por semana')}
      ${indicador('Cursos y grupos', num(d.grupos.size), 'cursos o grupos de electivo')}
      ${indicador('Ventanas', num(d.ventanas), d.ventanas === 0 ? 'jornada sin bloques muertos' : 'bloques libres entre clases')}
      ${indicador('Días con clases', `${d.diasConClase} <small>de ${D.dias.length}</small>`)}
    </div>`;

    return `${head}${indicadores}
      <div class="contenido">
        <section class="tarjeta" aria-label="Horario semanal del docente">${horarioSemanal(maxB, celda)}</section>
        <aside class="tarjeta">
          <div class="tarjeta-cab"><h3>Cursos y asignaturas</h3><span class="nota">${d.horas} h</span></div>
          <ul class="leyenda">${filas}</ul>
          ${otras}
          <p class="ley-pie no-print">Las <b>ventanas</b> son bloques libres entre dos clases del mismo día; el generador busca minimizarlas.</p>
        </aside>
      </div>`;
  }

  // ---------------------------------------------------------------- Vista: por día

  function vistaDia() {
    const dia = estado.dia;
    const maxB = Math.max(...D.cursos.map(c => Math.max(...c.bloquesPermitidos[dia])));
    const bloques = Array.from({ length: maxB }, (_, i) => i + 1);
    const trasRecreo = b => (D.recreos[b - 1] ? ' tras-recreo' : '');

    const dias = D.dias.map(d => `<a href="${ruta('dia', d)}"${d === dia ? ' aria-current="page"' : ''}>${esc(d)}</a>`).join('');
    const head = cabeceraVista({
      eyebrow: 'Vista general',
      titulo: `Todos los cursos · ${esc(dia)}`,
      meta: ['Cada fila es un curso y cada columna un bloque horario'],
      extra: `<nav class="segmentado no-print" aria-label="Día">${dias}</nav>`,
    });

    let filas = '';
    for (const [ciclo, cursos] of cursosPorCiclo()) {
      filas += `<tr class="grupo"><th colspan="${maxB + 1}">${esc(ciclo)}</th></tr>`;
      for (const c of cursos) {
        const celda = (d, b) => {
          if (!c.bloquesPermitidos[d].includes(b)) return { tipo: 'off', clave: 'off' };
          const it = D.asignaciones[c.id][d][b];
          if (!it) return { tipo: 'vacio', clave: 'vacio' };
          return { tipo: 'clase', clave: it.asignatura + '::' + it.docentes.join('|'), it };
        };
        filas += `<tr><th scope="row" class="curso"><a href="${ruta('curso', c.id)}">${esc(c.nombre)}</a></th>`;
        for (const s of segmentos(dia, maxB, celda)) {
          const n = s.hasta - s.desde + 1;
          const cs = n > 1 ? ` colspan="${n}"` : '';
          const x = s.celda;
          if (x.tipo !== 'clase') {
            filas += `<td class="${trasRecreo(s.desde)}"${cs}><span class="celda ${x.tipo}"></span></td>`;
            continue;
          }
          const it = x.it;
          const franja = esFranja(it.asignatura);
          const destino = franja ? ruta('curso', c.id) : ruta('docente', it.docentes[0]);
          const accion = franja ? 'Clic para ver el curso.' : 'Clic para ver el horario del docente.';
          const titulo = `${it.asignatura} — ${franja ? it.etiqueta : unir(it.docentes)} · ${rangoHorario(s)}. ${accion}`;
          filas += `<td class="${trasRecreo(s.desde)}"${cs}><a class="celda" style="--c:${colorDe(it.asignatura)}" href="${destino}"
            data-k="${esc(it.docentes.join('|'))}" data-resalta="${esc(it.docentes.join('|'))}" title="${esc(titulo)}">${esc(corto(it.asignatura))}</a></td>`;
        }
        filas += '</tr>';
      }
    }

    const ahora = dia === diaDeHoy() ? bloqueActual() : null;
    const cabecera = bloques.map(b =>
      `<th scope="col" class="${trasRecreo(b)}">B${b}${b === ahora ? ' · ahora' : ''}<span>${D.bloques[b][0]}</span></th>`).join('');

    return `${head}
      <p class="pista no-print" id="pista">${PISTA_DIA}</p>
      <div class="tabla-scroll">
        <table class="dt resaltable">
          <colgroup><col class="col-curso">${bloques.map(() => '<col>').join('')}</colgroup>
          <thead><tr><th scope="col">Curso</th>${cabecera}</tr></thead>
          <tbody>${filas}</tbody>
        </table>
      </div>`;
  }

  // ---------------------------------------------------------------- Vista: recintos deportivos

  function vistaRecintos() {
    const R = D.recintos;
    const usoDe = (dia, b) => ((R.uso[dia] || {})[b]) || {};
    const usados = D.dias.flatMap(d => Object.keys(R.uso[d] || {}).map(Number));
    const maxB = usados.some(b => b > 8) ? 10 : 8;
    const capacidadTotal = R.nombres.reduce((s, r) => s + (R.capacidad[r] || 1), 0);

    let totalHoras = 0, llenos = 0, conflictos = 0;
    const porRecinto = Object.fromEntries(R.nombres.map(r => [r, 0]));
    for (const d of D.dias) {
      for (const recintos of Object.values(R.uso[d] || {})) {
        let enBloque = 0;
        for (const [r, cursos] of Object.entries(recintos)) {
          totalHoras += cursos.length;
          enBloque += cursos.length;
          porRecinto[r] = (porRecinto[r] || 0) + 1;
          if (cursos.length > (R.capacidad[r] || 1)) conflictos++;
        }
        if (enBloque >= capacidadTotal) llenos++;
      }
    }

    const abreviado = r => r.replace(/^Gimnasio/, 'Gim.').replace('Patio Santo Domingo', 'Patio Sto. Domingo');
    const hoy = diaDeHoy();
    let filas = '';
    for (let b = 1; b <= maxB; b++) {
      const [ini, fin] = D.bloques[b];
      filas += `<tr><th scope="row" class="hora"><b>Bloque ${b}</b><span>${ini}–${fin}</span></th>`;
      for (const d of D.dias) {
        const uso = usoDe(d, b);
        const lineas = R.nombres.filter(r => (uso[r] || []).length).map(r => {
          const cursos = uso[r];
          const excede = cursos.length > (R.capacidad[r] || 1);
          const chips = cursos.map(c => {
            const it = D.asignaciones[c][d][b];
            return `<a class="mini" href="${ruta('curso', c)}" title="${esc(nombreCurso(c))}${it ? ' — ' + esc(unir(it.docentes)) : ''}">${esc(nombreCurso(c))}</a>`;
          }).join('');
          return `<div class="rec${excede ? ' excede' : ''}"><span class="rec-nombre">${excede ? ICONOS.alerta : ''}${esc(abreviado(r))}</span>${chips}</div>`;
        }).join('');
        filas += `<td>${lineas || '<span class="libre">Libre</span>'}</td>`;
      }
      filas += '</tr>';
      if (D.recreos[b] && b < maxB) filas += `<tr class="recreo"><td colspan="${D.dias.length + 1}">${esc(textoRecreo(b))}</td></tr>`;
    }

    const capacidades = R.nombres.map(r => `${r} (${R.capacidad[r] || 1})`);
    const head = cabeceraVista({
      eyebrow: 'Recursos compartidos',
      titulo: 'Recintos deportivos',
      meta: [`Cursos por bloque en ${unir(capacidades)}`],
    });

    const tilesRecintos = R.nombres.map(r => {
      const esPatio = /patio/i.test(r);
      return indicador(esc(r), num(porRecinto[r] || 0), esPatio ? 'bloques usados · uso penalizado, solo desborde' : 'bloques usados en la semana');
    }).join('');
    const indicadores = `<div class="indicadores">
      ${indicador('Horas de Ed. Física', num(totalHoras), 'cursos × bloque, incluye párvulos')}
      ${tilesRecintos}
      ${indicador('Conflictos de aforo', num(conflictos), conflictos ? 'más cursos que recintos en un bloque' : 'ningún recinto compartido', conflictos ? 'bad' : 'ok')}
    </div>`;

    return `${head}${indicadores}
      <div class="tabla-scroll">
        <table class="dt rt">
          <colgroup><col class="col-curso">${D.dias.map(() => '<col>').join('')}</colgroup>
          <thead><tr><th scope="col">Bloque</th>${D.dias.map(d => `<th scope="col">${esc(d)}${d === hoy ? '<span class="etiqueta-hoy">HOY</span>' : ''}</th>`).join('')}</tr></thead>
          <tbody>${filas}</tbody>
        </table>
      </div>
      <p class="pista" style="margin-top:10px">${plural(llenos, 'bloque tiene', 'bloques tienen')} todos los recintos ocupados. El generador asigna primero el gimnasio de cada zona (B: párvulos y 1° a 4° básico; A: 5° básico a 4° medio) y envía el desborde al patio.</p>`;
  }

  // ---------------------------------------------------------------- Vista: auditoría

  function vistaAuditoria() {
    const a = D.auditoria;
    const m = a.metricas;
    const requerido = m.total_bloques_esperados ?? D.cursos.reduce((s, c) => s + c.carga, 0);
    const nErrores = a.restricciones.reduce((s, r) => s + r.errores.length, 0) + (a.otrosErrores || []).length;
    const regulares = D.cursos.filter(c => !c.parvulo).length;
    const parvulos = D.cursos.length - regulares;

    const banner = a.valido
      ? `<div class="banner ok">${ICONOS.ok}<div><b>Horario factible</b><p>Cumple el 100% de las restricciones duras auditadas por el generador.</p></div></div>`
      : `<div class="banner bad">${ICONOS.alerta}<div><b>Horario con conflictos</b><p>Se detectaron ${plural(nErrores, 'incumplimiento', 'incumplimientos')} de restricciones duras. Revisa el detalle abajo.</p></div></div>`;

    const advertencias = (a.advertencias || []).length
      ? `<div class="banner warn">${ICONOS.alerta}<div><b>Advertencias</b><p>${a.advertencias.map(esc).join('<br>')}</p></div></div>` : '';

    const bloquesOk = m.total_bloques_asignados === requerido;
    const indicadores = `<div class="indicadores">
      ${indicador('Bloques asignados', num(m.total_bloques_asignados), `de ${num(requerido)} exigidos por los planes`, bloquesOk ? 'ok' : 'bad')}
      ${indicador('Bloques dobles', `${num(m.porcentaje_bloques_dobles)} <small>%</small>`, 'de las horas en pares de 90 min')}
      ${indicador('Ventanas docentes', num(m.total_ventanas_docentes), `bloques libres entre clases (${m.docentes_auditados} docentes)`)}
      ${indicador('Cursos programados', num(D.cursos.length), parvulos ? `${regulares} regulares y ${parvulos} de párvulos` : '1° Básico a 4° Medio, A y B')}
    </div>`;

    const restricciones = a.restricciones.map(r => {
      const ok = r.errores.length === 0;
      const detalle = ok ? '' : `<details><summary>Ver ${plural(r.errores.length, 'error', 'errores')}</summary><ul>${r.errores.map(e => `<li>${esc(e)}</li>`).join('')}</ul></details>`;
      return `<li class="restriccion">
        <span class="estado-ico ${ok ? 'ok' : 'bad'}">${ok ? ICONOS.ok : ICONOS.error}</span>
        <div><b><span class="codigo">${esc(r.codigo)}</span>${esc(r.nombre)}</b><p>${esc(r.descripcion)}</p>${detalle}</div>
        <span class="resultado ${ok ? 'ok' : 'bad'}">${ok ? 'Cumple' : plural(r.errores.length, 'error', 'errores')}</span>
      </li>`;
    }).join('');

    const conVentanas = I.listaDocentes.filter(d => d.ventanas > 0).sort((x, y) => y.ventanas - x.ventanas || natural(x.id, y.id));
    const maxV = Math.max(1, ...conVentanas.map(d => d.ventanas));
    const barra = d => `<a class="barra-fila" href="${ruta('docente', d.id)}" title="${esc(d.id)}: ${plural(d.ventanas, 'ventana', 'ventanas')} en ${plural(d.horas, 'hora', 'horas')} de clases">
        <span class="barra-nombre">${esc(d.id)}</span>
        <span class="barra-pista"><span class="barra" style="width:${(d.ventanas / maxV * 100).toFixed(1)}%"></span></span>
        <span class="barra-valor">${d.ventanas}</span></a>`;
    const LIMITE = 12;
    const sinVentanas = I.listaDocentes.length - conVentanas.length;
    const barras = conVentanas.length
      ? `<div class="barras">${conVentanas.slice(0, LIMITE).map(barra).join('')}</div>
         ${conVentanas.length > LIMITE ? `<details class="barras-mas"><summary>Ver ${conVentanas.length - LIMITE} docentes más</summary><div class="barras">${conVentanas.slice(LIMITE).map(barra).join('')}</div></details>` : ''}`
      : '<p class="libre">Ningún docente tiene ventanas.</p>';

    const otros = (a.otrosErrores || []).length
      ? `<section class="tarjeta" style="margin-top:16px"><div class="tarjeta-cab"><h3>Otros errores</h3></div><ul>${a.otrosErrores.map(e => `<li>${esc(e)}</li>`).join('')}</ul></section>` : '';

    const head = cabeceraVista({
      eyebrow: 'Calidad de la solución',
      titulo: 'Auditoría de restricciones',
      meta: [`Resultado de ValidadorRestricciones para la semilla ${esc(D.meta.semilla)}`],
    });

    return `${head}${banner}${advertencias}${indicadores}
      <div class="dos-col">
        <section class="tarjeta">
          <div class="tarjeta-cab"><h3>Restricciones duras</h3><span class="nota">${a.restricciones.filter(r => !r.errores.length).length} de ${a.restricciones.length} cumplidas</span></div>
          <ul class="restricciones">${restricciones}</ul>
        </section>
        <section class="tarjeta">
          <div class="tarjeta-cab"><h3>Ventanas por docente</h3><span class="nota">${sinVentanas} sin ventanas</span></div>
          ${barras}
        </section>
      </div>${otros}`;
  }

  // ---------------------------------------------------------------- Panel lateral y pestañas

  function renderPestanas() {
    const valor = { curso: estado.curso, docente: estado.docente, dia: estado.dia };
    $('#pestanas').innerHTML = VISTAS.map(v =>
      `<a class="pestana" href="${ruta(v.id, valor[v.id])}"${v.id === estado.vista ? ' aria-current="page"' : ''}>${v.nombre}</a>`).join('');
  }

  function renderLateral() {
    const lat = $('#lateral');
    if (estado.vista === 'curso') {
      const grupos = cursosPorCiclo().map(([ciclo, cs]) => {
        const filas = agrupar(cs, c => c.nivel).map(([nivel, secciones]) =>
          `<div class="nivel"><span class="nivel-nombre">${esc(nivel)}</span>${secciones.map(c =>
            `<a class="chip" href="${ruta('curso', c.id)}" title="${esc(c.nombre)}"${c.id === estado.curso ? ' aria-current="page"' : ''}>${esc(c.seccion)}</a>`).join('')}</div>`).join('');
        return `<div class="lat-grupo"><p class="lat-grupo-nombre">${esc(ciclo)}</p>${filas}</div>`;
      }).join('');
      lat.innerHTML = `<p class="lat-titulo">Cursos</p>${grupos}`;
      return;
    }

    const grupos = docentesPorDepartamento().map(([g, ds]) =>
      `<div class="lat-grupo" data-grupo><p class="lat-grupo-nombre">${esc(g)}</p>${ds.map(d =>
        `<a class="doc-item" href="${ruta('docente', d.id)}" data-buscar="${esc(sinTildes(d.id + ' ' + d.departamento))}"${d.id === estado.docente ? ' aria-current="page"' : ''}>
          <span class="doc-nombre">${esc(d.id)}</span><span class="doc-horas">${d.horas} h</span></a>`).join('')}</div>`).join('');
    lat.innerHTML = `<p class="lat-titulo">Docentes (${I.listaDocentes.length})</p>
      <input type="search" class="buscador" id="buscador" placeholder="Buscar docente o departamento…" aria-label="Buscar docente" value="${esc(estado.busqueda)}">
      ${grupos}<p class="sin-resultados" id="sin-resultados" hidden>Sin coincidencias.</p>`;
    filtrarDocentes();
  }

  function filtrarDocentes() {
    const q = sinTildes(estado.busqueda.trim());
    let visibles = 0;
    for (const g of $$('[data-grupo]')) {
      let n = 0;
      for (const it of $$('.doc-item', g)) {
        const ok = !q || it.dataset.buscar.includes(q);
        it.hidden = !ok;
        if (ok) n++;
      }
      g.hidden = n === 0;
      visibles += n;
    }
    const sr = $('#sin-resultados');
    if (sr) sr.hidden = visibles > 0;
  }

  // ---------------------------------------------------------------- Resaltado

  // 'k' puede traer varias claves separadas por '|' (clases con co-docencia)
  function resaltar(k) {
    const claves = k == null ? null : new Set(k.split('|'));
    for (const t of $$('.resaltable')) t.classList.toggle('resaltando', !!claves);
    for (const el of $$('[data-k]', $('#principal'))) {
      el.classList.toggle('hl', !!claves && el.dataset.k.split('|').some(x => claves.has(x)));
    }

    const pista = $('#pista');
    if (!pista || estado.vista !== 'dia') return;
    if (!claves) { pista.textContent = PISTA_DIA; return; }
    const nombres = [...claves];
    if (nombres.length > 1) {
      pista.textContent = `Clase compartida por ${unir(nombres)}: se resaltan todas sus clases del ${estado.dia.toLowerCase()}.`;
      return;
    }
    const d = I.docentes.get(nombres[0]);
    const n = d ? Object.keys(d.clases[estado.dia] || {}).length : 0;
    pista.textContent = `${nombres[0]}: ${plural(n, 'bloque', 'bloques')} el ${estado.dia.toLowerCase()} · ${plural(d ? d.horas : 0, 'hora', 'horas')} en la semana.`;
  }

  // ---------------------------------------------------------------- Render principal

  function renderCabecera() {
    const meta = D.meta || {};
    let fecha = meta.generado || '';
    const m = fecha.match(/^(\d{4})-(\d{2})-(\d{2})\s+(.*)$/);
    if (m) fecha = `${m[3]}-${m[2]}-${m[1]} ${m[4]}`;
    const partes = ['Prototipo 1'];
    if (meta.anio) partes.push(`Año ${meta.anio}`);
    partes.push(`Semilla ${meta.semilla ?? '—'}`);
    if (fecha) partes.push(`Generado el ${fecha}`);
    $('#subtitulo').textContent = partes.join(' · ');

    const valido = D.auditoria && D.auditoria.valido;
    $('#estado-global').innerHTML = valido
      ? `<a class="pill ok" href="${ruta('auditoria')}" title="Ver auditoría">${ICONOS.ok}<span class="pill-txt">Factible</span></a>`
      : `<a class="pill bad" href="${ruta('auditoria')}" title="Ver auditoría">${ICONOS.alerta}<span class="pill-txt">Con conflictos</span></a>`;
  }

  const VISTA_RENDER = { curso: vistaCurso, docente: vistaDocente, dia: vistaDia, recintos: vistaRecintos, auditoria: vistaAuditoria };

  function render() {
    leerRuta();
    estado.ant = estado.sig = null;
    renderPestanas();
    const conLateral = estado.vista === 'curso' || estado.vista === 'docente';
    $('#layout').classList.toggle('sin-lateral', !conLateral);
    if (conLateral) renderLateral();
    $('#principal').innerHTML = VISTA_RENDER[estado.vista]();

    const nombre = { curso: nombreCurso(estado.curso), docente: estado.docente, dia: estado.dia,
      recintos: 'Recintos deportivos', auditoria: 'Auditoría' }[estado.vista];
    document.title = `${nombre} · Horarios MMDD`;
  }

  function renderVacio() {
    $('#layout').classList.add('sin-lateral');
    $('#pestanas').innerHTML = '';
    $('#principal').innerHTML = `<div class="vacio-estado">
      <h2>Aún no hay horarios para mostrar</h2>
      <p>No se encontró <code>datos_horarios.js</code>. Genera el archivo ejecutando, desde la carpeta <b>Prototipo 1</b>:</p>
      <pre>python exportar_datos.py</pre>
      <p>Luego recarga esta página, o abre un archivo de horario generado anteriormente.</p>
      <button type="button" class="btn" data-accion="abrir">Abrir horario…</button>
    </div>`;
  }

  function iniciar(datos) {
    D = datos;
    I = indexar(D);
    renderCabecera();
    if (!location.hash) history.replaceState(null, '', ruta('curso', D.cursos[0].id));
    render();
  }

  // ---------------------------------------------------------------- Abrir otro archivo

  function abrirArchivo(archivo) {
    const lector = new FileReader();
    lector.onload = () => {
      try {
        const txt = String(lector.result);
        const datos = JSON.parse(txt.slice(txt.indexOf('{'), txt.lastIndexOf('}') + 1));
        if (!Array.isArray(datos.cursos) || !datos.asignaciones || !Array.isArray(datos.docentes)) throw new Error('formato');
        iniciar(datos);
        aviso(`Horario cargado: ${archivo.name} (semilla ${datos.meta ? datos.meta.semilla : '—'})`);
      } catch (e) {
        aviso('No se pudo leer el archivo. Usa un .js generado por exportar_datos.py.');
      }
    };
    lector.readAsText(archivo, 'utf-8');
  }

  // ---------------------------------------------------------------- Tema

  function cambiarTema() {
    const raiz = document.documentElement;
    const actual = raiz.dataset.theme || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    const nuevo = actual === 'dark' ? 'light' : 'dark';
    raiz.dataset.theme = nuevo;
    try { localStorage.setItem('mmdd-tema', nuevo); } catch (e) { /* almacenamiento no disponible */ }
  }

  // ---------------------------------------------------------------- Eventos

  function ajustarAppbar() {
    document.documentElement.style.setProperty('--appbar-h', $('.appbar').offsetHeight + 'px');
  }

  document.addEventListener('click', e => {
    const accion = e.target.closest('[data-accion]');
    if (accion) {
      const a = accion.dataset.accion;
      if (a === 'abrir') $('#archivo').click();
      if (a === 'imprimir') window.print();
      if (a === 'tema') cambiarTema();
      return;
    }
    const botonDia = e.target.closest('[data-dia-movil]');
    if (botonDia) {
      estado.diaMovil = botonDia.dataset.diaMovil;
      render();
    }
  });

  document.addEventListener('change', e => {
    if (e.target.matches('[data-navegar]')) location.hash = e.target.value;
    if (e.target.id === 'archivo' && e.target.files[0]) {
      abrirArchivo(e.target.files[0]);
      e.target.value = '';
    }
  });

  document.addEventListener('input', e => {
    if (e.target.id === 'buscador') {
      estado.busqueda = e.target.value;
      filtrarDocentes();
    }
  });

  document.addEventListener('keydown', e => {
    if (e.target.id === 'buscador' && e.key === 'Enter') {
      const primero = $$('.doc-item').find(it => !it.hidden);
      if (primero) location.hash = primero.getAttribute('href');
      return;
    }
    if (e.altKey || e.ctrlKey || e.metaKey || e.target.closest('input, select, textarea')) return;
    if (e.key === 'ArrowLeft' && estado.ant) location.hash = estado.ant;
    if (e.key === 'ArrowRight' && estado.sig) location.hash = estado.sig;
  });

  const principal = $('#principal');
  principal.addEventListener('mouseover', e => {
    const el = e.target.closest('[data-resalta]');
    if (el) resaltar(el.dataset.resalta);
  });
  principal.addEventListener('mouseout', e => {
    const el = e.target.closest('[data-resalta]');
    if (el && !el.contains(e.relatedTarget)) resaltar(null);
  });
  principal.addEventListener('focusin', e => {
    const el = e.target.closest('[data-resalta]');
    resaltar(el ? el.dataset.resalta : null);
  });
  principal.addEventListener('focusout', () => resaltar(null));

  window.addEventListener('hashchange', () => {
    if (!D) return;
    render();
    window.scrollTo(0, 0);
  });
  window.addEventListener('resize', ajustarAppbar);

  // ---------------------------------------------------------------- Arranque

  if (window.DATOS_HORARIOS) iniciar(window.DATOS_HORARIOS);
  else renderVacio();
  ajustarAppbar();
})();
