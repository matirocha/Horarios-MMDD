# -*- coding: utf-8 -*-
"""
METAHEURÍSTICA: BÚSQUEDA TABÚ ITERADA (Iterated Tabu Search, ITS; Misevicius, 2005).

Es una búsqueda local iterada cuya búsqueda local es una búsqueda tabú (Glover, 1989).
Parte de la solución de la heurística constructiva:

    s0  = construcción voraz                         (heuristicas/construccion_voraz.py)
    s*  = BúsquedaTabú(s0)
    repetir hasta f(s*) = 0, 'max_pasos' o 'tiempo_max':
        s'  = Perturbación(s*)                       k = 'perturbaciones' intercambios al azar
        s*' = BúsquedaTabú(s')
        s*  = s*'  si f(s*') <= f(s*)                criterio de aceptación "mejor o igual"

BúsquedaTabú: en cada paso evalúa TODO el vecindario N(x) (vecindario.py) y aplica el mejor
intercambio admisible AUNQUE EMPEORE f(x). Para no deshacerlo de inmediato, las sesiones
movidas no pueden volver a su posición anterior durante 'tabu_min' + U[0, 'tabu_rango'] pasos
(lista tabú), salvo que ese movimiento lleve a una solución mejor que la mejor encontrada
(criterio de aspiración). Termina tras 'largo_tabu' pasos seguidos sin mejorar su mejor
solución, y entrega esa mejor solución.

Diferencia con ILS: la búsqueda local de ILS se detiene en el primer óptimo local; la de
ITS sigue más allá aceptando movimientos que empeoran, guiada por la memoria tabú.

Cada movimiento aplicado cuenta como un paso; cada perturbación + búsqueda tabú, como una
iteración.
"""

from ..mejora import Metaheuristica
from .vecindario import mejor_movimiento, perturbar, sesiones_movidas, vecindario


class ListaTabu:
    """Memoria de corto plazo: (sesión, posición) -> último paso en que volver ahí es tabú."""

    def __init__(self, tabu_min=10, tabu_rango=10):
        self.tabu_min = tabu_min
        self.tabu_rango = tabu_rango
        self.hasta = {}

    def prohibir(self, sid, celdas, paso, rng):
        """Prohíbe que la sesión 'sid' vuelva a 'celdas' durante una permanencia aleatoria."""
        self.hasta[(sid, celdas)] = paso + self.tabu_min + rng.randint(0, self.tabu_rango)

    def es_tabu(self, sid, celdas, paso):
        return self.hasta.get((sid, celdas), -1) > paso


class BusquedaTabuIterada(Metaheuristica):
    """ITS: búsqueda tabú + perturbación + aceptación "mejor o igual"."""

    nombre = 'its'
    titulo = 'Búsqueda tabú iterada (ITS)'

    # Valores por defecto calibrados con las semillas 1 a 5 (ver notebooks/README.md, "Calibración");
    # la perturbación es la misma que la de ILS (15 intercambios al azar)
    def __init__(self, max_pasos=150000, tiempo_max=None, tabu_min=10, tabu_rango=10, largo_tabu=150,
                 perturbaciones=15, vecindario='conflictos'):
        super().__init__(max_pasos, tiempo_max)
        self.tabu_min = tabu_min               # permanencia tabú: tabu_min + entero en [0, tabu_rango]
        self.tabu_rango = tabu_rango
        self.largo_tabu = largo_tabu           # pasos sin mejora que cierran cada búsqueda tabú
        self.perturbaciones = perturbaciones   # intercambios al azar de cada perturbación (k)
        self.vecindario = vecindario           # 'conflictos' o 'completo' (ver vecindario.py)

    def busqueda_tabu(self, modelo, rng, seg, paso):
        """
        Búsqueda tabú desde la solución actual; deja en 'modelo' la mejor solución que encontró.
        Retorna (paso, motivo de parada o None).
        """
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

            def admisible(c, mapa, delta, paso=paso):
                # Aspiración: se permite un movimiento tabú si mejora la mejor solución global
                if modelo.costo + delta < seg.mejor_costo:
                    return True
                return not any(tabu.es_tabu(sid, destino, paso) for sid, destino in sesiones_movidas(modelo, c, mapa))

            elegido, _ = mejor_movimiento(modelo, vecindario(modelo, self.vecindario), rng, admisible)
            if elegido is None:
                break   # todos los movimientos son tabú
            origenes = [(sid, modelo.pos[sid]) for sid, _ in sesiones_movidas(modelo, *elegido)]
            modelo.mover(*elegido)
            for sid, origen in origenes:
                tabu.prohibir(sid, origen, paso, rng)
            seg.registrar(paso, modelo)
            paso += 1
            if modelo.costo < mejor_costo:
                mejor_costo, mejor_pos, sin_mejora = modelo.costo, dict(modelo.pos), 0
            else:
                sin_mejora += 1
        if modelo.costo > mejor_costo:
            modelo.restaurar(mejor_pos)
        return paso, motivo

    def _buscar(self, modelo, rng, seg):
        paso, motivo = self.busqueda_tabu(modelo, rng, seg, 0)
        actual_pos, actual_costo = dict(modelo.pos), modelo.costo
        iteraciones = aceptadas = 0
        while motivo is None:
            iteraciones += 1
            perturbar(modelo, rng, self.perturbaciones)
            seg.registrar(paso, modelo)
            paso, motivo = self.busqueda_tabu(modelo, rng, seg, paso)
            # Criterio de aceptación: la nueva solución reemplaza a la actual si no es peor
            if modelo.costo <= actual_costo:
                actual_pos, actual_costo = dict(modelo.pos), modelo.costo
                aceptadas += 1
            elif motivo is None:
                modelo.restaurar(actual_pos)
        return {'pasos': paso, 'motivo_parada': motivo, 'iteraciones': iteraciones, 'aceptadas': aceptadas}
