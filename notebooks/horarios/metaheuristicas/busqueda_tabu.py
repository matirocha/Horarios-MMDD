# -*- coding: utf-8 -*-
"""
METAHEURÍSTICA: BÚSQUEDA TABÚ (Tabu Search, Glover 1986).

Usa la vecindad Min-Conflicts (heuristicas/min_conflicts.py), pero en cada paso aplica
el mejor intercambio admisible aunque empeore el costo: así sale de los óptimos locales.
Para no volver de inmediato a la solución anterior usa una memoria de corto plazo:

  - Lista tabú: cuando una sesión deja una posición, se le prohíbe volver a ella durante
    'tabu_min' + U{0..tabu_rango} pasos (permanencia aleatoria, evita ciclos).
  - Criterio de aspiración: un movimiento tabú se permite si lleva a un costo menor que
    el de la mejor solución encontrada.
"""

from ..heuristicas.min_conflicts import elegir_sesion_en_conflicto, mejor_movimiento, posicion_destino
from ..mejora import Metaheuristica


class ListaTabu:
    """Memoria de corto plazo: (sesión, posición) -> último paso en que la posición es tabú."""

    def __init__(self, tabu_min=10, tabu_rango=10):
        self.tabu_min = tabu_min
        self.tabu_rango = tabu_rango
        self.hasta = {}

    def prohibir(self, sid, celdas, paso, rng):
        """Prohíbe que la sesión 'sid' vuelva a 'celdas' durante una permanencia aleatoria."""
        self.hasta[(sid, celdas)] = paso + self.tabu_min + rng.randint(0, self.tabu_rango)

    def es_tabu(self, sid, celdas, paso):
        return self.hasta.get((sid, celdas), -1) > paso

    def admisible(self, modelo, sid, paso, mejor_costo):
        """
        Filtro para mejor_movimiento: descarta los movimientos tabú, salvo que cumplan el
        criterio de aspiración (mejorar la mejor solución encontrada).
        """
        def criterio(mov, delta):
            es_tabu = self.es_tabu(sid, posicion_destino(modelo, sid, mov), paso)
            return not es_tabu or modelo.costo + delta < mejor_costo
        return criterio


class BusquedaTabu(Metaheuristica):
    """Búsqueda tabú sobre la vecindad Min-Conflicts, con aspiración."""

    nombre = 'busqueda_tabu'

    def __init__(self, max_pasos=150000, tiempo_max=None, tabu_min=10, tabu_rango=10, parada_factible=3000):
        super().__init__(max_pasos, tiempo_max)
        self.tabu_min = tabu_min                # permanencia tabú: tabu_min + entero en [0, tabu_rango]
        self.tabu_rango = tabu_rango
        self.parada_factible = parada_factible  # pasos sin mejora para parar si ya es factible

    def _buscar(self, modelo, rng, seg):
        tabu = ListaTabu(self.tabu_min, self.tabu_rango)
        sin_mejora = 0
        for paso in range(self.max_pasos):
            motivo = self.parada_comun(modelo, seg)
            if motivo is None and modelo.duras == 0 and sin_mejora > self.parada_factible:
                motivo = 'factible_sin_mejora'
            if motivo:
                return {'pasos': paso, 'motivo_parada': motivo}
            sid, motivo = elegir_sesion_en_conflicto(modelo, rng)
            if sid is None:
                return {'pasos': paso, 'motivo_parada': motivo}
            movimientos = modelo.vecinos(sid)
            if not movimientos:
                continue
            elegido, _ = mejor_movimiento(modelo, sid, movimientos, rng,
                                          tabu.admisible(modelo, sid, paso, seg.mejor_costo))
            if elegido is None:
                continue   # todos los movimientos son tabú
            origen = modelo.pos[sid]
            modelo.mover(modelo.ses[sid]['curso'], elegido)
            tabu.prohibir(sid, origen, paso, rng)
            if seg.registrar(paso, modelo):
                sin_mejora = 0
            else:
                sin_mejora += 1
        return {'pasos': self.max_pasos, 'motivo_parada': 'max_pasos'}
