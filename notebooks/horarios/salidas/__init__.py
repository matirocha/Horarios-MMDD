# -*- coding: utf-8 -*-
"""
Salidas: todo lo que trabaja sobre el horario ya generado.

  horario.py            HorarioEscolar: estructura del horario final (cursos, docentes, recintos).
  validador.py          ValidadorRestricciones: auditoría independiente de las restricciones.
  exportador_excel.py   ExportadorExcel: libros .xlsx con el diseño oficial 2026.
  menu.py               MenuInteractivo: consola para consultar horarios y exportar.
"""

from .exportador_excel import ExportadorExcel
from .horario import HorarioEscolar
from .menu import MenuInteractivo
from .validador import ValidadorRestricciones

__all__ = ['HorarioEscolar', 'ValidadorRestricciones', 'ExportadorExcel', 'MenuInteractivo']
