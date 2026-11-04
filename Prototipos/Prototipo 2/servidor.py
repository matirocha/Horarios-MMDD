#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
PROTOTIPO 2 — SERVIDOR LOCAL DEL MODO DESARROLLADOR
===============================================================================

Sirve la página del Prototipo 2 y una pequeña API que ejecuta el motor de
'notebooks/horarios' sobre una instancia editada en la pestaña "Edición" (modo
desarrollador): dotación docente, asignación profesor-curso y electivos.

  GET  /api/estado      Métodos disponibles (heurísticas, metaheurísticas y modelo
                        matemático), sus parámetros y los solvers de OR-Tools instalados.
  GET  /api/instancia   Instancia original (datos 2026 de DatosColegio) en el formato
                        que edita la página.
  POST /api/resolver    Resuelve una instancia con el método pedido y retorna tiempos,
                        función objetivo, auditoría y, si se pide, el horario completo
                        con el mismo formato que datos/horarios_<año>.js.

La instancia editada se aplica sobre DatosColegio solo mientras dura cada resolución
(y una a la vez), así que el motor, el validador y el exportador trabajan sin cambios.

La misma API se publica en Vercel con las funciones de la carpeta api/ de la raíz del
repositorio (ver vercel.json): usan ManejadorVercel, definido aquí.

Uso:
    python "Prototipos/Prototipo 2/servidor.py"              # http://localhost:8765
    python "Prototipos/Prototipo 2/servidor.py" --abrir      # y abre el navegador
    python "Prototipos/Prototipo 2/servidor.py" --puerto 9000
    python "Prototipos/Prototipo 2/servidor.py" --origen https://mi-app.vercel.app
        # además acepta a esa página publicada (si su solver en línea no está disponible)

Requiere lo mismo que el motor; el modelo matemático, además, OR-Tools (pip install ortools).
"""

import argparse
import copy
import inspect
import json
import os
import random
import sys
import threading
import time
import webbrowser
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.join(RAIZ, 'notebooks'))
sys.path.insert(0, AQUI)

import exportar_datos as EX  # noqa: E402  (también deja 'notebooks' en sys.path)
from horarios import (DatosColegio as D, METAHEURISTICAS, MetodoMejora, MotorHorarios,  # noqa: E402
                      ValidadorRestricciones, crear_metaheuristica)

PUERTO = 8765
MAX_CUERPO = 2 * 1024 * 1024        # bytes de una petición
EN_VERCEL = bool(os.environ.get('VERCEL'))   # funciones de api/ desplegadas en Vercel (ver vercel.json)
# Segundos máximos que acepta una resolución. En Vercel la función se corta a los 300 s
# (plan Hobby), así que se deja margen para armar el modelo y enviar la respuesta.
TIEMPO_MAX_TOPE = 240 if EN_VERCEL else 600
CANDADO = threading.Lock()          # una resolución a la vez (DatosColegio es global)

# -----------------------------------------------------------------------------
# Catálogo de métodos
# -----------------------------------------------------------------------------


class SoloConstruccion(MetodoMejora):
    """Sin fase de mejora: deja el horario de la construcción voraz tal cual."""

    nombre = 'voraz'
    tipo = 'heurística constructiva'

    def _buscar(self, modelo, rng, seg):
        return {'pasos': 0, 'motivo_parada': 'solo_construccion'}


METODOS = [
    {'id': 'voraz', 'nombre': 'Construcción voraz', 'tipo': 'heurística constructiva',
     'descripcion': 'Solo la solución inicial: ubica cada sesión en la posición de menor costo y no la reconsidera.'},
    {'id': 'min_conflicts', 'nombre': 'Min-Conflicts', 'tipo': 'heurística',
     'descripcion': 'Búsqueda local de descenso: aplica el mejor intercambio si no empeora. Puede quedar en un óptimo local.'},
    {'id': 'busqueda_tabu', 'nombre': 'Búsqueda tabú', 'tipo': 'metaheurística',
     'descripcion': 'Aplica el mejor intercambio admisible aunque empeore, con lista tabú y criterio de aspiración.'},
    {'id': 'busqueda_local_iterada', 'nombre': 'Búsqueda local iterada', 'tipo': 'metaheurística',
     'descripcion': 'ILS: descenso Min-Conflicts y perturbaciones desde la mejor solución encontrada.'},
    {'id': 'min_conflicts_tabu', 'nombre': 'Min-Conflicts + tabú', 'tipo': 'metaheurística',
     'descripcion': 'Híbrido del proyecto (método por defecto): tabú, ruido aleatorio y reinicios ILS.'},
    {'id': 'modelo', 'nombre': 'Modelo matemático', 'tipo': 'modelo exacto',
     'descripcion': 'Programación lineal entera con OR-Tools: las restricciones duras van como restricciones.'},
]
IDS_METODOS = {m['id'] for m in METODOS}

AYUDA_PARAMETROS = {
    'max_sin_mejora': 'Pasos sin mejorar antes de declarar un óptimo local',
    'tabu_min': 'Permanencia mínima de un movimiento en la lista tabú (pasos)',
    'tabu_rango': 'Rango aleatorio que se suma a la permanencia tabú',
    'parada_factible': 'Pasos sin mejora para detenerse si ya es factible',
    'largo_busqueda_local': 'Pasos sin mejora que cierran cada búsqueda local',
    'perturbaciones': 'Intercambios al azar de cada perturbación',
    'prob_ruido': 'Probabilidad de aplicar un intercambio al azar (0 a 1)',
    'reinicio': 'Pasos sin mejora antes de volver a la mejor solución y perturbarla',
}

# GUROBI no se ofrece: con una licencia o DLL incompatible, OR-Tools aborta el proceso al crearlo
SOLVERS = ['CP-SAT', 'HIGHS', 'SCIP', 'CBC']
_solvers_disponibles = None


def parametros_de(clase):
    """Parámetros propios del constructor de un método (sin max_pasos ni tiempo_max)."""
    firma = inspect.signature(clase.__init__)
    return [{'nombre': n, 'defecto': p.default, 'ayuda': AYUDA_PARAMETROS.get(n, '')}
            for n, p in firma.parameters.items()
            if n not in ('self', 'max_pasos', 'tiempo_max') and p.default is not inspect.Parameter.empty]


def solvers_disponibles():
    """Solvers de OR-Tools que se pueden crear en esta instalación (se calcula una vez)."""
    global _solvers_disponibles
    if _solvers_disponibles is None:
        try:
            from ortools.linear_solver import pywraplp
            import ortools
            disponibles = [s for s in SOLVERS if pywraplp.Solver.CreateSolver(s) is not None]
            _solvers_disponibles = {'ortools': getattr(ortools, '__version__', 'instalado'), 'solvers': disponibles}
        except ImportError:
            _solvers_disponibles = {'ortools': None, 'solvers': []}
    return _solvers_disponibles


def estado_api():
    metodos = []
    for m in METODOS:
        clase = METAHEURISTICAS.get(m['id'])
        metodos.append({**m, 'parametros': parametros_de(clase) if clase else [],
                        'defecto': m['id'] == 'min_conflicts_tabu'})
    return {'ok': True, 'version': 1, 'metodos': metodos, **solvers_disponibles(),
            'python': sys.version.split()[0], 'entorno': 'vercel' if EN_VERCEL else 'local',
            'tiempo_max_tope': TIEMPO_MAX_TOPE}


# -----------------------------------------------------------------------------
# Instancia editable
# -----------------------------------------------------------------------------
CAMPOS = ('DEPARTAMENTOS', 'PROFESORES_JEFES', 'FRANJAS_ELECTIVOS', 'ELECTIVOS_OFERTA',
          'HORAS_NO_LECTIVAS', '_malla_cache')
D.get_malla_curricular()   # llena la caché para copiarla
ORIGINAL = {k: copy.deepcopy(getattr(D, k)) for k in CAMPOS}
SALAS = [nombre for nombre, tipo, _ in EX.ESPACIOS if tipo == 'sala']


class ErrorInstancia(ValueError):
    """La instancia enviada por la página no es válida."""


def instancia_base():
    """Instancia original (datos 2026) en el formato que edita la página."""
    malla = ORIGINAL['_malla_cache']
    return {
        'version': 1,
        'departamentos': [depto for depto, _ in ORIGINAL['DEPARTAMENTOS']],
        'docentes': [{'nombre': d, 'departamento': depto, 'original': d}
                     for depto, nombres in ORIGINAL['DEPARTAMENTOS'] for d in nombres],
        'jefes': dict(ORIGINAL['PROFESORES_JEFES']),
        'malla': {c: [{'asignatura': a, 'horas': h, 'docentes': list(D.docentes_de(doc)), 'espacio': e}
                      for a, h, doc, e in malla[c] if not a.startswith('Formación Diferenciada')]
                  for c in D.todos_los_cursos()},
        'franjas': {nivel: [{'periodos': [{'dia': dia, 'bloque': b} for dia, b in f['periodos']],
                             'grupos': [{'asignatura': a, 'seccion': s, 'docente': doc, 'sala': sala, 'etiqueta': et}
                                        for a, s, doc, sala, et in f['grupos']]}
                            for f in franjas]
                    for nivel, franjas in ORIGINAL['FRANJAS_ELECTIVOS'].items()},
        'salas': SALAS,
    }


def _texto(valor, campo, largo=80):
    if not isinstance(valor, str) or not valor.strip():
        raise ErrorInstancia(f'Falta {campo}')
    valor = ' '.join(valor.split())
    if len(valor) > largo:
        raise ErrorInstancia(f'{campo} es demasiado largo: "{valor[:30]}…"')
    return valor


def _etiqueta(asignatura, seccion):
    """Etiqueta corta para la grilla de una sala: 'ECONOMÍA S.1'."""
    palabra = asignatura.split()[0].rstrip(',')
    return f'{palabra[:12]} {seccion}'


def convertir_instancia(inst):
    """Valida la instancia de la página y retorna los atributos de DatosColegio que reemplaza."""
    if not isinstance(inst, dict):
        raise ErrorInstancia('La instancia debe ser un objeto JSON')

    # Docentes y departamentos
    deptos = [depto for depto, _ in ORIGINAL['DEPARTAMENTOS']]
    por_depto = {depto: [] for depto in deptos}
    nombres, no_lectivas = set(), {}
    for d in inst.get('docentes') or []:
        nombre = _texto(d.get('nombre'), 'el nombre de un docente', 60)
        if nombre in nombres:
            raise ErrorInstancia(f'Docente repetido: {nombre}')
        if d.get('departamento') not in por_depto:
            raise ErrorInstancia(f'Departamento desconocido para {nombre}')
        nombres.add(nombre)
        por_depto[d['departamento']].append(nombre)
        original = d.get('original')
        if original in ORIGINAL['HORAS_NO_LECTIVAS']:
            no_lectivas[nombre] = copy.deepcopy(ORIGINAL['HORAS_NO_LECTIVAS'][original])
    if not nombres:
        raise ErrorInstancia('La instancia no tiene docentes')

    def docente(nombre, donde):
        if nombre not in nombres:
            raise ErrorInstancia(f'{donde}: el docente "{nombre}" no está en la dotación')
        return nombre

    # Profesores jefes
    jefes_in = inst.get('jefes') or {}
    jefes = {c: docente(jefes_in.get(c), f'Jefatura de {c}') for c in D.CURSOS}

    # Mallas: misma estructura que la original; solo cambian los docentes
    malla_in = inst.get('malla') or {}
    malla = {}
    for c in D.todos_los_cursos():
        base = [fila for fila in ORIGINAL['_malla_cache'][c] if not fila[0].startswith('Formación Diferenciada')]
        filas = malla_in.get(c)
        if not isinstance(filas, list) or len(filas) != len(base):
            raise ErrorInstancia(f'La malla de {c} no coincide con la original')
        malla[c] = []
        for fila, (asig, horas, doc0, espacio) in zip(filas, base):
            if fila.get('asignatura') != asig or fila.get('horas') != horas or fila.get('espacio') != espacio:
                raise ErrorInstancia(f'{c}: solo se pueden cambiar los docentes de "{asig}"')
            docs = fila.get('docentes') or []
            if len(docs) != len(D.docentes_de(doc0)):
                raise ErrorInstancia(f'{c} - {asig}: se esperan {len(D.docentes_de(doc0))} docente(s)')
            docs = [docente(x, f'{c} - {asig}') for x in docs]
            if len(set(docs)) != len(docs):
                raise ErrorInstancia(f'{c} - {asig}: la co-docencia necesita dos docentes distintos')
            malla[c].append((asig, horas, docs[0] if len(docs) == 1 else tuple(docs), espacio))

    # Franjas de electivos: mismos periodos; cambian los grupos (asignatura, sección, docente, sala)
    franjas_in = inst.get('franjas') or {}
    franjas, oferta = {}, {}
    for nivel, lista in ORIGINAL['FRANJAS_ELECTIVOS'].items():
        recibidas = franjas_in.get(nivel)
        if not isinstance(recibidas, list) or len(recibidas) != len(lista):
            raise ErrorInstancia(f'Las franjas de {nivel} no coinciden con las originales')
        franjas[nivel] = []
        oferta[nivel] = []
        for k, (franja, recibida) in enumerate(zip(lista, recibidas), 1):
            grupos = recibida.get('grupos') or []
            if not 1 <= len(grupos) <= 10:
                raise ErrorInstancia(f'{nivel}, franja {k}: debe tener entre 1 y 10 electivos')
            usados = set()
            nuevos = []
            for g in grupos:
                asig = _texto(g.get('asignatura'), f'el nombre de un electivo ({nivel}, franja {k})').upper()
                seccion = _texto(g.get('seccion'), f'la sección de {asig}', 12)
                doc = docente(g.get('docente'), f'{asig} ({nivel}, franja {k})')
                if doc in usados:
                    raise ErrorInstancia(f'{nivel}, franja {k}: {doc} no puede dictar dos electivos a la vez')
                usados.add(doc)
                sala = g.get('sala')
                if sala not in SALAS:
                    raise ErrorInstancia(f'{asig} ({nivel}, franja {k}): sala desconocida "{sala}"')
                etiqueta = g.get('etiqueta')
                etiqueta = ' '.join(etiqueta.split())[:24] if isinstance(etiqueta, str) and etiqueta.strip() \
                    else _etiqueta(asig, seccion)
                nuevos.append((asig, seccion, doc, sala, etiqueta))
                if asig not in oferta[nivel]:
                    oferta[nivel].append(asig)
            franjas[nivel].append({'periodos': copy.deepcopy(franja['periodos']),
                                   'etiquetas': copy.deepcopy(franja['etiquetas']),
                                   'grupos': nuevos})

    # Filas de las franjas en la malla de 3° y 4° medio (como en get_malla_curricular)
    for nivel, lista in franjas.items():
        for k, franja in enumerate(lista, 1):
            docentes = tuple(dict.fromkeys(g[2] for g in franja['grupos']))
            for seccion in ('A', 'B'):
                malla[f'{nivel} {seccion}'].append((D.nombre_franja(k), 6, docentes, 'Salas electivos'))

    return {
        'DEPARTAMENTOS': [(depto, por_depto[depto]) for depto in deptos],
        'PROFESORES_JEFES': jefes,
        'FRANJAS_ELECTIVOS': franjas,
        'ELECTIVOS_OFERTA': oferta,
        'HORAS_NO_LECTIVAS': no_lectivas,
        '_malla_cache': malla,
    }


@contextmanager
def instancia_aplicada(inst):
    """Aplica la instancia (None = la original) sobre DatosColegio mientras dura el bloque."""
    with CANDADO:
        valores = convertir_instancia(inst) if inst is not None else copy.deepcopy(ORIGINAL)
        for k, v in valores.items():
            setattr(D, k, v)
        try:
            yield
        finally:
            for k, v in ORIGINAL.items():
                setattr(D, k, copy.deepcopy(v))


# -----------------------------------------------------------------------------
# Resolución
# -----------------------------------------------------------------------------
def _numero(valor, defecto, minimo, maximo, entero=False):
    if valor is None or valor == '':
        return defecto
    try:
        valor = int(valor) if entero else float(valor)
    except (TypeError, ValueError):
        raise ErrorInstancia(f'Valor numérico inválido: {valor!r}')
    return max(minimo, min(maximo, valor))


def ms(segundos):
    return None if segundos is None else round(segundos * 1000, 1)


def desglose(modelo):
    """Violaciones duras por tipo de restricción: D docente, F familia, R sala, G gimnasio."""
    d = {'D': 0, 'F': 0, 'R': 0, 'G': 0}
    for k in modelo.malos:
        d[k[0]] = d.get(k[0], 0) + modelo.costo_clave(k)[1]
    return d


def recortar(historial, maximo=400):
    """Historial de convergencia [(t_ms, paso, costo, duras)] con a lo más 'maximo' puntos."""
    filas = [[ms(t), paso, costo, duras] for t, paso, costo, duras in historial]
    if len(filas) <= maximo:
        return filas
    paso = (len(filas) - 1) / (maximo - 1)
    return [filas[round(i * paso)] for i in range(maximo)]


def auditoria(horario):
    a = EX.exportar_auditoria(horario)
    return {'valido': a['valido'], 'totalErrores': a['totalErrores'], 'errores': a['errores'][:40],
            'metricas': a['metricas'], 'criterios': a['criterios']}


def resolver_heuristico(metodo, semilla, tiempo_max, max_pasos, parametros):
    if metodo == 'voraz':
        mejora = SoloConstruccion(max_pasos, tiempo_max)
        parametros = {}
    else:
        validos = {p['nombre']: p['defecto'] for p in parametros_de(METAHEURISTICAS[metodo])}
        extra = {}
        for nombre, valor in (parametros or {}).items():
            if nombre in validos:
                extra[nombre] = _numero(valor, validos[nombre], 0, 10 ** 7, isinstance(validos[nombre], int))
        mejora = crear_metaheuristica(metodo, max_pasos=max_pasos, tiempo_max=tiempo_max, **extra)
        parametros = extra
    motor = MotorHorarios(seed=semilla, max_pasos=max_pasos, metaheuristica=mejora, tiempo_max=tiempo_max)
    horario = motor.generar()
    e, t = motor.estadisticas, motor.tiempos
    return horario, {
        'costo_inicial': e['costo_construccion'],
        'duras_iniciales': e['duras_construccion'],
        'costo_final': e['costo_final'],
        'duras_finales': e['duras_finales'],
        'desglose': desglose(motor.modelo),
        'pasos': e['pasos'],
        'pasos_por_s': round(e['pasos'] / t['busqueda']) if t['busqueda'] > 0 else None,
        'motivo_parada': e['motivo_parada'],
        'tiempos_ms': {k: ms(v) for k, v in t.items()},
        't_factible_ms': ms(e['t_factible']),
        't_mejor_ms': ms(e['t_mejor']),
        'historial': recortar(e['historial']),
        'parametros': parametros or {},
    }


def resolver_modelo(solver, tiempo_max, peso_ventanas, hilos):
    try:
        from modelo_matematico import ModeloMatematico
        mm = ModeloMatematico(solver, peso_ventanas)
    except SystemExit as error:   # OR-Tools no instalado o solver no disponible
        raise ErrorInstancia(str(error))
    r = mm.resolver(tiempo_max, False, hilos)
    t0 = time.perf_counter()
    horario, inst = None, None
    if r['con_solucion']:
        inst = mm.a_modelo_horario()
        horario = inst.a_horario()
    t_salida = time.perf_counter() - t0
    total = r['t_construccion'] + r['t_resolucion'] + t_salida
    costo = inst.costo if inst else None
    duras = inst.duras if inst else None
    return horario, {
        'costo_inicial': None,
        'duras_iniciales': None,
        'costo_final': costo,
        'duras_finales': duras,
        'desglose': desglose(inst) if inst else None,
        'pasos': None,
        'pasos_por_s': None,
        'motivo_parada': r['estado'],
        'tiempos_ms': {'preparacion': ms(r['t_construccion']), 'construccion': None,
                       'busqueda': ms(r['t_resolucion']), 'salida': ms(t_salida), 'total': ms(total)},
        't_factible_ms': ms(r['t_resolucion']) if duras == 0 else None,
        't_mejor_ms': ms(r['t_resolucion']) if inst else None,
        'historial': [[ms(r['t_resolucion']), 0, costo, duras]] if inst else [],
        'parametros': {'solver': r['solver'], 'peso_ventanas': peso_ventanas, 'hilos': hilos},
        'modelo': {k: r[k] for k in ('solver', 'estado', 'objetivo', 'cota', 'gap', 'ventanas_modelo',
                                     'variables', 'restricciones')},
    }


def resolver(cuerpo):
    metodo = cuerpo.get('metodo') or 'min_conflicts_tabu'
    if metodo not in IDS_METODOS:
        raise ErrorInstancia(f'Método desconocido: {metodo}')
    semilla = _numero(cuerpo.get('semilla'), 3, 0, 2 ** 31 - 1, entero=True)
    tiempo_max = _numero(cuerpo.get('tiempo_max'), 20, 0.1, TIEMPO_MAX_TOPE)
    max_pasos = _numero(cuerpo.get('max_pasos'), 150000, 1, 10 ** 7, entero=True)
    anio = _numero(cuerpo.get('anio'), D.ANIO_HORARIO, 2000, 2100, entero=True)
    nombre = next(m['nombre'] for m in METODOS if m['id'] == metodo)

    with instancia_aplicada(cuerpo.get('instancia')):
        if metodo == 'modelo':
            solver = str(cuerpo.get('solver') or 'CP-SAT').upper()
            if solver not in SOLVERS:
                raise ErrorInstancia(f'Solver desconocido: {solver}')
            peso = _numero(cuerpo.get('peso_ventanas'), 0, 0, 1000)
            hilos = _numero(cuerpo.get('hilos'), None, 1, 64, entero=True)
            horario, r = resolver_modelo(solver, tiempo_max, peso, hilos)
            nombre = f'{nombre} · {solver}'
        else:
            horario, r = resolver_heuristico(metodo, semilla, tiempo_max, max_pasos, cuerpo.get('parametros'))

        resultado = {
            'metodo': metodo, 'nombre': nombre,
            'tipo': next(m['tipo'] for m in METODOS if m['id'] == metodo),
            'semilla': None if metodo == 'modelo' else semilla,
            'tiempo_max': tiempo_max, 'max_pasos': max_pasos,
            'editada': cuerpo.get('instancia') is not None,
            **r,
        }
        resultado['auditoria'] = auditoria(horario) if horario else None
        resultado['factible'] = bool(horario) and resultado['auditoria']['valido']
        respuesta = {'ok': True, 'resultado': resultado}

        if horario and cuerpo.get('incluir_horario'):
            meta = EX.meta_base(anio, 'generado', semilla=resultado['semilla'], desarrollador={
                'metodo': metodo, 'nombre': nombre, 'costo': resultado['costo_final'],
                'tiempo_ms': resultado['tiempos_ms']['total'], 'editada': resultado['editada'],
            })
            respuesta['datos'] = EX.construir_datos(horario, meta)
    return respuesta


# -----------------------------------------------------------------------------
# Servidor HTTP
# -----------------------------------------------------------------------------
class APIMixin:
    """
    La API JSON (/api/estado, /api/instancia, /api/resolver), común al servidor local
    (Manejador, abajo) y a las funciones de Vercel (ManejadorVercel y la carpeta api/).
    """

    permitidos = set()   # orígenes de otras páginas que pueden usar la API (CORS)
    ruta_fija = None     # en Vercel cada archivo de api/ atiende una sola ruta

    def _ruta(self):
        return self.ruta_fija or urlsplit(self.path).path

    def _origen_valido(self):
        # Sin Origin (GET del mismo sitio), la propia página (mismo host) o un origen permitido.
        # El origen 'null' es la página abierta con doble clic (file://)
        origen = self.headers.get('Origin')
        if origen is None or origen in self.permitidos:
            return True
        host = self.headers.get('X-Forwarded-Host') or self.headers.get('Host')
        return bool(host) and urlsplit(origen).netloc == host

    def _cors(self):
        origen = self.headers.get('Origin')
        if origen and origen in self.permitidos:
            self.send_header('Access-Control-Allow-Origin', origen)
            self.send_header('Vary', 'Origin')

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def _json(self, codigo, datos):
        cuerpo = json.dumps(datos, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        self.send_response(codigo)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(cuerpo)))
        self._cors()
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_OPTIONS(self):
        if not self._origen_valido():
            self.send_error(403)
            return
        self.send_response(204)
        self._cors()
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Allow-Private-Network', 'true')
        self.send_header('Access-Control-Max-Age', '600')
        self.end_headers()

    def api_get(self):
        ruta = self._ruta()
        if not self._origen_valido():
            self._json(403, {'ok': False, 'error': 'Origen no permitido'})
        elif ruta == '/api/estado':
            self._json(200, estado_api())
        elif ruta == '/api/instancia':
            self._json(200, {'ok': True, 'instancia': instancia_base()})
        else:
            self._json(404, {'ok': False, 'error': 'Ruta desconocida'})

    def do_POST(self):
        ruta = self._ruta()
        if not self._origen_valido():
            self._json(403, {'ok': False, 'error': 'Origen no permitido'})
            return
        if ruta != '/api/resolver':
            self._json(404, {'ok': False, 'error': 'Ruta desconocida'})
            return
        # Exigir JSON obliga a los sitios de otro origen a pasar por la verificación CORS
        if not self.headers.get('Content-Type', '').startswith('application/json'):
            self._json(415, {'ok': False, 'error': 'Se espera Content-Type: application/json'})
            return
        largo = int(self.headers.get('Content-Length') or 0)
        if largo > MAX_CUERPO:
            self._json(413, {'ok': False, 'error': 'Petición demasiado grande'})
            return
        try:
            cuerpo = json.loads(self.rfile.read(largo) or b'{}')
            t0 = time.perf_counter()
            respuesta = resolver(cuerpo)
            r = respuesta['resultado']
            print(f"  {r['nombre']:<34} semilla {str(r['semilla']):>5}  f(x)={r['costo_final']}  "
                  f"{r['tiempos_ms']['total']} ms  ({(time.perf_counter() - t0):.2f} s con la respuesta)", flush=True)
            self._json(200, respuesta)
        except (ErrorInstancia, json.JSONDecodeError) as error:
            self._json(400, {'ok': False, 'error': str(error)})
        except RuntimeError as error:   # p. ej. la construcción voraz no encuentra espacio
            self._json(422, {'ok': False, 'error': str(error)})
        except Exception as error:      # noqa: BLE001 — se informa a la página en vez de cortar la conexión
            self._json(500, {'ok': False, 'error': f'{type(error).__name__}: {error}'})
            raise


class Manejador(APIMixin, SimpleHTTPRequestHandler):
    """Servidor local: archivos estáticos del prototipo + API JSON en /api/."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=AQUI, **kwargs)

    def do_GET(self):
        if urlsplit(self.path).path.startswith('/api/'):
            self.api_get()
        else:
            super().do_GET()

    def log_message(self, formato, *args):
        if '/api/' in self.path and self.command != 'POST':
            super().log_message(formato, *args)


class ManejadorVercel(APIMixin, BaseHTTPRequestHandler):
    """
    Base de las funciones de Vercel (api/estado.py, api/instancia.py, api/resolver.py):
    cada una define 'ruta_fija'. La página se sirve como archivos estáticos (vercel.json).
    """

    def do_GET(self):
        self.api_get()


def main():
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding='utf-8', errors='replace')
        except AttributeError:
            pass
    parser = argparse.ArgumentParser(description='Servidor local del modo desarrollador (Prototipo 2)')
    parser.add_argument('--puerto', type=int, default=PUERTO, help=f'Puerto (default: {PUERTO})')
    parser.add_argument('--abrir', action='store_true', help='Abre la página en el navegador')
    parser.add_argument('--origen', action='append', default=[], metavar='URL',
                        help='Página publicada que puede usar este servidor, p. ej. https://mi-app.vercel.app '
                             '(se puede repetir). Sin esto solo responde a la página local o abierta con doble clic.')
    args = parser.parse_args()

    publicadas = set()
    for origen in args.origen:
        partes = urlsplit(origen.strip())
        if partes.scheme not in ('http', 'https') or not partes.netloc:
            raise SystemExit(f'--origen debe ser una dirección como https://mi-app.vercel.app (recibí "{origen}")')
        publicadas.add(f'{partes.scheme}://{partes.netloc}')   # el navegador envía el origen sin ruta ni "/" final
    Manejador.permitidos = {'null', f'http://localhost:{args.puerto}', f'http://127.0.0.1:{args.puerto}'} | publicadas
    try:
        servidor = ThreadingHTTPServer(('127.0.0.1', args.puerto), Manejador)
    except OSError as error:
        raise SystemExit(f'No se pudo abrir el puerto {args.puerto}: {error}. Prueba con --puerto 9000.')

    url = f'http://localhost:{args.puerto}/?anio={D.ANIO_HORARIO}#/edicion/resolver'
    s = solvers_disponibles()
    print('Servidor del modo desarrollador · Horarios MMDD (Prototipo 2)')
    print(f'  Página:    {url}')
    for origen in sorted(publicadas):
        print(f'  Acepta:    {origen} (página publicada; el navegador puede pedir permiso de red local)')
    print(f"  OR-Tools:  {s['ortools'] or 'no instalado (el modelo matemático no estará disponible)'}"
          + (f" · solvers: {', '.join(s['solvers'])}" if s['solvers'] else ''))
    print('  Ctrl + C para detener.\n')
    if args.abrir:
        webbrowser.open(url)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print('\nServidor detenido.')
    finally:
        servidor.server_close()


if __name__ == '__main__':
    main()
