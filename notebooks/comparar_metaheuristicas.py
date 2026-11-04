#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compara los métodos de mejora registrados en horarios/metaheuristicas/ (las
metaheurísticas y la heurística Min-Conflicts sola, como línea base).

Diseño del experimento (para que la comparación sea justa):
  - Misma instancia (datos 2026) y, para cada semilla, la misma solución inicial: la
    construcción voraz se ejecuta antes de la búsqueda con el mismo generador aleatorio.
  - Mismo presupuesto: cada búsqueda se detiene al llegar a costo 0, a 'max_pasos' o
    a 'tiempo_max' segundos (por defecto 20 s).
  - Varias semillas por método (por defecto 1 a 10), porque los métodos son aleatorios.

Por ejecución se mide:
  factible          0 violaciones duras al final (y lo confirma ValidadorRestricciones).
  costo_final       función objetivo final: 1000·(violaciones duras).
  t_busqueda_ms     tiempo de la fase de mejora.
  t_factible_ms     tiempo hasta la primera solución sin violaciones duras (vacío si no llegó).
  t_mejor_ms        tiempo hasta la mejor solución encontrada.
  pasos, pasos_por_s  iteraciones realizadas y velocidad.
  ventanas_docentes, pct_dobles  indicadores de calidad de la auditoría.

Uso:
    python notebooks/comparar_metaheuristicas.py
    python notebooks/comparar_metaheuristicas.py --semillas 1 2 3 4 5 --tiempo-max 10
    python notebooks/comparar_metaheuristicas.py --metaheuristicas min_conflicts_tabu busqueda_tabu --csv resultados.csv
    python notebooks/comparar_metaheuristicas.py --convergencia convergencia.csv   # curvas costo vs. tiempo
"""

import argparse
import csv
import statistics

from horarios import METAHEURISTICAS, MotorHorarios, ValidadorRestricciones

COLUMNAS = ['metaheuristica', 'tipo', 'semilla', 'factible', 'costo_construccion', 'duras_construccion',
            'costo_final', 'duras_finales', 'pasos', 'motivo_parada', 'pasos_por_s',
            't_construccion_ms', 't_busqueda_ms', 't_factible_ms', 't_mejor_ms', 't_total_ms',
            'ventanas_docentes', 'pct_dobles']


def ms(segundos):
    return None if segundos is None else round(segundos * 1000, 1)


def ejecutar(nombre, semilla, max_pasos, tiempo_max):
    """Genera un horario y retorna (fila con tiempos, costo y calidad, historial de convergencia)."""
    motor = MotorHorarios(seed=semilla, max_pasos=max_pasos, metaheuristica=nombre, tiempo_max=tiempo_max)
    horario = motor.generar()
    e, t = motor.estadisticas, motor.tiempos
    auditoria = ValidadorRestricciones.auditar(horario)
    m = auditoria['metricas']
    fila = {
        'metaheuristica': nombre,
        'tipo': e['tipo'],
        'semilla': semilla,
        'factible': auditoria['valido'],
        'costo_construccion': e['costo_construccion'],
        'duras_construccion': e['duras_construccion'],
        'costo_final': e['costo_final'],
        'duras_finales': e['duras_finales'],
        'pasos': e['pasos'],
        'motivo_parada': e['motivo_parada'],
        'pasos_por_s': round(e['pasos'] / t['busqueda']) if t['busqueda'] > 0 else None,
        't_construccion_ms': ms(t['construccion']),
        't_busqueda_ms': ms(t['busqueda']),
        't_factible_ms': ms(e['t_factible']),
        't_mejor_ms': ms(e['t_mejor']),
        't_total_ms': ms(t['total']),
        'ventanas_docentes': m['total_ventanas_docentes'],
        'pct_dobles': m['porcentaje_bloques_dobles'],
    }
    return fila, e['historial']


def resumir(filas):
    """Indicadores agregados de las ejecuciones de un método."""
    factibles = [f for f in filas if f['factible']]
    t_fact = [f['t_factible_ms'] for f in factibles if f['t_factible_ms'] is not None]
    busq = [f['t_busqueda_ms'] for f in filas]
    return {
        'n': len(filas),
        'factibles': len(factibles),
        'tasa': len(factibles) / len(filas),
        'costo_medio': statistics.mean(f['costo_final'] for f in filas),
        'busq_mediana': statistics.median(busq),
        'busq_media': statistics.mean(busq),
        'busq_desv': statistics.stdev(busq) if len(busq) > 1 else 0.0,
        'busq_max': max(busq),
        'fact_mediana': statistics.median(t_fact) if t_fact else None,
        'pasos_medio': statistics.mean(f['pasos'] for f in filas),
        'ventanas_medio': statistics.mean(f['ventanas_docentes'] for f in filas),
        'dobles_medio': statistics.mean(f['pct_dobles'] for f in filas),
    }


def main():
    parser = argparse.ArgumentParser(description="Compara tiempos y resultados de las metaheurísticas")
    parser.add_argument('--metaheuristicas', nargs='+', choices=sorted(METAHEURISTICAS), default=sorted(METAHEURISTICAS),
                        help="Métodos a comparar (por defecto, todos los registrados)")
    parser.add_argument('--semillas', nargs='+', type=int, default=list(range(1, 11)),
                        help="Semillas a ejecutar (por defecto, 1 a 10)")
    parser.add_argument('--max-pasos', type=int, default=150000, help="Pasos máximos de cada búsqueda (default: 150000)")
    parser.add_argument('--tiempo-max', type=float, default=20.0,
                        help="Segundos máximos de cada búsqueda; 0 = sin límite (default: 20)")
    parser.add_argument('--csv', type=str, help="Guarda todas las ejecuciones en este archivo CSV")
    parser.add_argument('--convergencia', type=str,
                        help="Guarda en este CSV el historial (tiempo, paso, costo) de cada ejecución")
    args = parser.parse_args()
    tiempo_max = args.tiempo_max if args.tiempo_max > 0 else None

    filas, historiales = [], []
    print(f"Límite por búsqueda: {f'{tiempo_max:g} s' if tiempo_max else 'sin límite de tiempo'} "
          f"y {args.max_pasos} pasos\n")
    print(f"{'Método':<24} {'Semilla':>7} {'Factible':>8} {'Duras ini':>9} {'Duras fin':>9} {'Costo fin':>9} "
          f"{'Pasos':>7} {'Búsq. ms':>9} {'Factible ms':>11} {'Total ms':>9}  Motivo de parada")
    for nombre in args.metaheuristicas:
        for semilla in args.semillas:
            f, historial = ejecutar(nombre, semilla, args.max_pasos, tiempo_max)
            filas.append(f)
            historiales += [(nombre, semilla, round(t * 1000, 1), paso, costo, duras)
                            for t, paso, costo, duras in historial]
            t_fact = '-' if f['t_factible_ms'] is None else f['t_factible_ms']
            print(f"{nombre:<24} {semilla:>7} {'sí' if f['factible'] else 'no':>8} {f['duras_construccion']:>9} "
                  f"{f['duras_finales']:>9} {f['costo_final']:>9} {f['pasos']:>7} {f['t_busqueda_ms']:>9} "
                  f"{t_fact:>11} {f['t_total_ms']:>9}  {f['motivo_parada']}", flush=True)

    # Resumen ordenado: más factibles, menor costo final medio y menor tiempo hasta factible
    resumen = {n: resumir([f for f in filas if f['metaheuristica'] == n]) for n in args.metaheuristicas}
    orden = sorted(resumen, key=lambda n: (-resumen[n]['tasa'], resumen[n]['costo_medio'],
                                           resumen[n]['fact_mediana'] if resumen[n]['fact_mediana'] is not None
                                           else float('inf')))
    print("\nResumen por método (orden: % factibles ↓, costo final medio ↑, mediana del tiempo hasta factible ↑)")
    print(f"{'Método':<24} {'Tipo':<15} {'Factibles':>10} {'Costo medio':>11} {'Búsq. mediana ms':>16} "
          f"{'Búsq. media ± desv. ms':>22} {'Búsq. máx. ms':>13} {'Factible mediana ms':>19} {'Pasos prom.':>11} "
          f"{'Ventanas prom.':>14} {'% dobles':>8}")
    for n in orden:
        r = resumen[n]
        tipo = METAHEURISTICAS[n].tipo
        fact = '-' if r['fact_mediana'] is None else f"{r['fact_mediana']:.1f}"
        media = f"{r['busq_media']:.1f} ± {r['busq_desv']:.1f}"
        print(f"{n:<24} {tipo:<15} {r['factibles']:>4} / {r['n']:<3} {r['costo_medio']:>11.1f} "
              f"{r['busq_mediana']:>16.1f} {media:>22} {r['busq_max']:>13.1f} {fact:>19} {r['pasos_medio']:>11.0f} "
              f"{r['ventanas_medio']:>14.1f} {r['dobles_medio']:>8.1f}")

    if args.csv:
        with open(args.csv, 'w', newline='', encoding='utf-8') as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=COLUMNAS)
            escritor.writeheader()
            escritor.writerows(filas)
        print(f"\nEjecuciones guardadas en {args.csv}")
    if args.convergencia:
        with open(args.convergencia, 'w', newline='', encoding='utf-8') as archivo:
            escritor = csv.writer(archivo)
            escritor.writerow(['metaheuristica', 'semilla', 't_ms', 'paso', 'mejor_costo', 'duras'])
            escritor.writerows(historiales)
        print(f"Historial de convergencia guardado en {args.convergencia}")


if __name__ == '__main__':
    main()
