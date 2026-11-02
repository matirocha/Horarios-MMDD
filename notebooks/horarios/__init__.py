# -*- coding: utf-8 -*-
"""
Paquete del generador de horarios del Colegio Madres Dominicas (MMDD).

Módulos:
  datos.py              DatosColegio: parámetros y mallas del año escolar 2026.
  horario.py            HorarioEscolar: estructura del horario final.
  validador.py          ValidadorRestricciones: auditoría de restricciones.
  modelo.py             ModeloHorario: sesiones y función objetivo (costo incremental).
  heuristicas/          Heurísticas: construcción voraz (solución inicial) y Min-Conflicts.
  mejora.py             MetodoMejora: interfaz común de los métodos de mejora y medición de tiempos.
  metaheuristicas/      Metaheurísticas de mejora: búsqueda tabú, ILS e híbrido (por defecto).
  motor.py              MotorHorarios: encadena las fases y mide sus tiempos.
  exportador_excel.py   ExportadorExcel: libros .xlsx con el diseño oficial 2026.
  menu.py               MenuInteractivo: consola para consultar y exportar.
"""

from .datos import DatosColegio
from .exportador_excel import ExportadorExcel
from .heuristicas import ConstruccionVoraz, MinConflictos
from .horario import HorarioEscolar
from .mejora import MetodoMejora, Seguimiento
from .menu import MenuInteractivo
from .metaheuristicas import (METAHEURISTICAS, BusquedaLocalIterada, BusquedaTabu, Metaheuristica, MinConflictosTabu,
                              crear_metaheuristica)
from .modelo import ModeloHorario
from .motor import MotorHorarios
from .validador import ValidadorRestricciones

__all__ = [
    'DatosColegio', 'HorarioEscolar', 'ValidadorRestricciones', 'ModeloHorario', 'ConstruccionVoraz',
    'MetodoMejora', 'Seguimiento', 'Metaheuristica', 'MinConflictos', 'BusquedaTabu', 'BusquedaLocalIterada',
    'MinConflictosTabu', 'METAHEURISTICAS', 'crear_metaheuristica',
    'MotorHorarios', 'ExportadorExcel', 'MenuInteractivo',
]
