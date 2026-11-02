#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
MODELO MATEMÁTICO DEL HORARIO ESCOLAR MMDD (programación lineal entera, PLE)
===============================================================================

Formulación exacta del mismo problema que resuelven las heurísticas y metaheurísticas
de horarios/. Usa la misma instancia (ModeloHorario: datos 2026, sesiones dobles y
simples, electivos fijos), así que sus resultados se pueden comparar directamente:
una solución del modelo cumple todas las restricciones duras y su objetivo es el
mismo costo blando que minimizan las metaheurísticas.

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
  w_P, w_V     pesos del uso del Patio Santo Domingo y de las ventanas docentes.

VARIABLES
  y_lp ∈ {0,1}   la lección l tiene una sesión doble en el par p ∈ P_c(l).
  z_lx ∈ {0,1}   la lección l tiene una sesión simple en la celda x ∈ X_c(l).
  u_gx ∈ {0,1}   el gimnasio g desborda un curso al Patio Santo Domingo en la celda x.
  a, e, v ≥ 0    (solo si w_V > 0) auxiliares de las ventanas docentes, ver (R7).

  Ocupación (expresión):  o_lx = Σ_{p ∈ P_c: x ∈ p} y_lp + z_lx

FUNCIÓN OBJETIVO
  min  w_P · Σ_{g,x} u_gx  +  w_V · Σ_{t,d,b} v_tdb

  Las restricciones duras van como restricciones (no como penalización). Por eso, si
  el modelo tiene solución, su objetivo con w_V = 0 es la cota inferior del costo
  f = 1000·(violaciones duras) + 1·(bloques en el patio) que minimizan las
  metaheurísticas: si una metaheurística llega a f = 0, su horario es óptimo.

RESTRICCIONES
  (R1) Carga horaria:        Σ_p y_lp = n2_l   y   Σ_x z_lx = n1_l        ∀ l
  (R2) Jornada completa:     Σ_{l ∈ L_c} o_lx = 1   ∀ c ∈ C_R, x ∈ X_c   (≤ 1 en párvulos)
  (R3) Una sesión diaria por asignatura:
                             Σ_{l ∈ L_c, fam(l)=f} ( Σ_{p del día d} y_lp + Σ_{x del día d} z_lx ) ≤ 1
                                                                          ∀ c, f, d
  (R4) Docente sin choques:  Σ_{l: t ∈ T_l} o_l(d,b) ≤ 1 − F_tdb          ∀ t, d, b
  (R5) Sala English skills:  Σ_{l ∈ L^EI} o_l(d,b) ≤ 1                    ∀ d, b
  (R6) Recintos deportivos:  Σ_{l ∈ L^g} o_l(d,b) ≤ 1 + u_g(d,b)          ∀ g, d, b
                             Σ_g u_g(d,b) ≤ 1  (el patio recibe un solo curso)
  (R7) Ventanas docentes (opcional): con x_tdb = Σ_{l: t ∈ T_l} o_l(d,b) + F_tdb,
                             a_tdb ≥ x_tdb,  a_tdb ≥ a_td(b-1)   (ya empezó su jornada)
                             e_tdb ≥ x_tdb,  e_tdb ≥ e_td(b+1)   (aún le quedan clases)
                             v_tdb ≥ a_tdb + e_tdb − 1 − x_tdb    (bloque libre entre clases)

  Se cumplen por construcción de los conjuntos y parámetros: la asignación docente
  oficial y la jefatura (T_l viene de la distribución 2026), los bloques dobles dentro
  de un par pedagógico (y_lp solo existe para pares), las franjas de electivos
  sincronizadas en A y B (fijas, fuera de X_c) y los bloqueos de pastoral (salas de
  los electivos fijos).

USO (requiere: pip install ortools)
  python notebooks/modelo_matematico.py                         # CP-SAT, minimiza el uso del patio
  python notebooks/modelo_matematico.py --hilos 1               # 1 hilo: comparable con las metaheurísticas
  python notebooks/modelo_matematico.py --solver SCIP --tiempo-max 600     # solver MIP clásico
  python notebooks/modelo_matematico.py --peso-ventanas 1 --tiempo-max 120 # + ventanas docentes
  python notebooks/modelo_matematico.py --lp modelo.lp           # exporta el modelo en formato LP
  python notebooks/modelo_matematico.py --excel "Outputs Modelo"  # Excel del horario obtenido

  Tiempos de referencia (4 núcleos, datos 2026, objetivo = patio): CP-SAT ≈ 0,4 s
  (≈ 15 s con 1 hilo), HiGHS ≈ 90 s, SCIP ≈ 255 s; todos llegan al óptimo (objetivo 0).
  Con --peso-ventanas 1, CP-SAT prueba en ≈ 20 s que el óptimo tiene 1 ventana docente.
"""

import argparse
import os
import time
from collections import defaultdict

from horarios import DatosColegio, ExportadorExcel, ModeloHorario, ValidadorRestricciones

SOLVERS = ['CP-SAT', 'SCIP', 'CBC', 'HIGHS', 'GUROBI']


class ModeloMatematico:
    """Construye el modelo de programación entera, lo resuelve y valida la solución."""

    def __init__(self, solver='CP-SAT', peso_patio=ModeloHorario.PESO_PATIO, peso_ventanas=0):
        try:
            from ortools.linear_solver import pywraplp
        except ImportError as error:
            raise SystemExit("Falta OR-Tools. Instálalo con:  pip install ortools") from error
        self.pywraplp = pywraplp
        self.nombre_solver = solver.upper()
        self.solver = pywraplp.Solver.CreateSolver(self.nombre_solver)
        if self.solver is None:
            raise SystemExit(f"El solver '{solver}' no está disponible en esta instalación de OR-Tools. "
                             f"Prueba con: {', '.join(SOLVERS[:4])}")
        self.peso_patio = peso_patio
        self.peso_ventanas = peso_ventanas

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
            c = lec['curso']
            if lec['dobles']:
                for k, par in enumerate(inst.pares[c]):
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

        self.u = {(g, x): sv.BoolVar(f'u_{g[-1]}_{DatosColegio.DIAS.index(x[0])}_{x[1]}')
                  for (g, x), variables in self.uso_zona.items() if len(variables) > 1}

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
                sv.Add(suma(self.y[(l, p)] for p in inst.pares[c]) == len(lec['dobles']))
            if lec['simples']:
                sv.Add(suma(self.z[(l, x)] for x in inst.celda[c]) == len(lec['simples']))

        # (R2) Jornada completa: una actividad en cada celda del curso
        lecciones_curso = defaultdict(list)
        for l, lec in enumerate(self.lecciones):
            lecciones_curso[lec['curso']].append(l)
        for c in inst.cursos:
            for x in inst.celda[c]:
                ocupacion = suma(v for l in lecciones_curso[c] for v in self.ocupa[(l, x)])
                sv.Add(ocupacion <= 1 if DatosColegio.es_parvulo(c) else ocupacion == 1)

        # (R3) Una sesión diaria por asignatura (familia)
        for c in inst.cursos:
            familias = defaultdict(list)
            for l in lecciones_curso[c]:
                familias[self.lecciones[l]['fam']].append(l)
            for fam, ls in familias.items():
                if sum(len(self.lecciones[l]['dobles']) + len(self.lecciones[l]['simples']) for l in ls) < 2:
                    continue
                for d in DatosColegio.DIAS:
                    sesiones_dia = [self.y[(l, p)] for l in ls for p in inst.pares[c] if (l, p) in self.y and p[0][0] == d]
                    sesiones_dia += [self.z[(l, x)] for l in ls for x in inst.celda[c] if (l, x) in self.z and x[0] == d]
                    if len(sesiones_dia) > 1:
                        sv.Add(suma(sesiones_dia) <= 1)

        # (R4) Docente sin choques (descontando sus electivos fijos)
        for (t, x), variables in self.uso_docente.items():
            sv.Add(suma(variables) <= 1 - self.fijo[(t, x)])

        # (R5) Salas de capacidad limitada (English skills)
        for (sala, x), variables in self.uso_recurso.items():
            sv.Add(suma(variables) <= DatosColegio.RECURSOS_CAPACIDAD[sala])

        # (R6) Recintos deportivos: un curso por gimnasio y un desborde al patio
        for (g, x), variables in self.uso_zona.items():
            sv.Add(suma(variables) <= 1 + self.u.get((g, x), 0))
        por_celda = defaultdict(list)
        for (g, x), var in self.u.items():
            por_celda[x].append(var)
        for variables in por_celda.values():
            if len(variables) > 1:
                sv.Add(suma(variables) <= 1)

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

    def _objetivo(self):
        sv = self.solver
        sv.Minimize(self.peso_patio * sv.Sum(self.u.values()) + self.peso_ventanas * sv.Sum(self.v))

    # ------------------------------------------------------------------
    # Resolución
    # ------------------------------------------------------------------
    def resolver(self, tiempo_max=None, mostrar_log=False, hilos=None):
        """Resuelve el modelo y retorna un diccionario con estado, objetivo, cota, gap y tiempos."""
        sv, pw = self.solver, self.pywraplp
        if tiempo_max:
            sv.SetTimeLimit(int(tiempo_max * 1000))
        if mostrar_log:
            sv.EnableOutput()
        if hilos:
            sv.SetNumThreads(hilos)
        t0 = time.perf_counter()
        estado = sv.Solve()
        t_resolucion = time.perf_counter() - t0
        nombres = {pw.Solver.OPTIMAL: 'óptimo', pw.Solver.FEASIBLE: 'factible (sin probar optimalidad)',
                   pw.Solver.INFEASIBLE: 'infactible', pw.Solver.UNBOUNDED: 'no acotado',
                   pw.Solver.ABNORMAL: 'error del solver', pw.Solver.NOT_SOLVED: 'sin solución en el tiempo dado'}
        con_solucion = estado in (pw.Solver.OPTIMAL, pw.Solver.FEASIBLE)
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
            'patio': round(sum(v.solution_value() for v in self.u.values())) if con_solucion else None,
            'ventanas_modelo': round(sum(v.solution_value() for v in self.v)) if con_solucion and self.v else None,
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
            dobles = [p for p in inst.pares[c] if (l, p) in self.y and self.y[(l, p)].solution_value() > 0.5]
            simples = [(x,) for x in inst.celda[c] if (l, x) in self.z and self.z[(l, x)].solution_value() > 0.5]
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
    parser = argparse.ArgumentParser(description="Modelo de programación entera del horario MMDD (OR-Tools)")
    parser.add_argument('--solver', default='CP-SAT', choices=SOLVERS, help="Solver de OR-Tools (default: CP-SAT)")
    parser.add_argument('--tiempo-max', type=float, default=300, help="Segundos máximos de resolución (default: 300)")
    parser.add_argument('--peso-patio', type=float, default=ModeloHorario.PESO_PATIO,
                        help="Peso del uso del Patio Santo Domingo (default: 1)")
    parser.add_argument('--peso-ventanas', type=float, default=0,
                        help="Peso de las ventanas docentes; 0 = no se modelan (default: 0)")
    parser.add_argument('--hilos', type=int, default=None, help="Hilos del solver (default: los del solver)")
    parser.add_argument('--log', action='store_true', help="Muestra el registro del solver")
    parser.add_argument('--lp', type=str, help="Exporta el modelo a este archivo en formato LP")
    parser.add_argument('--excel', type=str, help="Carpeta donde exportar los Excel del horario obtenido")
    args = parser.parse_args()

    modelo = ModeloMatematico(args.solver, args.peso_patio, args.peso_ventanas)
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
    print(f"Objetivo: {r['objetivo']:g}   cota inferior: {r['cota']:g}   gap: {r['gap'] * 100:.2f}%")
    print(f"Bloques en el Patio Santo Domingo: {r['patio']}"
          + (f"   ventanas docentes: {r['ventanas_modelo']}" if r['ventanas_modelo'] is not None else ''))

    # Validación independiente: costo de la función objetivo de las metaheurísticas y auditoría
    instancia = modelo.a_modelo_horario()
    horario = instancia.a_horario()
    auditoria = ValidadorRestricciones.auditar(horario)
    m = auditoria['metricas']
    print(f"\nValidación con la función objetivo de las metaheurísticas: costo = {instancia.costo} "
          f"({instancia.duras} violaciones duras)")
    print(f"Auditoría: {'VÁLIDO' if auditoria['valido'] else 'CON ERRORES'} · "
          f"{m['total_bloques_asignados']}/{m['total_bloques_esperados']} bloques · "
          f"ventanas docentes {m['total_ventanas_docentes']} · bloques dobles {m['porcentaje_bloques_dobles']}% · "
          f"patio {m['uso_patio']}")
    for error in auditoria['errores_duros'][:10]:
        print(f"  - {error}")

    if args.excel:
        os.makedirs(args.excel, exist_ok=True)
        ExportadorExcel.exportar_horario_cursos(horario, os.path.join(args.excel, 'Horario_Cursos_Modelo.xlsx'))
        ExportadorExcel.exportar_horario_docentes(horario, os.path.join(args.excel, 'Horarios_Docentes_Modelo.xlsx'))
        print(f"\nExcel exportados en {args.excel}")


if __name__ == '__main__':
    main()
