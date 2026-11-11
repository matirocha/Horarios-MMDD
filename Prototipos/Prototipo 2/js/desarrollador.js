/* =============================================================================
   HORARIOS MMDD — Modo desarrollador (Prototipo 2)
   Se carga desde js/app.js al activar el botón </> de la barra superior y usa
   window.MMDD_APP. Vale para los dos horarios (2026 oficial y 2027 generado):

     1. Diagnóstico de la función objetivo del horario en pantalla, con la misma
        definición que el motor (f(x) = 1000 · H(x)): sección extra en Auditoría y
        marcas en las grillas de Cursos y Docentes, y en el detalle de cada clase.
     2. Pestaña Edición:
          Docentes    agregar, quitar (reasignando sus clases) y renombrar docentes.
          Asignación  quién dicta cada asignatura de cada curso y la jefatura.
          Electivos   nombre, sección, docente y sala de los electivos de 3° y 4° medio.
          Resolver    ejecuta un método (ILS, ITS o modelo matemático)
                      sobre la instancia editada.
          Comparar    varias semillas por método: tiempos de ejecución y función objetivo.

   La instancia editada se guarda en este navegador (localStorage). El solver corre en
   Python: necesita 'python servidor.py' en la carpeta del prototipo (ver README).
   ========================================================================== */
(() => {
  'use strict';

  const APP = window.MMDD_APP;
  if (!APP || window.MMDD_DEV) return;
  const { DATOS, DIAS, DIA_CORTO, BLOQUE, estado, esc, capitalizar, nombreNivel, nombreEspacio, infoAsig, guardar, leer } = APP;
  const $ = (sel, raiz = document) => raiz.querySelector(sel);
  const $$ = (sel, raiz = document) => [...raiz.querySelectorAll(sel)];

  const PUERTO = 8765;              // el de servidor.py
  const PESO_DURO = 1000;           // ModeloHorario.PESO_DURO
  const CURSOS = DATOS.cursos;
  const cursoPorId = new Map(CURSOS.map(c => [c.id, c]));
  const ORIENTACION = ['Orientación', 'Orientación / Tecnología'];   // siguen al profesor/a jefe
  const CLAVES = { instancia: 'mmdd-dev-instancia', base: 'mmdd-dev-base', resolver: 'mmdd-dev-resolver', comparar: 'mmdd-dev-comparar', ejecuciones: 'mmdd-dev-ejecuciones', resultado: 'mmdd-dev-resultado' };

  // ===========================================================================
  // 1. UTILIDADES
  // ===========================================================================
  const clonar = o => JSON.parse(JSON.stringify(o));
  const fmt = (n, decimales = 1) => (n == null || Number.isNaN(Number(n)) ? '—'
    : Number(n).toLocaleString('es-CL', { maximumFractionDigits: decimales }));
  function fmtMs(ms) {
    if (ms == null || Number.isNaN(ms)) return '—';
    if (ms < 10) return `${fmt(ms, 1)} ms`;
    if (ms < 1000) return `${fmt(Math.round(ms), 0)} ms`;
    if (ms < 60000) return `${fmt(ms / 1000, 2)} s`;
    return `${Math.floor(ms / 60000)} min ${Math.round((ms % 60000) / 1000)} s`;
  }
  const nombreCurso = id => cursoPorId.get(id)?.nombre || id;
  const titulo = s => capitalizar(String(s || ''));
  const mediana = xs => { const v = xs.filter(x => x != null).sort((a, b) => a - b); return v.length ? (v.length % 2 ? v[(v.length - 1) / 2] : (v[v.length / 2 - 1] + v[v.length / 2]) / 2) : null; };
  const media = xs => { const v = xs.filter(x => x != null); return v.length ? v.reduce((s, x) => s + x, 0) / v.length : null; };
  const desv = xs => { const v = xs.filter(x => x != null); if (v.length < 2) return 0; const m = media(v); return Math.sqrt(v.reduce((s, x) => s + (x - m) ** 2, 0) / (v.length - 1)); };
  const sesion = {
    leer(k) { try { return JSON.parse(sessionStorage.getItem(k)); } catch (e) { return null; } },
    guardar(k, v) { try { sessionStorage.setItem(k, JSON.stringify(v)); return true; } catch (e) { return false; } },
  };
  const leerJSON = k => { try { return JSON.parse(leer(k)); } catch (e) { return null; } };

  function descargar(nombre, contenido, tipo) {
    const url = URL.createObjectURL(new Blob([contenido], { type: tipo }));
    const a = Object.assign(document.createElement('a'), { href: url, download: nombre });
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
  }

  const ICONOS = {
    ok: '<svg class="icono" viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12.5 4.5 4.5L19 7.5"/></svg>',
    mal: '<svg class="icono" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg>',
    alerta: '<svg class="icono" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 8v5M12 16.5v.5M10.3 3.9 2.6 17.5A2 2 0 0 0 4.3 20.5h15.4a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"/></svg>',
    quitar: '<svg class="icono" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/></svg>',
    mas: '<svg class="icono" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>',
    play: '<svg class="icono" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 5v14l12-7Z"/></svg>',
    stop: '<svg class="icono" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 7h10v10H7z"/></svg>',
    bajar: '<svg class="icono" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3v12m-5-5 5 5 5-5M5 20h14"/></svg>',
    subir: '<svg class="icono" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 15V3m-5 5 5-5 5 5M5 20h14"/></svg>',
    ojo: '<svg class="icono" viewBox="0 0 24 24" aria-hidden="true"><path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12Z"/><circle cx="12" cy="12" r="2.8"/></svg>',
    deshacer: '<svg class="icono" viewBox="0 0 24 24" aria-hidden="true"><path d="M9 14 4 9l5-5M4 9h10.5a5.5 5.5 0 0 1 0 11H11"/></svg>',
    izq: '<svg class="icono" viewBox="0 0 24 24" aria-hidden="true"><path d="m15 6-6 6 6 6"/></svg>',
    der: '<svg class="icono" viewBox="0 0 24 24" aria-hidden="true"><path d="m9 6 6 6-6 6"/></svg>',
  };

  // ===========================================================================
  // 2. SERVIDOR LOCAL (servidor.py)
  // ===========================================================================
  const SRV = { estado: 'inicial', base: null, info: null };

  // Con la página servida por servidor.py la API está en el mismo origen; abierta con doble
  // clic (file://) se busca en el puerto por defecto
  function candidatos() {
    const locales = [`http://127.0.0.1:${PUERTO}`, `http://localhost:${PUERTO}`];
    return location.protocol.startsWith('http') ? ['', ...locales.filter(u => u !== location.origin)] : locales;
  }

  async function pedir(base, ruta, cuerpo, { senal, espera } = {}) {
    const control = new AbortController();
    const corte = espera ? setTimeout(() => control.abort(), espera) : null;
    if (senal) senal.addEventListener('abort', () => control.abort(), { once: true });
    try {
      const r = await fetch(`${base}/api/${ruta}`, cuerpo
        ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(cuerpo), signal: control.signal }
        : { signal: control.signal, cache: 'no-store' });
      let j = null;
      try { j = await r.json(); } catch (e) { /* respuesta sin JSON */ }
      if (!r.ok || !j || !j.ok) throw Object.assign(new Error((j && j.error) || `El servidor respondió ${r.status}`), { http: true });
      return j;
    } finally {
      if (corte) clearTimeout(corte);
    }
  }

  async function conectar() {
    if (SRV.estado === 'conectando') return;
    SRV.estado = 'conectando';
    pintarServidor();
    for (const base of candidatos()) {
      try {
        // En el mismo sitio (servidor.py o la función de Vercel) se espera más: la primera
        // llamada a una función de Vercel arranca en frío y carga Python y OR-Tools
        SRV.info = await pedir(base, 'estado', null, { espera: base === '' ? 30000 : 2500 });
        SRV.base = base;
        SRV.estado = 'conectado';
        break;
      } catch (e) { /* se prueba el siguiente */ }
    }
    if (SRV.estado !== 'conectado') { SRV.estado = 'sin-servidor'; SRV.info = null; }
    if (SRV.info) ajustarSolvers();
    pintarServidor();
    programarVerificacion(0);
    if (estado.vista === 'edicion' && ['resolver', 'comparar'].includes(estado.edicion)) refrescar();
  }

  // Si no se eligió un solver a mano, se usa el del servidor (Gurobi cuando tiene licencia completa)
  function ajustarSolvers() {
    const lista = SRV.info.solvers || [];
    const defecto = SRV.info.solver_defecto || lista[0] || 'CP-SAT';
    if (!R.solverElegido || !lista.includes(R.solver)) R.solver = defecto;
    if (!C.solversElegidos) C.solvers = [defecto];
    C.solvers = C.solvers.filter(s => lista.includes(s));
  }

  const api = (ruta, cuerpo, opciones) => pedir(SRV.base, ruta, cuerpo, opciones);
  // Segundos máximos por ejecución que acepta el servidor (240 en Vercel, 600 en local)
  const topeTiempo = () => (SRV.info && SRV.info.tiempo_max_tope) || 600;
  const errorDeRed = e => !e.http && e.name !== 'AbortError';

  // Si el servidor no está, los métodos se muestran igual (sin poder ejecutarlos)
  const METODOS_LOCAL = [
    { id: 'ils', nombre: 'Búsqueda local iterada (ILS)', tipo: 'metaheurística', descripcion: 'Construcción voraz y luego: descenso de mayor pendiente hasta un óptimo local, perturbación (intercambios al azar) y aceptación de la nueva solución si no es peor.', parametros: [] },
    { id: 'its', nombre: 'Búsqueda tabú iterada (ITS)', tipo: 'metaheurística', descripcion: 'Construcción voraz y luego: búsqueda tabú (acepta el mejor intercambio admisible aunque empeore, con lista tabú y aspiración), perturbación y aceptación. Método por defecto.', parametros: [] },
    { id: 'modelo', nombre: 'Modelo matemático', tipo: 'modelo exacto', descripcion: 'Programación lineal entera (Gurobi u OR-Tools): las restricciones duras van como restricciones.', parametros: [] },
  ];
  const METODO_DEFECTO = 'its';
  const metodos = () => (SRV.info && SRV.info.metodos) || METODOS_LOCAL;
  const solvers = () => (SRV.info ? SRV.info.solvers : ['GUROBI', 'CP-SAT', 'HIGHS', 'SCIP', 'CBC']);
  const conModelo = () => !SRV.info || Boolean(SRV.info.solvers && SRV.info.solvers.length);
  const NOMBRE_SOLVER = { GUROBI: 'Gurobi', 'CP-SAT': 'CP-SAT', HIGHS: 'HiGHS', SCIP: 'SCIP', CBC: 'CBC' };
  const NOTA_SOLVER = { GUROBI: 'comercial · licencia académica', 'CP-SAT': 'Google OR-Tools', HIGHS: 'libre', SCIP: 'libre · ≈ 45 s por ejecución', CBC: 'libre' };

  // Qué hace cada método, para la explicación de la sección Resolver
  const EXPLICACION = [
    ['voraz', 'Heurística constructiva voraz (solución inicial)', 'Es el primer paso de ILS y de ITS. Arma el horario de una pasada: ordena las sesiones de la más difícil a la más fácil y pone cada una donde agrega menos conflictos. Queda completo, pero con unas 50 violaciones que reparan las metaheurísticas. Las dos parten de la misma solución inicial con la misma semilla.'],
    ['ils', 'Búsqueda local iterada (ILS)', 'Repite tres pasos: búsqueda local (descenso de mayor pendiente: en cada paso revisa todos los intercambios de las sesiones en conflicto y aplica el mejor si baja f(x), hasta un óptimo local), perturbación (varios intercambios al azar) y aceptación (la nueva solución reemplaza a la actual si no es peor).'],
    ['its', 'Búsqueda tabú iterada (ITS)', 'Igual que ILS, pero su búsqueda local es una búsqueda tabú: aplica el mejor intercambio aunque empeore f(x), para seguir más allá de los óptimos locales, y prohíbe por unos pasos devolver las sesiones movidas a su lugar anterior (lista tabú), salvo que eso mejore la mejor solución encontrada (aspiración). Si pasan varios pasos sin mejorar, perturba y vuelve a empezar.'],
    ['modelo', 'Modelo matemático', 'No busca paso a paso: escribe el problema completo como programación lineal entera (variables 0/1 de qué sesión va en qué bloque) y un solver (Gurobi o los de OR-Tools) lo resuelve de forma exacta. Si existe un horario factible lo encuentra, y si no existe lo demuestra.'],
  ];

  // Color fijo por método (sigue a la entidad, no al orden): --serie-1 … --serie-8 en estilos.css
  const SERIE = { ils: 3, its: 4, 'modelo:GUROBI': 5, 'modelo:CP-SAT': 6, 'modelo:HIGHS': 7, 'modelo:SCIP': 8, 'modelo:CBC': 0, voraz: 1 };
  const colorDe = clave => `var(--serie-${SERIE[clave] ?? 0})`;
  const claveDe = r => (r.metodo === 'modelo' ? `modelo:${(r.parametros && r.parametros.solver) || 'CP-SAT'}` : r.metodo);
  // 'voraz' es la solución inicial de las dos metaheurísticas (no se ejecuta como método aparte)
  const CORTO = { voraz: ['Construcción voraz', 'Voraz'], ils: ['Búsqueda local iterada (ILS)', 'ILS'],
    its: ['Búsqueda tabú iterada (ITS)', 'ITS'] };
  function nombreClave(clave, estrecho = false) {
    if (clave.startsWith('modelo:')) {
      const s = NOMBRE_SOLVER[clave.slice(7)] || clave.slice(7);
      return estrecho ? `PLE ${s}` : `Modelo · ${s}`;
    }
    return (CORTO[clave] || [clave, clave])[estrecho ? 1 : 0];
  }
  const ORDEN_CLAVES = ['ils', 'its', 'modelo:GUROBI', 'modelo:CP-SAT', 'modelo:HIGHS', 'modelo:SCIP', 'modelo:CBC'];

  const MOTIVOS = {
    costo_cero: 'llegó a f(x) = 0', tiempo_max: 'se agotó el tiempo máximo', max_pasos: 'se agotaron los pasos',
    optimo_local: 'óptimo local (sin mejoras)', factible_sin_mejora: 'factible y sin más mejoras',
    sin_violaciones: 'sin violaciones que reparar', sin_candidatos: 'sin sesiones movibles en conflicto',
    solo_construccion: 'solo construcción, sin fase de mejora',
  };
  const motivo = m => MOTIVOS[m] || m || '—';

  // ===========================================================================
  // 3. INSTANCIA EDITABLE
  // ===========================================================================
  // Formato (el mismo que recibe servidor.py):
  //   docentes  [{ nombre, departamento (nombre completo), original (null si es nuevo) }]
  //   jefes     { curso: docente }               malla { curso: [{ asignatura, horas, docentes, espacio }] }
  //   franjas   { nivel: [{ periodos, grupos: [{ asignatura, seccion, docente, sala, etiqueta }] }] }
  function derivarBase(datos) {
    return {
      version: 1,
      departamentos: [...new Set(datos.docentes.map(d => d.departamentoCompleto))],
      docentes: datos.docentes.map(d => ({ nombre: d.nombre, departamento: d.departamentoCompleto, original: d.nombre })),
      jefes: Object.fromEntries(datos.cursos.filter(c => !c.parvulo).map(c => [c.id, c.jefe])),
      malla: Object.fromEntries(datos.cursos.map(c => [c.id, c.malla
        .filter(f => !f.asignatura.startsWith('Formación Diferenciada'))
        .map(f => ({ asignatura: f.asignatura, horas: f.horas, docentes: [...f.docentes], espacio: f.espacio }))])),
      franjas: Object.fromEntries(Object.entries(datos.franjas).map(([nivel, lista]) => [nivel, lista.map(f => ({
        periodos: f.periodos.map(p => ({ dia: p.dia, bloque: p.bloque })),
        grupos: f.grupos.map(g => ({ asignatura: g.asignatura, seccion: g.seccion, docente: g.docente, sala: g.sala, etiqueta: g.etiqueta })),
      }))])),
      salas: datos.espacios.filter(e => e.tipo === 'sala').map(e => e.nombre),
      franjas_fijas: true,   // el horario 2027 se generó con las franjas en los bloques del Excel 2026
    };
  }

  // Estructura que no se edita (cursos, asignaturas y franjas): sirve para validar lo guardado
  const ESTRUCTURA = derivarBase(DATOS);
  function compatible(inst) {
    try {
      if (!inst || inst.version !== 1 || !Array.isArray(inst.docentes) || !inst.malla || !inst.franjas || !inst.jefes) return false;
      const filasOk = CURSOS.every(c => {
        const a = inst.malla[c.id];
        const b = ESTRUCTURA.malla[c.id];
        return Array.isArray(a) && a.length === b.length && a.every((f, i) => f.asignatura === b[i].asignatura
          && f.horas === b[i].horas && Array.isArray(f.docentes) && f.docentes.length === b[i].docentes.length);
      });
      return filasOk && Object.keys(ESTRUCTURA.franjas).every(n => Array.isArray(inst.franjas[n])
        && inst.franjas[n].length === ESTRUCTURA.franjas[n].length && inst.franjas[n].every(f => Array.isArray(f.grupos)));
    } catch (e) {
      return false;
    }
  }

  // Instancia base = los datos con que se generó el horario 2027 (DatosColegio). Nunca se edita:
  // los cambios van en INST. Si en pantalla está un resultado del solver, la base viaja dentro de
  // ese resultado (verResultado) o se toma la guardada al abrir un horario normal.
  const BASE = (() => {
    if (!DATOS.meta.desarrollador) {
      guardar(CLAVES.base, JSON.stringify(ESTRUCTURA));
      return ESTRUCTURA;
    }
    const enResultado = DATOS.meta.desarrollador.base;
    if (compatible(enResultado)) return enResultado;
    const guardada = leerJSON(CLAVES.base);
    return compatible(guardada) ? guardada : ESTRUCTURA;
  })();
  Object.freeze(BASE);
  const NOMBRE_BASE = 'instancia base 2027';   // DatosColegio.ANIO_HORARIO: la del horario generado
  const SALAS = BASE.salas;
  const DEPARTAMENTOS = BASE.departamentos;
  const NIVELES = Object.keys(BASE.franjas);
  const pastoral = new Map(DATOS.espacios.map(e => [e.nombre, new Set(e.pastoral.map(p => `${p.dia}|${p.bloque}`))]));
  // Bloques distintos de la semana en que algún curso tiene clases (tope de carga de un docente)
  const BLOQUES_SEMANA = (() => {
    const s = new Set();
    CURSOS.forEach(c => c.jornada.forEach((j, d) => { for (let b = 1; b <= j; b++) s.add(`${d}|${b}`); }));
    return s.size;
  })();

  let INST = (() => {
    const guardada = leerJSON(CLAVES.instancia);
    return compatible(guardada) ? guardada : clonar(BASE);
  })();

  function guardarInstancia() {
    guardar(CLAVES.instancia, JSON.stringify(INST));
    cache = null;
  }

  // Deshacer: copias de la instancia antes de cada cambio (solo en esta visita)
  const HISTORIAL = [];
  function recordar(copia) {
    HISTORIAL.push(copia);
    if (HISTORIAL.length > 40) HISTORIAL.shift();
  }

  // Cálculos que dependen de la instancia (se rehacen tras cada cambio)
  let cache = null;
  function calc() {
    if (cache) return cache;
    const mapa = new Map(INST.docentes.filter(d => d.original).map(d => [d.original, d.nombre]));
    const carga = new Map(INST.docentes.map(d => [d.nombre, 0]));
    const suma = (d, h) => carga.set(d, (carga.get(d) || 0) + h);
    CURSOS.forEach(c => INST.malla[c.id].forEach(f => f.docentes.forEach(d => suma(d, f.horas))));
    Object.values(INST.franjas).forEach(lista => lista.forEach(f => [...new Set(f.grupos.map(g => g.docente))].forEach(d => suma(d, 6))));
    cache = { mapa, carga, cambios: null, validacion: null };
    cache.cambios = listarCambios(mapa);
    cache.validacion = validar(carga);
    return cache;
  }
  const hayCambios = () => calc().cambios.length > 0;

  function firmaGrupo(g, mapa) {
    return [g.asignatura, g.seccion, mapa ? (mapa.get(g.docente) ?? '∅') : g.docente, g.sala].join('|');
  }

  function filaEditada(curso, i, mapa) {
    const b = BASE.malla[curso][i];
    return INST.malla[curso][i].docentes.some((d, s) => d !== mapa.get(b.docentes[s]));
  }

  function grupoEditado(nivel, k, g, mapa) {
    return !BASE.franjas[nivel][k].grupos.some(b => firmaGrupo(b, mapa) === firmaGrupo(g));
  }

  function listarCambios(mapa) {
    const lista = [];
    const deptoBase = new Map(BASE.docentes.map(d => [d.nombre, d.departamento]));
    INST.docentes.forEach(d => {
      if (!d.original) { lista.push({ seccion: 'docentes', texto: `Nuevo docente: ${d.nombre}` }); return; }
      if (d.nombre !== d.original) lista.push({ seccion: 'docentes', texto: `${d.original} pasa a llamarse ${d.nombre}` });
      if (deptoBase.get(d.original) !== d.departamento) lista.push({ seccion: 'docentes', texto: `${d.nombre} cambia a ${APP.nombreDepartamento(d.departamento)}` });
    });
    BASE.docentes.forEach(b => { if (!mapa.has(b.nombre)) lista.push({ seccion: 'docentes', texto: `Se quitó a ${b.nombre}` }); });
    CURSOS.forEach(c => {
      if (!c.parvulo && INST.jefes[c.id] !== mapa.get(BASE.jefes[c.id])) {
        lista.push({ seccion: 'asignacion', curso: c.id, texto: `${c.nombre}: jefatura de ${INST.jefes[c.id]}` });
      }
      INST.malla[c.id].forEach((f, i) => {
        if (!ORIENTACION.includes(f.asignatura) && filaEditada(c.id, i, mapa)) {
          lista.push({ seccion: 'asignacion', curso: c.id, texto: `${c.nombre} · ${infoAsig(f.asignatura).nombre}: ${f.docentes.join(' y ')}` });
        }
      });
    });
    NIVELES.forEach(nivel => INST.franjas[nivel].forEach((f, k) => {
      const resto = BASE.franjas[nivel][k].grupos.map(g => firmaGrupo(g, mapa));
      let distintos = 0;
      f.grupos.forEach(g => { const j = resto.indexOf(firmaGrupo(g)); if (j >= 0) resto.splice(j, 1); else distintos += 1; });
      const n = Math.max(distintos, resto.length);
      if (n) lista.push({ seccion: 'electivos', texto: `${nombreNivel(nivel)}, franja ${k + 1}: ${n} electivo${n > 1 ? 's' : ''} con cambios` });
    }));
    if (INST.franjas_fijas === false) lista.push({ seccion: 'electivos', texto: 'Franjas de electivos móviles: los bloques los elige el solver' });
    return lista;
  }

  // Errores (impiden resolver: el servidor los rechazaría) y avisos (se puede resolver igual)
  function validar(carga) {
    const errores = [];
    const avisos = [];
    const nombres = new Set(INST.docentes.map(d => d.nombre));
    const existe = (doc, donde) => { if (!nombres.has(doc)) errores.push(`${donde}: falta el docente "${doc}"`); };
    CURSOS.forEach(c => {
      if (!c.parvulo) existe(INST.jefes[c.id], `Jefatura de ${c.nombre}`);
      INST.malla[c.id].forEach(f => {
        f.docentes.forEach(d => existe(d, `${c.nombre} · ${infoAsig(f.asignatura).nombre}`));
        if (new Set(f.docentes).size !== f.docentes.length) errores.push(`${c.nombre} · ${infoAsig(f.asignatura).nombre}: la co-docencia necesita dos docentes distintos`);
      });
    });
    NIVELES.forEach(nivel => INST.franjas[nivel].forEach((f, k) => {
      const lugar = `${nombreNivel(nivel)}, franja ${k + 1}`;
      if (!f.grupos.length) errores.push(`${lugar}: no tiene electivos`);
      const docentes = new Map();
      const salas = new Map();
      f.grupos.forEach(g => {
        if (!g.asignatura.trim()) errores.push(`${lugar}: un electivo no tiene nombre`);
        if (!g.seccion.trim()) errores.push(`${lugar}: ${titulo(g.asignatura)} no tiene sección`);
        existe(g.docente, `${lugar} · ${titulo(g.asignatura)}`);
        docentes.set(g.docente, (docentes.get(g.docente) || 0) + 1);
        salas.set(g.sala, (salas.get(g.sala) || 0) + 1);
        const bloqueos = pastoral.get(g.sala) || new Set();
        f.periodos.forEach(p => {
          if (bloqueos.has(`${p.dia}|${p.bloque}`) || bloqueos.has(`${p.dia}|${p.bloque + 1}`)) {
            avisos.push(`${lugar}: ${nombreEspacio(g.sala)} tiene un bloqueo de pastoral el ${p.dia.toLowerCase()} (la auditoría lo marcará)`);
          }
        });
      });
      docentes.forEach((n, d) => { if (n > 1) errores.push(`${lugar}: ${d} dicta ${n} electivos a la vez`); });
      salas.forEach((n, s) => { if (n > 1) avisos.push(`${lugar}: ${n} electivos usan ${nombreEspacio(s)} a la vez`); });
    }));
    carga.forEach((h, d) => {
      if (h > BLOQUES_SEMANA) avisos.push(`${d} tiene ${h} h en grilla y la semana tiene ${BLOQUES_SEMANA} bloques: no hay horario factible`);
    });
    return { errores, avisos };
  }

  // ------------------------------------------------------------- operaciones ---
  function referencias(nombre) {
    const filas = [];
    const jefaturas = [];
    const grupos = [];
    CURSOS.forEach(c => {
      if (INST.jefes[c.id] === nombre) jefaturas.push(c.id);
      INST.malla[c.id].forEach((f, i) => f.docentes.forEach((d, s) => { if (d === nombre) filas.push({ curso: c.id, i, s }); }));
    });
    NIVELES.forEach(nivel => INST.franjas[nivel].forEach((f, k) => f.grupos.forEach((g, i) => { if (g.docente === nombre) grupos.push({ nivel, k, i }); })));
    return { filas, jefaturas, grupos, total: filas.length + jefaturas.length + grupos.length };
  }

  function reemplazar(viejo, nuevo) {
    Object.keys(INST.jefes).forEach(c => { if (INST.jefes[c] === viejo) INST.jefes[c] = nuevo; });
    Object.values(INST.malla).forEach(filas => filas.forEach(f => { f.docentes = f.docentes.map(d => (d === viejo ? nuevo : d)); }));
    Object.values(INST.franjas).forEach(lista => lista.forEach(f => f.grupos.forEach(g => { if (g.docente === viejo) g.docente = nuevo; })));
  }

  function limpiarNombre(texto, excepto) {
    const n = String(texto || '').replace(/\s+/g, ' ').trim();
    if (!n) return [null, 'Escribe un nombre para el docente.'];
    if (n.length > 60) return [null, 'El nombre es demasiado largo (máximo 60 caracteres).'];
    if (INST.docentes.some(d => d.nombre === n && d.nombre !== excepto)) return [null, `Ya hay un docente llamado ${n}.`];
    return [n, null];
  }

  const OPERACIONES = {
    agregarDocente(nombre, departamento) {
      const [n, error] = limpiarNombre(nombre);
      if (error) return error;
      if (!DEPARTAMENTOS.includes(departamento)) return 'Elige un departamento.';
      INST.docentes.push({ nombre: n, departamento, original: null });
      return null;
    },
    renombrar(viejo, nombre) {
      const [n, error] = limpiarNombre(nombre, viejo);
      if (error) return error;
      if (n === viejo) return null;
      INST.docentes.find(d => d.nombre === viejo).nombre = n;
      reemplazar(viejo, n);
      return null;
    },
    departamento(nombre, departamento) {
      const d = INST.docentes.find(x => x.nombre === nombre);
      if (!d || !DEPARTAMENTOS.includes(departamento)) return 'Departamento desconocido.';
      d.departamento = departamento;
      return null;
    },
    quitar(nombre, reemplazo) {
      const r = referencias(nombre);
      if (INST.docentes.length <= 1) return 'Debe quedar al menos un docente.';
      if (r.total) {
        if (!reemplazo || reemplazo === nombre) return `Elige quién se queda con las clases de ${nombre}.`;
        const choques = [];
        r.filas.forEach(({ curso, i }) => {
          const f = INST.malla[curso][i];
          if (f.docentes.includes(reemplazo)) choques.push(`${nombreCurso(curso)} · ${infoAsig(f.asignatura).nombre}`);
        });
        r.grupos.forEach(({ nivel, k }) => {
          if (INST.franjas[nivel][k].grupos.some(g => g.docente === reemplazo)) choques.push(`${nombreNivel(nivel)}, franja ${k + 1}`);
        });
        if (choques.length) return `${reemplazo} ya participa en ${[...new Set(choques)].join(', ')}: elige a otro docente.`;
        reemplazar(nombre, reemplazo);
      }
      INST.docentes = INST.docentes.filter(d => d.nombre !== nombre);
      return null;
    },
    asignar(curso, i, s, docente) {
      const f = INST.malla[curso][i];
      if (f.docentes.some((d, j) => j !== s && d === docente)) return 'La co-docencia necesita dos docentes distintos.';
      f.docentes[s] = docente;
      return null;
    },
    jefe(curso, docente) {
      INST.jefes[curso] = docente;
      INST.malla[curso].forEach(f => { if (ORIENTACION.includes(f.asignatura)) f.docentes[0] = docente; });
      return null;
    },
    grupo(nivel, k, i, prop, valor) {
      const franja = INST.franjas[nivel][k];
      const g = franja.grupos[i];
      if (prop === 'docente') {
        if (franja.grupos.some((x, j) => j !== i && x.docente === valor)) return `${valor} ya dicta otro electivo en esta franja.`;
        g.docente = valor;
      } else if (prop === 'sala') {
        g.sala = valor;
      } else if (prop === 'asignatura' || prop === 'seccion') {
        const v = String(valor || '').replace(/\s+/g, ' ').trim();
        if (!v) return prop === 'asignatura' ? 'El electivo necesita un nombre.' : 'El electivo necesita una sección.';
        if (v.length > (prop === 'asignatura' ? 80 : 12)) return 'El texto es demasiado largo.';
        g[prop] = prop === 'asignatura' ? v.toLocaleUpperCase('es-CL') : v;
        g.etiqueta = etiquetaGrupo(g);
      }
      return null;
    },
    agregarGrupo(nivel, k) {
      const franja = INST.franjas[nivel][k];
      if (franja.grupos.length >= 10) return 'Una franja admite hasta 10 electivos.';
      const ocupados = new Set(franja.grupos.map(g => g.docente));
      const docente = INST.docentes.map(d => d.nombre).find(d => !ocupados.has(d));
      if (!docente) return 'No quedan docentes libres en esta franja.';
      const salasUsadas = new Set(franja.grupos.map(g => g.sala));
      const g = { asignatura: 'NUEVO ELECTIVO', seccion: `S.${k + 1}`, docente, sala: SALAS.find(s => !salasUsadas.has(s)) || SALAS[0] };
      g.etiqueta = etiquetaGrupo(g);
      franja.grupos.push(g);
      return null;
    },
    quitarGrupo(nivel, k, i) {
      const franja = INST.franjas[nivel][k];
      if (franja.grupos.length <= 1) return 'Cada franja necesita al menos un electivo.';
      franja.grupos.splice(i, 1);
      return null;
    },
    franjasFijas(valor) {
      INST.franjas_fijas = Boolean(valor);
      return null;
    },
  };

  // Igual que servidor.py: "ECONOMÍA S.1"
  function etiquetaGrupo(g) {
    return `${g.asignatura.split(/\s+/)[0].replace(/,$/, '').slice(0, 12)} ${g.seccion}`;
  }

  function aplicar(operacion, ...args) {
    const antes = JSON.stringify(INST);
    const error = OPERACIONES[operacion](...args);
    if (error) {
      INST = JSON.parse(antes);   // ninguna operación queda a medias
      cache = null;
      avisar(error, 'error');
      refrescar();
      return false;
    }
    if (JSON.stringify(INST) !== antes) {
      recordar(JSON.parse(antes));
      guardarInstancia();
      programarVerificacion();
    }
    avisar(null);
    refrescar();
    return true;
  }

  // Reemplaza la instancia completa (deshacer, volver a la base, importar) sin perder el historial
  function cambiarInstancia(nueva, mensaje, { guardarEnHistorial = true } = {}) {
    if (guardarEnHistorial) recordar(clonar(INST));
    INST = nueva;
    UI.quitando = null;
    guardarInstancia();
    avisar(mensaje);
    refrescar();
    programarVerificacion(0);
  }

  function deshacer() {
    if (!HISTORIAL.length) return;
    cambiarInstancia(HISTORIAL.pop(), 'Se deshizo el último cambio.', { guardarEnHistorial: false });
  }

  // ---------------------------------------------------------- factibilidad ---
  // Tras cada cambio se pregunta al servidor si la instancia admite un horario factible
  // (/api/factibilidad: revisión de cargas y modelo matemático en modo elástico). Si no, el
  // aviso muestra cuántas violaciones duras son inevitables y por qué.
  const FACT = { firma: null, estado: 'base', resultado: null, error: null, espera: null, control: null };
  const RESULTADOS_FACT = new Map(sesion.leer('mmdd-dev-factibilidad') || []);

  function huella(texto) {   // FNV-1a de 32 bits: identifica una instancia sin guardarla entera
    let h = 0x811c9dc5;
    for (let i = 0; i < texto.length; i++) { h ^= texto.charCodeAt(i); h = Math.imul(h, 0x01000193); }
    return `${(h >>> 0).toString(16)}-${texto.length}`;
  }
  const estadoFact = r => (r.factible === true ? 'factible' : r.factible === false ? 'infactible' : 'desconocido');

  function programarVerificacion(retardo = 900) {
    clearTimeout(FACT.espera);
    if (!hayCambios()) {
      FACT.firma = null;
      FACT.estado = 'base';
      pintarFactibilidad();
      return;
    }
    const firma = huella(JSON.stringify(INST));
    FACT.firma = firma;
    const previo = RESULTADOS_FACT.get(firma);
    if (calc().validacion.errores.length) FACT.estado = 'invalida';
    else if (previo) { FACT.resultado = previo; FACT.estado = estadoFact(previo); }
    else if (SRV.estado !== 'conectado') FACT.estado = 'sin-servidor';
    else {
      FACT.estado = 'pendiente';
      FACT.espera = setTimeout(() => verificarAhora(firma), retardo);
    }
    pintarFactibilidad();
  }

  async function verificarAhora(firma) {
    if (FACT.control) FACT.control.abort();
    const control = new AbortController();
    FACT.control = control;
    FACT.estado = 'verificando';
    pintarFactibilidad();
    try {
      const r = await api('factibilidad', { instancia: INST }, { senal: control.signal });
      RESULTADOS_FACT.set(firma, r);
      sesion.guardar('mmdd-dev-factibilidad', [...RESULTADOS_FACT].slice(-20));
      if (FACT.firma !== firma) return;   // la instancia cambió mientras se verificaba
      FACT.resultado = r;
      FACT.estado = estadoFact(r);
    } catch (e) {
      if (e.name === 'AbortError' || FACT.firma !== firma) return;
      FACT.estado = 'error';
      FACT.error = errorDeRed(e) ? 'Se perdió la conexión con el solver.' : e.message;
    } finally {
      if (FACT.control === control) FACT.control = null;
      pintarFactibilidad();
    }
  }

  function htmlFactibilidad() {
    const r = FACT.resultado;
    const seg = r ? fmtMs(r.tiempo_ms) : '';
    switch (FACT.estado) {
      case 'sin-servidor':
        return `<div class="dev-fact">${ICONOS.alerta}<p>Conecta el solver para comprobar si estos cambios todavía permiten armar un horario factible.</p></div>`;
      case 'pendiente':
      case 'verificando':
        return '<div class="dev-fact"><span class="dev-girando"></span><p>Comprobando si existe un horario factible con estos cambios…</p></div>';
      case 'factible':
        return `<div class="dev-fact bien">${ICONOS.ok}<p><b>Con estos cambios sí se puede armar un horario factible.</b> Lo comprobó el modelo exacto (${esc(NOMBRE_SOLVER[r.solver] || r.solver)}, ${seg}).</p></div>`;
      case 'infactible': {
        const n = r.violaciones_minimas;
        const razones = r.razones.map(x => `<li>${esc(x.texto)}</li>`).join('');
        return `
          <div class="dev-fact mal" role="alert">
            ${ICONOS.alerta}
            <div>
              <p><b>Con estos cambios no se puede armar un horario factible.</b>
                ${n ? `Hasta el mejor horario posible tendría ${r.probado ? '' : 'al menos '}${fmt(n, 0)} violaci${n > 1 ? 'ones' : 'ón'} dura${n > 1 ? 's' : ''} (f(x) ${r.probado ? '=' : '≥'} ${fmt(n * PESO_DURO, 0)}).` : ''} Por qué:</p>
              <ul>${razones}</ul>
              ${r.total_razones > r.razones.length ? `<p class="dev-tenue">… y ${r.total_razones - r.razones.length} más.</p>` : ''}
              <p class="dev-tenue">Comprobado con el modelo exacto en ${seg}. Los métodos de Resolver no llegarán a f(x) = 0 con esta instancia.</p>
              <div class="dev-acciones">
                ${HISTORIAL.length ? `<button type="button" class="boton" data-dev="deshacer">${ICONOS.deshacer}Deshacer el último cambio</button>` : ''}
                <button type="button" class="enlace" data-dev="restablecer">Volver a la ${esc(NOMBRE_BASE)}</button>
              </div>
            </div>
          </div>`;
      }
      case 'desconocido':
        return `<div class="dev-fact">${ICONOS.alerta}<p>No se alcanzó a comprobar la factibilidad en ${seg}${r.violaciones_encontradas ? `; el mejor horario encontrado tiene ${fmt(r.violaciones_encontradas, 0)} violaciones duras` : ''}.</p></div>`;
      case 'error':
        return `<div class="dev-fact">${ICONOS.alerta}<p>No se pudo comprobar la factibilidad: ${esc(FACT.error)}</p><button type="button" class="enlace" data-dev="verificar">Reintentar</button></div>`;
      default:
        return '';   // 'base' (factible por definición) o 'invalida' (los errores se muestran aparte)
    }
  }

  function pintarFactibilidad() {
    const el = $('#dev-factibilidad');
    if (!el) return;
    const html = htmlFactibilidad();
    el.innerHTML = html;
    el.hidden = !html;
    const pildora = $('#dev-instancia');
    if (pildora) pildora.innerHTML = htmlInstancia();
  }

  // ===========================================================================
  // 4. DIAGNÓSTICO DE LA FUNCIÓN OBJETIVO DEL HORARIO EN PANTALLA
  // ===========================================================================
  // Misma definición que ModeloHorario (notebooks/horarios/modelo.py), calculada sobre la grilla:
  //   D  por (docente, día, bloque): grupos que atiende a la vez − 1 (un electivo A+B es un grupo)
  //   F  por (curso, día, asignatura): sesiones ese día − 1 (un par pedagógico completo es una sesión)
  //   R  por (día, bloque): cursos en la sala English skills − 1
  //   G  por (gimnasio, día, bloque): cursos en Ed. Física − 1
  const EVAL = (() => {
    const H = { D: 0, F: 0, R: 0, G: 0 };
    const lista = [];
    const porCurso = new Map();
    const porDocente = new Map();
    const anotar = (mapa, k, i) => { if (!mapa.has(k)) mapa.set(k, []); mapa.get(k).push(i); };
    const agregar = (conflicto, cursos, docentes, bloques) => {
      const i = lista.push(conflicto) - 1;
      bloques.forEach(([dia, b]) => {
        cursos.forEach(c => anotar(porCurso, `${c}|${dia}|${b}`, i));
        docentes.forEach(d => anotar(porDocente, `${d}|${dia}|${b}`, i));
      });
    };
    const familia = a => (a === 'English Skills' ? 'Idioma Extranjero Inglés' : a);
    const inicioPar = new Set(DATOS.pares.map(p => p[0]));

    // D: docentes en dos grupos a la vez
    const grupos = new Map();
    CURSOS.forEach(c => c.clases.forEach(k => {
      const g = k.franja ? `${nombreNivel(c.nivel)} A-B` : c.nombre;
      k.docentes.forEach(doc => {
        const id = `${doc}|${k.dia}|${k.bloque}`;
        if (!grupos.has(id)) grupos.set(id, new Map());
        const m = grupos.get(id);
        if (!m.has(g)) m.set(g, []);
        m.get(g).push(c.id);
      });
    }));
    grupos.forEach((m, id) => {
      if (m.size < 2) return;
      const [doc, dia, b] = id.split('|');
      H.D += m.size - 1;
      agregar({ tipo: 'D', n: m.size - 1, dia, bloque: Number(b), texto: `${doc} atiende ${[...m.keys()].join(', ')} a la vez` },
        [...m.values()].flat(), [doc], [[dia, Number(b)]]);
    });

    // F: más de una sesión de la misma asignatura en el día
    CURSOS.forEach(c => {
      const porDia = new Map();
      c.clases.forEach(k => {
        if (k.franja) return;
        const id = `${k.dia}|${familia(k.asignatura)}`;
        if (!porDia.has(id)) porDia.set(id, []);
        porDia.get(id).push(k.bloque);
      });
      porDia.forEach((bloques, id) => {
        const [dia, asig] = id.split('|');
        const set = new Set(bloques);
        let sesiones = bloques.length;
        set.forEach(b => { if (inicioPar.has(b) && set.has(b + 1)) sesiones -= 1; });
        if (sesiones < 2) return;
        H.F += sesiones - 1;
        const orden = [...set].sort((a, b) => a - b);
        agregar({ tipo: 'F', n: sesiones - 1, dia, bloque: orden[0], texto: `${c.nombre}: ${infoAsig(asig).nombre} en ${sesiones} sesiones el ${dia.toLowerCase()} (bloques ${orden.join(', ')})` },
          [c.id], [], orden.map(b => [dia, b]));
      });
    });

    // R: sala English skills (un curso por bloque)
    const skills = new Map();
    CURSOS.forEach(c => c.clases.forEach(k => {
      if (k.espacio !== 'Sala English skills') return;
      const id = `${k.dia}|${k.bloque}`;
      if (!skills.has(id)) skills.set(id, []);
      skills.get(id).push(c.id);
    }));
    skills.forEach((cursos, id) => {
      if (cursos.length < 2) return;
      const [dia, b] = id.split('|');
      H.R += cursos.length - 1;
      agregar({ tipo: 'R', n: cursos.length - 1, dia, bloque: Number(b), texto: `Sala English skills con ${cursos.map(nombreCurso).join(', ')}` }, cursos, [], [[dia, Number(b)]]);
    });

    // G: un curso por gimnasio
    DATOS.espacios.filter(e => e.tipo === 'recinto').forEach(e => e.usos.forEach(u => {
      const cursos = u.items.map(it => it.curso).filter(Boolean);
      if (cursos.length < 2) return;
      H.G += cursos.length - 1;
      agregar({ tipo: 'G', n: cursos.length - 1, dia: u.dia, bloque: u.bloque, texto: `${nombreEspacio(e.nombre)} con ${cursos.map(nombreCurso).join(', ')}` }, cursos, [], [[u.dia, u.bloque]]);
    }));

    const total = H.D + H.F + H.R + H.G;
    lista.sort((a, b) => DIAS.indexOf(a.dia) - DIAS.indexOf(b.dia) || a.bloque - b.bloque || a.tipo.localeCompare(b.tipo));
    return { H, total, f: PESO_DURO * total, lista, porCurso, porDocente };
  })();

  const TIPOS = [
    ['D', 'Choques de docentes', 'Un docente con dos grupos en el mismo bloque'],
    ['F', 'Asignatura repetida en el día', 'Sesiones de una asignatura en un día, menos una'],
    ['R', 'Sala English skills', 'Cursos sobre la capacidad de la sala Electivo 1'],
    ['G', 'Gimnasios', 'Cursos en Ed. Física sobre uno por gimnasio'],
  ];

  // Conflictos que tocan los bloques inicio..fin; los de un bloque doble se juntan en uno
  function conflictosEn(mapa, prefijo, dia, inicio, fin) {
    const idx = new Set();
    for (let b = inicio; b <= fin; b++) (mapa.get(`${prefijo}|${dia}|${b}`) || []).forEach(i => idx.add(i));
    const grupos = new Map();
    [...idx].map(i => EVAL.lista[i]).forEach(c => {
      const k = `${c.tipo}|${c.texto}`;
      if (!grupos.has(k)) grupos.set(k, { ...c, n: 0, bloques: [] });
      const g = grupos.get(k);
      g.n += c.n;
      g.bloques.push(c.bloque);
    });
    return [...grupos.values()].map(g => {
      const bloques = [...new Set(g.bloques)].sort((a, b) => a - b);
      return { ...g, texto: g.tipo === 'F' ? g.texto : `${g.texto} (${bloques.length > 1 ? `bloques ${bloques.join(' y ')}` : `bloque ${bloques[0]}`})` };
    });
  }

  // Marcas en las grillas de Cursos y Docentes
  function marcarGrilla(panel, mapa, prefijo) {
    if (!panel) return;
    $$('.sesion[data-dia][data-inicio]', panel).forEach(el => {
      const lista = conflictosEn(mapa, prefijo, el.dataset.dia, Number(el.dataset.inicio), Number(el.dataset.fin || el.dataset.inicio));
      if (!lista.length) return;
      el.classList.add('dev-conflicto');
      el.dataset.tip = `<b>${lista.length === 1 ? 'Conflicto' : `${lista.length} conflictos`} de la función objetivo</b><br>${lista.map(c => esc(c.texto)).join('<br>')}`;
      if (!$('.dev-marca', el)) el.insertAdjacentHTML('beforeend', `<span class="dev-marca" aria-hidden="true">${lista.length > 1 ? lista.length : '!'}</span>`);
      el.setAttribute('aria-label', `${el.getAttribute('aria-label') || ''}. Conflicto: ${lista.map(c => c.texto).join('; ')}`);
    });
  }

  function detalleExtra(vista, dia, inicio, fin) {
    let lista = [];
    if (vista === 'cursos') lista = conflictosEn(EVAL.porCurso, estado.curso, dia, inicio, fin);
    else if (vista === 'docentes') lista = conflictosEn(EVAL.porDocente, estado.docente, dia, inicio, fin);
    if (!lista.length) return '';
    return `
      <div class="dev-detalle">
        <h3><span class="dev-sello">DEV</span>Conflictos en esta clase</h3>
        <ul>${lista.map(c => `<li><span class="dev-tipo">${c.tipo}</span>${esc(c.texto)}</li>`).join('')}</ul>
        <p class="nota">Suman ${fmt(PESO_DURO * lista.reduce((s, c) => s + c.n, 0))} a f(x). Ver todos en Auditoría.</p>
      </div>`;
  }

  function pintarAuditoria(el, animarEntrada) {
    if (!el) return;
    const m = DATOS.auditoria.metricas;
    const maxH = Math.max(1, ...TIPOS.map(t => EVAL.H[t[0]]));
    const bloquesClase = CURSOS.reduce((s, c) => s + c.clases.length, 0);
    const meta = DATOS.meta;
    const fuente = meta.desarrollador ? `Resultado del solver: ${meta.desarrollador.nombre}`
      : meta.fuente === 'oficial' ? `Excel oficial (${meta.archivo})` : `Motor del proyecto, semilla ${meta.semilla}`;
    const MAX_LISTA = 150;
    const conflictos = EVAL.lista.slice(0, MAX_LISTA).map(c => `
      <li><span class="dev-tipo">${c.tipo}</span><span>${esc(c.texto)}</span>
        <button type="button" class="enlace" data-momento="${c.dia}|${c.bloque}">${DIA_CORTO[c.dia]} · bloque ${c.bloque}</button></li>`).join('');

    el.innerHTML = `
      <section class="seccion dev-seccion">
        <div class="seccion-titulo"><h2><span class="dev-sello">DEV</span>Función objetivo del horario</h2>
          <p>La misma que minimiza el motor: f(x) = 1000 · H(x), con H(x) = violaciones duras</p></div>
        <div class="kpis">
          <div class="kpi"><span class="kpi-valor">${fmt(EVAL.f)}</span><span class="kpi-etiqueta">f(x) de este horario (0 = factible)</span></div>
          <div class="kpi"><span class="kpi-valor">${fmt(EVAL.total)}</span><span class="kpi-etiqueta">violaciones duras H(x)</span></div>
          <div class="kpi"><span class="kpi-valor">${fmt(m.porcentaje_bloques_dobles)}<small>%</small></span><span class="kpi-etiqueta">de las horas en bloques dobles de 90 min</span></div>
          <div class="kpi"><span class="kpi-valor">${fmt(bloquesClase)}</span><span class="kpi-etiqueta">bloques de clase en ${CURSOS.length} cursos</span></div>
        </div>
        <ul class="dev-desglose">${TIPOS.map(([k, nombre, ayuda]) => `
          <li>
            <span class="dev-tipo">${k}</span>
            <span class="dev-desglose-nombre"><b>${nombre}</b><small>${ayuda}</small></span>
            <span class="dev-desglose-pista" aria-hidden="true"><span style="width:${(EVAL.H[k] / maxH) * 100}%"></span></span>
            <span class="dev-desglose-num">${fmt(EVAL.H[k])}</span>
          </li>`).join('')}
        </ul>
        ${EVAL.lista.length ? `
          <details class="dev-conflictos">
            <summary>Ver las ${fmt(EVAL.lista.length)} violaciones${EVAL.lista.length > MAX_LISTA ? ` (primeras ${MAX_LISTA})` : ''}</summary>
            <ul>${conflictos}</ul>
          </details>
          <p class="nota">Las clases con conflictos quedan marcadas en las grillas de Cursos y Docentes mientras el modo desarrollador está activo.${meta.fuente === 'oficial' ? ' En el horario oficial, los choques de docentes salen de cruzar la grilla del Excel con la distribución horaria 2026.' : ''}</p>`
          : '<p class="nota">Sin violaciones duras: el horario es un óptimo de f(x).</p>'}
      </section>
      <section class="seccion dev-seccion">
        <div class="seccion-titulo"><h2>Datos técnicos</h2><p>Lo que lee la página en ${meta.instancia
          ? `<code>datos/instancias/horarios_${meta.anio}_${esc(meta.instancia)}.js</code>` : `<code>datos/horarios_${meta.anio}.js</code>`}</p></div>
        <dl class="datos dev-datos">
          <dt>Origen</dt><dd>${esc(fuente)}</dd>
          <dt>Generado</dt><dd>${esc(meta.generado)}</dd>
          ${meta.nombreInstancia ? `<dt>Instancia generada</dt><dd>${esc(meta.nombreInstancia)} (<code>${esc(meta.instancia)}</code>)${meta.metodo && meta.metodo.nombre ? ` · ${esc(meta.metodo.nombre)}` : ''}</dd>` : ''}
          <dt>Instancia</dt><dd>${meta.desarrollador ? (meta.desarrollador.editada ? 'editada en la pestaña Edición' : 'original') : 'original (datos 2026 de DatosColegio)'}</dd>
          <dt>Tamaño</dt><dd>${CURSOS.length} cursos · ${DATOS.docentes.length} docentes · ${DATOS.espacios.length} salas y recintos · ${Object.values(DATOS.franjas).reduce((s, l) => s + l.length, 0)} franjas de electivos</dd>
          <dt>Auditoría</dt><dd>${DATOS.auditoria.valido ? 'válida' : `${fmt(DATOS.auditoria.totalErrores)} errores`} · ${fmt(m.total_ventanas_docentes)} ventanas docentes</dd>
        </dl>
        <div class="dev-acciones">
          <button type="button" class="boton" data-dev-global="descargar-json">${ICONOS.bajar}Descargar datos (JSON)</button>
          <button type="button" class="boton" data-dev-global="ir-edicion">Abrir la pestaña Edición</button>
        </div>
      </section>`;
    if (animarEntrada) {
      APP.animar.aparecer($$('.dev-seccion', el), { stagger: 0.08 });
      APP.animar.barras($$('.dev-desglose-pista span', el), 'x');
    }
  }

  // Botones del modo desarrollador fuera de la pestaña Edición (Auditoría)
  document.addEventListener('click', ev => {
    const b = ev.target.closest('[data-dev-global]');
    if (!b) return;
    if (b.dataset.devGlobal === 'descargar-json') {
      descargar(`horarios_${DATOS.meta.anio}.json`, JSON.stringify(DATOS, null, 1), 'application/json');
    } else if (b.dataset.devGlobal === 'ir-edicion') {
      APP.ir('edicion', { edicion: 'resolver' });
    }
  });

  function despuesRender(vista, animarEntrada) {
    if (vista === 'auditoria') pintarAuditoria($('#auditoria-dev'), animarEntrada);
    else if (vista === 'cursos') marcarGrilla($('#panel-curso'), EVAL.porCurso, estado.curso);
    else if (vista === 'docentes') marcarGrilla($('#panel-docente'), EVAL.porDocente, estado.docente);
  }

  // ===========================================================================
  // 5. PESTAÑA EDICIÓN: estado, cabecera y navegación
  // ===========================================================================
  const UI = {
    curso: estado.curso,     // curso abierto en Asignación
    quitando: null,          // docente cuyo retiro se está confirmando
    reemplazo: null,         // quién se queda con sus clases
    nuevoDepto: null,        // departamento del docente que se va a agregar
    mensaje: null,           // { tipo: 'error' | 'ok', texto }
  };

  const R = Object.assign({
    metodo: METODO_DEFECTO, semilla: 3, tiempo_max: 20, max_pasos: 150000,
    solver: 'GUROBI', peso_ventanas: 0, hilos: '', parametros: {}, usarBase: false, solverElegido: false,
  }, leerJSON(CLAVES.resolver) || {}, { ejecutando: false, resultado: null, datos: null, error: null, inicio: 0 });
  const guardarR = () => guardar(CLAVES.resolver, JSON.stringify({
    metodo: R.metodo, semilla: R.semilla, tiempo_max: R.tiempo_max, max_pasos: R.max_pasos,
    solver: R.solver, peso_ventanas: R.peso_ventanas, hilos: R.hilos, parametros: R.parametros,
    usarBase: R.usarBase, solverElegido: R.solverElegido,
  }));

  const C = Object.assign({
    metodos: ['ils', 'its'],
    solvers: ['GUROBI'], desde: 1, hasta: 5, tiempo_max: 30, max_pasos: 150000, usarBase: false, solversElegidos: false,
  }, leerJSON(CLAVES.comparar) || {}, { ejecutando: false, detener: false, control: null, progreso: null, errores: [] });
  // Métodos guardados en el navegador que ya no existen (Min-Conflicts, tabú e híbrido anteriores)
  C.metodos = C.metodos.filter(m => m === 'modelo' || CORTO[m] && m !== 'voraz');
  if (!C.metodos.length) C.metodos = ['ils', 'its'];
  const guardarC = () => guardar(CLAVES.comparar, JSON.stringify({
    metodos: C.metodos, solvers: C.solvers, desde: C.desde, hasta: C.hasta, tiempo_max: C.tiempo_max, max_pasos: C.max_pasos,
    usarBase: C.usarBase, solversElegidos: C.solversElegidos,
  }));
  // ¿Se resuelve la instancia editada? (si no hay cambios, siempre es la base)
  const usaEditada = op => hayCambios() && !op.usarBase;

  // Ejecuciones de esta sesión del navegador (Resolver y Comparar). Cada una tiene un id (las de
  // antes de existir el id reciben uno aquí) con el que se guarda su horario en HORARIOS
  const nuevoId = () => `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  let EJECUCIONES = (sesion.leer(CLAVES.ejecuciones) || []).map((e, i) => (e.id ? e : { ...e, id: `${e.cuando || 0}-v${i}` }));
  let LOTE = (EJECUCIONES.filter(e => e.lote).pop() || {}).lote || null;   // última comparación
  R.resultado = [...EJECUCIONES].reverse().find(e => !e.lote) || null;
  // instancia: la que se resolvió (null = base); su huella permite saber si se puede volver a resolver igual
  function registrar(resultado, lote, instancia = null) {
    const r = { ...resultado, lote, cuando: Date.now(), id: nuevoId(), huella: instancia ? huella(JSON.stringify(instancia)) : null };
    if (r.historial && r.historial.length > 150) {
      const paso = (r.historial.length - 1) / 149;
      r.historial = Array.from({ length: 150 }, (_, i) => r.historial[Math.round(i * paso)]);
    }
    EJECUCIONES.push(r);
    if (EJECUCIONES.length > 300) {
      HORARIOS.borrar(EJECUCIONES.slice(0, -300).map(e => e.id));
      EJECUCIONES = EJECUCIONES.slice(-300);
    }
    sesion.guardar(CLAVES.ejecuciones, EJECUCIONES);
    return r;
  }

  // Horario completo de cada ejecución (≈ 0,5 MB) para abrir cualquiera en el visualizador. Va en
  // IndexedDB porque sessionStorage no alcanza para varios; si IndexedDB no está disponible (p. ej.
  // navegación privada en algunos navegadores) se guardan los últimos en memoria, hasta recargar.
  const HORARIOS = (() => {
    const claves = new Set();   // ids con horario guardado
    const memoria = new Map();
    let base = null;
    const abrir = () => base || (base = new Promise((ok, mal) => {
      try {
        const p = indexedDB.open('mmdd-dev-horarios', 1);
        p.onupgradeneeded = () => p.result.createObjectStore('horarios');
        p.onsuccess = () => {
          // Si otra pestaña borra o actualiza la base, se suelta para no bloquearla (se reabre al usarla)
          p.result.onversionchange = () => { p.result.close(); base = null; };
          ok(p.result);
        };
        p.onerror = () => mal(p.error);
        p.onblocked = () => mal(new Error('IndexedDB bloqueado'));
      } catch (e) {
        mal(e);
      }
    }));
    const pedir = (modo, accion) => abrir().then(db => new Promise((ok, mal) => {
      const t = db.transaction('horarios', modo);
      const peticion = accion(t.objectStore('horarios'));
      t.oncomplete = () => ok(peticion ? peticion.result : undefined);
      t.onerror = () => mal(t.error);
      t.onabort = () => mal(t.error);
    }));
    const H = {
      listo: false,   // ya se sabe qué ejecuciones tienen horario guardado
      tiene: id => claves.has(id),
      async guardar(id, datos) {
        claves.add(id);
        try {
          await pedir('readwrite', s => s.put(datos, id));
        } catch (e) {
          memoria.set(id, datos);
          if (memoria.size > 12) { const viejo = memoria.keys().next().value; memoria.delete(viejo); claves.delete(viejo); }
        }
      },
      async leer(id) {
        if (memoria.has(id)) return memoria.get(id);
        try { return (await pedir('readonly', s => s.get(id))) || null; } catch (e) { return null; }
      },
      async borrar(ids) {
        ids.forEach(id => { claves.delete(id); memoria.delete(id); });
        try { await pedir('readwrite', s => { ids.forEach(id => s.delete(id)); return null; }); } catch (e) { /* sin IndexedDB */ }
      },
      // Al cargar: qué ejecuciones de esta pestaña tienen horario, y se borran los horarios de más de un
      // día que no son de esta pestaña (los de otra pestaña abierta se dejan)
      async cargar() {
        try {
          const vigentes = new Set(EJECUCIONES.map(e => e.id));
          const todas = await pedir('readonly', s => s.getAllKeys());
          const viejas = todas.filter(k => !vigentes.has(k) && Date.now() - Number(String(k).split('-')[0]) > 864e5);
          todas.filter(k => vigentes.has(k)).forEach(k => claves.add(k));
          if (viejas.length) await pedir('readwrite', s => { viejas.forEach(k => s.delete(k)); return null; });
        } catch (e) { /* sin IndexedDB: solo los horarios de esta visita, en memoria */ }
        H.listo = true;
      },
    };
    return H;
  })();

  // ¿Se puede volver a calcular el horario de una ejecución? Con la base siempre; con una instancia
  // editada, solo si sigue igual a la que se resolvió
  const reproducible = r => !r.editada || (r.huella != null && hayCambios() && r.huella === huella(JSON.stringify(INST)));

  function avisar(texto, tipo = 'ok') {
    UI.mensaje = texto ? { texto, tipo } : null;
    const el = $('#dev-mensaje');
    if (el) pintarMensaje(el);
  }
  function pintarMensaje(el) {
    el.className = `dev-mensaje${UI.mensaje ? ` ${UI.mensaje.tipo}` : ''}`;
    el.innerHTML = UI.mensaje ? `${UI.mensaje.tipo === 'error' ? ICONOS.alerta : ICONOS.ok}<span>${esc(UI.mensaje.texto)}</span>` : '';
  }

  function htmlServidor() {
    const s = SRV.estado;
    if (s === 'conectado') {
      const i = SRV.info;
      const nombre = i.entorno === 'vercel' ? 'Solver en Vercel conectado' : 'Servidor local conectado';
      const g = i.gurobi || {};
      const gurobi = g.licencia === 'completa' ? `Gurobi ${esc(g.version)}` : g.version ? `Gurobi ${esc(g.version)} sin licencia completa` : 'sin Gurobi';
      return `<span class="dev-pildora bien"><span class="dev-punto"></span>${nombre}</span>
        <span class="dev-pildora-nota">Python ${esc(i.python)} · ${gurobi} · ${i.ortools ? `OR-Tools ${esc(i.ortools)}` : 'sin OR-Tools'}${i.entorno === 'vercel' ? ` · máx. ${i.tiempo_max_tope} s por ejecución` : ''}</span>`;
    }
    if (s === 'sin-servidor') {
      return `<span class="dev-pildora mal"><span class="dev-punto"></span>Sin servidor local</span>
        <button type="button" class="enlace" data-dev="reconectar">Reintentar</button>`;
    }
    return '<span class="dev-pildora"><span class="dev-punto"></span>Buscando el servidor local…</span>';
  }
  function pintarServidor() {
    const el = $('#dev-servidor');
    if (el) el.innerHTML = htmlServidor();
  }

  function htmlInstancia() {
    const { cambios, validacion } = calc();
    const n = cambios.length;
    const errores = validacion.errores.length;
    const factible = { factible: ['bien', 'factible'], infactible: ['mal', 'no factible'], verificando: ['', 'comprobando…'], pendiente: ['', 'comprobando…'] }[FACT.estado];
    const pildora = n
      ? `<span class="dev-pildora acento"><span class="dev-punto"></span>Instancia editada · ${n} cambio${n > 1 ? 's' : ''} respecto de la base</span>`
      : `<span class="dev-pildora"><span class="dev-punto"></span>${esc(capitalizar(NOMBRE_BASE))} (sin cambios)</span>`;
    const lista = n ? `
      <details class="dev-cambios"><summary>Ver cambios</summary>
        <ul>${cambios.slice(0, 60).map(c => `<li><button type="button" class="enlace" data-dev="seccion" data-valor="${c.seccion}"${c.curso ? ` data-curso-dev="${esc(c.curso)}"` : ''}>${esc(c.texto)}</button></li>`).join('')}</ul>
      </details>` : '';
    return `${pildora}${n && factible ? `<span class="dev-pildora ${factible[0]}">${factible[1]}</span>` : ''}${errores ? `<span class="dev-pildora mal">${ICONOS.alerta}${errores} error${errores > 1 ? 'es' : ''}</span>` : ''}${lista}
      <span class="dev-acciones-mini">
        ${HISTORIAL.length ? `<button type="button" class="enlace" data-dev="deshacer">Deshacer</button>` : ''}
        <button type="button" class="enlace" data-dev="exportar">Exportar</button>
        <button type="button" class="enlace" data-dev="importar">Importar</button>
        ${n ? '<button type="button" class="enlace" data-dev="restablecer">Volver a la base</button>' : ''}
      </span>
      <input type="file" id="dev-archivo" accept="application/json,.json" hidden>`;
  }

  const SECCIONES = [
    ['docentes', 'Docentes', () => INST.docentes.length],
    ['asignacion', 'Asignación', () => null],
    ['electivos', 'Electivos', () => NIVELES.reduce((s, n) => s + INST.franjas[n].reduce((t, f) => t + f.grupos.length, 0), 0)],
    ['resolver', 'Resolver', () => null],
    ['comparar', 'Comparar', () => (LOTE ? EJECUCIONES.filter(e => e.lote === LOTE).length : null)],
  ];

  function renderEdicion(panel, animarEntrada) {
    if (!APP.SECCIONES_EDICION.includes(estado.edicion)) estado.edicion = 'docentes';
    if (SRV.estado === 'inicial') conectar();
    panel.innerHTML = `
      <header class="edicion-cabecera">
        <div class="edicion-titulo">
          <span class="eyebrow"><span class="dev-sello">DEV</span>Modo desarrollador · la instancia base es la del horario 2027</span>
          <h1>Edición y solver</h1>
          <p>Cambia la dotación docente, quién dicta cada asignatura y los electivos de 3° y 4° medio; después resuelve con el método que prefieras y compara sus tiempos y su función objetivo. La instancia base (con que se generó el horario 2027) nunca se modifica: los cambios quedan aparte y puedes volver a ella o resolverla cuando quieras.</p>
        </div>
        <div class="edicion-estado">
          <div class="dev-linea" id="dev-servidor">${htmlServidor()}</div>
          <div class="dev-linea" id="dev-instancia">${htmlInstancia()}</div>
        </div>
      </header>
      <nav class="segmentado edicion-secciones" aria-label="Secciones de la edición">
        ${SECCIONES.map(([id, nombre, cuenta]) => {
          const n = cuenta();
          return `<button type="button" data-dev="seccion" data-valor="${id}" aria-pressed="${estado.edicion === id}">${nombre}${n != null ? ` <b>${n}</b>` : ''}</button>`;
        }).join('')}
      </nav>
      <div class="dev-factibilidad" id="dev-factibilidad" aria-live="polite" hidden></div>
      <div class="dev-mensaje" id="dev-mensaje" role="status" aria-live="polite"></div>
      <div class="edicion-cuerpo" id="edicion-cuerpo">${cuerpo()}</div>`;
    pintarMensaje($('#dev-mensaje'));
    pintarFactibilidad();
    despuesDibujar();
    if (animarEntrada) APP.animar.aparecer($$('#edicion-cuerpo > *', panel), { stagger: 0.06 });
  }

  function cuerpo() {
    switch (estado.edicion) {
      case 'asignacion': return htmlAsignacion();
      case 'electivos': return htmlElectivos();
      case 'resolver': return htmlResolver();
      case 'comparar': return htmlComparar();
      default: return htmlDocentes();
    }
  }

  // Redibuja la sección abierta conservando el foco y la posición de la página
  function refrescar() {
    if (estado.vista !== 'edicion') return;
    const panel = $('#panel-edicion');
    if (!$('#edicion-cuerpo', panel)) { renderEdicion(panel, false); return; }
    const activo = document.activeElement;
    const foco = activo && panel.contains(activo) ? activo.dataset.foco : null;
    const abiertos = $$('details[data-recordar][open]', panel).map(d => d.dataset.recordar);
    const y = window.scrollY;
    $('#dev-instancia', panel).innerHTML = htmlInstancia();
    $$('.edicion-secciones button', panel).forEach((b, i) => {
      const n = SECCIONES[i][2]();
      b.innerHTML = `${SECCIONES[i][1]}${n != null ? ` <b>${n}</b>` : ''}`;
    });
    $('#edicion-cuerpo', panel).innerHTML = cuerpo();
    abiertos.forEach(k => { const d = $(`details[data-recordar="${k}"]`, panel); if (d) d.open = true; });
    pintarFactibilidad();
    despuesDibujar();
    window.scrollTo({ top: y });
    if (foco) {
      const el = $(`[data-foco="${CSS.escape(foco)}"]`, panel);
      if (el) el.focus({ preventScroll: true });
    }
  }

  // ------------------------------------------- selector emergente (picker) ---
  // Reemplaza a los <select> nativos: un botón con el valor actual que abre un panel con las
  // opciones agrupadas en fichas (como el menú "Horario de" de Cursos), con búsqueda y teclado.
  // tipo: 'docente' | 'depto' | 'sala' | 'curso'. Al elegir se llama a cambiarCampo(campo, botón, valor).
  // datos: atributos data-* extra; 'excluir' y 'notas' son listas [valor, motivo] en JSON.
  function picker({ tipo, campo, valor, texto, sub = '', etiqueta, foco, datos = {}, deshabilitado = false, clase = '' }) {
    const attrs = Object.entries(datos).map(([k, v]) => ` data-${k}="${esc(v)}"`).join('');
    const visible = texto ?? valor;
    return `<button type="button" class="dev-picker${clase ? ` ${clase}` : ''}" data-dev-picker="${tipo}" data-dev-campo="${campo}"
        data-actual="${esc(valor)}"${attrs} data-foco="${esc(foco)}" aria-haspopup="dialog" aria-expanded="false"
        aria-label="${esc(etiqueta)}: ${esc(visible)}"${deshabilitado ? ' disabled' : ''}>
        <span class="dev-picker-texto"><span class="dev-picker-valor">${esc(visible)}</span>${sub ? `<span class="dev-picker-sub">${esc(sub)}</span>` : ''}</span>
        <svg class="icono" viewBox="0 0 24 24" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>
      </button>`;
  }
  const pickerDocente = op => picker({ tipo: 'docente', sub: `${calc().carga.get(op.valor) || 0} h`, ...op });
  const grupoSala = s => (/PADRE|MADRE/.test(s) ? 'Salas pastorales' : /ARTES|MÚSICA/.test(s) ? 'Salas de especialidad'
    : /^SALA DE [34]°/.test(s) ? 'Salas de 3° y 4° medio' : 'Salas de electivos');

  // Opciones del panel según el tipo de selector
  function configuracionPicker(b) {
    const excluir = new Map(JSON.parse(b.dataset.excluir || '[]'));
    const notas = new Map(JSON.parse(b.dataset.notas || '[]'));
    switch (b.dataset.devPicker) {
      case 'docente': {
        const { carga } = calc();
        return {
          titulo: 'Elige un docente', buscar: 'Buscar por nombre o departamento',
          grupos: DEPARTAMENTOS.map(depto => ({
            titulo: APP.nombreDepartamento(depto),
            opciones: INST.docentes.filter(d => d.departamento === depto)
              .map(d => ({ valor: d.nombre, texto: d.nombre, sub: `${carga.get(d.nombre) || 0} h`, motivo: excluir.get(d.nombre) })),
          })).filter(g => g.opciones.length),
        };
      }
      case 'depto':
        return { titulo: 'Elige un departamento', grupos: [{ opciones: DEPARTAMENTOS.map(d => ({ valor: d, texto: APP.nombreDepartamento(d) })) }] };
      case 'sala': {
        const grupos = new Map();
        SALAS.forEach(s => {
          const g = grupoSala(s);
          if (!grupos.has(g)) grupos.set(g, []);
          grupos.get(g).push({ valor: s, texto: nombreEspacio(s), sub: notas.get(s) });
        });
        return { titulo: 'Elige una sala', grupos: [...grupos].map(([titulo, opciones]) => ({ titulo, opciones })) };
      }
      default:
        return { titulo: 'Elige un curso', cursos: true };
    }
  }

  const POP = Object.assign(document.createElement('div'), { className: 'dev-pop', hidden: true });
  POP.setAttribute('role', 'dialog');
  document.body.appendChild(POP);
  let disparador = null;

  function htmlOpcion(o, actual, grupo = '') {
    const bloqueada = o.motivo && o.valor !== actual;
    return `<button type="button" class="dev-pop-opcion" data-opcion="${esc(o.valor)}" aria-pressed="${o.valor === actual}"
        data-buscar="${esc(APP.normalizar(`${o.texto} ${grupo}`))}"${bloqueada ? ` disabled title="${esc(o.motivo)}"` : ''}>
        <span class="dev-pop-opcion-texto">${esc(o.texto)}</span>${o.sub ? `<small>${esc(o.sub)}</small>` : ''}${bloqueada ? `<small class="dev-pop-motivo">${esc(o.motivo)}</small>` : ''}
      </button>`;
  }

  function htmlCursosPop(actual) {
    return DATOS.ciclos.map(ciclo => {
      const cursos = CURSOS.filter(c => c.ciclo === ciclo.id);
      return `<div class="dev-pop-grupo"><span class="eyebrow">${esc(ciclo.nombre)}</span>${[...new Set(cursos.map(c => c.nivel))].map(nivel => `
        <div class="dev-pop-fila"><span class="dev-pop-nivel">${esc(nombreNivel(nivel))}</span>
          ${cursos.filter(c => c.nivel === nivel).map(c => `<button type="button" class="dev-pop-opcion ficha" data-opcion="${esc(c.id)}"
            aria-pressed="${c.id === actual}" aria-label="${esc(c.nombre)}" data-buscar="${esc(APP.normalizar(c.nombre))}">${esc(c.seccion)}</button>`).join('')}
        </div>`).join('')}</div>`;
    }).join('');
  }

  function abrirPicker(b) {
    cerrarPicker();
    disparador = b;
    const conf = configuracionPicker(b);
    const actual = b.dataset.actual;
    POP.dataset.tipo = b.dataset.devPicker;
    POP.setAttribute('aria-label', conf.titulo);
    POP.innerHTML = `
      <div class="dev-pop-cabecera">
        <span class="dev-pop-titulo">${esc(conf.titulo)}</span>
        <button type="button" class="boton-icono" data-pop-cerrar aria-label="Cerrar">${ICONOS.mal}</button>
      </div>
      ${conf.buscar ? `<label class="dev-pop-buscar"><svg class="icono" viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6.5"/><path d="m16 16 4.5 4.5"/></svg>
        <input type="search" placeholder="${esc(conf.buscar)}" autocomplete="off" spellcheck="false" aria-label="${esc(conf.buscar)}"></label>` : ''}
      <div class="dev-pop-cuerpo">
        ${conf.cursos ? htmlCursosPop(actual) : conf.grupos.map(g => `
          <div class="dev-pop-grupo">${g.titulo ? `<span class="eyebrow">${esc(g.titulo)}</span>` : ''}
            <div class="dev-pop-opciones">${g.opciones.map(o => htmlOpcion(o, actual, g.titulo)).join('')}</div>
          </div>`).join('')}
        <p class="dev-pop-vacio" hidden>Sin coincidencias.</p>
      </div>`;
    POP.hidden = false;
    b.setAttribute('aria-expanded', 'true');
    posicionarPicker();
    const elegida = $('.dev-pop-opcion[aria-pressed="true"]', POP);
    if (elegida) elegida.scrollIntoView({ block: 'nearest' });
    ($('input', POP) || elegida || $('.dev-pop-opcion:not(:disabled)', POP)).focus({ preventScroll: true });
    APP.animar.aparecer([POP], { y: -4, duracion: 0.16 });
  }

  function cerrarPicker(devolverFoco = false) {
    if (POP.hidden) return;
    POP.hidden = true;
    POP.innerHTML = '';
    if (disparador) {
      disparador.setAttribute('aria-expanded', 'false');
      if (devolverFoco && document.contains(disparador)) disparador.focus({ preventScroll: true });
    }
    disparador = null;
  }

  function posicionarPicker() {
    if (POP.hidden || !disparador) return;
    if (!document.contains(disparador)) { cerrarPicker(); return; }
    const r = disparador.getBoundingClientRect();
    const movil = window.innerWidth < 720;
    POP.classList.toggle('hoja', movil);
    if (movil) { POP.style.left = POP.style.top = POP.style.maxHeight = ''; return; }
    if (r.bottom < 0 || r.top > window.innerHeight) { cerrarPicker(); return; }
    POP.style.maxHeight = '';
    const abajo = window.innerHeight - r.bottom - 12;
    const arriba = r.top - 12;
    const alto = POP.offsetHeight;
    const haciaAbajo = alto <= abajo || abajo >= arriba;
    const maximo = Math.max(180, haciaAbajo ? abajo : arriba);
    POP.style.maxHeight = `${maximo}px`;
    POP.style.left = `${Math.max(8, Math.min(r.left, window.innerWidth - POP.offsetWidth - 8))}px`;
    POP.style.top = haciaAbajo ? `${r.bottom + 6}px` : `${Math.max(8, r.top - 6 - Math.min(alto, maximo))}px`;
  }

  function elegirOpcion(valor) {
    const b = disparador;
    cerrarPicker();
    if (!b) return;
    b.focus({ preventScroll: true });   // refrescar() devuelve el foco a este mismo selector
    if (valor !== b.dataset.actual) cambiarCampo(b.dataset.devCampo, b, valor);
  }

  function filtrarPicker(texto) {
    const terminos = APP.normalizar(texto.trim()).split(/\s+/).filter(Boolean);
    let visibles = 0;
    $$('.dev-pop-opcion', POP).forEach(o => {
      const ok = terminos.every(t => o.dataset.buscar.includes(t));
      o.hidden = !ok;
      if (ok) visibles += 1;
    });
    $$('.dev-pop-fila, .dev-pop-grupo', POP).forEach(g => { g.hidden = !$('.dev-pop-opcion:not([hidden])', g); });
    $('.dev-pop-vacio', POP).hidden = visibles > 0;
  }

  // Opción vecina en la dirección de la flecha, por su posición en pantalla
  function opcionVecina(actual, tecla) {
    const opciones = $$('.dev-pop-opcion:not([hidden]):not(:disabled)', POP);
    if (!actual || !opciones.includes(actual)) return opciones[0];
    const centro = el => { const r = el.getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; };
    const c0 = centro(actual);
    const horizontal = tecla === 'ArrowLeft' || tecla === 'ArrowRight';
    const signo = tecla === 'ArrowRight' || tecla === 'ArrowDown' ? 1 : -1;
    let mejor = null;
    let menor = Infinity;
    opciones.forEach(el => {
      if (el === actual) return;
      const c = centro(el);
      const avance = signo * (horizontal ? c.x - c0.x : c.y - c0.y);
      if (avance <= 1) return;
      const distancia = avance + 2 * Math.abs(horizontal ? c.y - c0.y : c.x - c0.x);
      if (distancia < menor) { menor = distancia; mejor = el; }
    });
    return mejor;
  }

  POP.addEventListener('click', ev => {
    if (ev.target.closest('[data-pop-cerrar]')) { cerrarPicker(true); return; }
    const o = ev.target.closest('[data-opcion]');
    if (o && !o.disabled) elegirOpcion(o.dataset.opcion);
  });
  POP.addEventListener('input', ev => { if (ev.target.matches('input')) filtrarPicker(ev.target.value); });
  POP.addEventListener('keydown', ev => {
    if (ev.key === 'Escape') { ev.preventDefault(); ev.stopPropagation(); cerrarPicker(true); return; }
    const enBusqueda = ev.target.matches('input');
    if (enBusqueda && (ev.key === 'ArrowDown' || ev.key === 'Enter')) {
      ev.preventDefault();
      const primera = $('.dev-pop-opcion:not([hidden]):not(:disabled)', POP);
      if (primera) { if (ev.key === 'Enter') elegirOpcion(primera.dataset.opcion); else primera.focus(); }
      return;
    }
    if (!enBusqueda && ev.key.startsWith('Arrow')) {
      ev.preventDefault();
      const destino = opcionVecina(ev.target.closest('.dev-pop-opcion'), ev.key);
      if (destino) destino.focus();
      else if (ev.key === 'ArrowUp' && $('input', POP)) $('input', POP).focus();
    }
  });
  POP.addEventListener('focusout', ev => {
    if (ev.relatedTarget && !POP.contains(ev.relatedTarget) && ev.relatedTarget !== disparador) cerrarPicker();
  });
  document.addEventListener('pointerdown', ev => {
    if (!POP.hidden && !POP.contains(ev.target) && !(disparador && disparador.contains(ev.target))) cerrarPicker();
  });
  let marcoPicker = 0;
  const reposicionar = () => { cancelAnimationFrame(marcoPicker); marcoPicker = requestAnimationFrame(posicionarPicker); };
  window.addEventListener('scroll', reposicionar, { passive: true });
  window.addEventListener('resize', reposicionar);

  // ===========================================================================
  // 6. DOCENTES
  // ===========================================================================
  function resumenAsignaciones(nombre) {
    const r = referencias(nombre);
    const items = [];
    const porCurso = new Map();
    r.filas.forEach(({ curso, i }) => {
      const f = INST.malla[curso][i];
      if (!porCurso.has(curso)) porCurso.set(curso, []);
      porCurso.get(curso).push(`${infoAsig(f.asignatura).nombre} ${f.horas} h`);
    });
    porCurso.forEach((asigs, curso) => items.push(`<li><button type="button" class="enlace" data-dev="ir-curso" data-curso-dev="${esc(curso)}">${esc(nombreCurso(curso))}</button> ${esc(asigs.join(' · '))}</li>`));
    r.grupos.forEach(({ nivel, k, i }) => {
      const g = INST.franjas[nivel][k].grupos[i];
      items.push(`<li><button type="button" class="enlace" data-dev="seccion" data-valor="electivos">${esc(nombreNivel(nivel))}, franja ${k + 1}</button> ${esc(titulo(g.asignatura))} (${esc(g.seccion)}) 6 h</li>`);
    });
    const texto = [porCurso.size ? `${porCurso.size} curso${porCurso.size > 1 ? 's' : ''}` : '', r.grupos.length ? `${r.grupos.length} electivo${r.grupos.length > 1 ? 's' : ''}` : ''].filter(Boolean).join(' · ');
    return items.length
      ? `<details class="dev-asignaciones" data-recordar="asig-${esc(nombre)}"><summary>${texto}</summary><ul>${items.join('')}</ul></details>`
      : '<span class="dev-tenue">Sin asignaciones</span>';
  }

  function filaQuitar(d) {
    const r = referencias(d.nombre);
    const partes = [];
    if (r.filas.length) partes.push(`${r.filas.length} asignatura${r.filas.length > 1 ? 's' : ''}`);
    if (r.grupos.length) partes.push(`${r.grupos.length} electivo${r.grupos.length > 1 ? 's' : ''}`);
    if (r.jefaturas.length) partes.push(`la jefatura de ${r.jefaturas.map(nombreCurso).join(', ')}`);
    const otros = INST.docentes.filter(x => x.nombre !== d.nombre);
    const sugerido = otros.find(x => x.departamento === d.departamento) || otros[0];
    if (!otros.some(x => x.nombre === UI.reemplazo)) UI.reemplazo = sugerido ? sugerido.nombre : null;
    return `
      <tr class="dev-fila-quitar"><td colspan="6">
        <div class="dev-quitar">
          ${r.total
            ? `<p><b>${esc(d.nombre)}</b> tiene ${partes.join(', ')}. ¿Quién se queda con todo?</p>
               ${pickerDocente({ campo: 'reemplazo', valor: UI.reemplazo, etiqueta: `Reemplazo de ${d.nombre}`, foco: 'reemplazo',
                 datos: { excluir: JSON.stringify([[d.nombre, 'es quien se quita']]) } })}`
            : `<p>¿Quitar a <b>${esc(d.nombre)}</b>? No tiene clases asignadas.</p>`}
          <button type="button" class="boton boton-peligro" data-dev="confirmar-quitar" data-docente-dev="${esc(d.nombre)}">${ICONOS.quitar}Quitar docente</button>
          <button type="button" class="enlace" data-dev="cancelar-quitar">Cancelar</button>
        </div>
      </td></tr>`;
  }

  function htmlDocentes() {
    const { carga, mapa } = calc();
    const originales = new Map(BASE.docentes.map(d => [d.nombre, d]));
    const jefaturas = new Map();
    Object.entries(INST.jefes).forEach(([c, d]) => { if (!jefaturas.has(d)) jefaturas.set(d, []); jefaturas.get(d).push(c); });
    const totalHoras = [...carga.values()].reduce((s, h) => s + h, 0);
    const quitados = BASE.docentes.filter(b => !mapa.has(b.nombre));

    const filas = DEPARTAMENTOS.map(depto => {
      const lista = INST.docentes.filter(d => d.departamento === depto);
      if (!lista.length) return '';
      return `<tr class="grupo-fila"><th colspan="6">${esc(APP.nombreDepartamento(depto))} · ${lista.length}</th></tr>${lista.map(d => {
        const h = carga.get(d.nombre) || 0;
        const base = d.original ? originales.get(d.original) : null;
        const editado = !base || base.nombre !== d.nombre || base.departamento !== d.departamento;
        const exceso = h > BLOQUES_SEMANA;
        const marca = !d.original ? '<span class="etiqueta dev-etiqueta">nuevo</span>'
          : d.nombre !== d.original ? `<span class="etiqueta dev-etiqueta" title="Nombre original">antes ${esc(d.original)}</span>` : '';
        return `
          <tr class="${editado ? 'dev-editado' : ''}">
            <td><div class="dev-celda-nombre">
              <input class="dev-input" type="text" value="${esc(d.nombre)}" maxlength="60" spellcheck="false"
                     data-dev-campo="nombre" data-docente-dev="${esc(d.nombre)}" data-foco="nombre|${esc(d.nombre)}" aria-label="Nombre de ${esc(d.nombre)}">${marca}</div></td>
            <td>${picker({ tipo: 'depto', campo: 'depto', valor: d.departamento, texto: APP.nombreDepartamento(d.departamento),
              etiqueta: `Departamento de ${d.nombre}`, foco: `depto|${d.nombre}`, datos: { 'docente-dev': d.nombre } })}</td>
            <td>${(jefaturas.get(d.nombre) || []).map(c => `<button type="button" class="enlace" data-dev="ir-curso" data-curso-dev="${esc(c)}">${esc(nombreCurso(c))}</button>`).join(', ') || '<span class="dev-tenue">—</span>'}</td>
            <td class="num"><span class="dev-carga${exceso ? ' mal' : ''}" title="${h} de ${BLOQUES_SEMANA} bloques de la semana">
              <span class="dev-carga-pista"><span style="width:${Math.min(100, (h / BLOQUES_SEMANA) * 100)}%"></span></span>${h}</span></td>
            <td>${resumenAsignaciones(d.nombre)}</td>
            <td class="dev-col-accion"><button type="button" class="boton-icono" data-dev="quitar" data-docente-dev="${esc(d.nombre)}" aria-label="Quitar a ${esc(d.nombre)}" title="Quitar docente">${ICONOS.quitar}</button></td>
          </tr>${UI.quitando === d.nombre ? filaQuitar(d) : ''}`;
      }).join('')}`;
    }).join('');

    return `
      <section class="seccion">
        <div class="seccion-titulo"><h2>Dotación docente</h2>
          <p>${INST.docentes.length} docentes · ${fmt(totalHoras)} horas en grilla · tope ${BLOQUES_SEMANA} bloques por docente</p></div>
        <form class="dev-agregar" data-dev-form="agregar-docente" autocomplete="off">
          <label class="dev-campo"><span>Nombre</span><input class="dev-input" name="nombre" type="text" maxlength="60" placeholder="p. ej. Lenguaje 6" data-foco="nuevo-nombre" required></label>
          <div class="dev-campo"><span>Departamento</span>${picker({ tipo: 'depto', campo: 'nuevo-depto', valor: UI.nuevoDepto || DEPARTAMENTOS[0],
            texto: APP.nombreDepartamento(UI.nuevoDepto || DEPARTAMENTOS[0]), etiqueta: 'Departamento del nuevo docente', foco: 'nuevo-depto' })}</div>
          <button type="submit" class="boton boton-primario">${ICONOS.mas}Agregar docente</button>
        </form>
        <div class="tabla-marco"><table class="tabla dev-tabla dev-tabla-docentes">
          <thead><tr><th>Docente</th><th>Departamento</th><th>Jefatura</th><th class="num">Horas</th><th>Asignaciones</th><th><span class="visualmente-oculto">Acciones</span></th></tr></thead>
          <tbody>${filas}</tbody>
        </table></div>
        ${quitados.length ? `<p class="nota">Quitados respecto de la ${esc(NOMBRE_BASE)}: ${quitados.map(q => esc(q.nombre)).join(', ')}. Usa <b>Deshacer</b> o <b>Volver a la base</b> si quieres recuperarlos.</p>` : ''}
        <p class="nota">Renombrar o quitar un docente actualiza todas sus clases, jefaturas y electivos. Un docente nuevo aparece en la planilla sin clases: asígnalas en <button type="button" class="enlace" data-dev="seccion" data-valor="asignacion">Asignación</button> o <button type="button" class="enlace" data-dev="seccion" data-valor="electivos">Electivos</button>.</p>
      </section>`;
  }

  // ===========================================================================
  // 7. ASIGNACIÓN POR CURSO
  // ===========================================================================
  function htmlAsignacion() {
    if (!cursoPorId.has(UI.curso)) UI.curso = CURSOS[0].id;
    const curso = cursoPorId.get(UI.curso);
    const { mapa } = calc();
    const filas = INST.malla[curso.id];
    const editadosCurso = new Set(calc().cambios.filter(c => c.curso).map(c => c.curso));
    const horas = filas.reduce((s, f) => s + f.horas, 0);
    const franjas = (INST.franjas[curso.nivel] || []);

    const cuerpoTabla = filas.map((f, i) => {
      const info = infoAsig(f.asignatura);
      const sigueJefe = ORIENTACION.includes(f.asignatura) && !curso.parvulo;
      const editada = filaEditada(curso.id, i, mapa);
      const selects = f.docentes.map((d, s) => pickerDocente({
        campo: 'asignar', valor: d, etiqueta: `${info.nombre}, docente ${s + 1}`, foco: `asignar|${i}|${s}`, deshabilitado: sigueJefe,
        datos: { 'curso-dev': curso.id, i, s, excluir: JSON.stringify(f.docentes.filter((x, j) => j !== s).map(x => [x, 'ya está en esta co-docencia'])) },
      })).join('');
      const original = BASE.malla[curso.id][i].docentes.join(' y ');
      return `
        <tr class="${editada ? 'dev-editado' : ''}">
          <td><span class="asig"><span class="punto cat-${info.cat}"></span><span>${esc(info.nombre)}${info.nombre !== f.asignatura ? `<small class="dev-tenue"> · ${esc(f.asignatura)}</small>` : ''}</span></span></td>
          <td class="num">${f.horas}</td>
          <td><div class="dev-docentes">${selects}</div>
            ${sigueJefe ? '<small class="dev-tenue">Sigue a la jefatura del curso</small>' : ''}
            ${editada && !sigueJefe ? `<small class="dev-tenue">Original: ${esc(original)}</small>` : ''}
            ${f.docentes.length > 1 ? '<small class="dev-tenue">Co-docencia: dos docentes en el mismo bloque</small>' : ''}</td>
          <td>${esc(nombreEspacio(f.espacio))}</td>
        </tr>`;
    }).join('') + franjas.map((f, k) => `
        <tr class="dev-fila-franja">
          <td><span class="asig"><span class="punto cat-electivo"></span>Franja ${k + 1} · Electivos</span></td>
          <td class="num">6</td>
          <td><span class="dev-tenue">${f.grupos.length} electivos con ${[...new Set(f.grupos.map(g => g.docente))].map(esc).join(', ')}</span>
            <button type="button" class="enlace" data-dev="seccion" data-valor="electivos">Editar en Electivos</button></td>
          <td>Salas de electivos</td>
        </tr>`).join('');

    const jefeEditado = !curso.parvulo && INST.jefes[curso.id] !== mapa.get(BASE.jefes[curso.id]);
    return `
      <section class="seccion">
        <div class="dev-barra-curso">
          <div class="dev-campo"><span>Curso</span>
            ${picker({ tipo: 'curso', campo: 'curso', valor: curso.id, texto: curso.nombre, etiqueta: 'Curso', foco: 'curso', clase: 'grande' })}</div>
          <div class="cabecera-acciones">
            <button type="button" class="boton-icono" data-dev="curso-paso" data-valor="-1" aria-label="Curso anterior">${ICONOS.izq}</button>
            <button type="button" class="boton-icono" data-dev="curso-paso" data-valor="1" aria-label="Curso siguiente">${ICONOS.der}</button>
          </div>
          ${curso.parvulo ? '' : `
          <div class="dev-campo${jefeEditado ? ' dev-editado' : ''}"><span>Profesor/a jefe</span>
            ${pickerDocente({ campo: 'jefe', valor: INST.jefes[curso.id], etiqueta: 'Profesor/a jefe', foco: 'jefe', datos: { 'curso-dev': curso.id } })}</div>`}
        </div>
        <p class="cabecera-meta"><span><b>${horas + franjas.length * 6}</b> horas semanales</span>
          <span><b>${curso.jornada.reduce((s, j) => s + j, 0)}</b> bloques de jornada</span>
          ${editadosCurso.has(curso.id) ? '<span class="dev-pildora acento"><span class="dev-punto"></span>Curso con cambios</span>' : ''}</p>
        <div class="tabla-marco"><table class="tabla dev-tabla">
          <thead><tr><th>Asignatura</th><th class="num">Horas</th><th>Docente(s)</th><th>Espacio</th></tr></thead>
          <tbody>${cuerpoTabla}</tbody>
        </table></div>
        <p class="nota">Las horas y la jornada de cada curso no se editan: así cada curso sigue cubriendo su malla completa. Al cambiar la jefatura, la Orientación del curso pasa al nuevo profesor/a jefe (lo exige la auditoría). Cada docente muestra sus horas en grilla; después de cada cambio se comprueba si todavía existe un horario factible.</p>
      </section>`;
  }

  // ===========================================================================
  // 8. ELECTIVOS
  // ===========================================================================
  function htmlElectivos() {
    const { mapa } = calc();
    const nombresElectivos = [...new Set([...Object.values(BASE.franjas), ...Object.values(INST.franjas)]
      .flatMap(l => l.flatMap(f => f.grupos.map(g => titulo(g.asignatura)))))].sort();
    const { errores, avisos } = calc().validacion;

    const niveles = NIVELES.map(nivel => {
      const oferta = [...new Set(INST.franjas[nivel].flatMap(f => f.grupos.map(g => g.asignatura)))];
      const franjas = INST.franjas[nivel].map((f, k) => {
        const lugar = `${nombreNivel(nivel)}, franja ${k + 1}`;
        const problemas = [...errores.filter(e => e.startsWith(lugar)).map(e => ['error', e]), ...avisos.filter(e => e.startsWith(lugar)).map(e => ['aviso', e])];
        // Bloques de la franja con bloqueo de pastoral, para avisar en el selector de salas
        const conPastoral = SALAS.filter(s => f.periodos.some(p => (pastoral.get(s) || new Set()).has(`${p.dia}|${p.bloque}`)
          || (pastoral.get(s) || new Set()).has(`${p.dia}|${p.bloque + 1}`)));
        const filas = f.grupos.map((g, i) => {
          const id = `${nivel}|${k}|${i}`;
          const editado = grupoEditado(nivel, k, g, mapa);
          const otros = f.grupos.filter((x, j) => j !== i);
          const ocupados = otros.map(x => [x.docente, `dicta ${titulo(x.asignatura)} en esta franja`]);
          const notasSala = [...otros.map(x => [x.sala, `la usa ${titulo(x.asignatura)}`]), ...conPastoral.map(s => [s, 'bloqueo de pastoral en esta franja'])];
          return `
            <tr class="${editado ? 'dev-editado' : ''}">
              <td><input class="dev-input dev-input-largo" type="text" list="dev-lista-electivos" value="${esc(titulo(g.asignatura))}" maxlength="80"
                         data-dev-campo="grupo" data-prop="asignatura" data-id="${esc(id)}" data-foco="g|${esc(id)}|a" aria-label="Nombre del electivo"></td>
              <td><input class="dev-input dev-input-corto" type="text" value="${esc(g.seccion)}" maxlength="12"
                         data-dev-campo="grupo" data-prop="seccion" data-id="${esc(id)}" data-foco="g|${esc(id)}|s" aria-label="Sección de ${esc(titulo(g.asignatura))}"></td>
              <td>${pickerDocente({ campo: 'grupo', valor: g.docente, etiqueta: `Docente de ${titulo(g.asignatura)}`, foco: `g|${id}|d`,
                datos: { prop: 'docente', id, excluir: JSON.stringify(ocupados) } })}</td>
              <td>${picker({ tipo: 'sala', campo: 'grupo', valor: g.sala, texto: nombreEspacio(g.sala), etiqueta: `Sala de ${titulo(g.asignatura)}`,
                foco: `g|${id}|r`, datos: { prop: 'sala', id, notas: JSON.stringify(notasSala) } })}</td>
              <td class="dev-col-accion"><button type="button" class="boton-icono" data-dev="quitar-grupo" data-id="${esc(id)}" aria-label="Quitar ${esc(titulo(g.asignatura))}"${f.grupos.length <= 1 ? ' disabled' : ''}>${ICONOS.quitar}</button></td>
            </tr>`;
        }).join('');
        return `
          <article class="dev-franja">
            <header class="dev-franja-cabecera">
              <h3><span class="punto cat-electivo"></span>Franja ${k + 1}</h3>
              <span class="dev-tenue">${INST.franjas_fijas === false ? 'Bloques: los elige el solver · en la base: ' : ''}${f.periodos.map(p => `${DIA_CORTO[p.dia]} ${BLOQUE[p.bloque].inicio}–${BLOQUE[p.bloque + 1].fin}`).join(' · ')}</span>
            </header>
            <div class="tabla-marco"><table class="tabla dev-tabla">
              <thead><tr><th>Electivo</th><th>Sección</th><th>Docente</th><th>Sala</th><th><span class="visualmente-oculto">Acciones</span></th></tr></thead>
              <tbody>${filas}</tbody>
            </table></div>
            ${problemas.length ? `<ul class="dev-problemas">${problemas.map(([t, p]) => `<li class="${t}">${t === 'error' ? ICONOS.mal : ICONOS.alerta}${esc(p.slice(lugar.length + 2))}</li>`).join('')}</ul>` : ''}
            <button type="button" class="boton" data-dev="agregar-grupo" data-id="${esc(`${nivel}|${k}`)}">${ICONOS.mas}Agregar electivo a la franja ${k + 1}</button>
          </article>`;
      }).join('');
      return `
        <section class="seccion">
          <div class="seccion-titulo"><h2>${esc(nombreNivel(nivel))}</h2>
            <p>${oferta.length} electivos ofrecidos · 3 franjas de 6 horas · A y B se mezclan en cada franja</p></div>
          ${franjas}
        </section>`;
    }).join('');
    const fijas = INST.franjas_fijas !== false;
    return `
      <div class="dev-interruptor-fila">
        <button type="button" class="dev-interruptor" role="switch" aria-checked="${fijas}" data-dev="franjas-fijas" data-foco="franjas-fijas"
                aria-describedby="dev-franjas-fijas-nota"><span class="dev-interruptor-riel" aria-hidden="true"><span></span></span>Franjas de electivos fijas</button>
        <span class="dev-tenue" id="dev-franjas-fijas-nota">${fijas
          ? 'Quedan en los bloques del Excel 2026, como en la instancia base.'
          : 'El solver elige los 3 bloques dobles de cada franja (días distintos, los mismos para A y B).'}</span>
      </div>
      ${niveles}
      <datalist id="dev-lista-electivos">${nombresElectivos.map(n => `<option value="${esc(n)}"></option>`).join('')}</datalist>
      <p class="nota">Un docente no puede dictar dos electivos de la misma franja: el selector no lo deja elegir.</p>`;
  }

  // ===========================================================================
  // 9. RESOLVER
  // ===========================================================================
  function camposParametros() {
    const esModelo = R.metodo === 'modelo';
    const m = metodos().find(x => x.id === R.metodo) || {};
    const propios = (m.parametros || []);
    const valores = R.parametros[R.metodo] || {};
    const num = (prop, etiqueta, valor, extra = '', ayuda = '') => `
      <label class="dev-campo"><span>${etiqueta}</span>
        <input class="dev-input" type="number" value="${esc(valor)}" data-dev-campo="r" data-prop="${prop}" data-foco="r|${prop}" ${extra}>
        ${ayuda ? `<small>${ayuda}</small>` : ''}</label>`;
    return `
      <div class="dev-campos">
        ${esModelo ? `
          <div class="dev-campo dev-campo-ancho"><span>Solver</span>
            <div class="segmentado dev-solvers" role="radiogroup" aria-label="Solver del modelo matemático">${solvers().map(s => `
              <button type="button" role="radio" data-dev="solver" data-valor="${s}" aria-checked="${s === R.solver}" aria-pressed="${s === R.solver}"
                data-foco="solver|${s}" title="${esc(NOTA_SOLVER[s] || '')}">${esc(NOMBRE_SOLVER[s] || s)}</button>`).join('')}
            </div>
            <small>${esc(NOTA_SOLVER[R.solver] || '')}${notaGurobi()}</small></div>
          ${num('tiempo_max', 'Tiempo máximo (s)', R.tiempo_max, `min="0.1" max="${topeTiempo()}" step="any"`)}
          ${num('peso_ventanas', 'Peso de las ventanas w<sub>V</sub>', R.peso_ventanas, 'min="0" step="any"', '0 = solo factibilidad (como las metaheurísticas)')}
          ${num('hilos', 'Hilos', R.hilos, 'min="1" max="64" placeholder="los del solver"', '1 hilo es comparable con las metaheurísticas')}`
        : `
          ${num('semilla', 'Semilla', R.semilla, 'min="0" step="1"')}
          ${num('tiempo_max', 'Tiempo máximo (s)', R.tiempo_max, `min="0.1" max="${topeTiempo()}" step="any"`)}
          ${num('max_pasos', 'Pasos máximos', R.max_pasos, 'min="1" step="1"')}`}
      </div>
      ${propios.length ? `
        <details class="dev-avanzados" data-recordar="avanzados">
          <summary>Parámetros de ${esc(m.nombre)} (${propios.length})</summary>
          <div class="dev-campos">${propios.map(p => `
            <label class="dev-campo"><span>${esc(p.nombre.replace(/_/g, ' '))}</span>
              <input class="dev-input" type="number" step="any" value="${esc(valores[p.nombre] ?? p.defecto)}" data-dev-campo="rp" data-prop="${esc(p.nombre)}" data-foco="rp|${esc(p.nombre)}">
              <small>${esc(p.ayuda || '')} · por defecto ${esc(p.defecto)}</small></label>`).join('')}
          </div>
        </details>` : ''}`;
  }

  // Por qué Gurobi no aparece entre los solvers (licencia del servidor)
  function notaGurobi() {
    const g = SRV.info && SRV.info.gurobi;
    if (!g || g.licencia === 'completa') return '';
    return g.version
      ? ` · Gurobi ${g.version} no está disponible en este servidor: ${g.detalle}.`
      : ' · Gurobi no está instalado en este servidor (pip install gurobipy).';
  }

  // Base 2027 o instancia editada: elegir una no borra la otra
  function selectorInstancia(op, campo) {
    const n = calc().cambios.length;
    if (!n) return `<p class="dev-tenue">Se resuelve la ${esc(NOMBRE_BASE)} (no hay cambios).</p>`;
    const estadoEditada = FACT.estado === 'infactible' ? ' · no factible' : FACT.estado === 'factible' ? ' · factible' : '';
    return `
      <div class="dev-campo dev-campo-ancho"><span>Instancia</span>
        <div class="segmentado dev-instancias" role="radiogroup" aria-label="Instancia que se resuelve">
          <button type="button" role="radio" data-dev="usar-instancia" data-campo="${campo}" data-valor="base" aria-checked="${op.usarBase}" aria-pressed="${op.usarBase}" data-foco="inst|${campo}|base">Base 2027</button>
          <button type="button" role="radio" data-dev="usar-instancia" data-campo="${campo}" data-valor="editada" aria-checked="${!op.usarBase}" aria-pressed="${!op.usarBase}" data-foco="inst|${campo}|editada">Editada · ${n} cambio${n > 1 ? 's' : ''}${estadoEditada}</button>
        </div>
        <small>La base (con que se generó el horario 2027) nunca se modifica; puedes resolver una u otra sin perder tus cambios.</small>
      </div>`;
  }

  function htmlExplicacion() {
    return `
      <details class="dev-explicacion" data-recordar="explicacion">
        <summary>¿Qué hace cada método y en qué se diferencian?</summary>
        <dl>${EXPLICACION.map(([id, nombre, texto]) => `
          <div style="--c:${colorDe(id === 'modelo' ? 'modelo:GUROBI' : id)}"><dt><span class="dev-metodo-punto"></span>${esc(nombre)}</dt><dd>${esc(texto)}</dd></div>`).join('')}
        </dl>
        <p class="nota">En corto: la <b>heurística constructiva</b> arma la solución inicial; <b>ILS</b> la repara con descensos que se detienen en el primer óptimo local y
          perturbaciones para salir de él; <b>ITS</b> usa en cambio una búsqueda tabú, que acepta empeoramientos controlados por la memoria tabú; y el <b>modelo</b> resuelve todo
          de una vez y además puede demostrar que no hay solución. ILS e ITS usan el mismo vecindario (intercambios dentro de cada curso de las sesiones en conflicto) y la misma
          perturbación, así que la diferencia entre sus horarios y tiempos se debe solo a la estrategia de búsqueda. Todos minimizan la misma f(x) = 1000 · violaciones duras.</p>
      </details>`;
  }

  function avisoServidor() {
    if (SRV.estado === 'conectado') return '';
    const archivo = location.protocol === 'file:';
    // Página publicada (Vercel u otro hosting): solo sirve archivos estáticos, así que el solver
    // corre en el computador de quien la usa y servidor.py debe aceptar este origen
    const publicada = !archivo && !['localhost', '127.0.0.1', '[::1]'].includes(location.hostname);
    const comando = publicada
      ? `python "Prototipos/Prototipo 2/servidor.py" --origen ${location.origin}`
      : 'python "Prototipos/Prototipo 2/servidor.py" --abrir';
    const despues = publicada
      ? `Esta página está publicada en <b>${esc(location.host)}</b> y su solver en línea (<code>/api</code>) no respondió: revisa el
         log del despliegue en Vercel (ver "Publicación en Vercel" en el README del prototipo). Mientras tanto, el comando de arriba
         abre el solver en tu computador: con él corriendo, pulsa Reintentar y, si el navegador pregunta si la página puede acceder a los
         dispositivos de tu red local, acepta (Chrome, Edge o Firefox; Safari no lo permite desde una página https).`
      : archivo
        ? `Luego abre la página desde <code>http://localhost:${PUERTO}</code> (o vuelve aquí y pulsa Reintentar).`
        : 'Luego pulsa Reintentar.';
    return `
      <div class="dev-aviso">
        ${ICONOS.alerta}
        <div>
          <b>${SRV.estado === 'conectando' || SRV.estado === 'inicial' ? 'Buscando el servidor local…' : 'El solver necesita el servidor local'}</b>
          <p>Los métodos corren en Python con el mismo motor del proyecto. En una terminal, desde la carpeta del repositorio:</p>
          <pre><code>${esc(comando)}</code></pre>
          <p>${despues} La edición funciona igual sin servidor y se guarda en este navegador.</p>
          <button type="button" class="boton" data-dev="reconectar">Reintentar</button>
        </div>
      </div>`;
  }

  function htmlResolver() {
    const { validacion } = calc();
    // Un método guardado que ya no existe (p. ej. la antigua "Construcción voraz") vuelve al por defecto
    if (!metodos().some(m => m.id === R.metodo)) R.metodo = METODO_DEFECTO;
    const editada = usaEditada(R);
    const bloqueada = editada && validacion.errores.length > 0;
    const listo = SRV.estado === 'conectado' && !bloqueada && !R.ejecutando;
    const tarjetas = metodos().map(m => {
      const deshabilitado = m.id === 'modelo' && !conModelo();
      const clave = m.id === 'modelo' ? `modelo:${R.solver}` : m.id;
      return `
        <label class="dev-metodo${R.metodo === m.id ? ' elegido' : ''}${deshabilitado ? ' deshabilitado' : ''}" style="--c:${colorDe(clave)}">
          <input type="radio" name="dev-metodo" value="${m.id}" data-dev-campo="metodo" data-foco="metodo|${m.id}"${R.metodo === m.id ? ' checked' : ''}${deshabilitado ? ' disabled' : ''}>
          <span class="dev-metodo-tipo"><span class="dev-metodo-punto"></span>${esc(m.tipo)}${m.defecto ? ' · por defecto' : ''}</span>
          <span class="dev-metodo-nombre">${esc(m.nombre)}</span>
          <span class="dev-metodo-desc">${esc(deshabilitado ? 'El servidor no tiene solvers para el modelo (pip install ortools o gurobipy)' : m.descripcion)}</span>
        </label>`;
    }).join('');
    const nombreInstancia = editada ? 'instancia editada' : NOMBRE_BASE;
    return `
      <div class="dev-resolver">
        <section class="seccion">
          <div class="seccion-titulo"><h2>Método</h2><p>Heurística constructiva + metaheurística, o modelo exacto</p></div>
          <div class="dev-metodos" role="radiogroup" aria-label="Método de solución">${tarjetas}</div>
          ${htmlExplicacion()}
        </section>
        <section class="seccion">
          <div class="seccion-titulo"><h2>Parámetros</h2><p>Todos parten de la misma construcción voraz (salvo el modelo)</p></div>
          ${selectorInstancia(R, 'r')}
          <p class="dev-tenue">Franjas de electivos: <b>${editada && INST.franjas_fijas === false ? 'móviles (las ubica el solver)' : 'fijas (bloques del Excel 2026)'}</b>
            · <button type="button" class="enlace" data-dev="seccion" data-valor="electivos">cambiar en Electivos</button></p>
          ${camposParametros()}
          <div class="dev-ejecutar">
            <button type="button" class="boton boton-primario boton-grande" id="dev-resolver-boton" data-dev="resolver"${listo ? '' : ' disabled'}>
              ${R.ejecutando ? `<span class="dev-girando"></span>Resolviendo… <span class="dev-reloj">${fmtMs(performance.now() - R.inicio)}</span>` : `${ICONOS.play}Resolver`}</button>
            <span class="dev-tenue">Con la ${esc(nombreInstancia)}${bloqueada ? ` · <b class="dev-error-texto">corrige ${validacion.errores.length} error${validacion.errores.length > 1 ? 'es' : ''} primero</b>` : ''}</span>
          </div>
          ${editada && FACT.estado === 'infactible' ? `<p class="dev-problemas"><span class="error">${ICONOS.alerta}Con la instancia editada ningún método puede llegar a f(x) = 0 (ver el aviso de arriba). Puedes resolverla igual para ver el mejor horario posible.</span></p>` : ''}
          ${editada && validacion.errores.length ? `<ul class="dev-problemas">${validacion.errores.slice(0, 8).map(e => `<li class="error">${ICONOS.mal}${esc(e)}</li>`).join('')}</ul>` : ''}
          ${editada && validacion.avisos.length ? `<ul class="dev-problemas">${validacion.avisos.slice(0, 6).map(e => `<li class="aviso">${ICONOS.alerta}${esc(e)}</li>`).join('')}</ul>` : ''}
          ${avisoServidor()}
        </section>
      </div>
      ${R.error ? `<div class="dev-aviso mal">${ICONOS.mal}<div><b>No se pudo resolver</b><p>${esc(R.error)}</p></div></div>` : ''}
      ${R.resultado ? htmlResultado(R.resultado, Boolean(R.datos)) : ''}
      ${htmlEjecuciones()}`;
  }

  // Bloques que eligió el solver para las franjas (solo con franjas móviles)
  function htmlFranjasResultado(r) {
    if (!r.franjas) return '';
    return `
      <div class="dev-franjas-resultado">
        <h3>Franjas de electivos que eligió el solver</h3>
        <dl class="datos dev-datos">${Object.entries(r.franjas).map(([nivel, franjas]) => franjas.map((periodos, k) => `
          <dt>${esc(nombreNivel(nivel))} · franja ${k + 1}</dt>
          <dd>${periodos.map(([dia, b]) => `${DIA_CORTO[dia]} ${BLOQUE[b].inicio}–${BLOQUE[b + 1].fin}`).join(' · ')}</dd>`).join('')).join('')}
        </dl>
      </div>`;
  }

  function htmlResultado(r, conDatos) {
    const a = r.auditoria;
    const m = a ? a.metricas : null;
    const sinSolucion = r.costo_final == null;
    const veredicto = sinSolucion ? `Sin solución (${r.motivo_parada})`
      : r.factible ? 'Horario factible' : r.duras_finales ? `${fmt(r.duras_finales)} violaciones duras` : 'Horario con observaciones';
    const t = r.tiempos_ms;
    const desglose = r.desglose ? TIPOS.map(([k, nombre]) => `<span class="dev-chip"><span class="dev-tipo">${k}</span>${nombre} <b>${fmt(r.desglose[k])}</b></span>`).join('') : '';
    const partes = r.metodo === 'modelo'
      ? `modelo ${fmtMs(t.preparacion)} · resolución ${fmtMs(t.busqueda)} · salida ${fmtMs(t.salida)}`
      : `construcción ${fmtMs(t.construccion)} · búsqueda ${fmtMs(t.busqueda)} · salida ${fmtMs(t.salida)}`;
    const criterios = a ? a.criterios.map(c => `
      <li class="criterio"><span class="criterio-nombre">${esc(c.criterio)}</span><span class="criterio-valor">${esc(c.valor)}</span>
        <span class="estado${c.errores ? ' mal' : ''}">${c.errores ? ICONOS.mal : ICONOS.ok}${c.errores ? 'No cumple' : 'Cumple'}</span></li>`).join('') : '';
    const modelo = r.modelo ? `
      <dl class="datos dev-datos">
        <dt>Estado</dt><dd>${esc(r.modelo.estado)}</dd>
        <dt>Tamaño</dt><dd>${fmt(r.modelo.variables)} variables · ${fmt(r.modelo.restricciones)} restricciones</dd>
        <dt>Objetivo</dt><dd>${fmt(r.modelo.objetivo)} · cota ${fmt(r.modelo.cota)} · gap ${r.modelo.gap == null ? '—' : `${fmt(r.modelo.gap * 100, 2)} %`}</dd>
        ${r.modelo.ventanas_modelo != null ? `<dt>Ventanas (modelo)</dt><dd>${fmt(r.modelo.ventanas_modelo)}</dd>` : ''}
      </dl>` : '';
    return `
      <section class="seccion dev-resultado" style="--c:${colorDe(claveDe(r))}">
        <div class="veredicto">
          <div class="veredicto-sello${r.factible ? '' : ' mal'}">${r.factible ? ICONOS.ok : ICONOS.mal}</div>
          <div>
            <span class="eyebrow">Resultado · ${esc(r.nombre)}${r.semilla != null ? ` · semilla ${r.semilla}` : ''} · ${r.editada ? 'instancia editada' : esc(NOMBRE_BASE)}</span>
            <h1>${esc(veredicto)}</h1>
            <p>Se detuvo porque ${esc(r.metodo === 'modelo' ? `el solver informó: ${r.motivo_parada}` : motivo(r.motivo_parada))}${r.pasos ? `, tras ${fmt(r.pasos, 0)} pasos (${fmt(r.pasos_por_s, 0)} por segundo)` : ''}.</p>
          </div>
        </div>
        <div class="kpis">
          <div class="kpi"><span class="kpi-valor">${fmt(r.costo_final)}</span><span class="kpi-etiqueta">f(x) final${r.costo_inicial != null ? ` · partió de ${fmt(r.costo_inicial)} (construcción voraz)` : ''}</span></div>
          <div class="kpi"><span class="kpi-valor">${fmtMs(t.total)}</span><span class="kpi-etiqueta">tiempo total · ${partes}</span></div>
          <div class="kpi"><span class="kpi-valor">${fmtMs(r.t_factible_ms)}</span><span class="kpi-etiqueta">hasta la primera solución factible${r.metodo === 'modelo' ? ' (resolución)' : ' (desde el inicio de la búsqueda)'}</span></div>
          <div class="kpi"><span class="kpi-valor">${m ? fmt(m.total_ventanas_docentes) : '—'}</span><span class="kpi-etiqueta">ventanas docentes · ${m ? `${fmt(m.porcentaje_bloques_dobles)} % en bloques dobles` : ''}</span></div>
        </div>
        ${desglose ? `<div class="dev-chips" aria-label="Violaciones duras finales por tipo">${desglose}</div>` : ''}
        <div class="columnas">
          <section class="seccion">
            <div class="seccion-titulo"><h2>Convergencia</h2><p>Mejor f(x) según el tiempo de búsqueda (escala logarítmica)</p></div>
            <div class="dev-grafico" data-grafico="resultado"></div>
            ${modelo}
            ${htmlFranjasResultado(r)}
          </section>
          <section class="seccion">
            <div class="seccion-titulo"><h2>Auditoría</h2><p>Validador independiente del proyecto</p></div>
            ${a ? `<ul class="criterios dev-criterios">${criterios}</ul>` : '<p class="nota">Sin horario que auditar.</p>'}
            ${a && a.errores.length ? `<details class="dev-conflictos"><summary>Ver ${fmt(a.totalErrores)} errores</summary><ul>${a.errores.map(e => `<li>${esc(e)}</li>`).join('')}</ul></details>` : ''}
          </section>
        </div>
        <div class="dev-acciones">
          <button type="button" class="boton boton-primario" data-dev="ver-resultado"${conDatos ? '' : ' disabled'}>${ICONOS.ojo}Ver en el visualizador</button>
          <button type="button" class="boton" data-dev="descargar-resultado"${conDatos ? '' : ' disabled'}>${ICONOS.bajar}Descargar datos (.js)</button>
          ${conDatos ? '' : !HORARIOS.listo ? '<span class="dev-tenue">Cargando el horario guardado…</span>' : `<span class="dev-tenue">Vuelve a resolver para ver o descargar este horario.</span>
          <button type="button" class="boton" data-dev="resolver-de-nuevo"${R.ejecutando || SRV.estado !== 'conectado' ? ' disabled' : ''}
                  title="${esc(`Resuelve otra vez con ${r.nombre}${r.semilla != null ? `, semilla ${r.semilla}` : ''} y la ${r.editada ? 'instancia editada' : NOMBRE_BASE}`)}">${ICONOS.play}Resolver</button>`}
        </div>
      </section>`;
  }

  function botonVerEjecucion(r) {
    const guardado = HORARIOS.tiene(r.id) || !HORARIOS.listo || (R.resultado && R.resultado.id === r.id && R.datos);
    const quien = `${nombreClave(claveDe(r))}${r.semilla != null ? `, semilla ${r.semilla}` : ''}`;
    let titulo = `Abre el horario de ${quien} en el visualizador`;
    let deshabilitado = false;
    if (!guardado) {
      deshabilitado = !reproducible(r) || SRV.estado !== 'conectado';
      titulo = !reproducible(r) ? 'Este horario no quedó guardado y la instancia editada cambió desde que se resolvió'
        : SRV.estado !== 'conectado' ? 'Este horario no quedó guardado: para volver a calcularlo se necesita el servidor'
          : `Este horario no quedó guardado: se vuelve a resolver con ${quien} y se abre`;
    }
    return `<button type="button" class="boton dev-boton-tabla" data-dev="ver-ejecucion" data-id="${esc(r.id)}"
              title="${esc(titulo)}"${deshabilitado ? ' disabled' : ''}>${ICONOS.ojo}<span>Ver en el visualizador</span></button>`;
  }

  function htmlEjecuciones() {
    if (!EJECUCIONES.length) return '';
    const filas = [...EJECUCIONES].reverse().slice(0, 40).map(r => `
      <tr>
        <td><span class="asig"><span class="dev-metodo-punto" style="--c:${colorDe(claveDe(r))}"></span>${esc(nombreClave(claveDe(r)))}</span></td>
        <td class="num">${r.semilla ?? '—'}</td>
        <td>${r.factible ? '<span class="estado">Sí</span>' : '<span class="estado mal">No</span>'}</td>
        <td class="num">${fmt(r.costo_inicial)}</td>
        <td class="num">${fmt(r.costo_final)}</td>
        <td class="num">${fmtMs(r.tiempos_ms.total)}</td>
        <td class="num">${r.auditoria ? fmt(r.auditoria.metricas.total_ventanas_docentes) : '—'}</td>
        <td>${r.lote ? 'Comparar' : 'Resolver'} · ${r.editada ? 'editada' : 'base'}</td>
        <td class="dev-col-ver">${botonVerEjecucion(r)}</td>
      </tr>`).join('');
    return `
      <section class="seccion">
        <div class="seccion-titulo"><h2>Ejecuciones de esta sesión</h2>
          <p>${EJECUCIONES.length} en total · se borran al cerrar la pestaña · <button type="button" class="enlace" data-dev="limpiar-ejecuciones">Borrar</button></p></div>
        <div class="tabla-marco"><table class="tabla dev-tabla">
          <thead><tr><th>Método</th><th class="num">Semilla</th><th>Factible</th><th class="num">f(x) inicial</th><th class="num">f(x) final</th><th class="num">Tiempo</th><th class="num">Ventanas</th><th>Origen</th><th><span class="visualmente-oculto">Horario</span></th></tr></thead>
          <tbody>${filas}</tbody>
        </table></div>
      </section>`;
  }

  function cuerpoPeticion(metodo, op, extra = {}) {
    const parametros = (R.parametros[metodo] || {});
    return {
      metodo,
      semilla: op.semilla,
      tiempo_max: op.tiempo_max,
      max_pasos: op.max_pasos,
      solver: op.solver,
      peso_ventanas: op.peso_ventanas,
      hilos: op.hilos === '' || op.hilos == null ? null : op.hilos,
      parametros,
      instancia: usaEditada(op) ? INST : null,   // null = la base (DatosColegio, horario 2027)
      anio: DATOS.meta.anio,
      ...extra,
    };
  }

  async function resolverUno() {
    if (R.ejecutando || SRV.estado !== 'conectado') return;
    if (usaEditada(R) && calc().validacion.errores.length) return;
    R.ejecutando = true;
    R.error = null;
    R.inicio = performance.now();
    refrescar();
    const reloj = setInterval(() => {
      const el = $('#dev-resolver-boton .dev-reloj');
      if (el) el.textContent = fmtMs(performance.now() - R.inicio);
    }, 100);
    try {
      const instancia = usaEditada(R) ? clonar(INST) : null;
      const j = await api('resolver', cuerpoPeticion(R.metodo, R, { incluir_horario: true }));
      R.resultado = registrar(j.resultado, null, instancia);
      R.datos = j.datos || null;
      if (R.datos) HORARIOS.guardar(R.resultado.id, R.datos);
    } catch (e) {
      R.error = errorDeRed(e) ? 'Se perdió la conexión con servidor.py. ¿Sigue abierto en la terminal?' : e.message;
      if (errorDeRed(e)) { SRV.estado = 'sin-servidor'; pintarServidor(); }
    } finally {
      clearInterval(reloj);
      R.ejecutando = false;
      refrescar();
      if (R.resultado && !R.error) {
        const el = $('.dev-resultado');
        if (el) {
          el.scrollIntoView({ behavior: 'smooth', block: 'start' });
          APP.animar.aparecer([el], { y: 14 });
        }
      }
    }
  }

  // El horario de un resultado no se guarda al recargar la página: "Resolver" lo vuelve a calcular
  // con la misma configuración (método, semilla, tiempo, solver e instancia) del resultado que se ve
  function resolverDeNuevo() {
    const r = R.resultado;
    if (r) {
      if (metodos().some(m => m.id === r.metodo)) R.metodo = r.metodo;
      if (r.semilla != null) R.semilla = r.semilla;
      if (r.tiempo_max) R.tiempo_max = r.tiempo_max;
      if (r.max_pasos) R.max_pasos = r.max_pasos;
      const solver = r.modelo && r.modelo.solver;
      if (r.metodo === 'modelo' && solvers().includes(solver)) R.solver = solver;
      if (r.metodo === 'modelo' && r.parametros && r.parametros.peso_ventanas != null) R.peso_ventanas = r.parametros.peso_ventanas;
      R.usarBase = !r.editada;
      guardarR();
    }
    resolverUno();
  }

  function verResultado() {
    if (R.datos) abrirEnVisualizador(R.datos);
  }

  function abrirEnVisualizador(datos) {
    // El resultado lleva la instancia base: al verlo no se pierde la base aunque sea de una instancia editada
    datos.meta.desarrollador = { ...datos.meta.desarrollador, base: BASE };
    if (!sesion.guardar(CLAVES.resultado, datos)) {
      window.alert('El navegador no tiene espacio para guardar el horario en esta pestaña. Usa "Descargar datos (.js)".');
      return;
    }
    location.href = `${location.pathname}?anio=${datos.meta.anio}&resultado=1#/cursos/${encodeURIComponent(estado.curso)}`;
  }

  // "Ver en el visualizador" de la tabla de ejecuciones: abre el horario guardado de esa ejecución o,
  // si no quedó guardado, lo vuelve a calcular con su misma configuración (sin agregar otra fila)
  async function verEjecucion(boton) {
    const r = EJECUCIONES.find(e => e.id === boton.dataset.id);
    if (!r || boton.getAttribute('aria-busy') === 'true') return;
    let datos = (R.resultado && R.resultado.id === r.id && R.datos) || await HORARIOS.leer(r.id);
    if (!datos) {
      if (!reproducible(r) || SRV.estado !== 'conectado') {
        avisar(SRV.estado !== 'conectado' ? 'Para volver a calcular este horario se necesita el servidor.'
          : 'Este horario no quedó guardado y la instancia editada cambió desde que se resolvió.', 'error');
        return;
      }
      boton.setAttribute('aria-busy', 'true');
      boton.lastChild.textContent = 'Resolviendo…';
      try {
        const op = {
          semilla: r.semilla, tiempo_max: r.tiempo_max, max_pasos: r.max_pasos, usarBase: !r.editada,
          solver: (r.modelo && r.modelo.solver) || R.solver,
          peso_ventanas: (r.metodo === 'modelo' && r.parametros && r.parametros.peso_ventanas) || 0,
          hilos: (r.metodo === 'modelo' && r.parametros && r.parametros.hilos) || null,
        };
        const extra = { incluir_horario: true, ...(r.metodo !== 'modelo' && r.parametros ? { parametros: r.parametros } : {}) };
        const j = await api('resolver', cuerpoPeticion(r.metodo, op, extra));
        datos = j.datos;
        if (datos) await HORARIOS.guardar(r.id, datos);
      } catch (e) {
        avisar(errorDeRed(e) ? 'Se perdió la conexión con el servidor.' : `No se pudo volver a calcular el horario: ${e.message}`, 'error');
        return;
      } finally {
        boton.removeAttribute('aria-busy');
        boton.lastChild.textContent = 'Ver en el visualizador';
      }
    }
    if (datos) abrirEnVisualizador(datos);
  }

  function descargarResultado() {
    if (!R.datos) return;
    const r = R.resultado;
    const nombre = `horarios_${R.datos.meta.anio}_${r.metodo}${r.semilla != null ? `_s${r.semilla}` : ''}.js`;
    descargar(nombre, `// Generado en el modo desarrollador del Prototipo 2 · ${r.nombre} · ${R.datos.meta.generado}\n`
      + `// Para agregarlo como instancia (Configuración la puede elegir), en la carpeta del prototipo:\n`
      + `//   python exportar_datos.py --importar ${nombre} --nombre "${r.nombre}"\n`
      + `window.HORARIOS_MMDD = ${JSON.stringify(R.datos)};\n`, 'text/javascript');
  }

  // ===========================================================================
  // 10. COMPARAR
  // ===========================================================================
  function semillas() {
    const a = Math.max(0, Math.floor(Number(C.desde) || 0));
    const b = Math.max(a, Math.min(a + 49, Math.floor(Number(C.hasta) || a)));
    return Array.from({ length: b - a + 1 }, (_, i) => a + i);
  }

  function tareasComparacion() {
    const s = semillas();
    const tareas = [];
    ORDEN_CLAVES.filter(k => !k.startsWith('modelo:') && C.metodos.includes(k)).forEach(metodo => s.forEach(semilla => tareas.push({ metodo, semilla })));
    if (conModelo()) {
      solvers().filter(sv => C.solvers.includes(sv)).forEach(solver => s.forEach((_, rep) => tareas.push({ metodo: 'modelo', solver, rep: rep + 1 })));
    }
    return tareas;
  }

  function resumir(runs) {
    const tiempos = runs.map(r => r.tiempos_ms.total);
    const factibles = runs.filter(r => r.factible);
    return {
      n: runs.length,
      factibles: factibles.length,
      tasa: runs.length ? factibles.length / runs.length : 0,
      fIni: media(runs.map(r => r.costo_inicial)),
      fFin: media(runs.map(r => r.costo_final)),
      fMin: Math.min(...runs.map(r => r.costo_final ?? Infinity)),
      fMax: Math.max(...runs.map(r => r.costo_final ?? -Infinity)),
      tMed: mediana(tiempos),
      tMedia: media(tiempos),
      tDesv: desv(tiempos),
      tFact: mediana(factibles.map(r => r.t_factible_ms)),
      pasos: media(runs.map(r => r.pasos)),
      ventanas: media(runs.map(r => r.auditoria && r.auditoria.metricas.total_ventanas_docentes)),
      dobles: media(runs.map(r => r.auditoria && r.auditoria.metricas.porcentaje_bloques_dobles)),
    };
  }

  // Filas de la comparación: una por método (y por solver del modelo), en el orden del ranking
  function filasComparacion() {
    if (!LOTE) return [];
    const runs = EJECUCIONES.filter(e => e.lote === LOTE);
    const grupos = new Map();
    runs.forEach(r => { const k = claveDe(r); if (!grupos.has(k)) grupos.set(k, []); grupos.get(k).push(r); });
    return [...grupos].map(([clave, lista]) => ({ clave, runs: lista, tipo: lista[0].tipo, ...resumir(lista) }))
      .sort((a, b) => b.tasa - a.tasa || (a.fFin ?? Infinity) - (b.fFin ?? Infinity) || (a.tFact ?? Infinity) - (b.tFact ?? Infinity) || a.tMed - b.tMed);
  }

  function htmlComparar() {
    const tareas = tareasComparacion();
    const listo = SRV.estado === 'conectado' && !(usaEditada(C) && calc().validacion.errores.length) && tareas.length > 0;
    const check = (grupo, valor, etiqueta, marcado, extra = '', nota = '') => `
      <label class="dev-check" style="--c:${colorDe(grupo === 'cmp-solver' ? `modelo:${valor}` : valor)}">
        <input type="checkbox" data-dev-campo="${grupo}" value="${esc(valor)}" data-foco="${grupo}|${esc(valor)}"${marcado ? ' checked' : ''}${C.ejecutando ? ' disabled' : ''} ${extra}>
        <span class="dev-metodo-punto"></span><span>${etiqueta}${nota ? ` <small class="dev-tenue">${nota}</small>` : ''}</span></label>`;
    const ms = metodos().filter(m => m.id !== 'modelo');
    const p = C.progreso;
    const progreso = C.ejecutando && p ? `
      <div class="dev-progreso" role="progressbar" aria-valuemin="0" aria-valuemax="${p.n}" aria-valuenow="${p.i}" aria-label="Avance de la comparación">
        <div class="dev-progreso-pista"><span style="width:${(p.i / p.n) * 100}%"></span></div>
        <p><b>${p.i} de ${p.n}</b> · ${esc(p.texto)}</p>
      </div>` : '';
    return `
      <section class="seccion">
        <div class="seccion-titulo"><h2>Configurar la comparación</h2>
          <p>Mismo presupuesto para todos: cada ejecución para al llegar a f(x) = 0, al tiempo máximo o a los pasos máximos</p></div>
        <div class="dev-comparar-config">
          <fieldset class="dev-grupo-checks"><legend>Metaheurísticas (desde la construcción voraz)</legend>
            ${ms.map(m => check('cmp-metodo', m.id, esc(m.nombre), C.metodos.includes(m.id), '', esc(m.tipo))).join('')}
          </fieldset>
          <fieldset class="dev-grupo-checks"><legend>Modelo matemático</legend>
            ${conModelo() ? solvers().map(s => check('cmp-solver', s, esc(NOMBRE_SOLVER[s] || s), C.solvers.includes(s), '', esc(NOTA_SOLVER[s] || ''))).join('')
              : '<p class="nota">El servidor no tiene solvers: <code>pip install gurobipy ortools</code>.</p>'}
            ${notaGurobi() ? `<p class="nota">${esc(notaGurobi().replace(/^ · /, ''))}</p>` : ''}
            <p class="nota">El modelo no usa semilla: se repite tantas veces como semillas haya, para medir la variación de su tiempo.</p>
          </fieldset>
          <fieldset class="dev-grupo-checks"><legend>Presupuesto</legend>
            <div class="dev-campos">
              <label class="dev-campo"><span>Semilla desde</span><input class="dev-input" type="number" min="0" step="1" value="${esc(C.desde)}" data-dev-campo="c" data-prop="desde" data-foco="c|desde"${C.ejecutando ? ' disabled' : ''}></label>
              <label class="dev-campo"><span>hasta</span><input class="dev-input" type="number" min="0" step="1" value="${esc(C.hasta)}" data-dev-campo="c" data-prop="hasta" data-foco="c|hasta"${C.ejecutando ? ' disabled' : ''}></label>
              <label class="dev-campo"><span>Tiempo máximo por ejecución (s)</span><input class="dev-input" type="number" min="0.1" max="${topeTiempo()}" step="any" value="${esc(C.tiempo_max)}" data-dev-campo="c" data-prop="tiempo_max" data-foco="c|tiempo_max"${C.ejecutando ? ' disabled' : ''}></label>
              <label class="dev-campo"><span>Pasos máximos</span><input class="dev-input" type="number" min="1" step="1" value="${esc(C.max_pasos)}" data-dev-campo="c" data-prop="max_pasos" data-foco="c|max_pasos"${C.ejecutando ? ' disabled' : ''}></label>
            </div>
          </fieldset>
        </div>
        ${selectorInstancia(C, 'c')}
        <div class="dev-ejecutar">
          ${C.ejecutando
            ? `<button type="button" class="boton boton-grande" data-dev="detener">${ICONOS.stop}Detener</button>`
            : `<button type="button" class="boton boton-primario boton-grande" data-dev="comparar"${listo ? '' : ' disabled'}>${ICONOS.play}Ejecutar comparación · ${tareas.length} ejecuciones</button>`}
          <span class="dev-tenue">Con la ${usaEditada(C) ? 'instancia editada' : esc(NOMBRE_BASE)} · los parámetros propios de cada método son los de Resolver</span>
        </div>
        ${progreso}
        ${C.errores.length ? `<ul class="dev-problemas">${C.errores.slice(-5).map(e => `<li class="error">${ICONOS.mal}${esc(e)}</li>`).join('')}</ul>` : ''}
        ${avisoServidor()}
      </section>
      <div id="dev-cmp-resultados">${htmlResultadosComparacion()}</div>`;
  }

  function htmlResultadosComparacion() {
    const filas = filasComparacion();
    if (!filas.length) {
      return `<section class="seccion"><p class="nota">${C.ejecutando ? 'Los resultados aparecen aquí a medida que terminan las ejecuciones.' : 'Elige los métodos y ejecuta la comparación: aquí aparecerán la tabla resumen, los tiempos de ejecución, la función objetivo y la convergencia de cada método.'}</p></section>`;
    }
    const runs = filas.flatMap(f => f.runs);
    const mejor = filas.filter(f => f.tasa === 1).sort((a, b) => a.tMed - b.tMed)[0];
    const cuerpoTabla = filas.map(f => `
      <tr>
        <td><span class="asig"><span class="dev-metodo-punto" style="--c:${colorDe(f.clave)}"></span><b>${esc(nombreClave(f.clave))}</b>${mejor && mejor.clave === f.clave ? ' <span class="etiqueta dev-etiqueta">más rápido factible</span>' : ''}</span></td>
        <td>${esc(f.tipo)}</td>
        <td class="num">${f.factibles} / ${f.n}</td>
        <td class="num">${fmt(f.fIni, 0)}</td>
        <td class="num">${fmt(f.fFin, 0)}${f.fMin !== f.fMax ? ` <small class="dev-tenue">(${fmt(f.fMin, 0)}–${fmt(f.fMax, 0)})</small>` : ''}</td>
        <td class="num">${fmtMs(f.tMed)}</td>
        <td class="num">${fmtMs(f.tMedia)} <small class="dev-tenue">± ${fmtMs(f.tDesv)}</small></td>
        <td class="num">${fmtMs(f.tFact)}</td>
        <td class="num">${f.pasos == null ? '—' : fmt(f.pasos, 0)}</td>
        <td class="num">${fmt(f.ventanas, 1)}</td>
        <td class="num">${fmt(f.dobles, 1)}</td>
      </tr>`).join('');
    const detalle = runs.map(r => `
      <tr>
        <td>${esc(nombreClave(claveDe(r)))}</td><td class="num">${r.semilla ?? `rep. ${r.rep || 1}`}</td>
        <td>${r.factible ? 'sí' : 'no'}</td><td class="num">${fmt(r.costo_inicial, 0)}</td><td class="num">${fmt(r.costo_final, 0)}</td>
        <td class="num">${fmtMs(r.tiempos_ms.total)}</td><td class="num">${fmtMs(r.tiempos_ms.busqueda)}</td><td class="num">${fmtMs(r.t_factible_ms)}</td>
        <td class="num">${r.pasos == null ? '—' : fmt(r.pasos, 0)}</td><td>${esc(r.metodo === 'modelo' ? r.motivo_parada : motivo(r.motivo_parada))}</td>
      </tr>`).join('');
    return `
      <section class="seccion">
        <div class="seccion-titulo"><h2>Resumen por método</h2>
          <p>${runs.length} ejecuciones · orden: % factibles ↓, f(x) final media ↑, tiempo hasta factible ↑ · ${runs[0].editada ? 'instancia editada' : esc(NOMBRE_BASE)}</p></div>
        <div class="tabla-marco"><table class="tabla dev-tabla dev-tabla-resumen">
          <thead><tr><th>Método</th><th>Tipo</th><th class="num">Factibles</th><th class="num">f(x) inicial</th><th class="num">f(x) final</th>
            <th class="num">Tiempo (mediana)</th><th class="num">Media ± desv.</th><th class="num">Hasta factible</th><th class="num">Pasos</th><th class="num">Ventanas</th><th class="num">% dobles</th></tr></thead>
          <tbody>${cuerpoTabla}</tbody>
        </table></div>
        <p class="nota">Tiempo = total de la ejecución (preparación, construcción o armado del modelo, búsqueda o resolución y salida). "Hasta factible" se mide desde el inicio de la búsqueda (en el modelo, de la resolución). f(x) = 1000 · violaciones duras; las ventanas docentes no forman parte de f(x) y se informan como criterio de calidad.</p>
      </section>
      <div class="columnas dev-columnas-graficos">
        <section class="seccion">
          <div class="seccion-titulo"><h2>Tiempo de ejecución</h2><p>Cada punto es una ejecución · la raya, su mediana · escala logarítmica</p></div>
          <div class="dev-leyenda"><span><i class="dev-key-punto"></i>factible</span><span><i class="dev-key-punto hueco"></i>con violaciones</span><span><i class="dev-key-raya"></i>mediana</span></div>
          <div class="dev-grafico" data-grafico="tiempos"></div>
        </section>
        <section class="seccion">
          <div class="seccion-titulo"><h2>Función objetivo</h2><p>f(x) media al empezar (construcción voraz) y al terminar</p></div>
          <div class="dev-leyenda"><span><i class="dev-key-punto hueco"></i>inicial</span><span><i class="dev-key-punto"></i>final</span></div>
          <div class="dev-grafico" data-grafico="fx"></div>
        </section>
      </div>
      <section class="seccion">
        <div class="seccion-titulo"><h2>Convergencia</h2><p>Mejor f(x) a lo largo de la búsqueda en la ejecución mediana de cada método · pasa el cursor para leer los valores</p></div>
        <div class="dev-leyenda" id="dev-leyenda-convergencia"></div>
        <div class="dev-grafico" data-grafico="convergencia"></div>
      </section>
      <section class="seccion">
        <details class="dev-detalle-ejecuciones" data-recordar="detalle-cmp">
          <summary>Todas las ejecuciones (${runs.length})</summary>
          <div class="tabla-marco"><table class="tabla dev-tabla">
            <thead><tr><th>Método</th><th class="num">Semilla</th><th>Factible</th><th class="num">f(x) inicial</th><th class="num">f(x) final</th><th class="num">Total</th><th class="num">Búsqueda</th><th class="num">Hasta factible</th><th class="num">Pasos</th><th>Parada</th></tr></thead>
            <tbody>${detalle}</tbody>
          </table></div>
        </details>
        <div class="dev-acciones"><button type="button" class="boton" data-dev="descargar-csv">${ICONOS.bajar}Descargar CSV</button></div>
      </section>`;
  }

  async function ejecutarComparacion() {
    if (C.ejecutando || SRV.estado !== 'conectado') return;
    const tareas = tareasComparacion();
    if (!tareas.length) return;
    C.ejecutando = true;
    C.detener = false;
    C.errores = [];
    LOTE = Date.now();
    C.progreso = { i: 0, n: tareas.length, texto: 'empezando…' };
    // La instancia se congela al empezar: editar mientras corre no cambia la comparación
    const instancia = usaEditada(C) ? clonar(INST) : null;
    refrescar();
    for (let i = 0; i < tareas.length; i++) {
      if (C.detener) break;
      const t = tareas[i];
      C.progreso = { i, n: tareas.length, texto: `${nombreClave(t.metodo === 'modelo' ? `modelo:${t.solver}` : t.metodo)} · ${t.metodo === 'modelo' ? `repetición ${t.rep}` : `semilla ${t.semilla}`}` };
      pintarProgreso();
      C.control = new AbortController();
      try {
        const op = { semilla: t.semilla, tiempo_max: C.tiempo_max, max_pasos: C.max_pasos, solver: t.solver, peso_ventanas: 0, hilos: null };
        // Con el horario completo, para poder abrir cada ejecución en el visualizador (no cambia los tiempos
        // medidos: el servidor arma el horario después de cronometrar al método)
        const j = await api('resolver', cuerpoPeticion(t.metodo, op, { instancia, incluir_horario: true }), { senal: C.control.signal });
        const r = registrar({ ...j.resultado, rep: t.rep || null }, LOTE, instancia);
        if (j.datos) HORARIOS.guardar(r.id, j.datos);
        actualizarResultadosComparacion();
      } catch (e) {
        if (e.name === 'AbortError') break;
        C.errores.push(`${C.progreso.texto}: ${errorDeRed(e) ? 'se perdió la conexión con servidor.py' : e.message}`);
        if (errorDeRed(e)) { SRV.estado = 'sin-servidor'; pintarServidor(); break; }
      }
    }
    C.ejecutando = false;
    C.control = null;
    C.progreso = null;
    refrescar();
  }

  function pintarProgreso() {
    const p = C.progreso;
    const el = $('.dev-progreso');
    if (!el || !p) {
      if (estado.vista === 'edicion' && estado.edicion === 'comparar') refrescar();
      return;
    }
    el.setAttribute('aria-valuenow', p.i);
    $('.dev-progreso-pista span', el).style.width = `${(p.i / p.n) * 100}%`;
    $('p', el).innerHTML = `<b>${p.i} de ${p.n}</b> · ${esc(p.texto)}`;
  }

  function actualizarResultadosComparacion() {
    const el = $('#dev-cmp-resultados');
    if (!el) return;
    const abiertos = $$('details[data-recordar][open]', el).map(d => d.dataset.recordar);
    el.innerHTML = htmlResultadosComparacion();
    abiertos.forEach(k => { const d = $(`details[data-recordar="${k}"]`, el); if (d) d.open = true; });
    despuesDibujar();
    const s = $$('.edicion-secciones button')[4];
    if (s) s.innerHTML = `Comparar <b>${EJECUCIONES.filter(e => e.lote === LOTE).length}</b>`;
  }

  function descargarCSV() {
    const runs = filasComparacion().flatMap(f => f.runs);
    const columnas = ['metodo', 'solver', 'tipo', 'semilla', 'repeticion', 'factible', 'costo_inicial', 'duras_iniciales', 'costo_final', 'duras_finales',
      'pasos', 'pasos_por_s', 'motivo_parada', 't_preparacion_ms', 't_construccion_ms', 't_busqueda_ms', 't_salida_ms', 't_total_ms', 't_factible_ms', 't_mejor_ms',
      'ventanas_docentes', 'pct_dobles', 'tiempo_max_s', 'instancia'];
    const celda = v => (v == null ? '' : /[",;\n]/.test(String(v)) ? `"${String(v).replace(/"/g, '""')}"` : String(v));
    const filas = runs.map(r => [r.metodo, r.metodo === 'modelo' ? r.parametros.solver : '', r.tipo, r.semilla, r.rep, r.factible, r.costo_inicial, r.duras_iniciales,
      r.costo_final, r.duras_finales, r.pasos, r.pasos_por_s, r.motivo_parada, r.tiempos_ms.preparacion, r.tiempos_ms.construccion, r.tiempos_ms.busqueda,
      r.tiempos_ms.salida, r.tiempos_ms.total, r.t_factible_ms, r.t_mejor_ms, r.auditoria && r.auditoria.metricas.total_ventanas_docentes,
      r.auditoria && r.auditoria.metricas.porcentaje_bloques_dobles, r.tiempo_max, r.editada ? 'editada' : 'original'].map(celda).join(','));
    descargar(`comparacion_metodos_${new Date(LOTE).toISOString().slice(0, 16).replace(/[:T]/g, '-')}.csv`, `${columnas.join(',')}\n${filas.join('\n')}\n`, 'text/csv');
  }

  // ===========================================================================
  // 11. GRÁFICOS (SVG)
  // ===========================================================================
  const svgAbrir = (ancho, alto, etiqueta) => `<svg class="dev-svg" width="${ancho}" height="${alto}" viewBox="0 0 ${ancho} ${alto}" role="img" aria-label="${esc(etiqueta)}">`;

  // Escala logarítmica en milisegundos, con décadas como marcas
  function escalaLog(valores, x0, x1) {
    const v = valores.filter(x => x != null && x > 0);
    let a = Math.floor(Math.log10(Math.max(0.1, Math.min(...v, 1))));
    let b = Math.ceil(Math.log10(Math.max(...v, 10)));
    if (b <= a) b = a + 1;
    const f = t => x0 + ((Math.log10(Math.max(t, 10 ** a)) - a) / (b - a)) * (x1 - x0);
    const marcas = [];
    for (let k = a; k <= b; k++) marcas.push(10 ** k);
    return { f, marcas, min: 10 ** a, max: 10 ** b };
  }
  const textoMs = ms => (ms >= 1000 ? `${fmt(ms / 1000, 2)} s` : `${fmt(ms, 1)} ms`);
  // Cada cuántas marcas va una etiqueta, para que no se toquen (~52 px por etiqueta)
  const saltoMarcas = (n, largo) => Math.max(1, Math.ceil(52 / (largo / Math.max(1, n - 1))));

  function escalaLineal(max, x0, x1) {
    const bruto = max > 0 ? max : 1000;
    const paso = 10 ** Math.floor(Math.log10(bruto / 4));
    const util = [1, 2, 2.5, 5, 10].map(m => m * paso).find(p => bruto / p <= 5) || paso * 10;
    const tope = Math.ceil(bruto / util) * util;
    const marcas = [];
    for (let v = 0; v <= tope + 1e-9; v += util) marcas.push(v);
    return { f: v => x0 + (v / tope) * (x1 - x0), marcas, tope };
  }

  function medidas(el) {
    const ancho = Math.max(300, Math.floor(el.clientWidth || el.getBoundingClientRect().width || 600));
    const estrecho = ancho < 520;
    return { ancho, estrecho, izq: estrecho ? 92 : 156, der: estrecho ? 66 : 96 };
  }

  // Filas por método: puntos de cada ejecución (tiempo) o pesa inicial → final (f(x))
  function graficoPorMetodo(el, tipo) {
    const filas = filasComparacion();
    const { ancho, estrecho, izq, der } = medidas(el);
    const altoFila = 34;
    const arriba = 8;
    const abajo = 30;
    const alto = arriba + filas.length * altoFila + abajo;
    const x0 = izq;
    const x1 = ancho - der;
    const runs = filas.flatMap(f => f.runs);
    const escala = tipo === 'tiempos'
      ? escalaLog(runs.map(r => r.tiempos_ms.total), x0, x1)
      : escalaLineal(Math.max(...runs.map(r => Math.max(r.costo_inicial || 0, r.costo_final || 0))), x0, x1);
    const yBase = alto - abajo;
    let s = svgAbrir(ancho, alto, tipo === 'tiempos' ? 'Tiempo de ejecución por método' : 'Función objetivo inicial y final por método');
    const salto = saltoMarcas(escala.marcas.length, x1 - x0);
    escala.marcas.forEach((m, i) => {
      const x = escala.f(m);
      s += `<line class="dev-g-grilla" x1="${x}" x2="${x}" y1="${arriba}" y2="${yBase}"/>`;
      if (i % salto === 0) s += `<text class="dev-g-eje" x="${x}" y="${yBase + 18}" text-anchor="middle">${tipo === 'tiempos' ? textoMs(m) : fmt(m, 0)}</text>`;
    });
    s += `<line class="dev-g-base" x1="${x0}" x2="${x1}" y1="${yBase}" y2="${yBase}"/>`;
    filas.forEach((f, i) => {
      const y = arriba + i * altoFila + altoFila / 2;
      const c = colorDe(f.clave);
      s += `<text class="dev-g-etiqueta" x="${x0 - 12}" y="${y}" text-anchor="end" dominant-baseline="middle">${esc(nombreClave(f.clave, estrecho))}</text>`;
      if (tipo === 'tiempos') {
        f.runs.forEach((r, j) => {
          const x = escala.f(r.tiempos_ms.total);
          const dy = ((j % 3) - 1) * 6;
          const tip = `<b>${esc(nombreClave(f.clave))}</b> · ${r.semilla != null ? `semilla ${r.semilla}` : `repetición ${r.rep || 1}`}<br>Tiempo total ${fmtMs(r.tiempos_ms.total)}<br>f(x) final ${fmt(r.costo_final, 0)}${r.factible ? ' · factible' : ' · con violaciones'}`;
          s += `<circle class="dev-g-punto${r.factible ? '' : ' hueco'}" cx="${x}" cy="${y + dy}" r="5" style="--c:${c}" data-tip="${esc(tip)}"/>`;
        });
        const xm = escala.f(f.tMed);
        s += `<line class="dev-g-mediana" x1="${xm}" x2="${xm}" y1="${y - 12}" y2="${y + 12}"/>`;
        s += `<text class="dev-g-valor" x="${x1 + 10}" y="${y}" dominant-baseline="middle">${fmtMs(f.tMed)}</text>`;
      } else {
        const xi = f.fIni != null ? escala.f(f.fIni) : null;
        const xf = escala.f(f.fFin ?? 0);
        const tip = `<b>${esc(nombreClave(f.clave))}</b><br>f(x) inicial media ${fmt(f.fIni, 0)}<br>f(x) final media ${fmt(f.fFin, 0)}<br>${f.factibles} de ${f.n} factibles`;
        if (xi != null) {
          s += `<line class="dev-g-pesa" x1="${xi}" x2="${xf}" y1="${y}" y2="${y}" style="--c:${c}"/>`;
          s += `<circle class="dev-g-punto hueco" cx="${xi}" cy="${y}" r="5" style="--c:${c}" data-tip="${esc(tip)}"/>`;
        }
        s += `<circle class="dev-g-punto" cx="${xf}" cy="${y}" r="5" style="--c:${c}" data-tip="${esc(tip)}"/>`;
        s += `<text class="dev-g-valor" x="${x1 + 10}" y="${y}" dominant-baseline="middle">${fmt(f.fFin, 0)}</text>`;
      }
    });
    el.innerHTML = `${s}</svg>`;
  }

  // Serie de convergencia de una ejecución: [[t_ms, f(x)], ...] y el instante en que terminó
  function serieDe(r) {
    const h = r.historial || [];
    if (!h.length) return null;
    const fin = Math.max(r.tiempos_ms.busqueda || 0, h[h.length - 1][0] || 0);
    return { puntos: h.map(p => [p[0], p[2]]), fin };
  }

  function graficoConvergencia(el, series) {
    const { ancho } = medidas(el);
    const alto = Math.round(Math.min(340, Math.max(220, ancho * 0.42)));
    const izq = 60;
    const der = 18;
    const arriba = 12;
    const abajo = 32;
    const x0 = izq;
    const x1 = ancho - der;
    const y0 = alto - abajo;
    const tiempos = series.flatMap(s => [...s.puntos.map(p => p[0]), s.fin]);
    const ex = escalaLog(tiempos, x0, x1);
    const ey = escalaLineal(Math.max(...series.flatMap(s => s.puntos.map(p => p[1] || 0))), y0, arriba);
    let s = svgAbrir(ancho, alto, 'Convergencia de la función objetivo');
    ey.marcas.forEach(m => {
      const y = ey.f(m);
      s += `<line class="dev-g-grilla" x1="${x0}" x2="${x1}" y1="${y}" y2="${y}"/>`;
      s += `<text class="dev-g-eje" x="${x0 - 8}" y="${y}" text-anchor="end" dominant-baseline="middle">${fmt(m, 0)}</text>`;
    });
    const salto = saltoMarcas(ex.marcas.length, x1 - x0);
    ex.marcas.forEach((m, i) => {
      const x = ex.f(m);
      s += `<line class="dev-g-grilla" x1="${x}" x2="${x}" y1="${arriba}" y2="${y0}"/>`;
      if (i % salto === 0) s += `<text class="dev-g-eje" x="${x}" y="${y0 + 18}" text-anchor="middle">${textoMs(m)}</text>`;
    });
    s += `<line class="dev-g-base" x1="${x0}" x2="${x1}" y1="${y0}" y2="${y0}"/>`;
    series.forEach(serie => {
      if (serie.punto) {   // modelo matemático: un solo resultado
        const [t, f] = serie.puntos[serie.puntos.length - 1];
        const tip = `<b>${esc(serie.nombre)}</b><br>f(x) = ${fmt(f, 0)} en ${fmtMs(t)}`;
        s += `<circle class="dev-g-punto" cx="${ex.f(t)}" cy="${ey.f(f)}" r="6" style="--c:${serie.color}" data-tip="${esc(tip)}"/>`;
        return;
      }
      let d = '';
      serie.puntos.forEach(([t, f], i) => {
        const x = ex.f(t);
        const y = ey.f(f);
        d += i === 0 ? `M${x0},${y}H${x}` : `H${x}V${y}`;
      });
      d += `H${ex.f(serie.fin)}`;
      const [tf, ff] = serie.puntos[serie.puntos.length - 1];
      s += `<path class="dev-g-linea" d="${d}" style="--c:${serie.color}"/>`;
      s += `<circle class="dev-g-punto" cx="${ex.f(Math.max(serie.fin, tf))}" cy="${ey.f(ff)}" r="4.5" style="--c:${serie.color}"/>`;
    });
    s += `<line class="dev-g-cursor" x1="0" x2="0" y1="${arriba}" y2="${y0}" visibility="hidden"/>`;
    s += `<rect class="dev-g-captura" x="${x0}" y="${arriba}" width="${x1 - x0}" height="${y0 - arriba}" data-tip=""/>`;
    el.innerHTML = `${s}</svg>`;

    // Cursor vertical: valor de cada serie en ese instante (la serie es escalonada)
    const captura = $('.dev-g-captura', el);
    const cursor = $('.dev-g-cursor', el);
    const valorEn = (serie, t) => {
      let v = serie.puntos[0][1];
      serie.puntos.forEach(([ti, fi]) => { if (ti <= t) v = fi; });
      return v;
    };
    captura.addEventListener('pointermove', ev => {
      const caja = el.querySelector('svg').getBoundingClientRect();
      const x = Math.max(x0, Math.min(x1, ev.clientX - caja.left));
      const t = 10 ** (Math.log10(ex.min) + ((x - x0) / (x1 - x0)) * (Math.log10(ex.max) - Math.log10(ex.min)));
      cursor.setAttribute('x1', x);
      cursor.setAttribute('x2', x);
      cursor.setAttribute('visibility', 'visible');
      captura.dataset.tip = `<b>${fmtMs(t)}</b>${series.map(se => {
        const fin = se.punto ? se.puntos[0][0] : se.fin;
        const v = se.punto ? (t >= fin ? se.puntos[0][1] : null) : valorEn(se, t);
        return `<br>${esc(se.nombre)}: ${v == null ? 'resolviendo' : fmt(v, 0)}${!se.punto && t > fin ? ' (terminó)' : ''}`;
      }).join('')}`;
    });
    captura.addEventListener('pointerleave', () => cursor.setAttribute('visibility', 'hidden'));
  }

  function seriesComparacion() {
    return filasComparacion().filter(f => f.clave !== 'voraz').map(f => {
      if (f.clave.startsWith('modelo:')) {
        const r = [...f.runs].sort((a, b) => a.tiempos_ms.busqueda - b.tiempos_ms.busqueda)[Math.floor(f.runs.length / 2)];
        const se = serieDe(r);
        return se && { ...se, punto: true, clave: f.clave, nombre: nombreClave(f.clave), color: colorDe(f.clave) };
      }
      const orden = [...f.runs].sort((a, b) => a.tiempos_ms.busqueda - b.tiempos_ms.busqueda);
      const r = orden[Math.floor((orden.length - 1) / 2)];
      const se = serieDe(r);
      return se && { ...se, clave: f.clave, nombre: nombreClave(f.clave), semilla: r.semilla, color: colorDe(f.clave) };
    }).filter(Boolean);
  }

  function dibujar(el) {
    const tipo = el.dataset.grafico;
    if (tipo === 'tiempos' || tipo === 'fx') { graficoPorMetodo(el, tipo); return; }
    if (tipo === 'convergencia') {
      const series = seriesComparacion();
      const leyenda = $('#dev-leyenda-convergencia');
      if (leyenda) leyenda.innerHTML = series.map(se => `<span><i class="${se.punto ? 'dev-key-punto' : 'dev-key-linea'}" style="--c:${se.color}"></i>${esc(se.nombre)}${se.semilla != null ? ` <small class="dev-tenue">semilla ${se.semilla}</small>` : ''}</span>`).join('');
      if (series.length) graficoConvergencia(el, series);
      else el.innerHTML = '<p class="nota">Sin historial de convergencia.</p>';
      return;
    }
    if (tipo === 'resultado' && R.resultado) {
      const se = serieDe(R.resultado);
      if (!se) { el.innerHTML = '<p class="nota">Sin historial: el método no encontró una solución.</p>'; return; }
      const clave = claveDe(R.resultado);
      graficoConvergencia(el, [{ ...se, punto: R.resultado.metodo === 'modelo' || R.resultado.metodo === 'voraz', nombre: nombreClave(clave), color: colorDe(clave) }]);
    }
  }

  function despuesDibujar() {
    $$('#panel-edicion [data-grafico]').forEach(dibujar);
  }

  let esperaRedimension = null;
  window.addEventListener('resize', () => {
    clearTimeout(esperaRedimension);
    esperaRedimension = setTimeout(() => { if (estado.vista === 'edicion') despuesDibujar(); }, 160);
  });

  // ===========================================================================
  // 12. EVENTOS DE LA PESTAÑA EDICIÓN
  // ===========================================================================
  const panel = $('#panel-edicion');
  const idGrupo = id => { const [nivel, k, i] = id.split('|'); return [nivel, Number(k), Number(i)]; };

  panel.addEventListener('click', ev => {
    const selector = ev.target.closest('[data-dev-picker]');
    if (selector) {
      if (!selector.disabled) { if (disparador === selector && !POP.hidden) cerrarPicker(); else abrirPicker(selector); }
      return;
    }
    const b = ev.target.closest('[data-dev]');
    if (!b || b.disabled) return;
    const accion = b.dataset.dev;
    switch (accion) {
      case 'seccion':
        if (b.dataset.cursoDev) UI.curso = b.dataset.cursoDev;
        UI.mensaje = null;
        APP.ir('edicion', { edicion: b.dataset.valor }, { subir: false });
        break;
      case 'reconectar': SRV.estado = 'sin-servidor'; conectar(); break;
      case 'exportar':
        descargar('instancia_mmdd.json', JSON.stringify(INST, null, 2), 'application/json');
        break;
      case 'importar': $('#dev-archivo').click(); break;
      case 'deshacer': deshacer(); break;
      case 'verificar': programarVerificacion(0); break;
      case 'restablecer':
        // La base no se toca; los cambios quedan en el historial (Deshacer los recupera)
        cambiarInstancia(clonar(BASE), `Volviste a la ${NOMBRE_BASE}. Si fue sin querer, usa Deshacer.`);
        break;
      case 'solver':
        R.solver = b.dataset.valor;
        R.solverElegido = true;
        guardarR();
        refrescar();
        break;
      case 'usar-instancia': {
        const op = b.dataset.campo === 'c' ? C : R;
        op.usarBase = b.dataset.valor === 'base';
        if (op === C) guardarC(); else guardarR();
        refrescar();
        break;
      }
      case 'quitar': UI.quitando = b.dataset.docenteDev; UI.reemplazo = null; refrescar(); break;
      case 'cancelar-quitar': UI.quitando = null; refrescar(); break;
      case 'confirmar-quitar': {
        const nombre = b.dataset.docenteDev;
        const reemplazo = referencias(nombre).total ? UI.reemplazo : null;
        if (aplicar('quitar', nombre, reemplazo)) {
          UI.quitando = null;
          avisar(reemplazo ? `Se quitó a ${nombre}; sus clases pasaron a ${reemplazo}.` : `Se quitó a ${nombre}.`);
          refrescar();
        }
        break;
      }
      case 'ir-curso':
        UI.curso = b.dataset.cursoDev;
        UI.mensaje = null;
        APP.ir('edicion', { edicion: 'asignacion' }, { subir: false });
        break;
      case 'curso-paso': {
        const i = CURSOS.findIndex(c => c.id === UI.curso);
        UI.curso = CURSOS[(i + Number(b.dataset.valor) + CURSOS.length) % CURSOS.length].id;
        refrescar();
        break;
      }
      case 'agregar-grupo': { const [nivel, k] = idGrupo(b.dataset.id); aplicar('agregarGrupo', nivel, k); break; }
      case 'quitar-grupo': { const [nivel, k, i] = idGrupo(b.dataset.id); aplicar('quitarGrupo', nivel, k, i); break; }
      case 'franjas-fijas': aplicar('franjasFijas', INST.franjas_fijas === false); break;
      case 'resolver': resolverUno(); break;
      case 'resolver-de-nuevo': resolverDeNuevo(); break;
      case 'ver-ejecucion': verEjecucion(b); break;
      case 'ver-resultado': verResultado(); break;
      case 'descargar-resultado': descargarResultado(); break;
      case 'limpiar-ejecuciones':
        HORARIOS.borrar(EJECUCIONES.map(e => e.id));
        EJECUCIONES = [];
        LOTE = null;
        R.resultado = null;
        R.datos = null;
        sesion.guardar(CLAVES.ejecuciones, EJECUCIONES);
        refrescar();
        break;
      case 'comparar': ejecutarComparacion(); break;
      case 'detener':
        C.detener = true;
        if (C.control) C.control.abort();
        break;
      case 'descargar-csv': descargarCSV(); break;
      default: break;
    }
  });

  const numeroDe = (valor, entero) => {
    if (valor === '' || valor == null) return '';
    const n = Number(valor);
    return Number.isFinite(n) ? (entero ? Math.round(n) : n) : '';
  };

  // Un campo cambió: 'el' es el control (input, casilla o selector) y 'valor' su nuevo valor
  function cambiarCampo(campo, el, valor) {
    switch (campo) {
      case 'nombre': aplicar('renombrar', el.dataset.docenteDev, valor); break;
      case 'depto': aplicar('departamento', el.dataset.docenteDev, valor); break;
      case 'nuevo-depto': UI.nuevoDepto = valor; refrescar(); break;
      case 'reemplazo': UI.reemplazo = valor; refrescar(); break;
      case 'jefe': aplicar('jefe', el.dataset.cursoDev, valor); break;
      case 'asignar': aplicar('asignar', el.dataset.cursoDev, Number(el.dataset.i), Number(el.dataset.s), valor); break;
      case 'curso': UI.curso = valor; refrescar(); break;
      case 'grupo': { const [nivel, k, i] = idGrupo(el.dataset.id); aplicar('grupo', nivel, k, i, el.dataset.prop, valor); break; }
      case 'metodo': R.metodo = valor; guardarR(); refrescar(); break;
      case 'r': {
        const p = el.dataset.prop;
        R[p] = numeroDe(valor, ['semilla', 'max_pasos', 'hilos'].includes(p));
        guardarR();
        break;
      }
      case 'rp': {
        R.parametros[R.metodo] = R.parametros[R.metodo] || {};
        const v = numeroDe(valor, false);
        if (v === '') delete R.parametros[R.metodo][el.dataset.prop];
        else R.parametros[R.metodo][el.dataset.prop] = v;
        guardarR();
        break;
      }
      case 'cmp-metodo':
      case 'cmp-solver': {
        const lista = campo === 'cmp-metodo' ? C.metodos : C.solvers;
        const i = lista.indexOf(el.value);
        if (el.checked && i < 0) lista.push(el.value);
        if (!el.checked && i >= 0) lista.splice(i, 1);
        if (campo === 'cmp-solver') C.solversElegidos = true;
        guardarC();
        refrescar();
        break;
      }
      case 'c': {
        const p = el.dataset.prop;
        C[p] = numeroDe(valor, p !== 'tiempo_max');
        guardarC();
        refrescar();
        break;
      }
      default: break;
    }
  }

  panel.addEventListener('change', ev => {
    const el = ev.target;
    if (el.id === 'dev-archivo') { importar(el.files && el.files[0]); return; }
    if (el.dataset.devCampo) cambiarCampo(el.dataset.devCampo, el, el.value);
  });

  panel.addEventListener('submit', ev => {
    const form = ev.target.closest('[data-dev-form]');
    if (!form) return;
    ev.preventDefault();
    if (form.dataset.devForm === 'agregar-docente') {
      const nombre = form.elements.nombre.value;
      const depto = UI.nuevoDepto || DEPARTAMENTOS[0];
      if (aplicar('agregarDocente', nombre, depto)) avisar(`Se agregó a ${nombre.trim()} en ${APP.nombreDepartamento(depto)}.`);
    }
  });

  // Enter confirma un texto (dispara 'change'); Escape lo descarta
  panel.addEventListener('keydown', ev => {
    const el = ev.target;
    if (!el.matches('input[type="text"][data-dev-campo]')) return;
    if (ev.key === 'Enter') { ev.preventDefault(); el.blur(); }
    if (ev.key === 'Escape') { el.value = el.defaultValue; el.blur(); }
  });

  function importar(archivo) {
    if (!archivo) return;
    const lector = new FileReader();
    lector.onload = () => {
      try {
        const inst = JSON.parse(lector.result);
        if (!compatible(inst)) throw new Error('incompatible');
        cambiarInstancia(inst, `Instancia importada desde ${archivo.name}. Si no era la que querías, usa Deshacer.`);
      } catch (e) {
        avisar('El archivo no es una instancia válida de este prototipo (exporta una desde aquí para ver el formato).', 'error');
        refrescar();
      }
    };
    lector.readAsText(archivo);
  }

  // ===========================================================================
  // 13. INTERFAZ PARA app.js
  // ===========================================================================
  window.MMDD_DEV = { renderEdicion, despuesRender, detalleExtra };
  programarVerificacion(0);   // con cambios guardados de otra visita, su estado se muestra al abrir Edición
  // Horarios guardados de las ejecuciones: el último resultado de Resolver recupera el suyo sin volver a resolver
  HORARIOS.cargar().then(async () => {
    if (R.resultado && !R.datos && HORARIOS.tiene(R.resultado.id)) R.datos = await HORARIOS.leer(R.resultado.id);
    if (estado.vista === 'edicion' && estado.edicion === 'resolver') refrescar();
  });
})();
