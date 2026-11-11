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

Metodología: una heurística constructiva voraz arma la solución inicial y una
metaheurística la repara hasta un horario factible: búsqueda local iterada (ILS) o
búsqueda tabú iterada (ITS, por defecto).

El código vive en el paquete horarios/ (ver notebooks/README.md). El modelo
matemático exacto está en modelo_matematico.py y la comparación de ILS e ITS en
comparar_metaheuristicas.py.
"""

import argparse

from horarios import METAHEURISTICAS, POR_DEFECTO, MenuInteractivo, MotorHorarios
# Los prototipos web importan estas clases desde este archivo ('from generador_horarios import ...')
from horarios import DatosColegio, ExportadorExcel, HorarioEscolar, ValidadorRestricciones  # noqa: F401


def main():
    parser = argparse.ArgumentParser(description="Generador de Horarios Escolares MMDD (año 2026)")
    parser.add_argument('--curso', type=str, help="Nombre del curso a consultar directamente")
    parser.add_argument('--docente', type=str, help="Nombre del docente a consultar directamente")
    parser.add_argument('--export', action='store_true', help="Generar Excel automáticamente y salir")
    parser.add_argument('--audit', action='store_true', help="Mostrar auditoría de restricciones y salir")
    parser.add_argument('--seed', type=int, default=3, help="Semilla del generador (default: 3)")
    parser.add_argument('--metaheuristica', choices=sorted(METAHEURISTICAS), default=POR_DEFECTO,
                        help=f"Metaheurística de mejora: ils (búsqueda local iterada) o its (búsqueda tabú "
                             f"iterada) (default: {POR_DEFECTO})")
    parser.add_argument('--tiempo-max', type=float, default=None,
                        help="Segundos máximos de la búsqueda (default: sin límite)")
    args = parser.parse_args()

    # 1. Generar horario factible
    motor = MotorHorarios(seed=args.seed, metaheuristica=args.metaheuristica, tiempo_max=args.tiempo_max)
    horario = motor.generar()
    e, t = motor.estadisticas, motor.tiempos
    print(f"Horario generado con {e['metaheuristica']} (semilla {args.seed}): {e['duras_finales']} violaciones "
          f"duras, costo {e['costo_final']}, {e['pasos']} pasos. Tiempo: construcción "
          f"{t['construccion'] * 1000:.0f} ms, búsqueda {t['busqueda'] * 1000:.0f} ms, total {t['total'] * 1000:.0f} ms.")
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
