#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
MODELO MATEMÁTICO DEL HORARIO ESCOLAR MMDD (programación lineal entera, PLE)
===============================================================================

Formulación exacta del mismo problema que resuelven las heurísticas y metaheurísticas
de horarios/. Usa la misma instancia (ModeloHorario: datos 2026, sesiones dobles y
simples, electivos fijos), así que sus resultados se pueden comparar directamente:
una solución del modelo cumple todas las restricciones duras, igual que un horario
con costo 0 de las metaheurísticas.

CONJUNTOS
  C            cursos (24 regulares C_R y 3 de párvulos C_P).
  D            días (lunes a viernes);  B = {1..10} bloques de 45 min.
  X_c          celdas (d, b) de la jornada del curso c no ocupadas por electivos fijos.
  P_c          pares pedagógicos p = {(d,b), (d,b+1)} con b impar, ambos en X_c.
  L            lecciones (curso, asignatura, docentes, espacio); L_c las del curso c.
  T            docentes;  T_l los docentes de la lección l (dos o más si hay co-docencia).
  Fam_c        familias de asignaturas del curso c (English skills cuenta como Inglés).
  G            gimnasios {A, B};  L^g las lecciones de Ed. Física que van al gimnasio g.
  L^EI         lecciones de English skills (sala Electivo 1, capacidad 1).

PARÁMETROS
  n2_l, n1_l   sesiones dobles y simples de la lección l: n2 = floor(h/2), n1 = h mod 2
               (párvulos: n2 = 0, n1 = h).
  F_tdb        1 si el docente t dicta un electivo fijo en (d,b) (franjas de 3° y 4° medio).
  w_V          peso de las ventanas docentes (0 por defecto).

VARIABLES
  y_lp ∈ {0,1}   la lección l tiene una sesión doble en el par p ∈ P_c(l).
  z_lx ∈ {0,1}   la lección l tiene una sesión simple en la celda x ∈ X_c(l).
  a, e, v ≥ 0    (solo si w_V > 0) auxiliares de las ventanas docentes, ver (R7).

  Ocupación (expresión):  o_lx = Σ_{p ∈ P_c: x ∈ p} y_lp + z_lx

FUNCIÓN OBJETIVO
  min  w_V · Σ_{t,d,b} v_tdb

  Las restricciones duras van como restricciones (no como penalización). Con w_V = 0
  (por defecto) el objetivo es constante y el modelo solo busca un horario factible,
  igual que las metaheurísticas, que minimizan f = 1000·(violaciones duras): f = 0
  equivale a una solución del modelo. Con w_V > 0 minimiza además las ventanas.

RESTRICCIONES
  (R1) Carga horaria:        Σ_p y_lp = n2_l   y   Σ_x z_lx = n1_l        ∀ l
  (R2) Jornada completa:     Σ_{l ∈ L_c} o_lx = 1   ∀ c ∈ C_R, x ∈ X_c   (≤ 1 en párvulos)
  (R3) Una sesión diaria por asignatura:
                             Σ_{l ∈ L_c, fam(l)=f} ( Σ_{p del día d} y_lp + Σ_{x del día d} z_lx ) ≤ 1
                                                                          ∀ c, f, d
  (R4) Docente sin choques:  Σ_{l: t ∈ T_l} o_l(d,b) ≤ 1 − F_tdb          ∀ t, d, b
  (R5) Sala English skills:  Σ_{l ∈ L^EI} o_l(d,b) ≤ 1                    ∀ d, b
  (R6) Recintos deportivos:  Σ_{l ∈ L^g} o_l(d,b) ≤ 1                    ∀ g, d, b
  (R7) Ventanas docentes (opcional): con x_tdb = Σ_{l: t ∈ T_l} o_l(d,b) + F_tdb,
                             a_tdb ≥ x_tdb,  a_tdb ≥ a_td(b-1)   (ya empezó su jornada)
                             e_tdb ≥ x_tdb,  e_tdb ≥ e_td(b+1)   (aún le quedan clases)
                             v_tdb ≥ a_tdb + e_tdb − 1 − x_tdb    (bloque libre entre clases)

  Se cumplen por construcción de los conjuntos y parámetros: la asignación docente
  oficial y la jefatura (T_l viene de la distribución 2026), los bloques dobles dentro
  de un par pedagógico (y_lp solo existe para pares), las franjas de electivos
  sincronizadas en A y B (fijas, fuera de X_c) y los bloqueos de pastoral (salas de
  los electivos fijos).

FRANJAS MÓVILES (--franjas-moviles, o DatosColegio.FRANJAS_FIJAS = False)
  Cada franja de electivos pasa a ser una lección de 3 sesiones dobles compartida por A y B:
  sus variables y_lp van sobre los pares comunes a ambos cursos, ocupa las celdas de los dos
  en (R2), tiene una sesión por día en (R3) y sus docentes entran en (R4) (F_tdb = 0).

MODO ELÁSTICO (--elastico)
  Agrega una holgura entera s ≥ 0 a (R3), (R4), (R5) y (R6) y minimiza 1000 · Σ s, que es la
  misma función objetivo f(x) de las metaheurísticas. El óptimo es la menor cantidad de
  violaciones duras posible: 0 si la instancia es factible y, si no, cuántas son inevitables y
  dónde (holguras positivas). Lo usa el Prototipo 2 para avisar cuándo una edición de los datos
  impide armar un horario factible.

GUROBI
  --solver GUROBI usa gurobipy directamente (no a través de OR-Tools, que en algunos equipos no
  carga la biblioteca de Gurobi 13). La licencia es la del equipo (gurobi.lic) o, en un servidor,
  una licencia WLS en las variables de entorno GRB_WLSACCESSID, GRB_WLSSECRET y GRB_LICENSEID.

USO (requiere: pip install ortools; para Gurobi, pip install gurobipy)
  python notebooks/modelo_matematico.py                         # CP-SAT, busca un horario factible
  python notebooks/modelo_matematico.py --solver GUROBI         # Gurobi (gurobipy)
  python notebooks/modelo_matematico.py --elastico              # menor cantidad de violaciones duras
  python notebooks/modelo_matematico.py --hilos 1               # 1 hilo: comparable con las metaheurísticas
  python notebooks/modelo_matematico.py --solver SCIP --tiempo-max 600     # solver MIP clásico
  python notebooks/modelo_matematico.py --peso-ventanas 1 --tiempo-max 120 # + ventanas docentes
  python notebooks/modelo_matematico.py --lp modelo.lp           # exporta el modelo en formato LP
  python notebooks/modelo_matematico.py --excel "Outputs Modelo"  # Excel del horario obtenido

  Tiempos de referencia (4 núcleos, datos 2026, w_V = 0): CP-SAT ≈ 0,4 s
  (≈ 0,8 s con 1 hilo), HiGHS ≈ 0,4 s, SCIP ≈ 46 s; todos encuentran un horario factible.
  Con --peso-ventanas 1 --tiempo-max 120, CP-SAT llega a 2 ventanas docentes (cota inferior 1).
"""

import argparse
import os
import tempfile
import time
from collections import defaultdict

from horarios import DatosColegio, ExportadorExcel, ModeloHorario, ValidadorRestricciones

SOLVERS = ['CP-SAT', 'SCIP', 'CBC', 'HIGHS', 'GUROBI']

_entorno_gurobi = None   # un solo entorno (y una sola sesión de licencia) por proceso


def credenciales_wls():
    """
    Credenciales WLS de Gurobi en variables de entorno, con los mismos nombres que tienen en
    gurobi.lic (WLSACCESSID, WLSSECRET, LICENSEID) o con el prefijo GRB_. Así, en Vercel basta
    con pegar el contenido de gurobi.lic en Environment Variables. None si falta alguna.
    """
    wls = {clave: (os.environ.get(f'GRB_{clave}') or os.environ.get(clave) or '').strip()
           for clave in ('WLSACCESSID', 'WLSSECRET', 'LICENSEID')}
    return wls if all(wls.values()) else None


def entorno_gurobi():
    """
    Entorno de Gurobi, creado una vez. Usa las credenciales WLS de las variables de entorno si
    están (ver credenciales_wls; así se configura en un servidor como Vercel, sin subir el
    archivo de licencia) o, si no, la licencia del equipo (gurobi.lic).
    """
    global _entorno_gurobi
    if _entorno_gurobi is None:
        import gurobipy as gp
        env = gp.Env(empty=True)
        env.setParam('OutputFlag', 0)
        wls = credenciales_wls()
        if wls:
            env.setParam('WLSACCESSID', wls['WLSACCESSID'])
            env.setParam('WLSSECRET', wls['WLSSECRET'])
            env.setParam('LICENSEID', int(wls['LICENSEID']))
        env.start()
        _entorno_gurobi = env
    return _entorno_gurobi


class SolverGurobi:
    """
    Gurobi (gurobipy) con la misma interfaz de pywraplp que usa este archivo, para que el
    modelo se escriba una sola vez. Los estados tienen los mismos valores que pywraplp.
    """

    OPTIMAL, FEASIBLE, INFEASIBLE, UNBOUNDED, ABNORMAL, NOT_SOLVED = 0, 1, 2, 3, 4, 6

    def __init__(self):
        try:
            import gurobipy as gp
        except ImportError as error:
            raise SystemExit("Falta gurobipy. Instálalo con:  pip install gurobipy") from error
        self.gp, self.GRB = gp, gp.GRB
        try:
            self.m = gp.Model('horario_mmdd', env=entorno_gurobi())
        except gp.GurobiError as error:
            raise SystemExit(f"Gurobi no pudo iniciar su licencia: {error}") from error

    def BoolVar(self, nombre):
        return self.m.addVar(vtype=self.GRB.BINARY, name=nombre)

    def IntVar(self, lb, ub, nombre):
        return self.m.addVar(lb=lb, ub=ub, vtype=self.GRB.INTEGER, name=nombre)

    def NumVar(self, lb, ub, nombre):
        return self.m.addVar(lb=lb, ub=ub, name=nombre)

    def Sum(self, terminos):
        return self.gp.quicksum(terminos)

    def Add(self, restriccion):
        return self.m.addConstr(restriccion)

    def Minimize(self, expresion):
        self.m.setObjective(expresion, self.GRB.MINIMIZE)

    def SetTimeLimit(self, milisegundos):
        self.m.Params.TimeLimit = milisegundos / 1000

    def EnableOutput(self):
        self.m.Params.OutputFlag = 1

    def SetNumThreads(self, hilos):
        self.m.Params.Threads = hilos

    def NumVariables(self):
        self.m.update()
        return self.m.NumVars

    def NumConstraints(self):
        self.m.update()
        return self.m.NumConstrs

    def Solve(self):
        try:
            self.m.optimize()
        except self.gp.GurobiError as error:   # p. ej. licencia limitada (modelo demasiado grande)
            raise SystemExit(f"Gurobi no pudo resolver: {error}") from error
        estado, GRB = self.m.Status, self.GRB
        if estado == GRB.OPTIMAL:
            return self.OPTIMAL
        if self.m.SolCount > 0:
            return self.FEASIBLE
        if estado in (GRB.INFEASIBLE, GRB.INF_OR_UNBD):
            return self.INFEASIBLE
        if estado == GRB.UNBOUNDED:
            return self.UNBOUNDED
        if estado in (GRB.TIME_LIMIT, GRB.INTERRUPTED, GRB.NODE_LIMIT, GRB.SOLUTION_LIMIT):
            return self.NOT_SOLVED
        return self.ABNORMAL

    def Objective(self):
        m = self.m

        class _Objetivo:
            Value = staticmethod(lambda: m.ObjVal)
            BestBound = staticmethod(lambda: m.ObjBound)
        return _Objetivo

    def ExportModelAsLpFormat(self, _obfuscado=False):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = os.path.join(carpeta, 'modelo.lp')
            self.m.write(ruta)
            with open(ruta, encoding='utf-8') as archivo:
                return archivo.read()


def valor(variable):
    """Valor de una variable en la solución (OR-Tools o Gurobi)."""
    return variable.solution_value() if hasattr(variable, 'solution_value') else variable.X


class ModeloMatematico:
    """Construye el modelo de programación entera, lo resuelve y valida la solución."""

    def __init__(self, solver='CP-SAT', peso_ventanas=0, elastico=False):
        self.nombre_solver = solver.upper()
        if self.nombre_solver == 'GUROBI':
            self.solver = SolverGurobi()
        else:
            try:
                from ortools.linear_solver import pywraplp
            except ImportError as error:
                raise SystemExit("Falta OR-Tools. Instálalo con:  pip install ortools") from error
            self.solver = pywraplp.Solver.CreateSolver(self.nombre_solver)
            if self.solver is None:
                raise SystemExit(f"El solver '{solver}' no está disponible en esta instalación de OR-Tools. "
                                 f"Prueba con: {', '.join(SOLVERS[:4])}")
        self.peso_ventanas = peso_ventanas
        self.elastico = elastico
        self.holguras = []   # modo elástico: (restricción, clave, variable de holgura)

        t0 = time.perf_counter()
        self.instancia = ModeloHorario()   # mismos datos y sesiones que usan las metaheurísticas
        self._conjuntos()
        self._variables()
        self._restricciones()
        self._objetivo()
        self.t_construccion = time.perf_counter() - t0
        self.resultado = {}

    # ------------------------------------------------------------------
    # Conjuntos y parámetros
    # ------------------------------------------------------------------
    def _conjuntos(self):
        inst = self.instancia
        # Lecciones: sesiones movibles agrupadas por (curso, asignatura, docentes, espacio)
        self.lecciones = []
        indice = {}
        for sid, s in enumerate(inst.ses):
            if s['fijo']:
                continue
            clave = (s['curso'], s['asig'], s['docs'], s['espacio'])
            if clave not in indice:
                indice[clave] = len(self.lecciones)
                self.lecciones.append({'curso': s['curso'], 'asig': s['asig'], 'fam': s['fam'], 'docs': s['docs'],
                                       'zona': s['zona'], 'recurso': s['recurso'], 'dobles': [], 'simples': []})
            leccion = self.lecciones[indice[clave]]
            (leccion['dobles'] if s['largo'] == 2 else leccion['simples']).append(sid)

        # F_tdb: bloques de los electivos fijos de cada docente
        self.fijo = defaultdict(int)
        for sid, s in enumerate(inst.ses):
            if s['fijo']:
                for x in inst.pos[sid]:
                    for t in s['docs']:
                        self.fijo[(t, x)] += 1

    # ------------------------------------------------------------------
    # Variables
    # ------------------------------------------------------------------
    def _variables(self):
        inst, sv = self.instancia, self.solver
        self.y, self.z = {}, {}
        self.ocupa = defaultdict(list)   # (l, celda) -> variables cuya suma es o_lx
        for l, lec in enumerate(self.lecciones):
            c = lec['curso']   # tupla (A, B) en una franja móvil: pares comunes a ambos cursos
            if lec['dobles']:
                for k, par in enumerate(inst.pares_de(c)):
                    self.y[(l, par)] = sv.BoolVar(f'y_{l}_{k}')
                    for x in par:
                        self.ocupa[(l, x)].append(self.y[(l, par)])
            if lec['simples']:
                for k, x in enumerate(inst.celda[c]):
                    self.z[(l, x)] = sv.BoolVar(f'z_{l}_{k}')
                    self.ocupa[(l, x)].append(self.z[(l, x)])

        # Ocupación agregada por docente, sala de capacidad limitada y gimnasio
        self.uso_docente = defaultdict(list)   # (t, celda) -> variables
        self.uso_recurso = defaultdict(list)   # (sala, celda) -> variables
        self.uso_zona = defaultdict(list)      # (gimnasio, celda) -> variables
        for (l, x), variables in self.ocupa.items():
            lec = self.lecciones[l]
            for t in lec['docs']:
                self.uso_docente[(t, x)] += variables
            if lec['recurso']:
                self.uso_recurso[(lec['recurso'], x)] += variables
            if lec['zona']:
                self.uso_zona[(lec['zona'], x)] += variables

    # ------------------------------------------------------------------
    # Restricciones
    # ------------------------------------------------------------------
    def _restricciones(self):
        inst, sv = self.instancia, self.solver
        suma = sv.Sum

        # (R1) Carga horaria
        for l, lec in enumerate(self.lecciones):
            c = lec['curso']
            if lec['dobles']:
                sv.Add(suma(self.y[(l, p)] for p in inst.pares_de(c)) == len(lec['dobles']))
            if lec['simples']:
                sv.Add(suma(self.z[(l, x)] for x in inst.celda[c]) == len(lec['simples']))

        # (R2) Jornada completa: una actividad en cada celda del curso (una franja móvil cuenta en A y en B)
        lecciones_curso = defaultdict(list)
        for l, lec in enumerate(self.lecciones):
            for c in ModeloHorario.como_tupla(lec['curso']):
                lecciones_curso[c].append(l)
        for c in inst.cursos:
            for x in inst.celda[c]:
                ocupacion = suma(v for l in lecciones_curso[c] for v in self.ocupa[(l, x)])
                sv.Add(ocupacion <= 1 if DatosColegio.es_parvulo(c) else ocupacion == 1)

        # (R3) Una sesión diaria por asignatura (familia); una franja móvil, una vez (en su curso A)
        for c in inst.cursos:
            familias = defaultdict(list)
            for l in lecciones_curso[c]:
                propio = self.lecciones[l]['curso']
                if isinstance(propio, tuple) and c != propio[0]:
                    continue
                familias[self.lecciones[l]['fam']].append(l)
            for fam, ls in familias.items():
                if sum(len(self.lecciones[l]['dobles']) + len(self.lecciones[l]['simples']) for l in ls) < 2:
                    continue
                for d in DatosColegio.DIAS:
                    sesiones_dia = [self.y[(l, p)] for l in ls for p in inst.pares[c] if (l, p) in self.y and p[0][0] == d]
                    sesiones_dia += [self.z[(l, x)] for l in ls for x in inst.celda[c] if (l, x) in self.z and x[0] == d]
                    if len(sesiones_dia) > 1:
                        sv.Add(suma(sesiones_dia) <= 1 + self._holgura('R3', (c, fam, d), len(sesiones_dia)))

        # (R4) Docente sin choques (descontando sus electivos fijos)
        for (t, x), variables in self.uso_docente.items():
            sv.Add(suma(variables) <= 1 - self.fijo[(t, x)]
                   + self._holgura('R4', (t, x), len(variables) + self.fijo[(t, x)]))

        # (R5) Salas de capacidad limitada (English skills)
        for (sala, x), variables in self.uso_recurso.items():
            sv.Add(suma(variables) <= DatosColegio.RECURSOS_CAPACIDAD[sala]
                   + self._holgura('R5', (sala, x), len(variables)))

        # (R6) Recintos deportivos: un curso por gimnasio
        for (g, x), variables in self.uso_zona.items():
            if len(variables) > 1:
                sv.Add(suma(variables) <= 1 + self._holgura('R6', (g, x), len(variables)))

        # (R7) Ventanas docentes (solo si se ponderan en el objetivo)
        self.v = []
        if self.peso_ventanas > 0:
            self._ventanas()

    def _ventanas(self):
        sv = self.solver
        entero = self.nombre_solver in ('CP-SAT', 'SAT')   # CP-SAT solo admite variables enteras
        nueva = (lambda n: sv.IntVar(0, 1, n)) if entero else (lambda n: sv.NumVar(0, 1, n))
        docentes = sorted({t for t, _ in self.uso_docente} | {t for t, _ in self.fijo})
        bloques = sorted(DatosColegio.HORARIOS_BLOQUES)
        for i, t in enumerate(docentes):
            for j, d in enumerate(DatosColegio.DIAS):
                x = {b: self.solver.Sum(self.uso_docente.get((t, (d, b)), [])) + self.fijo.get((t, (d, b)), 0)
                     for b in bloques}
                activos = [b for b in bloques if self.uso_docente.get((t, (d, b))) or self.fijo.get((t, (d, b)))]
                if len(activos) < 2:
                    continue   # con menos de dos bloques posibles no puede haber ventanas
                rango = range(activos[0], activos[-1] + 1)
                a = {b: nueva(f'a_{i}_{j}_{b}') for b in rango}
                e = {b: nueva(f'e_{i}_{j}_{b}') for b in rango}
                for b in rango:
                    sv.Add(a[b] >= x[b])
                    sv.Add(e[b] >= x[b])
                    if b - 1 in a:
                        sv.Add(a[b] >= a[b - 1])
                    if b + 1 in e:
                        sv.Add(e[b] >= e[b + 1])
                    if activos[0] < b < activos[-1]:
                        v = nueva(f'v_{i}_{j}_{b}')
                        sv.Add(v >= a[b] + e[b] - 1 - x[b])
                        self.v.append(v)

    def _holgura(self, restriccion, clave, tope):
        """Modo elástico: holgura entera de una restricción dura (0 en el modo normal)."""
        if not self.elastico:
            return 0
        s = self.solver.IntVar(0, tope, f's_{restriccion}_{len(self.holguras)}')
        self.holguras.append((restriccion, clave, s))
        return s

    def _objetivo(self):
        sv = self.solver
        objetivo = self.peso_ventanas * sv.Sum(self.v)
        if self.elastico:   # f(x) de las metaheurísticas: 1000 por cada violación dura
            objetivo = objetivo + ModeloHorario.PESO_DURO * sv.Sum(s for _, _, s in self.holguras)
        sv.Minimize(objetivo)

    def holguras_activas(self):
        """Modo elástico: [(restricción, clave, violaciones)] de la solución encontrada."""
        return [(r, clave, round(valor(s))) for r, clave, s in self.holguras if valor(s) > 0.5]

    # ------------------------------------------------------------------
    # Resolución
    # ------------------------------------------------------------------
    def resolver(self, tiempo_max=None, mostrar_log=False, hilos=None):
        """Resuelve el modelo y retorna un diccionario con estado, objetivo, cota, gap y tiempos."""
        sv = self.solver
        if tiempo_max:
            sv.SetTimeLimit(int(tiempo_max * 1000))
        if mostrar_log:
            sv.EnableOutput()
        if hilos:
            sv.SetNumThreads(hilos)
        t0 = time.perf_counter()
        estado = sv.Solve()
        t_resolucion = time.perf_counter() - t0
        # Los estados son atributos del solver (pywraplp.Solver o SolverGurobi, con los mismos valores)
        nombres = {sv.OPTIMAL: 'óptimo', sv.FEASIBLE: 'factible (sin probar optimalidad)',
                   sv.INFEASIBLE: 'infactible', sv.UNBOUNDED: 'no acotado',
                   sv.ABNORMAL: 'error del solver', sv.NOT_SOLVED: 'sin solución en el tiempo dado'}
        con_solucion = estado in (sv.OPTIMAL, sv.FEASIBLE)
        objetivo = sv.Objective().Value() if con_solucion else None
        cota = sv.Objective().BestBound() if con_solucion else None
        gap = None
        if con_solucion:
            gap = 0.0 if abs(objetivo - cota) < 1e-6 else abs(objetivo - cota) / max(abs(objetivo), 1e-9)
        self.resultado = {
            'solver': self.nombre_solver,
            'estado': nombres.get(estado, str(estado)),
            'con_solucion': con_solucion,
            'objetivo': objetivo,
            'cota': cota,
            'gap': gap,
            'ventanas_modelo': round(sum(valor(v) for v in self.v)) if con_solucion and self.v else None,
            'violaciones_minimas': round(sum(valor(s) for _, _, s in self.holguras)) if con_solucion and self.elastico else None,
            'infactible': estado == sv.INFEASIBLE,
            'variables': sv.NumVariables(),
            'restricciones': sv.NumConstraints(),
            't_construccion': self.t_construccion,
            't_resolucion': t_resolucion,
        }
        return self.resultado

    def a_modelo_horario(self):
        """Carga la solución en un ModeloHorario (recalcula su costo incremental)."""
        inst = self.instancia
        pos = {sid: inst.pos[sid] for sid, s in enumerate(inst.ses) if s['fijo']}
        for l, lec in enumerate(self.lecciones):
            c = lec['curso']
            dobles = [p for p in inst.pares_de(c) if (l, p) in self.y and valor(self.y[(l, p)]) > 0.5]
            simples = ([(x,) for x in inst.celda[c] if (l, x) in self.z and valor(self.z[(l, x)]) > 0.5]
                       if lec['simples'] else [])
            for sid, celdas in zip(lec['dobles'], dobles):
                pos[sid] = celdas
            for sid, celdas in zip(lec['simples'], simples):
                pos[sid] = celdas
        inst.restaurar(pos)
        return inst

    def exportar_lp(self, ruta):
        with open(ruta, 'w', encoding='utf-8') as archivo:
            archivo.write(self.solver.ExportModelAsLpFormat(False))


def main():
    parser = argparse.ArgumentParser(description="Modelo de programación entera del horario MMDD (OR-Tools o Gurobi)")
    parser.add_argument('--solver', default='CP-SAT', choices=SOLVERS,
                        help="Solver (default: CP-SAT); GUROBI usa gurobipy directamente")
    parser.add_argument('--elastico', action='store_true',
                        help="Minimiza las violaciones duras en vez de exigir que no haya ninguna")
    parser.add_argument('--franjas-moviles', action='store_true',
                        help="El modelo elige los bloques de las franjas de electivos (por defecto quedan fijas)")
    parser.add_argument('--tiempo-max', type=float, default=300, help="Segundos máximos de resolución (default: 300)")
    parser.add_argument('--peso-ventanas', type=float, default=0,
                        help="Peso de las ventanas docentes; 0 = no se modelan (default: 0)")
    parser.add_argument('--hilos', type=int, default=None, help="Hilos del solver (default: los del solver)")
    parser.add_argument('--log', action='store_true', help="Muestra el registro del solver")
    parser.add_argument('--lp', type=str, help="Exporta el modelo a este archivo en formato LP")
    parser.add_argument('--excel', type=str, help="Carpeta donde exportar los Excel del horario obtenido")
    args = parser.parse_args()

    if args.franjas_moviles:
        DatosColegio.FRANJAS_FIJAS = False
    modelo = ModeloMatematico(args.solver, args.peso_ventanas, args.elastico)
    print(f"Modelo construido en {modelo.t_construccion:.2f} s: {modelo.solver.NumVariables()} variables, "
          f"{modelo.solver.NumConstraints()} restricciones, {len(modelo.lecciones)} lecciones.")
    if args.lp:
        modelo.exportar_lp(args.lp)
        print(f"Modelo exportado a {args.lp}")

    print(f"Resolviendo con {args.solver} (límite {args.tiempo_max:g} s)...")
    r = modelo.resolver(args.tiempo_max, args.log, args.hilos)
    print(f"\nEstado: {r['estado']}   tiempo de resolución: {r['t_resolucion']:.2f} s")
    if not r['con_solucion']:
        return
    print(f"Objetivo: {r['objetivo']:g}   cota inferior: {r['cota']:g}   gap: {r['gap'] * 100:.2f}%"
          + (f"   ventanas docentes: {r['ventanas_modelo']}" if r['ventanas_modelo'] is not None else ''))
    if args.elastico:
        print(f"Menor cantidad de violaciones duras encontrada: {r['violaciones_minimas']}")
        for restriccion, clave, n in modelo.holguras_activas()[:20]:
            print(f"  - {restriccion} {clave}: {n}")

    # Validación independiente: costo de la función objetivo de las metaheurísticas y auditoría
    instancia = modelo.a_modelo_horario()
    horario = instancia.a_horario()
    if args.franjas_moviles:   # la auditoría y los Excel usan los periodos que eligió el modelo
        instancia.aplicar_periodos_franjas()
        for nivel, franjas in instancia.periodos_franjas().items():
            for k, periodos in enumerate(franjas, 1):
                print(f"Franja {k} de {nivel}: " + ', '.join(f'{dia} {b}-{b + 1}' for dia, b in periodos))
    auditoria = ValidadorRestricciones.auditar(horario)
    m = auditoria['metricas']
    print(f"\nValidación con la función objetivo de las metaheurísticas: costo = {instancia.costo} "
          f"({instancia.duras} violaciones duras)")
    print(f"Auditoría: {'VÁLIDO' if auditoria['valido'] else 'CON ERRORES'} · "
          f"{m['total_bloques_asignados']}/{m['total_bloques_esperados']} bloques · "
          f"ventanas docentes {m['total_ventanas_docentes']} · bloques dobles {m['porcentaje_bloques_dobles']}%")
    for error in auditoria['errores_duros'][:10]:
        print(f"  - {error}")

    if args.excel:
        os.makedirs(args.excel, exist_ok=True)
        ExportadorExcel.exportar_horario_cursos(horario, os.path.join(args.excel, 'Horario_Cursos_Modelo.xlsx'))
        ExportadorExcel.exportar_horario_docentes(horario, os.path.join(args.excel, 'Horarios_Docentes_Modelo.xlsx'))
        print(f"\nExcel exportados en {args.excel}")


if __name__ == '__main__':
    main()
