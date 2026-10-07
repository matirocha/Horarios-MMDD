# -*- coding: utf-8 -*-
"""
Interfaz común de las metaheurísticas de mejora.

Para agregar una metaheurística nueva:
  1. Crear un módulo en esta carpeta con una subclase de Metaheuristica que defina
     'nombre' e implemente 'buscar'. Su constructor debe aceptar 'max_pasos'.
  2. Registrarla en METAHEURISTICAS (metaheuristicas/__init__.py).
Luego queda disponible en 'generador_horarios.py --metaheuristica <nombre>' y en
'comparar_metaheuristicas.py'.
"""


class Metaheuristica:
    """
    Recibe un ModeloHorario con una solución completa (la de la construcción voraz)
    y lo modifica en el lugar para bajar su costo. Para moverse puede usar
    modelo.vecinos(sid), modelo.mover(curso, mapa) y modelo.restaurar(posiciones);
    el costo actual está en modelo.costo y las violaciones duras en modelo.duras.
    """

    nombre = None

    def __init__(self, max_pasos=150000):
        self.max_pasos = max_pasos

    def buscar(self, modelo, rng):
        """
        Mejora 'modelo' usando el generador aleatorio 'rng' y retorna un diccionario
        de estadísticas con, al menos, 'pasos' (iteraciones realizadas) y 'motivo_parada'.
        """
        raise NotImplementedError
