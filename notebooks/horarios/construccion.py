# -*- coding: utf-8 -*-
"""
Solución inicial: heurística constructiva voraz.

Ubica todas las sesiones movibles del ModeloHorario, de la más restringida a la
menos restringida, cada una en la posición libre de menor costo. El resultado es
un horario completo (cada curso cubre su malla y su jornada), pero puede tener
violaciones que luego repara una metaheurística.
"""

from .datos import DatosColegio


class ConstruccionVoraz:
    """Construcción voraz: sesiones dobles y luego simples, en la posición de menor costo."""

    nombre = 'voraz'

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
            if s['largo'] == 2:
                opciones = [par for par in modelo.pares[c]
                            if modelo.celda[c][par[0]] is None and modelo.celda[c][par[1]] is None]
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
