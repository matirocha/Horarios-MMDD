#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
SISTEMA DE PROGRAMACIÓN AUTOMATIZADA DE HORARIOS ESCOLARES — AÑO ESCOLAR 2026
Colegio Madres Dominicas (MMDD) - Concepción, Chile
Taller de Gestión de Operaciones (TGOP) - Ingeniería Civil Industrial, UdeC
===============================================================================

Punto de entrada del generador. Construye mallas horarias factibles para los 24
cursos regulares del establecimiento (1° Básico a 4° Medio, secciones A y B) y
para la Educación Física de los 3 niveles de párvulos, usando los parámetros
oficiales del año 2026 (carpeta data/Data 2026):
  - HORARIO CURSOS 2026.xlsx       -> bloques, jornadas, cargas, electivos y recintos.
  - DISTRIBUCIÓN HORARIA 2026.docx -> dotación docente y asignación profesor-curso.

El código vive en el paquete horarios/ (ver horarios/__init__.py). Este archivo
reexporta sus clases para que 'from generador_horarios import ...' siga funcionando.
"""

import argparse

from horarios import (METAHEURISTICAS, ConstruccionVoraz, DatosColegio, ExportadorExcel,  # noqa: F401
                      HorarioEscolar, MenuInteractivo, Metaheuristica, MinConflictosTabu,
                      ModeloHorario, MotorHorarios, ValidadorRestricciones, crear_metaheuristica)


def main():
    parser = argparse.ArgumentParser(description="Generador de Horarios Escolares MMDD (año 2026)")
    parser.add_argument('--curso', type=str, help="Nombre del curso a consultar directamente")
    parser.add_argument('--docente', type=str, help="Nombre del docente a consultar directamente")
    parser.add_argument('--export', action='store_true', help="Generar Excel automáticamente y salir")
    parser.add_argument('--audit', action='store_true', help="Mostrar auditoría de restricciones y salir")
    parser.add_argument('--seed', type=int, default=3, help="Semilla del generador (default: 3)")
    parser.add_argument('--metaheuristica', choices=sorted(METAHEURISTICAS), default='min_conflicts_tabu',
                        help="Metaheurística de mejora (default: min_conflicts_tabu)")
    args = parser.parse_args()

    # 1. Generar horario factible
    motor = MotorHorarios(seed=args.seed, metaheuristica=args.metaheuristica)
    horario = motor.generar()
    menu = MenuInteractivo(horario)

    # 2. Generar siempre el Excel en Outputs Excel automáticamente
    menu.exportar()

    # 3. Procesar modos CLI
    if args.curso:
        menu.mostrar_tabla_curso(args.curso)
    elif args.docente:
        menu.mostrar_tabla_docente(args.docente)
    elif args.audit:
        menu.mostrar_auditoria()
    elif not args.export:
        # Modo interactivo en consola
        menu.iniciar()


if __name__ == '__main__':
    main()
