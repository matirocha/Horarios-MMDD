# -*- coding: utf-8 -*-
"""
HEURÍSTICA CONSTRUCTIVA VORAZ (solución inicial).

Ubica todas las sesiones movibles del ModeloHorario, de la más restringida a la
menos restringida, cada una en la posición libre de menor costo:

  1. Orden: sesiones dobles antes que simples; luego las de co-docencia, las de
     docentes con mayor carga, las de Educación Física (usan gimnasio) y, a igualdad,
     un desempate aleatorio.
  2. Para cada sesión se prueban sus posiciones libres (pares pedagógicos para las
     dobles, bloques sueltos para las simples) y se elige la de menor aumento de la
     función objetivo (ver ModeloHorario). Si una posición no agrega costo se toma de
     inmediato.

Es una heurística: decide una vez cada sesión y nunca la reconsidera. El resultado es
un horario completo (cada curso cubre su malla y su jornada), pero puede tener
violaciones duras que luego reparan los métodos de mejora (heuristicas/min_conflicts.py
y metaheuristicas/).
"""

from ..datos import DatosColegio


class ConstruccionVoraz:
    """Construcción voraz: sesiones dobles y luego simples, en la posición de menor costo."""

    nombre = 'voraz'
    tipo = 'heurística constructiva'

    def construir(self, modelo, rng):
        """Ubica en 'modelo' todas sus sesiones movibles. Modifica el modelo en el lugar."""
        carga = DatosColegio.carga_docente()
        orden = sorted(modelo.movibles(), key=lambda i: (
            -modelo.ses[i]['largo'],
            -len(modelo.ses[i]['docs']),
            -max(carga[d] for d in modelo.ses[i]['docs']),
            modelo.ses[i]['zona'] is None,
            rng.random(),
        ))
        for sid in orden:
            s = modelo.ses[sid]
            c = s['curso']
            if s['largo'] == 2:   # 'c' es una tupla (A, B) en una franja móvil: par libre en ambos cursos
                opciones = [par for par in modelo.pares_de(c) if modelo.libre(c, par)]
            else:
                opciones = [(x,) for x, v in modelo.celda[c].items() if v is None]
            mejor, mejor_delta = None, None
            rng.shuffle(opciones)
            for celdas in opciones:
                delta = modelo.registrar(sid, celdas, +1)
                modelo.registrar(sid, celdas, -1)
                if mejor_delta is None or delta < mejor_delta:
                    mejor, mejor_delta = celdas, delta
                    if delta == 0:
                        break
            if mejor is None:
                raise RuntimeError(f"No hay espacio en la jornada de {c} para {s['asig']}")
            modelo.ubicar(sid, mejor)
