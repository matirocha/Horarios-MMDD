# -*- coding: utf-8 -*-
"""
Paquete del generador de horarios del Colegio Madres Dominicas (MMDD).

Módulos, en el orden en que intervienen al generar un horario:
  datos.py              DatosColegio: parámetros y mallas del año escolar 2026 (entrada).
  modelo.py             ModeloHorario: sesiones y función objetivo (costo incremental).
  heuristicas/          Heurísticas: construcción voraz (solución inicial) y Min-Conflicts.
  mejora.py             Clases base de los métodos de mejora y medición de tiempos.
  metaheuristicas/      Metaheurísticas de mejora: búsqueda tabú, ILS e híbrido (por defecto).
  motor.py              MotorHorarios: encadena las fases y mide sus tiempos.
  salidas/              Horario final, auditoría, libros Excel y consola.

Ver notebooks/README.md para la descripción de cada archivo.
"""

from .datos import DatosColegio
from .heuristicas import ConstruccionVoraz, MinConflictos
from .mejora import Metaheuristica, MetodoMejora, Seguimiento
from .metaheuristicas import (METAHEURISTICAS, BusquedaLocalIterada, BusquedaTabu, MinConflictosTabu,
                              crear_metaheuristica)
from .modelo import ModeloHorario
from .motor import MotorHorarios
from .salidas import ExportadorExcel, HorarioEscolar, MenuInteractivo, ValidadorRestricciones

__all__ = [
    'DatosColegio', 'ModeloHorario', 'ConstruccionVoraz', 'MinConflictos',
    'MetodoMejora', 'Metaheuristica', 'Seguimiento', 'BusquedaTabu', 'BusquedaLocalIterada', 'MinConflictosTabu',
    'METAHEURISTICAS', 'crear_metaheuristica', 'MotorHorarios',
    'HorarioEscolar', 'ValidadorRestricciones', 'ExportadorExcel', 'MenuInteractivo',
]
