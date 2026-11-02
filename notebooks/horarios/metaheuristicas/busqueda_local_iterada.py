# -*- coding: utf-8 -*-
"""
METAHEURÍSTICA: BÚSQUEDA LOCAL ITERADA (Iterated Local Search, ILS; Lourenço et al. 2003).

Alterna una búsqueda local con perturbaciones:

  1. Búsqueda local: descenso Min-Conflicts (heuristicas/min_conflicts.py), que solo
     acepta intercambios que no empeoran, hasta que pasan 'largo_busqueda_local' pasos
     sin mejorar (óptimo local).
  2. Criterio de aceptación "mejor": se vuelve a la mejor solución encontrada.
  3. Perturbación: se aplican 'perturbaciones' intercambios al azar en cursos al azar,
     para salir de la cuenca del óptimo local, y se vuelve al paso 1.
"""

from ..heuristicas.min_conflicts import elegir_sesion_en_conflicto, mejor_movimiento
from .base import Metaheuristica


def perturbar(modelo, rng, intensidad):
    """Aplica 'intensidad' intercambios al azar, cada uno en un curso elegido al azar."""
    for _ in range(intensidad):
        c = rng.choice(modelo.cursos)
        sids_c = sorted({v for v in modelo.celda[c].values() if v is not None})
        if sids_c:
            vecinos = modelo.vecinos(rng.choice(sids_c))
            if vecinos:
                modelo.mover(c, rng.choice(vecinos))


class BusquedaLocalIterada(Metaheuristica):
    """ILS: descenso Min-Conflicts + perturbación desde la mejor solución."""

    nombre = 'busqueda_local_iterada'

    def __init__(self, max_pasos=150000, tiempo_max=None, largo_busqueda_local=100, perturbaciones=15,
                 parada_factible=3000):
        super().__init__(max_pasos, tiempo_max)
        self.largo_busqueda_local = largo_busqueda_local  # pasos sin mejora que cierran una búsqueda local
        self.perturbaciones = perturbaciones              # intercambios al azar de cada perturbación
        self.parada_factible = parada_factible            # pasos sin mejora global para parar si ya es factible

    def _buscar(self, modelo, rng, seg):
        sin_mejora = 0          # pasos sin mejorar la mejor solución global
        costo_local = modelo.costo
        sin_mejora_local = 0    # pasos sin mejorar en la búsqueda local en curso
        iteraciones = 0         # perturbaciones aplicadas
        for paso in range(self.max_pasos):
            motivo = self.parada_comun(modelo, seg)
            if motivo is None and modelo.duras == 0 and sin_mejora > self.parada_factible:
                motivo = 'factible_sin_mejora'
            if motivo:
                return {'pasos': paso, 'motivo_parada': motivo, 'iteraciones': iteraciones}
            sid, motivo = elegir_sesion_en_conflicto(modelo, rng)
            if sid is None:
                return {'pasos': paso, 'motivo_parada': motivo, 'iteraciones': iteraciones}

            # 1. Un paso de la búsqueda local (descenso)
            movimientos = modelo.vecinos(sid)
            if movimientos:
                mov, delta = mejor_movimiento(modelo, sid, movimientos, rng)
                if delta <= 0:
                    modelo.mover(modelo.ses[sid]['curso'], mov)
            sin_mejora = 0 if seg.registrar(paso, modelo) else sin_mejora + 1
            if modelo.costo < costo_local:
                costo_local, sin_mejora_local = modelo.costo, 0
            else:
                sin_mejora_local += 1

            # 2 y 3. Óptimo local: aceptar la mejor solución y perturbarla
            if sin_mejora_local >= self.largo_busqueda_local:
                iteraciones += 1
                modelo.restaurar(seg.mejor_pos)
                perturbar(modelo, rng, self.perturbaciones)
                costo_local, sin_mejora_local = modelo.costo, 0
        return {'pasos': self.max_pasos, 'motivo_parada': 'max_pasos', 'iteraciones': iteraciones}
