# -*- coding: utf-8 -*-
"""
Búsqueda local Min-Conflicts con lista tabú.

En cada paso elige al azar una restricción violada, una de sus sesiones movibles y
el mejor intercambio de esa sesión dentro de su curso (par por par, o bloque simple
por bloque simple). Usa lista tabú con criterio de aspiración, ruido aleatorio y
reinicios desde la mejor solución encontrada.
"""

from .base import Metaheuristica


class MinConflictosTabu(Metaheuristica):
    """Min-Conflicts con lista tabú, ruido aleatorio y reinicios."""

    nombre = 'min_conflicts_tabu'

    def __init__(self, max_pasos=150000, prob_ruido=0.03, tabu_min=10, tabu_rango=10,
                 reinicio=2500, perturbaciones=15, parada_factible=3000):
        super().__init__(max_pasos)
        self.prob_ruido = prob_ruido            # probabilidad de aplicar un vecino al azar
        self.tabu_min = tabu_min                # permanencia tabú: tabu_min + entero en [0, tabu_rango]
        self.tabu_rango = tabu_rango
        self.reinicio = reinicio                # pasos sin mejora antes de volver a la mejor solución
        self.perturbaciones = perturbaciones    # intercambios al azar tras cada reinicio
        self.parada_factible = parada_factible  # pasos sin mejora para parar si ya es factible

    def buscar(self, modelo, rng):
        tabu = {}
        mejor_costo = modelo.costo
        mejor_pos = dict(modelo.pos)
        sin_mejora = 0
        reinicios = 0
        pasos, motivo = self.max_pasos, 'max_pasos'
        for paso in range(self.max_pasos):
            if modelo.costo == 0:
                pasos, motivo = paso, 'costo_cero'
                break
            if modelo.duras == 0 and sin_mejora > self.parada_factible:
                pasos, motivo = paso, 'factible_sin_mejora'   # factible y sin mejoras en el uso del patio
                break
            fuente = modelo.malos if modelo.malos else modelo.blandos
            if not fuente:
                pasos, motivo = paso, 'sin_violaciones'
                break
            k = rng.choice(sorted(fuente))
            candidatos = sorted(i for i in modelo.occ[k] if not modelo.ses[i]['fijo'])
            if not candidatos:
                pasos, motivo = paso, 'sin_candidatos'
                break
            sid = rng.choice(candidatos)
            c = modelo.ses[sid]['curso']
            movimientos = modelo.vecinos(sid)
            if not movimientos:
                continue

            if rng.random() < self.prob_ruido:
                elegido = rng.choice(movimientos)
            else:
                elegido, mejor_delta = None, None
                for mov in movimientos:
                    destino = tuple(sorted(mov[x] for x in modelo.pos[sid]))
                    delta = modelo.mover(c, mov)
                    modelo.mover(c, {y: x for x, y in mov.items()})
                    es_tabu = tabu.get((sid, destino), -1) > paso
                    if es_tabu and modelo.costo + delta >= mejor_costo:
                        continue
                    if mejor_delta is None or delta < mejor_delta or (delta == mejor_delta and rng.random() < 0.5):
                        elegido, mejor_delta = mov, delta
                if elegido is None:
                    continue

            origen = modelo.pos[sid]
            modelo.mover(c, elegido)
            tabu[(sid, origen)] = paso + self.tabu_min + rng.randint(0, self.tabu_rango)

            if modelo.costo < mejor_costo:
                mejor_costo = modelo.costo
                mejor_pos = dict(modelo.pos)
                sin_mejora = 0
            else:
                sin_mejora += 1
                if sin_mejora % self.reinicio == 0:
                    # Reinicio: volver a la mejor solución y perturbarla
                    reinicios += 1
                    modelo.restaurar(mejor_pos)
                    for _ in range(self.perturbaciones):
                        c2 = rng.choice(modelo.cursos)
                        sids_c = sorted({v for v in modelo.celda[c2].values() if v is not None})
                        if sids_c:
                            vecinos = modelo.vecinos(rng.choice(sids_c))
                            if vecinos:
                                modelo.mover(c2, rng.choice(vecinos))
        if modelo.costo > mejor_costo:
            modelo.restaurar(mejor_pos)
        return {'pasos': pasos, 'motivo_parada': motivo, 'reinicios': reinicios}
