# -*- coding: utf-8 -*-
"""
HEURÍSTICA DE MEJORA MIN-CONFLICTS (búsqueda local, Minton et al., 1992).

Es la regla de búsqueda local que comparten todos los métodos de mejora del proyecto:

  1. Elegir al azar una restricción violada (una clave de modelo.malos; si no hay, una
     de modelo.blandos) y, de ella, una sesión movible.
  2. Evaluar todos los intercambios de esa sesión dentro de su curso (modelo.vecinos):
     par por par, o bloque simple por bloque simple. Así la jornada del curso sigue
     completa y la carga horaria no cambia.
  3. Aplicar el intercambio que deja menos conflictos (menor variación de costo).

Este archivo tiene esos tres operadores, que reutilizan las metaheurísticas, y la clase
MinConflictos: la heurística sola, como búsqueda local de descenso. Solo acepta
movimientos que no empeoran (variación <= 0, incluidos los laterales), por lo que puede
quedar atrapada en un óptimo local. Las metaheurísticas de metaheuristicas/ le agregan
estrategias para escapar de ellos (memoria tabú, perturbaciones, ruido...). Sirve como
línea base en comparar_metaheuristicas.py.
"""

from ..mejora import MetodoMejora


# ----------------------------------------------------------------------
# Operadores
# ----------------------------------------------------------------------
def elegir_sesion_en_conflicto(modelo, rng):
    """
    Paso 1: retorna (sid, None) con una sesión movible que participa en una violación,
    o (None, motivo) si no hay ninguna que mover.
    """
    fuente = modelo.malos if modelo.malos else modelo.blandos
    if not fuente:
        return None, 'sin_violaciones'
    k = rng.choice(sorted(fuente))
    candidatos = sorted(i for i in modelo.occ[k] if not modelo.ses[i]['fijo'])
    if not candidatos:
        return None, 'sin_candidatos'
    return rng.choice(candidatos), None


def posicion_destino(modelo, sid, mov):
    """Celdas que ocuparía la sesión 'sid' si se aplica el intercambio 'mov'."""
    return tuple(sorted(mov[x] for x in modelo.pos[sid]))


def evaluar_movimiento(modelo, sid, mov):
    """Variación del costo al aplicar 'mov' a la sesión 'sid' (lo aplica y lo deshace)."""
    c = modelo.ses[sid]['curso']
    delta = modelo.mover(c, mov)
    modelo.mover(c, {y: x for x, y in mov.items()})
    return delta


def mejor_movimiento(modelo, sid, movimientos, rng, admisible=None):
    """
    Pasos 2 y 3: retorna (movimiento, variación) con el intercambio de menor variación de
    costo; los empates se deciden al azar. 'admisible(mov, delta)', si se entrega, descarta
    movimientos (p. ej. los prohibidos por una lista tabú). Retorna (None, None) si
    ninguno es admisible.
    """
    elegido, mejor_delta = None, None
    for mov in movimientos:
        delta = evaluar_movimiento(modelo, sid, mov)
        if admisible is not None and not admisible(mov, delta):
            continue
        if mejor_delta is None or delta < mejor_delta or (delta == mejor_delta and rng.random() < 0.5):
            elegido, mejor_delta = mov, delta
    return elegido, mejor_delta


# ----------------------------------------------------------------------
# Heurística sola (búsqueda local de descenso)
# ----------------------------------------------------------------------
class MinConflictos(MetodoMejora):
    """Min-Conflicts puro: aplica el mejor intercambio solo si no empeora el costo."""

    nombre = 'min_conflicts'
    tipo = 'heurística'

    def __init__(self, max_pasos=150000, tiempo_max=None, max_sin_mejora=2000):
        super().__init__(max_pasos, tiempo_max)
        self.max_sin_mejora = max_sin_mejora  # pasos sin mejorar la mejor solución: óptimo local

    def _buscar(self, modelo, rng, seg):
        sin_mejora = 0
        for paso in range(self.max_pasos):
            motivo = self.parada_comun(modelo, seg)
            if motivo is None and sin_mejora >= self.max_sin_mejora:
                motivo = 'optimo_local'
            if motivo:
                return {'pasos': paso, 'motivo_parada': motivo}
            sid, motivo = elegir_sesion_en_conflicto(modelo, rng)
            if sid is None:
                return {'pasos': paso, 'motivo_parada': motivo}
            movimientos = modelo.vecinos(sid)
            if movimientos:
                mov, delta = mejor_movimiento(modelo, sid, movimientos, rng)
                if delta <= 0:
                    modelo.mover(modelo.ses[sid]['curso'], mov)
            if seg.registrar(paso, modelo):
                sin_mejora = 0
            else:
                sin_mejora += 1
        return {'pasos': self.max_pasos, 'motivo_parada': 'max_pasos'}
