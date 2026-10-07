# -*- coding: utf-8 -*-
"""
Metaheurísticas de mejora disponibles.

Cada una toma el horario de la construcción voraz y lo repara. Para comparar
tiempos de respuesta entre ellas, ver notebooks/comparar_metaheuristicas.py.
"""

from .base import Metaheuristica
from .min_conflicts_tabu import MinConflictosTabu

# Registro: nombre -> clase. Agregar aquí cada metaheurística nueva.
METAHEURISTICAS = {
    MinConflictosTabu.nombre: MinConflictosTabu,
}


def crear_metaheuristica(nombre, **parametros):
    """Instancia la metaheurística registrada con ese nombre."""
    if nombre not in METAHEURISTICAS:
        raise ValueError(f"Metaheurística desconocida: '{nombre}'. Disponibles: {', '.join(sorted(METAHEURISTICAS))}")
    return METAHEURISTICAS[nombre](**parametros)


__all__ = ['Metaheuristica', 'MinConflictosTabu', 'METAHEURISTICAS', 'crear_metaheuristica']
