# -*- coding: utf-8 -*-
"""
Modelo de sesiones del horario y función de costo incremental.

Es el estado compartido sobre el que trabajan la solución inicial (construccion.py)
y las metaheurísticas (metaheuristicas/). Cada curso se descompone en sesiones
(bloques dobles de 90 min o simples de 45 min). Los dobles ocupan siempre un par
pedagógico (1-2, 3-4, 5-6, 7-8, 9-10), por lo que nunca cruzan un recreo, y la
jornada de cada curso queda completa sin huecos. Las franjas de electivos son
sesiones fijas compartidas por las secciones A y B.

Cada restricción se representa con una clave ('D' docente, 'F' asignatura en el día,
'G' recintos deportivos, 'R' sala de capacidad limitada) cuyo costo se actualiza al
registrar o retirar una sesión, así un movimiento se evalúa sin recorrer el horario.
"""

from collections import defaultdict

from .datos import DatosColegio
from .horario import HorarioEscolar


class ModeloHorario:
    """Sesiones, celdas movibles de cada curso y costo incremental de las restricciones."""

    PESO_DURO = 1000   # Costo de cada violación dura
    PESO_PATIO = 1     # Costo blando por bloque de Ed. Física desbordado al Patio Santo Domingo

    def __init__(self):
        malla = DatosColegio.get_malla_curricular()
        self.cursos = DatosColegio.todos_los_cursos()
        self.ses = []                                 # sesiones (movibles y fijas)
        self.pos = {}                                 # sid -> tupla de celdas (dia, bloque)
        self.celda = {c: {} for c in self.cursos}     # celdas movibles: (dia, bloque) -> sid | None
        self.pares = {c: [] for c in self.cursos}     # pares pedagógicos completos y movibles
        self.par_de = {c: {} for c in self.cursos}    # celda -> par que la contiene
        self.occ = defaultdict(set)                   # clave de restricción -> sids
        self.malos = set()                            # claves con violación dura
        self.blandos = set()                          # claves con costo blando
        self.costo = 0
        self.duras = 0

        # Franjas de electivos: sesiones fijas compartidas por A y B
        fijas = defaultdict(set)
        for nivel, franjas in DatosColegio.FRANJAS_ELECTIVOS.items():
            for k, franja in enumerate(franjas, 1):
                docentes = tuple(dict.fromkeys(g[2] for g in franja['grupos']))
                for dia, b0 in franja['periodos']:
                    celdas = ((dia, b0), (dia, b0 + 1))
                    sid = self._nueva_sesion(None, DatosColegio.nombre_franja(k), docentes, 'Salas electivos',
                                             2, fijo=True, clave=f'ELECTIVOS {nivel}', nivel=nivel, franja=k)
                    self.pos[sid] = celdas
                    for seccion in ('A', 'B'):
                        fijas[f'{nivel} {seccion}'].update(celdas)

        # Celdas y pares movibles de cada curso
        for c in self.cursos:
            for dia in DatosColegio.DIAS:
                permitidos = DatosColegio.get_bloques_permitidos(c, dia)
                for b in permitidos:
                    if (dia, b) not in fijas[c]:
                        self.celda[c][(dia, b)] = None
                for b1, b2 in DatosColegio.PARES:
                    if (dia, b1) in self.celda[c] and (dia, b2) in self.celda[c]:
                        par = ((dia, b1), (dia, b2))
                        self.pares[c].append(par)
                        self.par_de[c][(dia, b1)] = par
                        self.par_de[c][(dia, b2)] = par

        # Sesiones de cada curso: dobles para las horas pares y un simple para el resto
        for c in self.cursos:
            for asig, horas, doc, espacio in malla[c]:
                if asig.startswith('Formación Diferenciada'):
                    continue
                docentes = DatosColegio.docentes_de(doc)
                if DatosColegio.es_parvulo(c):
                    largos = [1] * horas
                else:
                    largos = [2] * (horas // 2) + [1] * (horas % 2)
                for largo in largos:
                    self._nueva_sesion(c, asig, docentes, espacio, largo)

        for sid, s in enumerate(self.ses):
            if s['fijo']:
                self.registrar(sid, self.pos[sid], +1)

    def _nueva_sesion(self, curso, asig, docentes, espacio, largo, fijo=False, clave=None, **extra):
        sesion = {
            'curso': curso,
            'asig': asig,
            'fam': None if fijo else DatosColegio.familia(asig),
            'docs': docentes,
            'espacio': espacio,
            'recurso': espacio if espacio in DatosColegio.RECURSOS_CAPACIDAD else None,
            'zona': DatosColegio.zona_deportiva(curso) if espacio == 'Gimnasio' else None,
            'largo': largo,
            'fijo': fijo,
            'clave': clave or curso,
        }
        sesion.update(extra)
        self.ses.append(sesion)
        return len(self.ses) - 1

    def movibles(self):
        """Ids de las sesiones que se pueden ubicar y mover (todas salvo los electivos)."""
        return [i for i, s in enumerate(self.ses) if not s['fijo']]

    # ------------------------------------------------------------------
    # Costos incrementales
    # ------------------------------------------------------------------
    def costo_clave(self, k):
        """Retorna (costo, violaciones duras, costo blando) de una clave de restricción."""
        s = self.occ.get(k)
        if not s or len(s) < 2:
            return 0, 0, 0
        tipo = k[0]
        if tipo == 'D':
            n = len({self.ses[i]['clave'] for i in s}) - 1
            return n * self.PESO_DURO, n, 0
        if tipo == 'F':
            n = len(s) - 1
            return n * self.PESO_DURO, n, 0
        if tipo == 'R':
            n = max(0, len(s) - DatosColegio.RECURSOS_CAPACIDAD[k[1]])
            return n * self.PESO_DURO, n, 0
        # tipo 'G': un curso por gimnasio y uno más en el Patio Santo Domingo
        zona_b = sum(1 for i in s if self.ses[i]['zona'] == 'GIMNASIO B')
        exceso = max(0, zona_b - 1) + max(0, len(s) - zona_b - 1)
        dura = max(0, exceso - 1)
        blando = min(exceso, 1) * self.PESO_PATIO
        return dura * self.PESO_DURO + blando, dura, blando

    def claves_sesion(self, sid, celdas):
        """Claves de restricción que toca la sesión 'sid' si ocupa 'celdas'."""
        s = self.ses[sid]
        claves = []
        for (dia, b) in celdas:
            for doc in s['docs']:
                claves.append(('D', doc, dia, b))
            if s['zona']:
                claves.append(('G', dia, b))
            if s['recurso']:
                claves.append(('R', s['recurso'], dia, b))
        if s['fam'] is not None:
            claves.append(('F', s['curso'], celdas[0][0], s['fam']))
        return claves

    def registrar(self, sid, celdas, signo):
        """Agrega (+1) o quita (-1) una sesión de sus celdas y retorna la variación de costo."""
        delta = 0
        for k in self.claves_sesion(sid, celdas):
            c0, d0, b0 = self.costo_clave(k)
            if signo > 0:
                self.occ[k].add(sid)
            else:
                self.occ[k].discard(sid)
            c1, d1, b1 = self.costo_clave(k)
            delta += c1 - c0
            self.duras += d1 - d0
            if d1 > 0:
                self.malos.add(k)
            else:
                self.malos.discard(k)
            if b1 > 0:
                self.blandos.add(k)
            else:
                self.blandos.discard(k)
        self.costo += delta
        return delta

    def ubicar(self, sid, celdas):
        """Ubica una sesión aún no ubicada en celdas libres de su curso y retorna la variación de costo."""
        c = self.ses[sid]['curso']
        for x in celdas:
            self.celda[c][x] = sid
        self.pos[sid] = celdas
        return self.registrar(sid, celdas, +1)

    def mover(self, c, mapa):
        """Permuta el contenido de las celdas de un curso según 'mapa' y retorna la variación de costo."""
        cel = self.celda[c]
        sids = []
        for x in mapa:
            sid = cel[x]
            if sid is not None and sid not in sids:
                sids.append(sid)
        delta = 0
        nuevas = {}
        for sid in sids:
            delta += self.registrar(sid, self.pos[sid], -1)
            nuevas[sid] = tuple(sorted(mapa[x] for x in self.pos[sid]))
        contenido = {x: cel[x] for x in mapa}
        for x, y in mapa.items():
            cel[y] = contenido[x]
        for sid in sids:
            self.pos[sid] = nuevas[sid]
            delta += self.registrar(sid, nuevas[sid], +1)
        return delta

    # ------------------------------------------------------------------
    # Vecindario
    # ------------------------------------------------------------------
    def vecinos(self, sid):
        """Intercambios válidos que mueven la sesión 'sid' dentro de su curso."""
        s = self.ses[sid]
        c = s['curso']
        cel = self.celda[c]
        celdas = self.pos[sid]
        movimientos = []
        propio = self.par_de[c].get(celdas[0])
        if propio is not None:
            for otro in self.pares[c]:
                if otro != propio:
                    movimientos.append({propio[0]: otro[0], propio[1]: otro[1], otro[0]: propio[0], otro[1]: propio[1]})
        if s['largo'] == 1:
            u = celdas[0]
            for v, sv in cel.items():
                if v != u and (sv is None or self.ses[sv]['largo'] == 1):
                    movimientos.append({u: v, v: u})
        return movimientos

    def restaurar(self, posiciones):
        """Reconstruye todas las estructuras a partir de una asignación de posiciones."""
        self.occ = defaultdict(set)
        self.malos = set()
        self.blandos = set()
        self.costo = 0
        self.duras = 0
        self.pos = dict(posiciones)
        for c in self.cursos:
            for x in self.celda[c]:
                self.celda[c][x] = None
        for sid, s in enumerate(self.ses):
            if not s['fijo']:
                for x in self.pos[sid]:
                    self.celda[s['curso']][x] = sid
            self.registrar(sid, self.pos[sid], +1)

    # ------------------------------------------------------------------
    # Salida
    # ------------------------------------------------------------------
    def a_horario(self):
        """Convierte las posiciones de las sesiones en un HorarioEscolar."""
        horario = HorarioEscolar()
        for sid, s in enumerate(self.ses):
            if not s['fijo']:
                for dia, b in self.pos[sid]:
                    horario.asignar(s['curso'], dia, b, s['asig'], s['docs'], s['espacio'])
                continue
            franja = DatosColegio.FRANJAS_ELECTIVOS[s['nivel']][s['franja'] - 1]
            detalle = {}
            for asig, seccion, doc, sala, etiqueta in franja['grupos']:
                detalle[doc] = (etiqueta, sala, f"{asig.capitalize()} ({seccion})")
            for i, (dia, b) in enumerate(self.pos[sid]):
                for seccion in ('A', 'B'):
                    curso = f"{s['nivel']} {seccion}"
                    etiqueta = DatosColegio.etiquetas_franja(franja, curso)[i]
                    horario.asignar(curso, dia, b, s['asig'], s['docs'], s['espacio'], etiqueta=etiqueta,
                                    clave=f"{s['nivel']} A-B", detalle=detalle)
        return horario
