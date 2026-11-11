# -*- coding: utf-8 -*-
"""
Paquete del generador de horarios del Colegio Madres Dominicas (MMDD).

Módulos, en el orden en que intervienen al generar un horario:
  datos.py              DatosColegio: parámetros y mallas del año escolar 2026 (entrada).
  modelo.py             ModeloHorario: sesiones y función objetivo (costo incremental).
  heuristicas/          Heurística constructiva voraz: la solución inicial.
  mejora.py             Clase base de las metaheurísticas y medición de tiempos.
  metaheuristicas/      Metaheurísticas de mejora: ILS e ITS (por defecto), con su vecindario común.
  motor.py              MotorHorarios: encadena las fases y mide sus tiempos.
  salidas/              Horario final, auditoría, libros Excel y consola.

Ver notebooks/README.md para la descripción de cada archivo.
"""

from .datos import DatosColegio
from .heuristicas import ConstruccionVoraz
from .mejora import Metaheuristica, MetodoMejora, Seguimiento
from .metaheuristicas import (METAHEURISTICAS, POR_DEFECTO, BusquedaLocalIterada, BusquedaTabuIterada,
                              crear_metaheuristica)
from .modelo import ModeloHorario
from .motor import MotorHorarios
from .salidas import ExportadorExcel, HorarioEscolar, MenuInteractivo, ValidadorRestricciones

__all__ = [
    'DatosColegio', 'ModeloHorario', 'ConstruccionVoraz',
    'MetodoMejora', 'Metaheuristica', 'Seguimiento', 'BusquedaLocalIterada', 'BusquedaTabuIterada',
    'METAHEURISTICAS', 'POR_DEFECTO', 'crear_metaheuristica', 'MotorHorarios',
    'HorarioEscolar', 'ValidadorRestricciones', 'ExportadorExcel', 'MenuInteractivo',
]
