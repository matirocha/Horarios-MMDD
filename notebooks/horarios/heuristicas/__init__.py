# -*- coding: utf-8 -*-
"""
Heurísticas del generador de horarios.

  construccion_voraz.py  Heurística constructiva voraz: genera la solución inicial.
  min_conflicts.py       Heurística de mejora Min-Conflicts: operadores de búsqueda local
                         (elegir una sesión en conflicto y su mejor intercambio) que usan
                         todas las metaheurísticas, y la búsqueda local de descenso sola.
"""

from .construccion_voraz import ConstruccionVoraz
from .min_conflicts import (MinConflictos, elegir_sesion_en_conflicto, evaluar_movimiento, mejor_movimiento,
                            posicion_destino)

__all__ = ['ConstruccionVoraz', 'MinConflictos', 'elegir_sesion_en_conflicto', 'evaluar_movimiento',
           'mejor_movimiento', 'posicion_destino']
