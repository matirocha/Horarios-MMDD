# -*- coding: utf-8 -*-
"""
METAHEURÍSTICA HÍBRIDA: MIN-CONFLICTS + BÚSQUEDA TABÚ + REINICIOS ILS (método por defecto).

Es el método con que se generan los horarios del proyecto. Combina:

  - Heurística Min-Conflicts (heuristicas/min_conflicts.py): elige al azar una
    restricción violada, una de sus sesiones movibles y su mejor intercambio.
  - Búsqueda tabú (busqueda_tabu.py): aplica el mejor intercambio admisible aunque
    empeore, con lista tabú de permanencia aleatoria y criterio de aspiración.
  - Ruido (random walk): con probabilidad 'prob_ruido' aplica un intercambio al azar.
  - Reinicios de la búsqueda local iterada (busqueda_local_iterada.py): cada 'reinicio'
    pasos sin mejora vuelve a la mejor solución y la perturba.
"""

from ..heuristicas.min_conflicts import elegir_sesion_en_conflicto, mejor_movimiento
from ..mejora import Metaheuristica
from .busqueda_local_iterada import perturbar
from .busqueda_tabu import ListaTabu


class MinConflictosTabu(Metaheuristica):
    """Min-Conflicts con lista tabú, ruido aleatorio y reinicios."""

    nombre = 'min_conflicts_tabu'

    def __init__(self, max_pasos=150000, tiempo_max=None, prob_ruido=0.03, tabu_min=10, tabu_rango=10,
                 reinicio=2500, perturbaciones=15, parada_factible=3000):
        super().__init__(max_pasos, tiempo_max)
        self.prob_ruido = prob_ruido            # probabilidad de aplicar un vecino al azar
        self.tabu_min = tabu_min                # permanencia tabú: tabu_min + entero en [0, tabu_rango]
        self.tabu_rango = tabu_rango
        self.reinicio = reinicio                # pasos sin mejora antes de volver a la mejor solución
        self.perturbaciones = perturbaciones    # intercambios al azar tras cada reinicio
        self.parada_factible = parada_factible  # pasos sin mejora para parar si ya es factible

    def _buscar(self, modelo, rng, seg):
        tabu = ListaTabu(self.tabu_min, self.tabu_rango)
        sin_mejora = 0
        reinicios = 0
        for paso in range(self.max_pasos):
            motivo = self.parada_comun(modelo, seg)
            if motivo is None and modelo.duras == 0 and sin_mejora > self.parada_factible:
                motivo = 'factible_sin_mejora'   # factible y sin mejoras en el costo blando
            if motivo:
                return {'pasos': paso, 'motivo_parada': motivo, 'reinicios': reinicios}
            sid, motivo = elegir_sesion_en_conflicto(modelo, rng)
            if sid is None:
                return {'pasos': paso, 'motivo_parada': motivo, 'reinicios': reinicios}
            c = modelo.ses[sid]['curso']
            movimientos = modelo.vecinos(sid)
            if not movimientos:
                continue

            if rng.random() < self.prob_ruido:
                elegido = rng.choice(movimientos)   # ruido: ignora costo y lista tabú
            else:
                elegido, _ = mejor_movimiento(modelo, sid, movimientos, rng,
                                              tabu.admisible(modelo, sid, paso, seg.mejor_costo))
                if elegido is None:
                    continue   # todos los movimientos son tabú

            origen = modelo.pos[sid]
            modelo.mover(c, elegido)
            tabu.prohibir(sid, origen, paso, rng)

            if seg.registrar(paso, modelo):
                sin_mejora = 0
            else:
                sin_mejora += 1
                if sin_mejora % self.reinicio == 0:
                    # Reinicio: volver a la mejor solución y perturbarla
                    reinicios += 1
                    modelo.restaurar(seg.mejor_pos)
                    perturbar(modelo, rng, self.perturbaciones)
        return {'pasos': self.max_pasos, 'motivo_parada': 'max_pasos', 'reinicios': reinicios}
