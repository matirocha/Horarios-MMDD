# -*- coding: utf-8 -*-
"""
Motor de generación de horarios: encadena el modelo de sesiones, la solución
inicial y una metaheurística de mejora, y mide el tiempo de cada fase.
"""

import random
import time

from .construccion import ConstruccionVoraz
from .metaheuristicas import crear_metaheuristica
from .modelo import ModeloHorario


class MotorHorarios:
    """
    Motor heurístico para resolver el School Timetabling Problem del Colegio MMDD.

    1. Modelo de sesiones (ModeloHorario): bloques dobles de 90 min o simples de 45 min,
       con las franjas de electivos fijas y compartidas por las secciones A y B.
    2. Solución inicial (ConstruccionVoraz): sesiones dobles y luego simples, de la más
       restringida a la menos restringida, en la posición de menor costo.
    3. Metaheurística de mejora (por defecto Min-Conflicts con lista tabú): repara las
       violaciones intercambiando sesiones dentro de cada curso.

    Las tres fases comparten un mismo generador aleatorio con semilla 'seed', así cada
    ejecución con la misma semilla da el mismo horario. Tras generar(), 'tiempos' guarda
    la duración de cada fase en segundos y 'estadisticas' el resultado de la búsqueda.
    """

    PESO_DURO = ModeloHorario.PESO_DURO
    PESO_PATIO = ModeloHorario.PESO_PATIO

    def __init__(self, seed=42, max_pasos=150000, metaheuristica='min_conflicts_tabu', construccion=None):
        self.seed = seed
        self.max_pasos = max_pasos
        if isinstance(metaheuristica, str):
            metaheuristica = crear_metaheuristica(metaheuristica, max_pasos=max_pasos)
        self.metaheuristica = metaheuristica
        self.construccion = construccion or ConstruccionVoraz()
        self.modelo = None
        self.tiempos = {}
        self.estadisticas = {}

    def generar(self):
        """
        Ejecuta la construcción y optimización de horarios.
        Busca 0 colisiones duras, 0 repeticiones de asignaturas por día y bloques dobles.
        """
        rng = random.Random(self.seed)
        t0 = time.perf_counter()
        self.modelo = ModeloHorario()
        t1 = time.perf_counter()
        self.construccion.construir(self.modelo, rng)
        t2 = time.perf_counter()
        costo_construccion, duras_construccion = self.modelo.costo, self.modelo.duras
        resultado = self.metaheuristica.buscar(self.modelo, rng)
        t3 = time.perf_counter()
        horario = self.modelo.a_horario()
        t4 = time.perf_counter()

        self.tiempos = {'preparacion': t1 - t0, 'construccion': t2 - t1, 'busqueda': t3 - t2,
                        'salida': t4 - t3, 'total': t4 - t0}
        self.estadisticas = dict(resultado,
                                 metaheuristica=self.metaheuristica.nombre,
                                 costo_construccion=costo_construccion,
                                 duras_construccion=duras_construccion,
                                 costo_final=self.modelo.costo,
                                 duras_finales=self.modelo.duras)
        return horario
