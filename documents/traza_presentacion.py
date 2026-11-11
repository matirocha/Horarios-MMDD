#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera la traza real que reproduce documents/Presentacion_Algoritmos_Generador.html
(bloque <script id="traza">) con el motor actual de notebooks/horarios:

  - la construcción voraz con la semilla 3, sesión por sesión (y los candidatos de cada
    sesión de 1° básico B);
  - la búsqueda tabú iterada (ITS, método por defecto) desde esa solución, paso a paso;
  - la curva de la búsqueda local iterada (ILS) desde la misma solución inicial;
  - la comparación de ILS e ITS con 10 semillas (notebooks/resultados/*.csv).

Uso (desde la raíz del repositorio):
    python documents/traza_presentacion.py

Reescribe solo el bloque de datos de la presentación; el resto del HTML no cambia. Las
búsquedas se repiten aquí con copias instrumentadas de ILS e ITS que consumen el generador
aleatorio igual que las originales, y el script comprueba que llegan al mismo horario.
"""

import csv
import glob
import json
import os
import random
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, os.path.join(RAIZ, 'notebooks'))
sys.path.insert(0, os.path.join(RAIZ, 'Prototipos', 'Prototipo 2'))

from horarios import DatosColegio as D, ModeloHorario, MotorHorarios  # noqa: E402
from horarios.heuristicas import ConstruccionVoraz  # noqa: E402
from horarios.mejora import Seguimiento  # noqa: E402
from horarios.metaheuristicas import BusquedaLocalIterada, BusquedaTabuIterada  # noqa: E402
from horarios.metaheuristicas.busqueda_tabu_iterada import ListaTabu  # noqa: E402
from horarios.metaheuristicas.vecindario import mejor_movimiento, sesiones_movidas, vecindario  # noqa: E402
from exportar_datos import nombre_legible  # noqa: E402

PRESENTACION = os.path.join(AQUI, 'Presentacion_Algoritmos_Generador.html')
SEMILLA = 3
CURSO_EJEMPLO = '1° BÁSICO B'
DIAS_CORTOS = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes']


def celda(x):
    dia, b = x
    return D.DIAS.index(dia) * 10 + b - 1


def celdas(xs):
    return [celda(x) for x in xs]


def plano(mapa, primero=()):
    """
    {(dia, b): (dia, b)} -> [origen, destino, origen, destino, ...] con celdas codificadas.
    Las celdas de 'primero' (las de la sesión principal del paso) van al comienzo: la
    presentación lee en mov[0] -> mov[1] hacia dónde va esa sesión.
    """
    items = sorted(mapa.items(), key=lambda xy: (xy[0] not in primero, xy[0]))
    return [v for x, y in items for v in (celda(x), celda(y))]


# ----------------------------------------------------------------------
# Construcción voraz instrumentada (mismo orden y mismo consumo del azar que ConstruccionVoraz)
# ----------------------------------------------------------------------
def construir(modelo, rng, sids_ejemplo):
    carga = D.carga_docente()
    orden = sorted(modelo.movibles(), key=lambda i: (
        -modelo.ses[i]['largo'],
        -len(modelo.ses[i]['docs']),
        -max(carga[d] for d in modelo.ses[i]['docs']),
        modelo.ses[i]['zona'] is None,
        rng.random(),
    ))
    con, cb = [], {}
    for sid in orden:
        s = modelo.ses[sid]
        c = s['curso']
        if s['largo'] == 2:
            opciones = [par for par in modelo.pares_de(c) if modelo.libre(c, par)]
        else:
            opciones = [(x,) for x, v in modelo.celda[c].items() if v is None]
        mejor, mejor_delta, revisadas = None, None, len(opciones)
        rng.shuffle(opciones)
        todas = []
        for k, cel in enumerate(opciones):
            delta = modelo.registrar(sid, cel, +1)
            modelo.registrar(sid, cel, -1)
            todas.append([celdas(cel), delta])
            if mejor is None or (revisadas == len(opciones) and delta < mejor_delta):
                mejor, mejor_delta = cel, delta
                if delta == 0:
                    revisadas = k + 1   # la construcción se detiene aquí; el resto solo se muestra
        if sid in sids_ejemplo:
            cb[len(con)] = {'c': todas, 'r': revisadas}
        con.append([sid, celdas(mejor)])
        modelo.ubicar(sid, mejor)
    return con, cb


# ----------------------------------------------------------------------
# ITS instrumentada: registra cada movimiento (copia de BusquedaTabuIterada)
# ----------------------------------------------------------------------
def texto_clave(modelo, k, idx_asig):
    t = k[0]
    if t == 'D':
        return f"D({k[1]}, {DIAS_CORTOS[D.DIAS.index(k[2])]} {k[3]})"
    if t == 'F':
        return f"F({nombre_legible(k[1])}, {DIAS_CORTOS[D.DIAS.index(k[2])]}, {idx_asig[k[3]][2]})"
    if t == 'G':
        return f"G({DIAS_CORTOS[D.DIAS.index(k[1])]} {k[2]})"
    return f"R(English skills, {DIAS_CORTOS[D.DIAS.index(k[2])]} {k[3]})"


def clave_principal(modelo, movidas):
    """Sesión movida que está en una violación y la clave violada que la incluye (D, F, G y R, en ese orden)."""
    for tipo in 'DFGR':
        for sid, _ in movidas:
            for k in modelo.claves_sesion(sid, modelo.pos[sid]):
                if k[0] == tipo and k in modelo.malos:
                    return sid, k
    return movidas[0][0], None


class ITSTraza(BusquedaTabuIterada):
    def __init__(self, idx_asig, **kw):
        super().__init__(**kw)
        self.idx_asig = idx_asig
        self.pasos = []

    def busqueda_tabu(self, modelo, rng, seg, paso):
        tabu = ListaTabu(self.tabu_min, self.tabu_rango)
        mejor_costo, mejor_pos = modelo.costo, dict(modelo.pos)
        sin_mejora = 0
        motivo = None
        while sin_mejora < self.largo_tabu:
            motivo = self.parada_comun(modelo, seg)
            if motivo is None and paso >= self.max_pasos:
                motivo = 'max_pasos'
            if motivo:
                break
            descartados = [0]

            def admisible(c, mapa, delta, paso=paso):
                if modelo.costo + delta < seg.mejor_costo:
                    return True
                ok = not any(tabu.es_tabu(sid, destino, paso) for sid, destino in sesiones_movidas(modelo, c, mapa))
                descartados[0] += not ok
                return ok

            candidatos = vecindario(modelo, self.vecindario)
            elegido, delta = mejor_movimiento(modelo, candidatos, rng, admisible)
            if elegido is None:
                break
            movidas = sesiones_movidas(modelo, *elegido)
            sid, k = clave_principal(modelo, movidas)
            origenes = [(s, modelo.pos[s]) for s, _ in movidas]
            mov = plano(elegido[1], modelo.pos[sid])
            modelo.mover(*elegido)
            for s, origen in origenes:
                tabu.prohibir(s, origen, paso, rng)
            hasta = tabu.hasta[(sid, dict(origenes)[sid])]
            self.pasos.append([sid, 0, mov, delta, modelo.costo, modelo.duras, len(candidatos),
                               descartados[0], hasta, texto_clave(modelo, k, self.idx_asig) if k else '—'])
            seg.registrar(paso, modelo)
            paso += 1
            if modelo.costo < mejor_costo:
                mejor_costo, mejor_pos, sin_mejora = modelo.costo, dict(modelo.pos), 0
            else:
                sin_mejora += 1
        if modelo.costo > mejor_costo:
            raise RuntimeError('La búsqueda tabú volvió a una solución anterior: la traza no se podría reproducir paso a paso')
        return paso, motivo

    def _buscar(self, modelo, rng, seg):
        resultado = super()._buscar(modelo, rng, seg)
        if resultado['iteraciones']:
            raise RuntimeError('ITS necesitó perturbar con esta semilla: la reproducción paso a paso no lo contempla')
        return resultado


# ----------------------------------------------------------------------
# ILS instrumentada: violaciones duras tras cada movimiento (copia de BusquedaLocalIterada)
# ----------------------------------------------------------------------
class ILSTraza(BusquedaLocalIterada):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.curva = []   # [violaciones duras, tipo]: 0 descenso, 1 perturbación, 2 rechazo (vuelve a la actual)

    def busqueda_local(self, modelo, rng, seg, paso):
        laterales = 0
        while True:
            motivo = self.parada_comun(modelo, seg)
            if motivo is None and paso >= self.max_pasos:
                motivo = 'max_pasos'
            if motivo:
                return paso, motivo
            elegido, delta = mejor_movimiento(modelo, vecindario(modelo, self.vecindario), rng)
            if elegido is None or delta > 0 or (delta == 0 and laterales >= self.laterales):
                return paso, None
            laterales = laterales + 1 if delta == 0 else 0
            modelo.mover(*elegido)
            self.curva.append([modelo.duras, 0])
            seg.registrar(paso, modelo)
            paso += 1

    def _buscar(self, modelo, rng, seg):
        from horarios.metaheuristicas.vecindario import perturbar
        paso, motivo = self.busqueda_local(modelo, rng, seg, 0)
        actual_pos, actual_costo = dict(modelo.pos), modelo.costo
        iteraciones = aceptadas = 0
        while motivo is None:
            iteraciones += 1
            perturbar(modelo, rng, self.perturbaciones)
            self.curva.append([modelo.duras, 1])
            seg.registrar(paso, modelo)
            paso, motivo = self.busqueda_local(modelo, rng, seg, paso)
            if modelo.costo <= actual_costo:
                actual_pos, actual_costo = dict(modelo.pos), modelo.costo
                aceptadas += 1
            elif motivo is None:
                modelo.restaurar(actual_pos)
                self.curva.append([modelo.duras, 2])
        return {'pasos': paso, 'motivo_parada': motivo, 'iteraciones': iteraciones, 'aceptadas': aceptadas}


def comparacion():
    """Resultados de notebooks/resultados/comparacion_ils_its_*.csv (el más reciente)."""
    archivos = sorted(glob.glob(os.path.join(RAIZ, 'notebooks', 'resultados', 'comparacion_ils_its_*.csv')))
    if not archivos:
        return None
    filas = list(csv.DictReader(open(archivos[-1], encoding='utf-8')))
    datos = {}
    for f in filas:
        datos.setdefault(f['metaheuristica'], []).append([
            int(f['semilla']), float(f['t_busqueda_ms']), int(f['pasos']), int(f['iteraciones'] or 0),
            int(f['duras_construccion']), f['factible'] == 'True', int(f['ventanas_docentes'])])
    return {'archivo': os.path.basename(archivos[-1]), 'metodos': datos}


def main():
    html = open(PRESENTACION, encoding='utf-8').read()
    bloque = re.search(r'(<script id="traza" type="application/json">)(.*?)(</script>)', html, re.S)
    anterior = json.loads(bloque.group(2))

    cursos = D.todos_los_cursos()
    idx_curso = {c: i for i, c in enumerate(cursos)}
    carga = D.carga_docente()
    P = sorted(carga)
    idx_doc = {p: i for i, p in enumerate(P)}
    A = [list(a) for a in anterior['A']]   # asignaturas con su color y sigla (no cambian)
    idx_a = {a[0]: i for i, a in enumerate(A)}
    for k in (1, 2, 3):
        idx_a[f'Formación Diferenciada · Franja {k}'] = idx_a[f'Electivos · franja {k}']
    idx_asig = {a[0]: a for a in A}

    # Construcción
    rng = random.Random(SEMILLA)
    modelo = ModeloHorario()
    ejemplo = {i for i, s in enumerate(modelo.ses) if s['curso'] == CURSO_EJEMPLO}
    con, cb = construir(modelo, rng, ejemplo)
    z0, v0 = modelo.costo, modelo.duras

    # Comprobación: la construcción instrumentada coincide con ConstruccionVoraz
    m2 = ModeloHorario()
    ConstruccionVoraz().construir(m2, random.Random(SEMILLA))
    assert m2.pos == modelo.pos and m2.costo == z0, 'La construcción instrumentada no coincide con ConstruccionVoraz'

    S = []
    for s in modelo.ses:
        fija = s['fijo']
        cs = [idx_curso[f"{s['nivel']} {sec}"] for sec in ('A', 'B')] if fija else None
        fila = [-1 if fija else idx_curso[s['curso']], idx_a[s['asig']], [idx_doc[p] for p in s['docs']],
                -1 if s['fam'] is None else idx_a[s['fam']],
                {None: 0, 'GIMNASIO A': 1, 'GIMNASIO B': 2}[s['zona']], 1 if s['recurso'] else 0, s['largo'], 1 if fija else 0]
        if fija:
            fila.append(cs)
        S.append(fila)
    FX = {str(i): celdas(modelo.pos[i]) for i, s in enumerate(modelo.ses) if s['fijo']}

    # ITS desde la solución de la construcción (mismo generador aleatorio, como MotorHorarios)
    its = ITSTraza(idx_asig, max_pasos=150000)
    pos_ini = dict(modelo.pos)
    res_its = its.buscar(modelo, rng)
    assert modelo.costo == 0, 'ITS no llegó a costo 0'
    real = MotorHorarios(seed=SEMILLA, metaheuristica='its')
    real.generar()
    assert real.modelo.pos == modelo.pos, 'La ITS instrumentada no llega al mismo horario que MotorHorarios'

    # ILS desde la misma solución inicial (generador en el mismo estado que tras la construcción)
    rng_ils = random.Random(SEMILLA)
    m_ils = ModeloHorario()
    ConstruccionVoraz().construir(m_ils, rng_ils)
    assert m_ils.pos == pos_ini
    ils = ILSTraza(max_pasos=150000)
    res_ils = ils.buscar(m_ils, rng_ils)
    real_ils = MotorHorarios(seed=SEMILLA, metaheuristica='ils')
    real_ils.generar()
    assert real_ils.modelo.pos == m_ils.pos, 'La ILS instrumentada no llega al mismo horario que MotorHorarios'

    malla = D.get_malla_curricular()[CURSO_EJEMPLO]
    traza = {
        'seed': SEMILLA,
        'metodo': 'its',
        'C': [[c, nombre_legible(c), list(D.JORNADAS[c])] for c in cursos],
        'P': P,
        'A': A,
        'S': S,
        'FX': FX,
        'CON': con,
        'CB': {str(k): v for k, v in cb.items()},
        'BUS': its.pasos,
        'ILS': {'curva': ils.curva, 'pasos': res_ils['pasos'], 'iteraciones': res_ils['iteraciones'],
                'aceptadas': res_ils['aceptadas']},
        'FR': {nivel: [{'p': [celda(x) for x in f['periodos']],
                        'g': [[g[0].capitalize(), g[1], g[2], g[3].capitalize()] for g in f['grupos']]}
                       for f in franjas]
               for nivel, franjas in D.FRANJAS_ELECTIVOS.items()},
        'MALLA': {CURSO_EJEMPLO: [[idx_a[a], h, [idx_doc[p] for p in D.docentes_de(doc)], e] for a, h, doc, e in malla
                                  if not a.startswith('Formación Diferenciada')]},
        'carga': [carga[p] for p in P],
        'z0': z0,
        'v0': v0,
        'fin': 'costo0',
        'COMP': comparacion(),
    }
    texto = json.dumps(traza, ensure_ascii=False, separators=(',', ':'))
    html = html[:bloque.start(2)] + texto + html[bloque.end(2):]
    open(PRESENTACION, 'w', encoding='utf-8').write(html)
    print(f"Traza escrita: construcción {v0} violaciones (z0 = {z0}); ITS {len(its.pasos)} pasos "
          f"({res_its['iteraciones']} perturbaciones); ILS {res_ils['pasos']} pasos y {res_ils['iteraciones']} perturbaciones.")


if __name__ == '__main__':
    main()
