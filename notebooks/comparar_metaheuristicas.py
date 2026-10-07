#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compara las metaheurísticas registradas en horarios/metaheuristicas/.

Para cada metaheurística y cada semilla genera un horario completo con la misma
solución inicial (construcción voraz), mide el tiempo de cada fase y audita el
resultado con ValidadorRestricciones. No genera archivos Excel.

Uso:
    python notebooks/comparar_metaheuristicas.py
    python notebooks/comparar_metaheuristicas.py --semillas 1 2 3 4 5
    python notebooks/comparar_metaheuristicas.py --metaheuristicas min_conflicts_tabu --csv resultados.csv
"""

import argparse
import csv
import statistics

from horarios import METAHEURISTICAS, MotorHorarios, ValidadorRestricciones

COLUMNAS = ['metaheuristica', 'semilla', 'factible', 'duras_construccion', 'duras_finales', 'costo_final',
            'pasos', 'motivo_parada', 't_construccion_ms', 't_busqueda_ms', 't_total_ms']


def ejecutar(nombre, semilla, max_pasos):
    """Genera un horario y retorna una fila con tiempos, costo y factibilidad."""
    motor = MotorHorarios(seed=semilla, max_pasos=max_pasos, metaheuristica=nombre)
    horario = motor.generar()
    e, t = motor.estadisticas, motor.tiempos
    return {
        'metaheuristica': nombre,
        'semilla': semilla,
        'factible': ValidadorRestricciones.auditar(horario)['valido'],
        'duras_construccion': e['duras_construccion'],
        'duras_finales': e['duras_finales'],
        'costo_final': e['costo_final'],
        'pasos': e.get('pasos'),
        'motivo_parada': e.get('motivo_parada'),
        't_construccion_ms': round(t['construccion'] * 1000, 1),
        't_busqueda_ms': round(t['busqueda'] * 1000, 1),
        't_total_ms': round(t['total'] * 1000, 1),
    }


def main():
    parser = argparse.ArgumentParser(description="Compara tiempos y resultados de las metaheurísticas")
    parser.add_argument('--metaheuristicas', nargs='+', choices=sorted(METAHEURISTICAS), default=sorted(METAHEURISTICAS),
                        help="Metaheurísticas a comparar (por defecto, todas las registradas)")
    parser.add_argument('--semillas', nargs='+', type=int, default=list(range(1, 11)),
                        help="Semillas a ejecutar (por defecto, 1 a 10)")
    parser.add_argument('--max-pasos', type=int, default=150000, help="Pasos máximos de cada búsqueda (default: 150000)")
    parser.add_argument('--csv', type=str, help="Guarda todas las ejecuciones en este archivo CSV")
    args = parser.parse_args()

    filas = []
    print(f"{'Metaheurística':<22} {'Semilla':>7} {'Factible':>8} {'Duras ini':>9} {'Duras fin':>9} "
          f"{'Pasos':>7} {'Constr. ms':>10} {'Búsq. ms':>9} {'Total ms':>9}")
    for nombre in args.metaheuristicas:
        for semilla in args.semillas:
            f = ejecutar(nombre, semilla, args.max_pasos)
            filas.append(f)
            print(f"{nombre:<22} {semilla:>7} {'sí' if f['factible'] else 'no':>8} {f['duras_construccion']:>9} "
                  f"{f['duras_finales']:>9} {f['pasos']:>7} {f['t_construccion_ms']:>10} "
                  f"{f['t_busqueda_ms']:>9} {f['t_total_ms']:>9}")

    print("\nResumen por metaheurística")
    print(f"{'Metaheurística':<22} {'Factibles':>9} {'Pasos prom.':>11} {'Búsq. prom. ms':>14} "
          f"{'Búsq. máx. ms':>13} {'Total prom. ms':>14}")
    for nombre in args.metaheuristicas:
        g = [f for f in filas if f['metaheuristica'] == nombre]
        print(f"{nombre:<22} {sum(f['factible'] for f in g):>4} / {len(g):<2} "
              f"{statistics.mean(f['pasos'] for f in g):>11.0f} "
              f"{statistics.mean(f['t_busqueda_ms'] for f in g):>14.1f} "
              f"{max(f['t_busqueda_ms'] for f in g):>13.1f} "
              f"{statistics.mean(f['t_total_ms'] for f in g):>14.1f}")

    if args.csv:
        with open(args.csv, 'w', newline='', encoding='utf-8') as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=COLUMNAS)
            escritor.writeheader()
            escritor.writerows(filas)
        print(f"\nResultados guardados en {args.csv}")


if __name__ == '__main__':
    main()
