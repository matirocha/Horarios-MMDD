# -*- coding: utf-8 -*-
"""
Métodos de mejora disponibles: metaheurísticas y la heurística Min-Conflicts sola.

Todos parten del horario de la construcción voraz (heuristicas/construccion_voraz.py)
y lo reparan. El tiempo de cada búsqueda se mide en la clase base (mejora.py). Para
comparar tiempos y resultados entre ellos, ver notebooks/comparar_metaheuristicas.py.

  min_conflicts            Heurística Min-Conflicts sola (línea base, heuristicas/min_conflicts.py)
  busqueda_tabu            Búsqueda tabú (busqueda_tabu.py)
  busqueda_local_iterada   Búsqueda local iterada, ILS (busqueda_local_iterada.py)
  min_conflicts_tabu       Híbrido tabú + ruido + reinicios ILS (min_conflicts_tabu.py, por defecto)

CÓMO AGREGAR UNA METAHEURÍSTICA NUEVA
  1. Crear un archivo en esta carpeta con una subclase de Metaheuristica (mejora.py) que
     defina 'nombre' e implemente _buscar(modelo, rng, seg). Su constructor debe aceptar
     'max_pasos' y 'tiempo_max' y pasarlos a super().__init__.
  2. En el bucle de búsqueda: revisar self.parada_comun(modelo, seg) al inicio de cada paso
     y llamar a seg.registrar(paso, modelo) después de cada movimiento. Así el tiempo, la
     mejor solución y la curva de convergencia se miden igual que en las demás.
     Los operadores de búsqueda local están en heuristicas/min_conflicts.py.
  3. Registrarla en METAHEURISTICAS (abajo). Queda disponible en
     'generador_horarios.py --metaheuristica <nombre>' y en 'comparar_metaheuristicas.py'.
"""

from ..heuristicas.min_conflicts import MinConflictos
from ..mejora import Metaheuristica
from .busqueda_local_iterada import BusquedaLocalIterada
from .busqueda_tabu import BusquedaTabu
from .min_conflicts_tabu import MinConflictosTabu

# Registro: nombre -> clase. Agregar aquí cada metaheurística nueva.
METAHEURISTICAS = {
    MinConflictos.nombre: MinConflictos,
    BusquedaTabu.nombre: BusquedaTabu,
    BusquedaLocalIterada.nombre: BusquedaLocalIterada,
    MinConflictosTabu.nombre: MinConflictosTabu,
}


def crear_metaheuristica(nombre, **parametros):
    """Instancia el método de mejora registrado con ese nombre."""
    if nombre not in METAHEURISTICAS:
        raise ValueError(f"Metaheurística desconocida: '{nombre}'. Disponibles: {', '.join(sorted(METAHEURISTICAS))}")
    return METAHEURISTICAS[nombre](**parametros)


__all__ = ['Metaheuristica', 'MinConflictos', 'BusquedaTabu', 'BusquedaLocalIterada', 'MinConflictosTabu',
           'METAHEURISTICAS', 'crear_metaheuristica']
