# -*- coding: utf-8 -*-
"""
Fase de mejora: clases base y medición del tiempo de ejecución.

  MetodoMejora    base de todo método que mejora una solución completa.
  Metaheuristica  base de las metaheurísticas (metaheuristicas/).
  Seguimiento     cronómetro y memoria de la mejor solución de cada búsqueda.

La heurística Min-Conflicts (heuristicas/min_conflicts.py) hereda de MetodoMejora y
cada metaheurística de Metaheuristica. La clase base se encarga de lo que debe medirse
igual en todos los métodos para poder compararlos:

  - el cronómetro de la búsqueda y el límite de tiempo opcional ('tiempo_max');
  - la mejor solución encontrada (costo y posiciones) y su restauración al final;
  - el instante y el paso en que se alcanzó la primera solución factible y la mejor;
  - el historial de convergencia: (segundos, paso, costo, violaciones duras) cada vez
    que mejora la mejor solución.

Cada método solo implementa _buscar(modelo, rng, seg) y llama a seg.registrar(paso, modelo)
después de cada movimiento.
"""

import time


class Seguimiento:
    """Cronómetro de la búsqueda y memoria de la mejor solución encontrada."""

    def __init__(self, modelo, tiempo_max=None):
        self.inicio = time.perf_counter()
        self.tiempo_max = tiempo_max
        self.mejor_costo = modelo.costo
        self.mejor_pos = dict(modelo.pos)
        self.t_mejor, self.paso_mejor = 0.0, 0
        factible = modelo.duras == 0
        self.t_factible = 0.0 if factible else None
        self.paso_factible = 0 if factible else None
        self.historial = [(0.0, 0, modelo.costo, modelo.duras)]

    def transcurrido(self):
        """Segundos desde el inicio de la búsqueda."""
        return time.perf_counter() - self.inicio

    def tiempo_agotado(self):
        return self.tiempo_max is not None and self.transcurrido() >= self.tiempo_max

    def registrar(self, paso, modelo):
        """
        Se llama después de cada movimiento (paso = índice del paso, desde 0).
        Guarda la solución si mejora la mejor encontrada y retorna True en ese caso.
        """
        if self.t_factible is None and modelo.duras == 0:
            self.t_factible, self.paso_factible = self.transcurrido(), paso + 1
        if modelo.costo < self.mejor_costo:
            t = self.transcurrido()
            self.mejor_costo = modelo.costo
            self.mejor_pos = dict(modelo.pos)
            self.t_mejor, self.paso_mejor = t, paso + 1
            self.historial.append((t, paso + 1, modelo.costo, modelo.duras))
            return True
        return False

    def restaurar_mejor(self, modelo):
        """Deja en 'modelo' la mejor solución encontrada."""
        if modelo.costo > self.mejor_costo:
            modelo.restaurar(self.mejor_pos)

    def resumen(self):
        return {
            't_busqueda': self.transcurrido(),
            't_factible': self.t_factible,
            'paso_factible': self.paso_factible,
            't_mejor': self.t_mejor,
            'paso_mejor': self.paso_mejor,
            'historial': self.historial,
        }


class MetodoMejora:
    """
    Recibe un ModeloHorario con una solución completa (la de la construcción voraz)
    y lo modifica en el lugar para bajar su costo (modelo.costo, ver modelo.py).

    Para moverse puede usar modelo.vecinos(sid), modelo.mover(curso, mapa) y
    modelo.restaurar(posiciones), y los operadores de heuristicas/min_conflicts.py.

    Criterios de parada comunes: costo 0 (óptimo: no hay nada que mejorar),
    'max_pasos' pasos o 'tiempo_max' segundos (None = sin límite de tiempo).
    """

    nombre = None
    tipo = None   # 'heurística' o 'metaheurística'

    def __init__(self, max_pasos=150000, tiempo_max=None):
        self.max_pasos = max_pasos
        self.tiempo_max = tiempo_max

    def buscar(self, modelo, rng):
        """
        Mejora 'modelo' usando el generador aleatorio 'rng'. Retorna las estadísticas de
        la búsqueda: 'pasos', 'motivo_parada', los tiempos de Seguimiento.resumen() y las
        que agregue cada método.
        """
        seg = Seguimiento(modelo, self.tiempo_max)
        resultado = self._buscar(modelo, rng, seg)
        seg.restaurar_mejor(modelo)
        resultado.update(seg.resumen())
        return resultado

    def _buscar(self, modelo, rng, seg):
        """Bucle de búsqueda de cada método. Retorna al menos {'pasos', 'motivo_parada'}."""
        raise NotImplementedError

    @staticmethod
    def parada_comun(modelo, seg):
        """Motivo de parada común a todos los métodos, o None si la búsqueda sigue."""
        if modelo.costo == 0:
            return 'costo_cero'
        if seg.tiempo_agotado():
            return 'tiempo_max'
        return None


class Metaheuristica(MetodoMejora):
    """
    Método de mejora que guía a la búsqueda local para escapar de óptimos locales.
    Para crear una nueva, ver las instrucciones en metaheuristicas/__init__.py.
    """

    tipo = 'metaheurística'
