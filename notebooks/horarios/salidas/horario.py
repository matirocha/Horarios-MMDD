# -*- coding: utf-8 -*-
"""
Estructura de datos del horario escolar: asignaciones por curso, ocupación de
docentes y de recintos deportivos.
"""

from collections import defaultdict

from ..datos import DatosColegio


class HorarioEscolar:
    """Representación matricial global del horario del colegio."""

    def __init__(self):
        # asignaciones[curso][dia][bloque] = {asignatura, docentes, docente, espacio, etiqueta}
        self.asignaciones = {
            c: {d: {} for d in DatosColegio.DIAS} for c in DatosColegio.todos_los_cursos()
        }
        # docente_ocupado[docente][(dia, bloque)] = (curso, asignatura)
        self.docente_ocupado = defaultdict(dict)
        # docente_claves[docente][(dia, bloque)] = {cursos o grupos atendidos en ese bloque}
        self.docente_claves = defaultdict(lambda: defaultdict(set))
        # docente_detalle[docente][(dia, bloque)] = {'etiqueta', 'sala'} (electivos)
        self.docente_detalle = defaultdict(dict)
        # gimnasio_ocupado[(dia, bloque)] = list(cursos)
        self.gimnasio_ocupado = defaultdict(list)

    def asignar(self, curso, dia, bloque, asignatura, docentes, espacio='Aula', etiqueta=None,
                clave=None, detalle=None):
        """
        Asigna una lección en el horario garantizando actualización de estados.
        'clave' identifica a quién atiende el docente (el curso, o el grupo compartido de un
        electivo) y 'detalle' permite indicar por docente la etiqueta y sala de su sección.
        """
        docentes = DatosColegio.docentes_de(docentes)
        self.asignaciones[curso][dia][bloque] = {
            'asignatura': asignatura,
            'docentes': docentes,
            'docente': ' / '.join(docentes),
            'espacio': espacio,
            'etiqueta': etiqueta or DatosColegio.ETIQUETAS.get(asignatura, asignatura.upper()),
        }
        clave = clave or curso
        for doc in docentes:
            self.docente_claves[doc][(dia, bloque)].add(clave)
            if detalle and doc in detalle:
                etiqueta_doc, sala, asig_doc = detalle[doc]
                self.docente_ocupado[doc][(dia, bloque)] = (clave, asig_doc)
                self.docente_detalle[doc][(dia, bloque)] = {'etiqueta': etiqueta_doc, 'sala': sala}
            else:
                self.docente_ocupado[doc][(dia, bloque)] = (curso, asignatura)
        if espacio == 'Gimnasio':
            self.gimnasio_ocupado[(dia, bloque)].append(curso)

    def asignar_recintos(self):
        """
        Distribuye los cursos en Ed. Física de cada bloque en el gimnasio de su ciclo.
        Si un gimnasio recibe más de un curso, el validador lo informa como sobrecupo.
        Retorna {(recinto, dia, bloque): [cursos]}.
        """
        recintos = defaultdict(list)
        for (dia, bloque), cursos in self.gimnasio_ocupado.items():
            for curso in cursos:
                recintos[(DatosColegio.zona_deportiva(curso), dia, bloque)].append(curso)
        return recintos
