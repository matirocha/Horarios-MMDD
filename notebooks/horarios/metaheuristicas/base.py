# -*- coding: utf-8 -*-
"""
Interfaz común de las metaheurísticas de mejora.

Para agregar una metaheurística nueva:
  1. Crear un módulo en esta carpeta con una subclase de Metaheuristica que defina
     'nombre' e implemente _buscar(modelo, rng, seg). Su constructor debe aceptar
     'max_pasos' y 'tiempo_max' y pasarlos a super().__init__.
  2. En el bucle de búsqueda: revisar self.parada_comun(modelo, seg) al inicio de cada
     paso y llamar a seg.registrar(paso, modelo) después de cada movimiento. Con eso el
     tiempo, la mejor solución y la curva de convergencia se miden igual que en las demás.
  3. Registrarla en METAHEURISTICAS (metaheuristicas/__init__.py).
Luego queda disponible en 'generador_horarios.py --metaheuristica <nombre>' y en
'comparar_metaheuristicas.py'.

Los operadores de búsqueda local (elegir una sesión en conflicto, evaluar y elegir el
mejor intercambio) están en heuristicas/min_conflicts.py.
"""

from ..mejora import MetodoMejora, Seguimiento


class Metaheuristica(MetodoMejora):
    """
    Método de mejora que guía a la búsqueda local para escapar de óptimos locales.
    Ver MetodoMejora (mejora.py) para el contrato completo y la medición de tiempos.
    """

    tipo = 'metaheurística'


__all__ = ['Metaheuristica', 'Seguimiento']
