# -*- coding: utf-8 -*-
"""
VECINDARIO Y OPERADORES COMUNES DE LAS METAHEURÍSTICAS (ILS e ITS).

Las dos metaheurísticas parten de la solución de la heurística constructiva
(heuristicas/construccion_voraz.py) y se mueven con los mismos operadores, para que
la comparación de horarios y tiempos dependa solo de la estrategia de búsqueda:

  Movimiento   intercambio de sesiones dentro de un curso (modelo.vecinos): un bloque
               doble con otro par pedagógico, o un bloque simple con otra celda simple o
               libre. Así la carga horaria y la jornada de cada curso nunca cambian.

  Vecindario   N(x): todos los intercambios distintos de las sesiones que participan en
               alguna violación de x ('conflictos', por defecto) o de todas las sesiones
               movibles ('completo'). Se evalúa COMPLETO en cada paso y se elige el mejor
               movimiento (mejor mejora, empates al azar).

  Perturbación k intercambios al azar, cada uno en un curso elegido al azar.

La variación de costo de un movimiento se calcula de forma incremental (ModeloHorario.mover
lo aplica y retorna el delta; se deshace con la permutación inversa).
"""

VECINDARIOS = ('conflictos', 'completo')


def sesiones_del_vecindario(modelo, vecindario='conflictos'):
    """Sesiones cuyos intercambios forman N(x)."""
    if vecindario == 'completo':
        return modelo.movibles()
    fuente = modelo.malos if modelo.malos else modelo.blandos
    return sorted({i for k in fuente for i in modelo.occ[k] if not modelo.ses[i]['fijo']})


def movimientos(modelo, sids):
    """Intercambios distintos que mueven alguna de las sesiones 'sids': lista de (curso, mapa)."""
    vistos = set()
    lista = []
    for sid in sids:
        c = modelo.ses[sid]['curso']
        for mapa in modelo.vecinos(sid):
            clave = (c, frozenset(mapa.items()))
            if clave not in vistos:
                vistos.add(clave)
                lista.append((c, mapa))
    return lista


def vecindario(modelo, tipo='conflictos'):
    """N(x) de la solución actual: lista de movimientos (curso, mapa)."""
    return movimientos(modelo, sesiones_del_vecindario(modelo, tipo))


def evaluar(modelo, c, mapa):
    """Variación del costo al aplicar el movimiento (lo aplica y lo deshace)."""
    delta = modelo.mover(c, mapa)
    modelo.mover(c, {y: x for x, y in mapa.items()})
    return delta


def sesiones_movidas(modelo, c, mapa):
    """Sesiones que mueve el intercambio y la posición a la que llegaría cada una: [(sid, celdas)]."""
    sids = dict.fromkeys(modelo.celda[cur][x] for cur in modelo.como_tupla(c) for x in mapa
                         if modelo.celda[cur][x] is not None)
    return [(sid, tuple(sorted(mapa[x] for x in modelo.pos[sid]))) for sid in sids]


def mejor_movimiento(modelo, candidatos, rng, admisible=None):
    """
    Evalúa todos los candidatos y retorna (movimiento, variación) con la menor variación de
    costo; los empates se deciden al azar con probabilidad uniforme. 'admisible(c, mapa, delta)',
    si se entrega, descarta movimientos (los prohibidos por la lista tabú). Retorna (None, None)
    si ninguno es admisible.
    """
    elegido, mejor, empates = None, None, 0
    for c, mapa in candidatos:
        delta = evaluar(modelo, c, mapa)
        if admisible is not None and not admisible(c, mapa, delta):
            continue
        if mejor is None or delta < mejor:
            elegido, mejor, empates = (c, mapa), delta, 1
        elif delta == mejor:
            empates += 1
            if rng.randrange(empates) == 0:
                elegido = (c, mapa)
    return elegido, mejor


def perturbar(modelo, rng, intensidad):
    """Aplica 'intensidad' intercambios al azar, cada uno en un curso elegido al azar."""
    for _ in range(intensidad):
        c = rng.choice(modelo.cursos)
        sids_c = sorted({v for v in modelo.celda[c].values() if v is not None})
        if sids_c:
            sid = rng.choice(sids_c)
            vecinos = modelo.vecinos(sid)
            if vecinos:   # una franja móvil se mueve en sus dos cursos ('curso' es una tupla)
                modelo.mover(modelo.ses[sid]['curso'], rng.choice(vecinos))
