/* =============================================================================
   HORARIOS MMDD — Menú de inicio (Prototipo 2)
   Antes de entrar a la plataforma se elige el año escolar:
     - 2026: horario oficial, leído del Excel del colegio (data/Data 2026).
     - 2027: horario generado por el motor del proyecto.
   Al elegir, se cargan el horario del año y js/app.js, y el año queda en la URL
   (?anio=2027) para que al recargar se entre directo. El botón de la barra superior
   vuelve a abrir este menú. Las animaciones usan GSAP si está disponible.
   El 2027 tiene varias instancias generadas (datos/instancias_2027.js): el panel de
   Configuración (esquina superior derecha) elige cuál se carga.
   ========================================================================== */
(() => {
  'use strict';

  const $ = (sel, raiz = document) => raiz.querySelector(sel);
  const $$ = (sel, raiz = document) => [...raiz.querySelectorAll(sel)];

  const RESUMEN = window.HORARIOS_MMDD_RESUMEN || {};
  // Catálogo de instancias generadas por año (datos/instancias_<año>.js): cada una trae su
  // archivo y su resumen; Configuración elige cuál se muestra (se recuerda en este navegador)
  const INSTANCIAS = window.HORARIOS_MMDD_INSTANCIAS || {};
  const ANIOS = [2026, 2027];
  const raiz = document.documentElement;
  const menu = $('#menu');
  const tarjetas = $('#menu-tarjetas');
  const movimientoReducido = window.matchMedia('(prefers-reduced-motion: reduce)');
  const G = () => (window.gsap && !movimientoReducido.matches ? window.gsap : null);

  let anioCargado = null;   // año cuyo horario ya está en pantalla
  let ocupado = false;      // evita dobles clics durante una transición
  let focoPrevio = null;

  // Familia de color de cada asignatura (las mismas categorías que usa la grilla de app.js)
  const CATEGORIA = {
    'Lenguaje y Comunicación': 'lenguaje', 'Filosofía': 'humanidades',
    'Educación Matemática': 'matematica',
    'Idioma Extranjero Inglés': 'ingles', 'English Skills': 'ingles',
    'Ciencias Sociales': 'humanidades', 'Historia, Geografía y CC.SS.': 'humanidades', 'Educación Ciudadana': 'humanidades',
    'Ciencias Naturales': 'ciencias', 'Biología': 'ciencias', 'Química': 'ciencias', 'Física': 'ciencias',
    'Ciencias para la Ciudadanía': 'ciencias',
    'Educación Tecnológica': 'tecnologia', 'Orientación / Tecnología': 'tecnologia',
    'Artes Visuales': 'artes', 'Educación Musical': 'artes', 'Artes Visuales / Música': 'artes',
    'Educación Física y Salud': 'edfisica',
    'Orientación': 'formacion', 'Religión': 'formacion',
  };
  const categoria = a => (a.startsWith('Formación Diferenciada') ? 'electivo' : CATEGORIA[a] || 'formacion');

  const esc = s => String(s ?? '').replace(/[&<>"']/g, ch =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
  const numero = n => String(n).replace('.', ',');

  const anioEnUrl = () => {
    const n = Number(new URLSearchParams(location.search).get('anio'));
    return ANIOS.includes(n) ? n : null;
  };
  const urlDe = anio => `${location.pathname}?anio=${anio}${location.hash}`;
  const leerLocal = k => { try { return localStorage.getItem(k); } catch (e) { return null; } };
  const guardarLocal = (k, v) => {
    try { if (v == null) localStorage.removeItem(k); else localStorage.setItem(k, v); } catch (e) { /* almacenamiento no disponible */ }
  };

  // ===========================================================================
  // INSTANCIAS GENERADAS
  // ===========================================================================
  const claveInstancia = anio => `mmdd-instancia-${anio}`;

  // Instancia que se muestra: la elegida en Configuración o, si no hay (o ya no existe), la predeterminada
  function instanciaElegida(anio) {
    const cat = INSTANCIAS[anio];
    if (!cat || !cat.lista || !cat.lista.length) return null;
    const porId = id => cat.lista.find(e => e.id === id);
    return porId(leerLocal(claveInstancia(anio))) || porId(cat.defecto) || cat.lista[cat.lista.length - 1];
  }

  // La tarjeta del menú usa el resumen de la instancia elegida
  function actualizarResumenes() {
    Object.keys(INSTANCIAS).forEach(anio => {
      const e = instanciaElegida(Number(anio));
      if (e) RESUMEN[anio] = { ...e.resumen, nombreInstancia: e.nombre };
    });
  }
  actualizarResumenes();

  // ===========================================================================
  // TARJETAS
  // ===========================================================================
  const ICONO_OK = '<svg class="icono" viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12.5 4.5 4.5L19 7.5"/></svg>';
  const ICONO_ALERTA = '<svg class="icono" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 8v5M12 16.5v.5M10.3 3.9 2.6 17.5A2 2 0 0 0 4.3 20.5h15.4a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"/></svg>';
  const FLECHA = '<svg class="icono" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>';

  const TEXTOS = {
    oficial: {
      tipo: 'Horario oficial',
      sello: 'En uso',
      descripcion: 'El horario vigente del colegio, leído tal cual desde el Excel <i>HORARIO CURSOS 2026</i>.',
    },
    generado: {
      tipo: 'Horario generado',
      sello: 'Propuesta',
      descripcion: 'La propuesta que construye el motor de optimización del proyecto, auditada restricción por restricción.',
    },
  };

  function miniGrillaHTML(muestra) {
    if (!muestra) return '';
    const filas = Math.max(...muestra.dias.map(d => d.length));
    let celdas = '';
    for (let b = 0; b < filas; b++) {
      muestra.dias.forEach((dia, d) => {
        const a = dia[b];
        celdas += a
          ? `<span class="mini-celda cat-${categoria(a)}" data-col="${d}" data-fila="${b}"></span>`
          : `<span class="mini-celda vacia" data-col="${d}" data-fila="${b}"></span>`;
      });
    }
    return `
      <figure class="mini">
        <div class="mini-dias" aria-hidden="true"><span>L</span><span>M</span><span>M</span><span>J</span><span>V</span></div>
        <div class="mini-grilla" style="--filas:${filas}" aria-hidden="true">${celdas}</div>
        <figcaption>Semana de ${esc(muestra.curso)}</figcaption>
      </figure>`;
  }

  function tarjetaHTML(anio) {
    const r = RESUMEN[anio];
    if (!r) {
      return `
        <div class="tarjeta-anio sin-datos" role="listitem">
          <span class="eyebrow">Sin datos</span>
          <span class="tarjeta-numero">${anio}</span>
          <p class="tarjeta-desc">Faltan los datos de ${anio}. Ejecuta
          <code>python exportar_datos.py --anio ${anio}</code> en la carpeta del prototipo y recarga la página.</p>
        </div>`;
    }
    const t = TEXTOS[r.fuente] || TEXTOS.generado;
    const auditoria = r.valido
      ? `<span class="tarjeta-estado bien">${ICONO_OK}Factible · sin conflictos</span>`
      : `<span class="tarjeta-estado mal">${ICONO_ALERTA}${r.totalErrores} observaciones de auditoría</span>`;
    const actual = anio === anioCargado;
    return `
      <button type="button" class="tarjeta-anio tarjeta-${esc(r.fuente)}${actual ? ' actual' : ''}" role="listitem"
              data-anio="${anio}" aria-label="${t.tipo} ${anio}${actual ? ' (en pantalla)' : ''}">
        <span class="tarjeta-brillo" aria-hidden="true"></span>
        <span class="tarjeta-cabeza">
          <span class="eyebrow">${t.tipo}</span>
          <span class="tarjeta-sello">${actual ? 'En pantalla' : t.sello}</span>
        </span>
        <span class="tarjeta-numero" aria-hidden="true">${[...String(anio)].map(d => `<span class="digito">${d}</span>`).join('')}</span>
        <span class="tarjeta-desc">${t.descripcion}</span>
        ${r.nombreInstancia ? `<span class="tarjeta-instancia">Instancia: <b>${esc(r.nombreInstancia)}</b></span>` : ''}
        ${miniGrillaHTML(r.muestra)}
        <span class="tarjeta-datos">
          <span><b data-contar="${r.cursos}">${r.cursos}</b> cursos</span>
          <span><b data-contar="${r.docentes}">${r.docentes}</b> docentes</span>
          <span><b data-contar="${r.bloques}">${r.bloques}</b> bloques</span>
          <span><b data-contar="${r.ventanas}">${r.ventanas}</b> ventanas</span>
        </span>
        ${auditoria}
        <span class="tarjeta-accion">${actual ? 'Seguir viendo' : `Ver horario ${anio}`}${FLECHA}</span>
      </button>`;
  }

  function dibujarTarjetas() {
    tarjetas.innerHTML = ANIOS.map(tarjetaHTML).join('');
    $$('.tarjeta-anio[data-anio]', tarjetas).forEach(prepararInclinacion);
  }

  // Inclinación 3D y brillo que siguen al cursor
  function prepararInclinacion(t) {
    const g = G();
    if (!g || !window.matchMedia('(hover: hover)').matches) return;
    const rx = g.quickTo(t, 'rotationX', { duration: 0.5, ease: 'power3.out' });
    const ry = g.quickTo(t, 'rotationY', { duration: 0.5, ease: 'power3.out' });
    t.addEventListener('pointermove', ev => {
      if (ocupado) return;
      const r = t.getBoundingClientRect();
      const x = (ev.clientX - r.left) / r.width;
      const y = (ev.clientY - r.top) / r.height;
      rx((0.5 - y) * 7);
      ry((x - 0.5) * 9);
      t.style.setProperty('--mx', `${x * 100}%`);
      t.style.setProperty('--my', `${y * 100}%`);
    });
    t.addEventListener('pointerenter', () => {
      if (ocupado) return;
      g.to(t, { y: -6, duration: 0.35, ease: 'power3.out' });
      g.fromTo($$('.mini-celda:not(.vacia)', t), { scale: 1 }, {
        scale: 1.25, duration: 0.18, yoyo: true, repeat: 1, ease: 'power1.inOut',
        stagger: { each: 0.008, from: 'start', grid: 'auto' },
      });
    });
    t.addEventListener('pointerleave', () => {
      if (ocupado) return;
      rx(0); ry(0);
      g.to(t, { y: 0, duration: 0.4, ease: 'power3.out' });
    });
  }

  // ===========================================================================
  // FONDO: mosaico de bloques de colores que se encienden y apagan
  // ===========================================================================
  const parpadeos = [];   // tweens del fondo: se pausan mientras el menú está oculto

  function dibujarFondo() {
    const fondo = $('.menu-fondo');
    const cats = ['lenguaje', 'matematica', 'ingles', 'humanidades', 'ciencias', 'tecnologia', 'artes', 'edfisica', 'formacion', 'electivo'];
    let html = '';
    // Suficientes celdas para cubrir una pantalla grande (las que sobran quedan recortadas)
    for (let i = 0; i < 640; i++) {
      const c = Math.random() < 0.5 ? cats[Math.floor(Math.random() * cats.length)] : null;
      html += c ? `<span class="fondo-celda cat-${c}"></span>` : '<span class="fondo-celda"></span>';
    }
    fondo.innerHTML = html;
    const g = G();
    if (!g) return;
    $$('.fondo-celda[class*="cat-"]', fondo).forEach(el => {
      parpadeos.push(g.to(el, {
        opacity: 0.15 + Math.random() * 0.85,
        duration: 1.6 + Math.random() * 2.4,
        delay: Math.random() * 4,
        repeat: -1, yoyo: true, ease: 'sine.inOut',
      }));
    });
  }

  // ===========================================================================
  // ANIMACIONES DE ENTRADA Y SALIDA
  // ===========================================================================
  function contar(el) {
    const g = G();
    const hasta = Number(el.dataset.contar);
    if (!g || !hasta) return;
    const o = { v: 0 };
    const decimales = hasta % 1 ? 1 : 0;
    const sufijo = el.dataset.sufijo || '';
    g.to(o, { v: hasta, duration: 1.3, ease: 'power2.out', delay: 0.55,
      onUpdate: () => { el.textContent = o.v.toFixed(decimales).replace('.', ',') + sufijo; } });
  }

  function entrada({ completa }) {
    const g = G();
    if (!g) return;
    const tl = g.timeline({ defaults: { ease: 'power3.out' } });
    if (completa) {
      tl.fromTo('.menu-escudo', { opacity: 0, y: -24, rotate: -14, scale: 0.6 },
        { opacity: 1, y: 0, rotate: 0, scale: 1, duration: 0.9, ease: 'back.out(2)', clearProps: 'transform,opacity' }, 0);
      tl.fromTo('.menu-colegio', { opacity: 0, y: 8 }, { opacity: 1, y: 0, duration: 0.5, clearProps: 'transform,opacity' }, 0.15);
      tl.fromTo('.menu-letra', { yPercent: 110, rotate: 6 },
        { yPercent: 0, rotate: 0, duration: 0.85, ease: 'expo.out', stagger: 0.045, clearProps: 'transform' }, 0.2);
      tl.fromTo('.menu-bajada', { opacity: 0, y: 10 }, { opacity: 1, y: 0, duration: 0.6, clearProps: 'transform,opacity' }, 0.55);
      tl.fromTo('.menu-fondo', { opacity: 0 }, { opacity: 1, duration: 1.6, ease: 'power1.out', clearProps: 'opacity' }, 0);
    }
    const cards = $$('.tarjeta-anio', tarjetas);
    tl.fromTo(cards, { opacity: 0, y: 60, rotationX: -18, transformPerspective: 900 },
      { opacity: 1, y: 0, rotationX: 0, duration: 0.95, ease: 'expo.out', stagger: 0.12, clearProps: 'opacity' }, completa ? 0.45 : 0.1);
    cards.forEach((t, i) => {
      const inicio = (completa ? 0.75 : 0.35) + i * 0.12;
      tl.fromTo($$('.digito', t), { opacity: 0, yPercent: 60 },
        { opacity: 1, yPercent: 0, duration: 0.6, ease: 'back.out(1.8)', stagger: 0.06, clearProps: 'transform,opacity' }, inicio);
      tl.fromTo($$('.mini-celda', t), { opacity: 0, scale: 0.3 }, {
        opacity: 1, scale: 1, duration: 0.35, ease: 'back.out(2)',
        stagger: (k, el) => Number(el.dataset.col) * 0.06 + Number(el.dataset.fila) * 0.025,
        clearProps: 'transform,opacity',
      }, inicio + 0.1);
    });
    tl.fromTo('.menu-pie', { opacity: 0 }, { opacity: 1, duration: 0.6, clearProps: 'opacity' }, completa ? 1 : 0.5);
    $$('[data-contar]', tarjetas).forEach(contar);
  }

  // Cortina: el menú sube y descubre el horario (o baja para cubrirlo)
  function subirCortina() {
    const g = G();
    return new Promise(listo => {
      if (!g) { listo(); return; }
      g.timeline({ onComplete: listo })
        .to('.menu-contenido', { y: -40, opacity: 0, duration: 0.45, ease: 'power2.in' }, 0)
        .to(menu, { clipPath: 'inset(0% 0% 100% 0%)', duration: 0.75, ease: 'power4.inOut' }, 0.15)
        .set(['.menu-contenido', menu], { clearProps: 'all' });
    });
  }

  function bajarCortina() {
    const g = G();
    if (!g) return;
    g.fromTo(menu, { clipPath: 'inset(0% 0% 100% 0%)' }, { clipPath: 'inset(0% 0% 0% 0%)', duration: 0.7, ease: 'power4.inOut', clearProps: 'clipPath' });
  }

  // La tarjeta elegida se destaca y la otra se aparta
  function destacar(tarjeta) {
    const g = G();
    return new Promise(listo => {
      if (!g) { listo(); return; }
      const otras = $$('.tarjeta-anio', tarjetas).filter(t => t !== tarjeta);
      g.timeline({ onComplete: listo })
        .to(tarjeta, { rotationX: 0, rotationY: 0, y: -10, scale: 1.035, duration: 0.4, ease: 'power3.out' }, 0)
        .to(otras, { opacity: 0.25, scale: 0.94, filter: 'blur(2px)', duration: 0.4, ease: 'power2.out' }, 0)
        .fromTo($$('.mini-celda:not(.vacia)', tarjeta), { scale: 1 }, {
          scale: 0, duration: 0.25, ease: 'power2.in',
          stagger: (k, el) => Number(el.dataset.col) * 0.03 + Number(el.dataset.fila) * 0.012,
        }, 0.1)
        .to($('.tarjeta-accion .icono', tarjeta), { x: 10, duration: 0.3, ease: 'power2.out' }, 0);
    });
  }

  // ===========================================================================
  // CARGA DEL AÑO ELEGIDO
  // ===========================================================================
  function cargarScript(src) {
    return new Promise((listo, fallo) => {
      const s = document.createElement('script');
      s.src = src;
      s.onload = listo;
      s.onerror = () => fallo(new Error(`No se pudo cargar ${src}`));
      document.body.appendChild(s);
    });
  }

  // Horario resuelto en el modo desarrollador (?resultado=1): lo guarda js/desarrollador.js en
  // sessionStorage al pulsar "Ver en el visualizador" y solo vale para esta pestaña del navegador
  function resultadoDev(anio) {
    if (new URLSearchParams(location.search).get('resultado') !== '1') return null;
    try {
      const datos = JSON.parse(sessionStorage.getItem('mmdd-dev-resultado'));
      return datos && datos.meta && datos.meta.anio === anio ? datos : null;
    } catch (e) {
      return null;
    }
  }

  function etiquetarBarra(anio) {
    const r = RESUMEN[anio];
    const tipo = resultadoDev(anio) ? 'Solver' : r ? (r.fuente === 'oficial' ? 'Oficial' : 'Generado') : '';
    const instancia = !resultadoDev(anio) && instanciaElegida(anio);
    $('#anio-chip-texto').textContent = tipo ? `${anio} · ${tipo}` : String(anio);
    $('#cambiar-anio').dataset.fuente = r ? r.fuente : '';
    $('#cambiar-anio').title = `${instancia ? `Instancia: ${instancia.nombre}. ` : ''}Volver al menú para elegir otro año`;
    $('#cambiar-anio').setAttribute('aria-label', `Horario ${anio}${tipo ? ` (${tipo.toLowerCase()})` : ''}`
      + `${instancia ? `, instancia ${instancia.nombre}` : ''}. Cambiar de año`);
  }

  async function cargarAnio(anio) {
    etiquetarBarra(anio);
    const resultado = resultadoDev(anio);
    if (resultado) {
      window.HORARIOS_MMDD = resultado;
    } else {
      const instancia = instanciaElegida(anio);
      try {
        await cargarScript(instancia ? instancia.archivo : `datos/horarios_${anio}.js`);
      } catch (e) {
        window.HORARIOS_MMDD = null;   // app.js muestra el aviso de datos faltantes
      }
    }
    window.HORARIOS_MMDD_ANIO = anio;
    await cargarScript('js/app.js');
    anioCargado = anio;
  }

  async function elegir(anio) {
    if (ocupado || !RESUMEN[anio]) return;
    if (anio === anioCargado) { cerrar(); return; }
    ocupado = true;
    const tarjeta = $(`.tarjeta-anio[data-anio="${anio}"]`, tarjetas);
    await destacar(tarjeta);
    if (anioCargado) {
      // Ya hay otro año en pantalla: se recarga la página en el año nuevo, conservando la vista
      location.href = urlDe(anio);
      return;
    }
    try { history.replaceState(null, '', urlDe(anio)); } catch (e) { /* file:// sin history: se sigue igual */ }
    raiz.classList.add('con-anio');
    await cargarAnio(anio);
    await subirCortina();
    ocultar();
    ocupado = false;
  }

  // ===========================================================================
  // ABRIR Y CERRAR
  // ===========================================================================
  // Configuración queda disponible sobre el menú (no se vuelve inert)
  const fueraDelMenu = () => [...document.body.children].filter(el => el !== menu && el.id !== 'config' && el.tagName !== 'SCRIPT');

  function mostrar({ completa }) {
    focoPrevio = document.activeElement;
    menu.hidden = false;
    parpadeos.forEach(t => t.resume());
    raiz.classList.add('menu-abierto');
    fueraDelMenu().forEach(el => el.setAttribute('inert', ''));
    $('#menu-cerrar').hidden = !anioCargado;
    dibujarTarjetas();
    entrada({ completa });
    const inicial = $('.tarjeta-anio.actual', tarjetas) || $('.tarjeta-anio[data-anio]', tarjetas);
    if (inicial) inicial.focus({ preventScroll: true });
  }

  function ocultar() {
    menu.hidden = true;
    parpadeos.forEach(t => t.pause());
    raiz.classList.remove('menu-abierto');
    fueraDelMenu().forEach(el => el.removeAttribute('inert'));
    // El panel de detalle de app.js mantiene su propio inert mientras está cerrado
    const detalle = $('#detalle');
    if (detalle && !detalle.classList.contains('abierto')) detalle.setAttribute('inert', '');
  }

  async function cerrar() {
    if (ocupado || !anioCargado) return;
    ocupado = true;
    await subirCortina();
    ocultar();
    ocupado = false;
    if (focoPrevio && document.contains(focoPrevio)) focoPrevio.focus({ preventScroll: true });
  }

  function abrir() {
    if (ocupado || !menu.hidden) return;
    mostrar({ completa: false });
    bajarCortina();
  }

  // ===========================================================================
  // CONFIGURACIÓN: selector de instancias generadas
  // ===========================================================================
  const config = $('#config');
  const configCuerpo = $('#config-cuerpo');
  let disparadorConfig = null;

  const fechaCorta = generado => {
    const [f, h] = String(generado || '').split(' ');
    const [a, m, d] = f.split('-');
    return d ? `${Number(d)}-${m}-${a}${h ? ` · ${h}` : ''}` : '';
  };

  function opcionInstanciaHTML(anio, e, elegida, defecto) {
    const r = e.resumen || {};
    const enPantalla = anioCargado === anio && !resultadoDev(anio) && e.id === elegida.id;
    const metodo = (e.metodo && e.metodo.nombre) || '';
    const insignias = [
      e.id === defecto ? '<span class="config-insignia">Predeterminada</span>' : '',
      enPantalla ? '<span class="config-insignia en-pantalla">En pantalla</span>' : '',
    ].join('');
    const estado = r.valido
      ? `<span class="config-estado bien">${ICONO_OK}Factible</span>`
      : `<span class="config-estado mal">${ICONO_ALERTA}${r.totalErrores} errores</span>`;
    const elegidaAhora = e.id === elegida.id;
    return `
      <button type="button" class="config-opcion" role="radio" aria-checked="${elegidaAhora}" tabindex="${elegidaAhora ? 0 : -1}"
              data-anio="${anio}" data-instancia="${esc(e.id)}">
        <span class="config-marca" aria-hidden="true"></span>
        <span class="config-opcion-texto">
          <span class="config-opcion-cabeza"><span class="config-opcion-nombre">${esc(e.nombre)}</span>${insignias}</span>
          <span class="config-opcion-meta">${esc(metodo)}${e.semilla != null ? ` · semilla ${e.semilla}` : ''} · ${esc(fechaCorta(e.generado))}</span>
          <span class="config-opcion-datos">${estado}<span><b>${r.ventanas}</b> ventanas</span><span><b>${r.bloques}</b>/${r.bloquesEsperados} bloques</span></span>
          ${e.descripcion ? `<span class="config-opcion-desc">${esc(e.descripcion)}</span>` : ''}
        </span>
      </button>`;
  }

  function dibujarConfig() {
    const secciones = Object.keys(INSTANCIAS).map(Number).filter(a => INSTANCIAS[a].lista && INSTANCIAS[a].lista.length).map(anio => {
      const cat = INSTANCIAS[anio];
      const elegida = instanciaElegida(anio);
      const solver = anioCargado === anio && resultadoDev(anio)
        ? `<p class="config-aviso">Ahora ves un resultado del solver. Al elegir una instancia vuelves a los horarios guardados.</p>` : '';
      const restablecer = elegida.id !== cat.defecto && cat.lista.some(e => e.id === cat.defecto)
        ? `<button type="button" class="enlace" data-instancia-defecto="${anio}">Usar la predeterminada</button>` : '';
      return `
        <section class="config-seccion">
          <div class="config-seccion-titulo">
            <span class="eyebrow" id="config-instancias-${anio}">Horario ${anio} · instancia generada</span>
            ${restablecer}
          </div>
          <p class="config-ayuda">Elige cuál de los horarios generados se muestra en todas las vistas, en el menú y en los
            documentos que se descargan. Se recuerda en este navegador.</p>
          ${solver}
          <div class="config-opciones" role="radiogroup" aria-labelledby="config-instancias-${anio}">
            ${cat.lista.map(e => opcionInstanciaHTML(anio, e, elegida, cat.defecto)).join('')}
          </div>
          <p class="config-nota">Para agregar una instancia: <code>python exportar_datos.py --anio ${anio} --seed 7 --nombre "Semilla 7"</code>
            en la carpeta del prototipo (con <code>--importar archivo.js</code> se agrega un horario descargado desde Resolver).</p>
        </section>`;
    });
    configCuerpo.innerHTML = secciones.join('')
      || '<p class="config-ayuda">No hay instancias generadas. Ejecuta <code>python exportar_datos.py --anio 2027</code> en la carpeta del prototipo.</p>';
  }

  function abrirConfig(boton) {
    disparadorConfig = boton || null;
    dibujarConfig();
    config.hidden = false;
    $$('[data-abrir-config]').forEach(b => b.setAttribute('aria-expanded', 'true'));
    const g = G();
    if (g) {
      g.fromTo(config, { opacity: 0, y: -10, scale: 0.98 }, { opacity: 1, y: 0, scale: 1, duration: 0.3, ease: 'power3.out', clearProps: 'all' });
      g.fromTo($$('.config-opcion', config), { opacity: 0, y: 8 }, { opacity: 1, y: 0, duration: 0.3, stagger: 0.05, delay: 0.08, ease: 'power2.out', clearProps: 'all' });
    }
    const foco = $('.config-opcion[aria-checked="true"]', config) || $('#config-cerrar');
    foco.focus({ preventScroll: true });
  }

  function cerrarConfig(devolverFoco = true) {
    if (config.hidden) return;
    config.hidden = true;
    $$('[data-abrir-config]').forEach(b => b.setAttribute('aria-expanded', 'false'));
    if (devolverFoco && disparadorConfig && document.contains(disparadorConfig)) disparadorConfig.focus({ preventScroll: true });
  }

  function elegirInstancia(anio, id) {
    const cat = INSTANCIAS[anio];
    if (!cat || !cat.lista.some(e => e.id === id)) return;
    const antes = instanciaElegida(anio);
    // La predeterminada no se guarda: así, si el catálogo cambia de predeterminada, se sigue la nueva
    guardarLocal(claveInstancia(anio), id === cat.defecto ? null : id);
    actualizarResumenes();
    if (anioCargado === anio && (antes.id !== id || resultadoDev(anio))) {
      // El horario de ese año está en pantalla: se recarga con la instancia nueva, en la misma vista
      // (si solo cambiara el #fragmento, asignar location.href no recargaría la página)
      const destino = `${location.pathname}?anio=${anio}`;
      if (`${location.pathname}${location.search}` === destino) location.reload();
      else location.href = urlDe(anio);
      return;
    }
    dibujarConfig();
    const foco = $(`.config-opcion[data-instancia="${CSS.escape(id)}"]`, config);
    if (foco) foco.focus({ preventScroll: true });
    if (!menu.hidden) {
      dibujarTarjetas();
      entrada({ completa: false });
    }
  }

  document.addEventListener('click', ev => {
    const abrirBoton = ev.target.closest('[data-abrir-config]');
    if (abrirBoton) {
      if (config.hidden) abrirConfig(abrirBoton);
      else cerrarConfig();
      return;
    }
    if (ev.target.closest('#config-cerrar')) { cerrarConfig(); return; }
    const opcion = ev.target.closest('.config-opcion[data-instancia]');
    if (opcion) { elegirInstancia(Number(opcion.dataset.anio), opcion.dataset.instancia); return; }
    const defecto = ev.target.closest('[data-instancia-defecto]');
    if (defecto) {
      const anio = Number(defecto.dataset.instanciaDefecto);
      elegirInstancia(anio, INSTANCIAS[anio].defecto);
    }
  });
  // Se cierra al tocar fuera del panel
  document.addEventListener('pointerdown', ev => {
    if (config.hidden || config.contains(ev.target) || ev.target.closest('[data-abrir-config]')) return;
    cerrarConfig(false);
  });

  // ===========================================================================
  // EVENTOS
  // ===========================================================================
  tarjetas.addEventListener('click', ev => {
    const t = ev.target.closest('.tarjeta-anio[data-anio]');
    if (t) elegir(Number(t.dataset.anio));
  });
  $('#menu-cerrar').addEventListener('click', cerrar);
  $('#cambiar-anio').addEventListener('click', abrir);

  $('#menu-tema').addEventListener('click', () => {
    const oscuro = raiz.dataset.theme ? raiz.dataset.theme === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches;
    const nuevo = oscuro ? 'light' : 'dark';
    raiz.dataset.theme = nuevo;
    try { localStorage.setItem('mmdd-tema', nuevo); } catch (e) { /* almacenamiento no disponible */ }
    const g = G();
    if (g) g.fromTo('#menu-tema .icono', { rotate: -90, scale: 0.4 }, { rotate: 0, scale: 1, duration: 0.5, ease: 'back.out(2)', clearProps: 'transform' });
  });

  // Con el menú abierto, el teclado es solo del menú (los atajos de app.js no deben actuar detrás).
  // Con Configuración abierta, el teclado es de Configuración: Esc la cierra y las flechas recorren las opciones.
  window.addEventListener('keydown', ev => {
    if (!config.hidden) {
      ev.stopImmediatePropagation();
      if (ev.key === 'Escape') { ev.preventDefault(); cerrarConfig(); return; }
      const opcion = ev.target.closest && ev.target.closest('.config-opcion');
      if (opcion && ['ArrowDown', 'ArrowUp', 'ArrowRight', 'ArrowLeft', 'Home', 'End'].includes(ev.key)) {
        ev.preventDefault();
        const grupo = $$('.config-opcion', opcion.parentElement);
        const i = grupo.indexOf(opcion);
        const destino = ev.key === 'Home' ? grupo[0] : ev.key === 'End' ? grupo[grupo.length - 1]
          : grupo[(i + (ev.key === 'ArrowDown' || ev.key === 'ArrowRight' ? 1 : -1) + grupo.length) % grupo.length];
        grupo.forEach(b => { b.tabIndex = b === destino ? 0 : -1; });
        destino.focus();
      }
      return;
    }
    if (menu.hidden) return;
    ev.stopImmediatePropagation();
    if (ev.key === 'Escape') { ev.preventDefault(); cerrar(); return; }
    const lista = $$('.tarjeta-anio[data-anio]', tarjetas);
    const i = lista.indexOf(document.activeElement);
    if (ev.key === 'ArrowRight' || ev.key === 'ArrowLeft' || ev.key === 'ArrowDown' || ev.key === 'ArrowUp') {
      ev.preventDefault();
      const paso = ev.key === 'ArrowRight' || ev.key === 'ArrowDown' ? 1 : -1;
      const destino = lista[i < 0 ? 0 : (i + paso + lista.length) % lista.length];
      if (destino) destino.focus();
    }
    const directo = { 1: 2026, 2: 2027 }[ev.key];
    if (directo) elegir(directo);
  }, true);

  // ===========================================================================
  // INICIO
  // ===========================================================================
  $('.menu-letras').innerHTML = [...'Horarios'].map(l => `<span class="menu-letra">${l}</span>`).join('');
  dibujarFondo();

  const desdeUrl = anioEnUrl();
  if (desdeUrl && RESUMEN[desdeUrl]) {
    // Recarga o enlace directo a un año: se entra al horario sin pasar por el menú
    ocultar();
    cargarAnio(desdeUrl);
  } else {
    raiz.classList.remove('con-anio');
    raiz.classList.add('menu-abierto');
    mostrar({ completa: true });
  }
})();
