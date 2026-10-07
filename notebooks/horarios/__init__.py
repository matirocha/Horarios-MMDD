# -*- coding: utf-8 -*-
"""
Paquete del generador de horarios del Colegio Madres Dominicas (MMDD).

Módulos:
  datos.py              DatosColegio: parámetros y mallas del año escolar 2026.
  horario.py            HorarioEscolar: estructura del horario final.
  validador.py          ValidadorRestricciones: auditoría de restricciones.
  modelo.py             ModeloHorario: sesiones y función de costo incremental.
  construccion.py       ConstruccionVoraz: solución inicial.
  metaheuristicas/      Metaheurísticas de mejora (Min-Conflicts tabú y las que se agreguen).
  motor.py              MotorHorarios: encadena las fases y mide sus tiempos.
  exportador_excel.py   ExportadorExcel: libros .xlsx con el diseño oficial 2026.
  menu.py               MenuInteractivo: consola para consultar y exportar.
"""

from .construccion import ConstruccionVoraz
from .datos import DatosColegio
from .exportador_excel import ExportadorExcel
from .horario import HorarioEscolar
from .menu import MenuInteractivo
from .metaheuristicas import METAHEURISTICAS, Metaheuristica, MinConflictosTabu, crear_metaheuristica
from .modelo import ModeloHorario
from .motor import MotorHorarios
from .validador import ValidadorRestricciones

__all__ = [
    'DatosColegio', 'HorarioEscolar', 'ValidadorRestricciones', 'ModeloHorario', 'ConstruccionVoraz',
    'Metaheuristica', 'MinConflictosTabu', 'METAHEURISTICAS', 'crear_metaheuristica',
    'MotorHorarios', 'ExportadorExcel', 'MenuInteractivo',
]
