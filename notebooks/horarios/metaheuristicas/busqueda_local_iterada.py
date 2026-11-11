# -*- coding: utf-8 -*-
"""
METAHEURÍSTICA: BÚSQUEDA LOCAL ITERADA (Iterated Local Search, ILS; Lourenço, Martin y Stützle, 2003).

Parte de la solución de la heurística constructiva y alterna búsqueda local y perturbación:

    s0  = construcción voraz                         (heuristicas/construccion_voraz.py)
    s*  = BúsquedaLocal(s0)
    repetir hasta f(s*) = 0, 'max_pasos' o 'tiempo_max':
        s'  = Perturbación(s*)                       k = 'perturbaciones' intercambios al azar
        s*' = BúsquedaLocal(s')
        s*  = s*'  si f(s*') <= f(s*)                criterio de aceptación "mejor o igual"

BúsquedaLocal: descenso de mayor pendiente (steepest descent). En cada paso evalúa TODO el
vecindario N(x) (vecindario.py) y aplica el mejor intercambio si baja f(x). Si el mejor no
cambia f(x), puede aplicar hasta 'laterales' movimientos laterales seguidos para cruzar
mesetas; si empeora, la solución es un óptimo local y la búsqueda local termina.

Cada movimiento aplicado cuenta como un paso; cada perturbación + búsqueda local, como una
iteración.
"""

from ..mejora import Metaheuristica
from .vecindario import mejor_movimiento, perturbar, vecindario


class BusquedaLocalIterada(Metaheuristica):
    """ILS: descenso de mayor pendiente + perturbación + aceptación "mejor o igual"."""

    nombre = 'ils'
    titulo = 'Búsqueda local iterada (ILS)'

    # Valores por defecto calibrados con las semillas 1 a 5 (ver notebooks/README.md, "Calibración")
    def __init__(self, max_pasos=150000, tiempo_max=None, perturbaciones=15, laterales=10, vecindario='conflictos'):
        super().__init__(max_pasos, tiempo_max)
        self.perturbaciones = perturbaciones   # intercambios al azar de cada perturbación (k)
        self.laterales = laterales             # movimientos laterales seguidos permitidos en el descenso
        self.vecindario = vecindario           # 'conflictos' o 'completo' (ver vecindario.py)

    def busqueda_local(self, modelo, rng, seg, paso):
        """Descenso de mayor pendiente desde la solución actual. Retorna (paso, motivo de parada o None)."""
        laterales = 0
        while True:
            motivo = self.parada_comun(modelo, seg)
            if motivo is None and paso >= self.max_pasos:
                motivo = 'max_pasos'
            if motivo:
                return paso, motivo
            elegido, delta = mejor_movimiento(modelo, vecindario(modelo, self.vecindario), rng)
            if elegido is None or delta > 0 or (delta == 0 and laterales >= self.laterales):
                return paso, None   # óptimo local
            laterales = laterales + 1 if delta == 0 else 0
            modelo.mover(*elegido)
            seg.registrar(paso, modelo)
            paso += 1

    def _buscar(self, modelo, rng, seg):
        paso, motivo = self.busqueda_local(modelo, rng, seg, 0)
        actual_pos, actual_costo = dict(modelo.pos), modelo.costo
        iteraciones = aceptadas = 0
        while motivo is None:
            iteraciones += 1
            perturbar(modelo, rng, self.perturbaciones)
            seg.registrar(paso, modelo)
            paso, motivo = self.busqueda_local(modelo, rng, seg, paso)
            # Criterio de aceptación: la nueva solución reemplaza a la actual si no es peor
            if modelo.costo <= actual_costo:
                actual_pos, actual_costo = dict(modelo.pos), modelo.costo
                aceptadas += 1
            elif motivo is None:
                modelo.restaurar(actual_pos)
        return {'pasos': paso, 'motivo_parada': motivo, 'iteraciones': iteraciones, 'aceptadas': aceptadas}
