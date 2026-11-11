# -*- coding: utf-8 -*-
"""
Metaheurísticas de mejora. Las dos parten de la solución de la heurística constructiva
(heuristicas/construccion_voraz.py), usan el mismo vecindario y la misma perturbación
(vecindario.py) y se diferencian solo en su búsqueda local:

  ils   Búsqueda local iterada (busqueda_local_iterada.py): descenso de mayor pendiente.
  its   Búsqueda tabú iterada (busqueda_tabu_iterada.py): búsqueda tabú (por defecto).

El tiempo de cada búsqueda se mide en la clase base (mejora.py). Para comparar horarios y
tiempos de ejecución entre ellas, ver notebooks/comparar_metaheuristicas.py.

CÓMO AGREGAR UNA METAHEURÍSTICA NUEVA
  1. Crear un archivo en esta carpeta con una subclase de Metaheuristica (mejora.py) que
     defina 'nombre' y 'titulo' e implemente _buscar(modelo, rng, seg). Su constructor debe
     aceptar 'max_pasos' y 'tiempo_max' y pasarlos a super().__init__.
  2. En el bucle de búsqueda: revisar self.parada_comun(modelo, seg) antes de cada paso y
     llamar a seg.registrar(paso, modelo) después de cada movimiento. Así el tiempo, la
     mejor solución y la curva de convergencia se miden igual que en las demás.
     El vecindario, la evaluación de movimientos y la perturbación están en vecindario.py.
  3. Registrarla en METAHEURISTICAS (abajo). Queda disponible en
     'generador_horarios.py --metaheuristica <nombre>' y en 'comparar_metaheuristicas.py'.
"""

from ..mejora import Metaheuristica
from .busqueda_local_iterada import BusquedaLocalIterada
from .busqueda_tabu_iterada import BusquedaTabuIterada, ListaTabu

# Registro: nombre -> clase. Agregar aquí cada metaheurística nueva.
METAHEURISTICAS = {
    BusquedaLocalIterada.nombre: BusquedaLocalIterada,
    BusquedaTabuIterada.nombre: BusquedaTabuIterada,
}
POR_DEFECTO = BusquedaTabuIterada.nombre


def crear_metaheuristica(nombre, **parametros):
    """Instancia la metaheurística registrada con ese nombre."""
    if nombre not in METAHEURISTICAS:
        raise ValueError(f"Metaheurística desconocida: '{nombre}'. Disponibles: {', '.join(sorted(METAHEURISTICAS))}")
    return METAHEURISTICAS[nombre](**parametros)


__all__ = ['Metaheuristica', 'BusquedaLocalIterada', 'BusquedaTabuIterada', 'ListaTabu',
           'METAHEURISTICAS', 'POR_DEFECTO', 'crear_metaheuristica']
