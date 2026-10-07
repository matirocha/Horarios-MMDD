# -*- coding: utf-8 -*-
"""
Parámetros y datos del Colegio Madres Dominicas para el año escolar 2026.

Bloques, jornadas, dotación docente, mallas curriculares, franjas de electivos,
recintos deportivos y salas (fuente: carpeta data/Data 2026).
"""

from collections import defaultdict


class DatosColegio:
    """Catálogo y parámetros institucionales del Colegio Madres Dominicas (año escolar 2026)."""

    ANIO = 2026
    DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']

    # Bloques pedagógicos de 45 minutos (fuente: HORARIO CURSOS 2026.xlsx)
    HORARIOS_BLOQUES = {
        1: ('08:00', '08:45'),
        2: ('08:45', '09:30'),
        3: ('09:45', '10:30'),
        4: ('10:30', '11:15'),
        5: ('11:30', '12:15'),
        6: ('12:15', '13:00'),
        7: ('13:10', '13:55'),
        8: ('13:55', '14:40'),
        9: ('15:10', '15:55'),   # Jornada tarde: solo lunes en 3° y 4° medio
        10: ('15:55', '16:40')   # Jornada tarde: solo lunes en 3° y 4° medio
    }

    # Pausa que sigue a cada bloque: (nombre, rango horario)
    RECREOS = {
        2: ('RECREO', '09:30 - 09:45'),
        4: ('RECREO', '11:15 - 11:30'),
        6: ('RECREO', '13:00 - 13:10'),
        8: ('COLACIÓN', '14:40 - 15:10')
    }

    # Pares pedagógicos de 90 minutos (un bloque doble nunca cruza un recreo)
    PARES = [(1, 2), (3, 4), (5, 6), (7, 8), (9, 10)]

    # Los 24 cursos regulares del colegio
    CURSOS = [
        '1° BÁSICO A', '1° BÁSICO B',
        '2° BÁSICO A', '2° BÁSICO B',
        '3° BÁSICO A', '3° BÁSICO B',
        '4° BÁSICO A', '4° BÁSICO B',
        '5° BÁSICO A', '5° BÁSICO B',
        '6° BÁSICO A', '6° BÁSICO B',
        '7° BÁSICO A', '7° BÁSICO B',
        '8° BÁSICO A', '8° BÁSICO B',
        '1° MEDIO A', '1° MEDIO B',
        '2° MEDIO A', '2° MEDIO B',
        '3° MEDIO A', '3° MEDIO B',
        '4° MEDIO A', '4° MEDIO B'
    ]

    # Párvulos: solo se programa su Educación Física (comparten docente y Gimnasio B con básica)
    CURSOS_PARVULOS = ['PREKINDER A', 'KINDER A', 'KINDER B']

    # Último bloque lectivo de cada día (lunes a viernes) según las mallas 2026.
    # En los datos oficiales 5°A/5°B y 8°A/8°B no comparten la misma jornada.
    JORNADAS = {
        '1° BÁSICO A': (8, 8, 7, 8, 7), '1° BÁSICO B': (8, 8, 7, 8, 7),
        '2° BÁSICO A': (8, 8, 7, 8, 7), '2° BÁSICO B': (8, 8, 7, 8, 7),
        '3° BÁSICO A': (8, 8, 7, 8, 7), '3° BÁSICO B': (8, 8, 7, 8, 7),
        '4° BÁSICO A': (8, 8, 7, 8, 7), '4° BÁSICO B': (8, 8, 7, 8, 7),
        '5° BÁSICO A': (8, 8, 8, 6, 8), '5° BÁSICO B': (8, 8, 8, 8, 6),
        '6° BÁSICO A': (8, 8, 7, 8, 6), '6° BÁSICO B': (8, 8, 7, 8, 6),
        '7° BÁSICO A': (8, 8, 7, 8, 6), '7° BÁSICO B': (8, 8, 7, 8, 6),
        '8° BÁSICO A': (6, 8, 7, 8, 8), '8° BÁSICO B': (8, 8, 7, 8, 6),
        '1° MEDIO A': (8, 8, 8, 8, 8), '1° MEDIO B': (8, 8, 8, 8, 8),
        '2° MEDIO A': (8, 8, 8, 8, 8), '2° MEDIO B': (8, 8, 8, 8, 8),
        '3° MEDIO A': (10, 8, 8, 8, 8), '3° MEDIO B': (10, 8, 8, 8, 8),
        '4° MEDIO A': (10, 8, 8, 8, 8), '4° MEDIO B': (10, 8, 8, 8, 8),
        # Supuesto: la Ed. Física de párvulos se dicta en la jornada de mañana (bloques 1 a 6)
        'PREKINDER A': (6, 6, 6, 6, 6), 'KINDER A': (6, 6, 6, 6, 6), 'KINDER B': (6, 6, 6, 6, 6),
    }

    # Dotación docente 2026, agrupada como en DISTRIBUCIÓN HORARIA 2026.docx
    DEPARTAMENTOS = [
        ('LENGUAJE – FILOSOFÍA - ASIGNATURAS DE PROFUNDIZACIÓN',
         ['Lenguaje 1', 'Lenguaje 2', 'Lenguaje 3', 'Lenguaje 4', 'Lenguaje 5']),
        ('MATEMÁTICA - ASIGNATURAS DE PROFUNDIZACIÓN',
         ['Matemática 1', 'Matemática 2', 'Matemática 3', 'Matemática 4']),
        ('INGLÉS',
         ['Inglés 1', 'Inglés 2', 'Inglés 3', 'Inglés 4', 'Inglés 5']),
        ('HISTORIA, GEOGRAFÍA Y C. SOCIALES – EDUCACIÓN CIUDADANA - ASIGNATURAS DE PROFUNDIZACIÓN',
         ['Historia 1', 'Historia 2', 'Historia 3']),
        ('CIENCIAS NATURALES – CIENCIAS PARA LA CIUDADANÍA - ASIGNATURAS DE PROFUNDIZACIÓN – RELIGIÓN',
         ['Química', 'Biología', 'C. Naturales y Religión', 'C. Naturales', 'Física', 'Religión']),
        ('ARTES VISUALES – MÚSICA – TECNOLOGÍA - ASIGNATURAS DE PROFUNDIZACIÓN',
         ['Artes y Tecnología 1', 'Artes y Tecnología 2', 'Música']),
        ('EDUCACIÓN FÍSICA',
         ['Ed. Física 1', 'Ed. Física 2', 'Ed. Física 3']),
        ('EDUCACIÓN GENERAL BÁSICA',
         ['Básica 1', 'Básica 2', 'Básica 3', 'Básica 4', 'Básica 5', 'Básica 6', 'Básica 7', 'Básica 8']),
    ]

    # Horas declaradas en la distribución que no se programan en la grilla de cursos:
    # docente -> [(cursos, actividad, horas)]
    HORAS_NO_LECTIVAS = {
        'Matemática 2': [('Intv. Media (1° a 4°)', 'Intervención', 24), ('', 'ACLE', 2)],
        'Básica 1': [('', 'Intervención', 7)],
        'Básica 3': [('', 'Intervención', 7)],
        'Básica 4': [('', 'Intervención', 6)],
        'Básica 5': [('', 'Intervención', 6)],
        'Básica 6': [('', 'Intervención', 6)],
        'Básica 7': [('', 'Intervención', 7)],
        'Básica 8': [('', 'Intervención', 6)],
    }

    # Profesores jefes 2026 (filas "Jefatura" de la distribución horaria)
    PROFESORES_JEFES = {
        '1° BÁSICO A': 'Básica 1',
        '1° BÁSICO B': 'Básica 2',
        '2° BÁSICO A': 'Básica 3',
        '2° BÁSICO B': 'Básica 4',
        '3° BÁSICO A': 'Básica 5',
        '3° BÁSICO B': 'Básica 6',
        '4° BÁSICO A': 'Básica 7',
        '4° BÁSICO B': 'Básica 8',
        '5° BÁSICO A': 'Historia 2',
        '5° BÁSICO B': 'Inglés 1',
        '6° BÁSICO A': 'Inglés 4',
        '6° BÁSICO B': 'C. Naturales',
        '7° BÁSICO A': 'C. Naturales y Religión',
        '7° BÁSICO B': 'Inglés 3',
        '8° BÁSICO A': 'Historia 1',
        '8° BÁSICO B': 'Matemática 2',
        '1° MEDIO A': 'Química',
        '1° MEDIO B': 'Inglés 5',
        '2° MEDIO A': 'Matemática 1',
        '2° MEDIO B': 'Lenguaje 4',
        '3° MEDIO A': 'Matemática 3',
        '3° MEDIO B': 'Lenguaje 1',
        '4° MEDIO A': 'Lenguaje 3',
        '4° MEDIO B': 'Inglés 2',  # Supuesto: el documento repite la jefatura de 4°A y omite la de 4°B
    }

    # Etiqueta que muestra cada asignatura en la grilla de los cursos (igual que el Excel 2026)
    ETIQUETAS = {
        'Lenguaje y Comunicación': 'LENGUAJE',
        'Educación Matemática': 'MATEMÁTICA',
        'Idioma Extranjero Inglés': 'INGLÉS',
        'English Skills': 'INGLÉS',
        'Ciencias Sociales': 'C. SOCIALES',
        'Historia, Geografía y CC.SS.': 'HISTORIA',
        'Ciencias Naturales': 'C. NATURALES',
        'Biología': 'BIOLOGÍA',
        'Química': 'QUÍMICA',
        'Física': 'FÍSICA',
        'Educación Tecnológica': 'TECNOLOGÍA',
        'Artes Visuales': 'ARTES',
        'Educación Musical': 'MÚSICA',
        'Artes Visuales / Música': 'ARTES-MÚSICA',
        'Educación Física y Salud': 'ED. FÍSICA',
        'Orientación / Tecnología': 'ORIEN/TEC.',
        'Orientación': 'ORIENTACIÓN',
        'Religión': 'RELIGIÓN',
        'Filosofía': 'FILOSOFÍA',
        'Educación Ciudadana': 'ED. CIUDADANA',
        'Ciencias para la Ciudadanía': 'CC. CIUDADANA',
    }

    # Asignaturas que comparten la regla de "una sesión diaria" (English skills es parte de Inglés)
    FAMILIAS = {'English Skills': 'Idioma Extranjero Inglés'}

    # Asignaturas troncales que se dictan en bloques consecutivos de 90 minutos
    ASIGNATURAS_TRONCALES = ['Matemática', 'Lenguaje', 'Ciencias Naturales', 'Biología', 'Química', 'Física']

    # Salas con capacidad limitada (un curso por bloque)
    RECURSOS_CAPACIDAD = {'Sala English skills': 1}

    # Recintos deportivos: cada uno admite un curso por bloque. El Patio Santo Domingo
    # recibe el desborde de cualquiera de los dos gimnasios (uso penalizado).
    RECINTOS_DEPORTIVOS = ['GIMNASIO A', 'GIMNASIO B', 'PATIO SANTO DOMINGO']

    # Franjas institucionales de electivos (formación diferenciada), fijas según la grilla 2026.
    # Cada franja dura 6 horas: 3 periodos dobles en los que 3° (o 4°) A y B se mezclan.
    # 'periodos': bloque inicial de cada periodo doble; 'etiquetas': texto del 1er y 2do bloque
    # en la grilla del curso; 'grupos': (asignatura, sección, docente, sala, etiqueta en la sala).
    FRANJAS_ELECTIVOS = {
        '3° MEDIO': [
            {
                'periodos': [('Lunes', 3), ('Martes', 7), ('Jueves', 5)],
                'etiquetas': ('CHP 3AB', 'LE-QU-EC S. 1'),
                'grupos': [
                    ('COMPRENSIÓN HISTÓRICA DEL PRESENTE', '3AB', 'Historia 3', 'SALA DE 3°A', 'COMP.H 3AB'),
                    ('LECTURA Y ESCRITURA ESPECIALIZADA', 'S.1', 'Lenguaje 1', 'SALA DE 3°B', 'LECT ESP. S.1'),
                    ('QUÍMICA FORMACIÓN DIFERENCIADA', 'S.1', 'Química', 'ELECTIVO 2', 'QUÍMICA S.1'),
                    ('ECONOMÍA Y SOCIEDAD', 'S.1', 'Historia 1', 'ELECTIVO 3', 'ECONOMÍA S.1'),
                ],
            },
            {
                'periodos': [('Lunes', 7), ('Miércoles', 1), ('Jueves', 3)],
                'etiquetas': ('PROB. EST. 3AB', 'LE-QU-EC S. 2'),
                'grupos': [
                    ('PROBABILIDADES Y ESTADÍSTICA DESCRIPTIVA', '3AB', 'Matemática 1', 'SALA DE 3°A', 'PROB. ES. 3AB'),
                    ('LECTURA Y ESCRITURA ESPECIALIZADA', 'S.2', 'Lenguaje 1', 'SALA DE 3°B', 'LECT ESP. S.2'),
                    ('QUÍMICA FORMACIÓN DIFERENCIADA', 'S.2', 'Química', 'ELECTIVO 2', 'QUÍMICA S.2'),
                    ('ECONOMÍA Y SOCIEDAD', 'S.2', 'Historia 1', 'ELECTIVO 3', 'ECONOMÍA S.2'),
                ],
            },
            {
                'periodos': [('Martes', 5), ('Miércoles', 3), ('Jueves', 7)],
                'etiquetas': ('BIO. CEL. 3AB', 'LE-QU-EC S. 3'),
                'grupos': [
                    ('BIOLOGÍA CELULAR Y MOLECULAR', '3AB', 'Biología', 'SALA DE 3°A', 'BIO. CEL. 3AB'),
                    # El documento indica "3A-B s. 2" para Lenguaje 4; se interpreta como la sección 3
                    ('LECTURA Y ESCRITURA ESPECIALIZADA', 'S.3', 'Lenguaje 4', 'SALA DE 3°B', 'LECT ESP. S.3'),
                    ('QUÍMICA FORMACIÓN DIFERENCIADA', 'S.3', 'Química', 'ELECTIVO 2', 'QUÍMICA S.3'),
                    ('ECONOMÍA Y SOCIEDAD', 'S.3', 'Historia 2', 'ELECTIVO 3', 'ECONOMÍA S.3'),
                ],
            },
        ],
        '4° MEDIO': [
            {
                'periodos': [('Martes', 1), ('Miércoles', 7), ('Viernes', 1)],
                'etiquetas': {'4° MEDIO A': ('DISEÑO 4A', 'LIM-PA-GEO S.1'),
                              '4° MEDIO B': ('DISEÑO 4B', 'LIM-PA-GEO S.1')},
                'grupos': [
                    ('DISEÑO Y ARQUITECTURA', '4A', 'Artes y Tecnología 1', 'SALA DE 4°A', 'DISEÑO 4A'),
                    ('DISEÑO Y ARQUITECTURA', '4B', 'Artes y Tecnología 2', 'SALA DE 4°B', 'DISEÑO 4B'),
                    ('LÍMITES, DERIVADAS E INTEGRALES', 'S.1', 'Matemática 3', 'ELECTIVO 2', 'LIMITES S.1'),
                    ('PARTICIPACIÓN Y ARGUMENTACIÓN EN DEMOCRACIA', 'S.1', 'Lenguaje 1', 'SALA DE TECNOLOGÍA', 'PART.ARG S.1'),
                    ('GEOGRAFÍA, TERRITORIO Y PROBLEMAS SOCIOAMBIENTALES', 'S.1', 'Historia 3', 'ELECTIVO 3', 'GEOGRAFÍA S.1'),
                ],
            },
            {
                'periodos': [('Martes', 3), ('Miércoles', 5), ('Viernes', 3)],
                'etiquetas': {'4° MEDIO A': ('BIO. ECOS 4A', 'LIM-PA-GEO S.2'),
                              '4° MEDIO B': ('BIO. ECOS 4B', 'LIM-PA-GEO S.2')},
                'grupos': [
                    ('BIOLOGÍA DE LOS ECOSISTEMAS', '4A', 'Biología', 'SALA DE 4°A', 'BIO. ECOS. 4A'),
                    ('BIOLOGÍA DE LOS ECOSISTEMAS', '4B', 'C. Naturales', 'ELECTIVO 3', 'BIO. ECOS. 4B'),
                    ('LÍMITES, DERIVADAS E INTEGRALES', 'S.2', 'Matemática 1', 'ELECTIVO 2', 'LIMITES S.2'),
                    ('PARTICIPACIÓN Y ARGUMENTACIÓN EN DEMOCRACIA', 'S.2', 'Lenguaje 1', 'SALA DE TECNOLOGÍA', 'PART.ARG S.2'),
                    ('GEOGRAFÍA, TERRITORIO Y PROBLEMAS SOCIOAMBIENTALES', 'S.2', 'Historia 3', 'SALA DE 4°B', 'GEOGRAFÍA S.2'),
                ],
            },
            {
                'periodos': [('Lunes', 1), ('Jueves', 1), ('Viernes', 5)],
                'etiquetas': ('C. SALUD 4AB', 'LIM-PA-GEO S.3'),
                'grupos': [
                    ('CIENCIAS PARA LA SALUD', '4AB', 'C. Naturales', 'SALA DE 4°B', 'C.SALUD 4AB'),
                    ('LÍMITES, DERIVADAS E INTEGRALES', 'S.3', 'Matemática 1', 'ELECTIVO 2', 'LIMITES S.3'),
                    ('PARTICIPACIÓN Y ARGUMENTACIÓN EN DEMOCRACIA', 'S.3', 'Lenguaje 2', 'SALA DE 4°A', 'PART.ARG S.3'),
                    ('GEOGRAFÍA, TERRITORIO Y PROBLEMAS SOCIOAMBIENTALES', 'S.3', 'Historia 3', 'ELECTIVO 3', 'GEOGRAFÍA S.3'),
                ],
            },
        ],
    }

    # Electivos ofrecidos por nivel (orden de la tabla de horas del Excel 2026)
    ELECTIVOS_OFERTA = {
        '3° MEDIO': [
            'LECTURA Y ESCRITURA ESPECIALIZADA',
            'COMPRENSIÓN HISTÓRICA DEL PRESENTE',
            'PROBABILIDADES Y ESTADÍSTICA DESCRIPTIVA',
            'QUÍMICA FORMACIÓN DIFERENCIADA',
            'BIOLOGÍA CELULAR Y MOLECULAR',
            'ECONOMÍA Y SOCIEDAD',
        ],
        '4° MEDIO': [
            'CIENCIAS PARA LA SALUD',
            'LÍMITES, DERIVADAS E INTEGRALES',
            'PARTICIPACIÓN Y ARGUMENTACIÓN EN DEMOCRACIA',
            'GEOGRAFÍA, TERRITORIO Y PROBLEMAS SOCIOAMBIENTALES',
            'DISEÑO Y ARQUITECTURA',
            'BIOLOGÍA DE LOS ECOSISTEMAS',
        ],
    }

    # Bloqueos de pastoral por sala ('C' = horario de colación). Fuente: hoja SALAS ELECTIVOS 2026
    BLOQUEOS_PASTORAL = {
        'SALA DE TECNOLOGÍA': [('Martes', 'C'), ('Martes', 9), ('Martes', 10),
                               ('Jueves', 'C'), ('Jueves', 9), ('Jueves', 10)],
        'ELECTIVO 2': [('Jueves', 'C'), ('Jueves', 9), ('Jueves', 10)],
        'ELECTIVO 3': [('Jueves', 'C'), ('Jueves', 9), ('Jueves', 10)],
        'SALA PADRE CUETO': [('Martes', 'C'), ('Martes', 9), ('Martes', 10),
                             ('Jueves', 7), ('Jueves', 8), ('Jueves', 'C'), ('Jueves', 9), ('Jueves', 10)],
        'SALA MADRE PILAR': [('Lunes', 'C'), ('Lunes', 9), ('Lunes', 10),
                             ('Martes', 1), ('Martes', 2), ('Martes', 'C'), ('Martes', 9), ('Martes', 10),
                             ('Jueves', 1), ('Jueves', 2), ('Jueves', 3), ('Jueves', 4),
                             ('Jueves', 'C'), ('Jueves', 9), ('Jueves', 10)],
        'SALA DE ARTES': [('Jueves', 'C'), ('Jueves', 9), ('Jueves', 10)],
        'PÁRVULOS': [('Jueves', 'C'), ('Jueves', 9), ('Jueves', 10)],
    }

    _malla_cache = None

    @classmethod
    def todos_los_cursos(cls):
        """Párvulos y cursos regulares, en el orden de las hojas del Excel 2026."""
        return cls.CURSOS_PARVULOS + cls.CURSOS

    @classmethod
    def es_parvulo(cls, curso):
        return curso in cls.CURSOS_PARVULOS

    @classmethod
    def nivel(cls, curso):
        """'3° MEDIO A' -> '3° MEDIO'."""
        return curso[:-2]

    @classmethod
    def get_bloques_permitidos(cls, curso, dia):
        """Retorna los bloques pedagógicos de la jornada de un curso en un día."""
        return list(range(1, cls.JORNADAS[curso][cls.DIAS.index(dia)] + 1))

    @classmethod
    def get_total_bloques_semanal(cls, curso):
        """Calcula el total de bloques disponibles en la semana para un curso."""
        return sum(cls.JORNADAS[curso])

    @classmethod
    def zona_deportiva(cls, curso):
        """Gimnasio preferente: B para párvulos y 1° a 4° básico; A para 5° básico a 4° medio."""
        if cls.es_parvulo(curso) or ('BÁSICO' in curso and curso[0] in '1234'):
            return 'GIMNASIO B'
        return 'GIMNASIO A'

    @classmethod
    def codigo_corto(cls, curso):
        """Código del colegio en gimnasios: '1a' (1° básico A), '5A' (5° básico A), '1A' (1° medio A), 'Pk'."""
        if cls.es_parvulo(curso):
            return {'PREKINDER A': 'Pk', 'KINDER A': 'Ka', 'KINDER B': 'Kb'}[curso]
        numero, seccion = curso[0], curso[-1]
        if 'BÁSICO' in curso and numero in '1234':
            return f"{numero}{seccion.lower()}"
        return f"{numero}{seccion}"

    @classmethod
    def codigo_sala(cls, curso):
        """Código del colegio en las salas de especialidad: '6°b' (básica) o '1°B' (media)."""
        numero, seccion = curso[0], curso[-1]
        return f"{numero}°{seccion.lower()}" if 'BÁSICO' in curso else f"{numero}°{seccion}"

    @classmethod
    def familia(cls, asignatura):
        return cls.FAMILIAS.get(asignatura, asignatura)

    @staticmethod
    def docentes_de(docente):
        """Normaliza el docente de una lección a una tupla (las lecciones con co-docencia tienen varios)."""
        return tuple(docente) if isinstance(docente, (tuple, list)) else (docente,)

    @classmethod
    def franjas_de(cls, curso):
        return cls.FRANJAS_ELECTIVOS.get(cls.nivel(curso), [])

    @classmethod
    def etiquetas_franja(cls, franja, curso):
        etiquetas = franja['etiquetas']
        return etiquetas[curso] if isinstance(etiquetas, dict) else etiquetas

    @classmethod
    def nombre_franja(cls, k):
        return f'Formación Diferenciada · Franja {k}'

    @classmethod
    def get_malla_curricular(cls):
        """
        Retorna la asignación curricular completa de cada curso:
        (Asignatura, Horas semanales, Docente(s) asignado(s), Espacio)
        Horas según HORARIO CURSOS 2026.xlsx y docentes según DISTRIBUCIÓN HORARIA 2026.docx.
        Las lecciones con co-docencia (English skills, Artes/Música en media y electivos)
        indican una tupla de docentes que deben estar libres en el mismo bloque.
        """
        if cls._malla_cache is not None:
            return cls._malla_cache

        SK = 'Sala English skills'
        AM = 'Sala de Artes y Música'
        NR = 'C. Naturales y Religión'
        malla = {}

        # ---------------------------------------------------------------------
        # PÁRVULOS (solo Educación Física: 2 bloques simples en días distintos)
        # ---------------------------------------------------------------------
        for c in cls.CURSOS_PARVULOS:
            malla[c] = [('Educación Física y Salud', 2, 'Ed. Física 2', 'Gimnasio')]

        # ---------------------------------------------------------------------
        # 1° BÁSICO A (38 horas)
        # ---------------------------------------------------------------------
        malla['1° BÁSICO A'] = [
            ('Lenguaje y Comunicación', 8, 'Básica 2', 'Aula'),
            ('Educación Matemática', 8, 'Básica 1', 'Aula'),
            ('Idioma Extranjero Inglés', 6, 'Inglés 1', 'Aula'),
            ('Ciencias Sociales', 3, 'Básica 1', 'Aula'),
            ('Ciencias Naturales', 3, 'Básica 1', 'Aula'),
            ('Artes Visuales', 2, 'Básica 1', 'Aula'),
            ('Educación Musical', 2, 'Básica 1', 'Aula'),
            ('Orientación / Tecnología', 1, 'Básica 1', 'Aula'),
            ('Educación Física y Salud', 3, 'Ed. Física 2', 'Gimnasio'),
            ('Religión', 2, 'Religión', 'Aula'),
        ]

        # ---------------------------------------------------------------------
        # 1° BÁSICO B (38 horas)
        # ---------------------------------------------------------------------
        malla['1° BÁSICO B'] = [
            ('Lenguaje y Comunicación', 8, 'Básica 2', 'Aula'),
            ('Educación Matemática', 8, 'Básica 1', 'Aula'),
            ('Idioma Extranjero Inglés', 6, 'Inglés 1', 'Aula'),
            ('Ciencias Sociales', 3, 'Básica 2', 'Aula'),
            ('Ciencias Naturales', 3, 'Básica 2', 'Aula'),
            ('Artes Visuales', 2, 'Básica 2', 'Aula'),
            ('Educación Musical', 2, 'Básica 2', 'Aula'),
            ('Orientación / Tecnología', 1, 'Básica 2', 'Aula'),
            ('Educación Física y Salud', 3, 'Ed. Física 2', 'Gimnasio'),
            ('Religión', 2, 'Religión', 'Aula'),
        ]

        # ---------------------------------------------------------------------
        # 2° BÁSICO A (38 horas)
        # ---------------------------------------------------------------------
        malla['2° BÁSICO A'] = [
            ('Lenguaje y Comunicación', 8, 'Básica 3', 'Aula'),
            ('Educación Matemática', 8, 'Básica 4', 'Aula'),
            ('Idioma Extranjero Inglés', 4, 'Inglés 1', 'Aula'),
            ('English Skills', 2, ('Inglés 1', 'Inglés 4'), SK),
            ('Ciencias Sociales', 3, 'Básica 3', 'Aula'),
            ('Ciencias Naturales', 3, 'Básica 3', 'Aula'),
            ('Artes Visuales', 2, 'Básica 3', 'Aula'),
            ('Educación Musical', 2, 'Básica 3', 'Aula'),
            ('Orientación / Tecnología', 1, 'Básica 3', 'Aula'),
            ('Educación Física y Salud', 3, 'Ed. Física 2', 'Gimnasio'),
            ('Religión', 2, 'Religión', 'Aula'),
        ]

        # ---------------------------------------------------------------------
        # 2° BÁSICO B (38 horas)
        # ---------------------------------------------------------------------
        malla['2° BÁSICO B'] = [
            ('Lenguaje y Comunicación', 8, 'Básica 3', 'Aula'),
            ('Educación Matemática', 8, 'Básica 4', 'Aula'),
            ('Idioma Extranjero Inglés', 4, 'Inglés 1', 'Aula'),
            ('English Skills', 2, ('Inglés 1', 'Inglés 4'), SK),
            ('Ciencias Sociales', 3, 'Básica 4', 'Aula'),
            ('Ciencias Naturales', 3, 'Básica 4', 'Aula'),
            ('Artes Visuales', 2, 'Básica 4', 'Aula'),
            ('Educación Musical', 2, 'Básica 4', 'Aula'),
            ('Orientación / Tecnología', 1, 'Básica 4', 'Aula'),
            ('Educación Física y Salud', 3, 'Ed. Física 2', 'Gimnasio'),
            ('Religión', 2, 'Religión', 'Aula'),
        ]

        # ---------------------------------------------------------------------
        # 3° BÁSICO A (38 horas)
        # ---------------------------------------------------------------------
        malla['3° BÁSICO A'] = [
            ('Lenguaje y Comunicación', 8, 'Básica 5', 'Aula'),
            ('Educación Matemática', 8, 'Básica 6', 'Aula'),
            ('Idioma Extranjero Inglés', 4, 'Inglés 1', 'Aula'),
            ('English Skills', 2, ('Inglés 1', 'Inglés 3'), SK),
            ('Ciencias Sociales', 3, 'Básica 5', 'Aula'),
            ('Ciencias Naturales', 3, 'Básica 5', 'Aula'),
            ('Artes Visuales', 2, 'Básica 5', 'Aula'),
            ('Educación Musical', 2, 'Básica 5', 'Aula'),
            ('Orientación / Tecnología', 1, 'Básica 5', 'Aula'),
            ('Educación Física y Salud', 3, 'Ed. Física 2', 'Gimnasio'),
            ('Religión', 2, 'Religión', 'Aula'),
        ]

        # ---------------------------------------------------------------------
        # 3° BÁSICO B (38 horas)
        # ---------------------------------------------------------------------
        malla['3° BÁSICO B'] = [
            ('Lenguaje y Comunicación', 8, 'Básica 5', 'Aula'),
            ('Educación Matemática', 8, 'Básica 6', 'Aula'),
            ('Idioma Extranjero Inglés', 4, 'Inglés 2', 'Aula'),
            ('English Skills', 2, ('Inglés 2', 'Inglés 5'), SK),
            ('Ciencias Sociales', 3, 'Básica 6', 'Aula'),
            ('Ciencias Naturales', 3, 'Básica 6', 'Aula'),
            ('Artes Visuales', 2, 'Básica 6', 'Aula'),
            ('Educación Musical', 2, 'Básica 6', 'Aula'),
            ('Orientación / Tecnología', 1, 'Básica 6', 'Aula'),
            ('Educación Física y Salud', 3, 'Ed. Física 1', 'Gimnasio'),
            ('Religión', 2, 'Religión', 'Aula'),
        ]

        # ---------------------------------------------------------------------
        # 4° BÁSICO A (38 horas)
        # ---------------------------------------------------------------------
        malla['4° BÁSICO A'] = [
            ('Lenguaje y Comunicación', 8, 'Básica 7', 'Aula'),
            ('Educación Matemática', 8, 'Básica 8', 'Aula'),
            ('Idioma Extranjero Inglés', 4, 'Inglés 2', 'Aula'),
            ('English Skills', 2, ('Inglés 2', 'Inglés 3'), SK),
            ('Ciencias Sociales', 3, 'Básica 7', 'Aula'),
            ('Ciencias Naturales', 3, 'Básica 7', 'Aula'),
            ('Artes Visuales', 2, 'Básica 7', 'Aula'),
            ('Educación Musical', 2, 'Básica 7', 'Aula'),
            ('Orientación / Tecnología', 1, 'Básica 7', 'Aula'),
            ('Educación Física y Salud', 3, 'Ed. Física 1', 'Gimnasio'),
            ('Religión', 2, 'Religión', 'Aula'),
        ]

        # ---------------------------------------------------------------------
        # 4° BÁSICO B (38 horas)
        # ---------------------------------------------------------------------
        malla['4° BÁSICO B'] = [
            ('Lenguaje y Comunicación', 8, 'Básica 7', 'Aula'),
            ('Educación Matemática', 8, 'Básica 8', 'Aula'),
            ('Idioma Extranjero Inglés', 4, 'Inglés 3', 'Aula'),
            ('English Skills', 2, ('Inglés 3', 'Inglés 5'), SK),
            ('Ciencias Sociales', 3, 'Básica 8', 'Aula'),
            ('Ciencias Naturales', 3, 'Básica 8', 'Aula'),
            ('Artes Visuales', 2, 'Básica 8', 'Aula'),
            ('Educación Musical', 2, 'Básica 8', 'Aula'),
            ('Orientación / Tecnología', 1, 'Básica 8', 'Aula'),
            ('Educación Física y Salud', 3, 'Ed. Física 1', 'Gimnasio'),
            ('Religión', 2, 'Religión', 'Aula'),
        ]

        # ---------------------------------------------------------------------
        # 5° BÁSICO A (38 horas)
        # ---------------------------------------------------------------------
        malla['5° BÁSICO A'] = [
            ('Lenguaje y Comunicación', 6, 'Lenguaje 2', 'Aula'),
            ('Educación Matemática', 7, 'Matemática 4', 'Aula'),
            ('Idioma Extranjero Inglés', 4, 'Inglés 3', 'Aula'),
            ('English Skills', 2, ('Inglés 3', 'Inglés 4'), SK),
            ('Historia, Geografía y CC.SS.', 4, 'Historia 2', 'Aula'),
            ('Ciencias Naturales', 4, 'C. Naturales', 'Aula'),
            ('Educación Tecnológica', 2, 'Artes y Tecnología 2', 'Aula'),
            ('Artes Visuales', 2, 'Artes y Tecnología 1', 'Aula'),
            ('Educación Musical', 2, 'Música', 'Sala de Música'),
            ('Educación Física y Salud', 2, 'Ed. Física 2', 'Gimnasio'),
            ('Orientación', 1, 'Historia 2', 'Aula'),
            ('Religión', 2, 'Religión', 'Aula'),
        ]

        # ---------------------------------------------------------------------
        # 5° BÁSICO B (38 horas)
        # ---------------------------------------------------------------------
        malla['5° BÁSICO B'] = [
            ('Lenguaje y Comunicación', 6, 'Lenguaje 3', 'Aula'),
            ('Educación Matemática', 7, 'Matemática 4', 'Aula'),
            ('Idioma Extranjero Inglés', 4, 'Inglés 1', 'Aula'),
            ('English Skills', 2, ('Inglés 1', 'Inglés 3'), SK),
            ('Historia, Geografía y CC.SS.', 4, 'Historia 2', 'Aula'),
            ('Ciencias Naturales', 4, 'Química', 'Aula'),
            ('Educación Tecnológica', 2, 'Artes y Tecnología 2', 'Aula'),
            ('Artes Visuales', 2, 'Artes y Tecnología 1', 'Aula'),
            ('Educación Musical', 2, 'Música', 'Sala de Música'),
            ('Educación Física y Salud', 2, 'Ed. Física 1', 'Gimnasio'),
            ('Orientación', 1, 'Inglés 1', 'Aula'),
            ('Religión', 2, 'Religión', 'Aula'),
        ]

        # ---------------------------------------------------------------------
        # 6° BÁSICO A (37 horas)
        # ---------------------------------------------------------------------
        malla['6° BÁSICO A'] = [
            ('Lenguaje y Comunicación', 6, 'Lenguaje 3', 'Aula'),
            ('Educación Matemática', 6, 'Matemática 4', 'Aula'),
            ('Idioma Extranjero Inglés', 4, 'Inglés 4', 'Aula'),
            ('English Skills', 2, ('Inglés 4', 'Inglés 5'), SK),
            ('Historia, Geografía y CC.SS.', 4, 'Historia 2', 'Aula'),
            ('Ciencias Naturales', 4, 'C. Naturales', 'Aula'),
            ('Educación Tecnológica', 2, 'Artes y Tecnología 1', 'Aula'),
            ('Artes Visuales', 2, 'Artes y Tecnología 2', 'Aula'),
            ('Educación Musical', 2, 'Música', 'Sala de Música'),
            ('Educación Física y Salud', 2, 'Ed. Física 1', 'Gimnasio'),
            ('Orientación', 1, 'Inglés 4', 'Aula'),
            ('Religión', 2, 'Religión', 'Aula'),
        ]

        # ---------------------------------------------------------------------
        # 6° BÁSICO B (37 horas)
        # ---------------------------------------------------------------------
        malla['6° BÁSICO B'] = [
            ('Lenguaje y Comunicación', 6, 'Lenguaje 3', 'Aula'),
            ('Educación Matemática', 6, 'Matemática 2', 'Aula'),
            ('Idioma Extranjero Inglés', 4, 'Inglés 4', 'Aula'),
            ('English Skills', 2, ('Inglés 4', 'Inglés 2'), SK),
            ('Historia, Geografía y CC.SS.', 4, 'Historia 2', 'Aula'),
            ('Ciencias Naturales', 4, 'C. Naturales', 'Aula'),
            ('Educación Tecnológica', 2, 'Artes y Tecnología 1', 'Aula'),
            ('Artes Visuales', 2, 'Artes y Tecnología 2', 'Aula'),
            ('Educación Musical', 2, 'Música', 'Sala de Música'),
            ('Educación Física y Salud', 2, 'Ed. Física 1', 'Gimnasio'),
            ('Orientación', 1, 'C. Naturales', 'Aula'),
            ('Religión', 2, 'Religión', 'Aula'),
        ]

        # ---------------------------------------------------------------------
        # 7° BÁSICO A (37 horas)
        # ---------------------------------------------------------------------
        malla['7° BÁSICO A'] = [
            ('Lenguaje y Comunicación', 6, 'Lenguaje 2', 'Aula'),
            ('Educación Matemática', 6, 'Matemática 4', 'Aula'),
            ('Idioma Extranjero Inglés', 4, 'Inglés 3', 'Aula'),
            ('English Skills', 2, ('Inglés 3', 'Inglés 5'), SK),
            ('Historia, Geografía y CC.SS.', 4, 'Historia 3', 'Aula'),
            ('Ciencias Naturales', 4, NR, 'Aula'),
            ('Física', 1, 'Física', 'Aula'),
            ('Educación Tecnológica', 1, 'Artes y Tecnología 2', 'Aula'),
            ('Artes Visuales', 2, 'Artes y Tecnología 1', 'Aula'),
            ('Educación Musical', 2, 'Música', 'Sala de Música'),
            ('Educación Física y Salud', 2, 'Ed. Física 2', 'Gimnasio'),
            ('Orientación', 1, NR, 'Aula'),
            ('Religión', 2, NR, 'Aula'),
        ]

        # ---------------------------------------------------------------------
        # 7° BÁSICO B (37 horas)
        # ---------------------------------------------------------------------
        malla['7° BÁSICO B'] = [
            ('Lenguaje y Comunicación', 6, 'Lenguaje 2', 'Aula'),
            # El documento repite "7A" para Matemática 4; se interpreta la segunda fila como 7°B
            ('Educación Matemática', 6, 'Matemática 4', 'Aula'),
            ('Idioma Extranjero Inglés', 4, 'Inglés 3', 'Aula'),
            ('English Skills', 2, ('Inglés 3', 'Inglés 5'), SK),
            ('Historia, Geografía y CC.SS.', 4, 'Historia 3', 'Aula'),
            ('Ciencias Naturales', 4, NR, 'Aula'),
            ('Física', 1, 'Física', 'Aula'),
            ('Educación Tecnológica', 1, 'Artes y Tecnología 2', 'Aula'),
            ('Artes Visuales', 2, 'Artes y Tecnología 1', 'Aula'),
            ('Educación Musical', 2, 'Música', 'Sala de Música'),
            ('Educación Física y Salud', 2, 'Ed. Física 1', 'Gimnasio'),
            ('Orientación', 1, 'Inglés 3', 'Aula'),
            ('Religión', 2, NR, 'Aula'),
        ]

        # ---------------------------------------------------------------------
        # 8° BÁSICO A (37 horas)
        # ---------------------------------------------------------------------
        malla['8° BÁSICO A'] = [
            ('Lenguaje y Comunicación', 6, 'Lenguaje 4', 'Aula'),
            ('Educación Matemática', 6, 'Matemática 3', 'Aula'),
            ('Idioma Extranjero Inglés', 4, 'Inglés 2', 'Aula'),
            ('English Skills', 2, ('Inglés 2', 'Inglés 5'), SK),
            ('Historia, Geografía y CC.SS.', 4, 'Historia 1', 'Aula'),
            ('Ciencias Naturales', 4, NR, 'Aula'),
            ('Física', 1, 'Física', 'Aula'),
            ('Educación Tecnológica', 1, 'Artes y Tecnología 1', 'Aula'),
            ('Artes Visuales', 2, 'Artes y Tecnología 2', 'Aula'),
            ('Educación Musical', 2, 'Música', 'Sala de Música'),
            ('Educación Física y Salud', 2, 'Ed. Física 3', 'Gimnasio'),
            ('Orientación', 1, 'Historia 1', 'Aula'),
            ('Religión', 2, NR, 'Aula'),
        ]

        # ---------------------------------------------------------------------
        # 8° BÁSICO B (37 horas)
        # ---------------------------------------------------------------------
        malla['8° BÁSICO B'] = [
            ('Lenguaje y Comunicación', 6, 'Lenguaje 4', 'Aula'),
            ('Educación Matemática', 6, 'Matemática 2', 'Aula'),
            ('Idioma Extranjero Inglés', 4, 'Inglés 2', 'Aula'),
            ('English Skills', 2, ('Inglés 2', 'Inglés 5'), SK),
            ('Historia, Geografía y CC.SS.', 4, 'Historia 1', 'Aula'),
            ('Ciencias Naturales', 4, 'Biología', 'Aula'),
            ('Física', 1, 'Física', 'Aula'),
            ('Educación Tecnológica', 1, 'Artes y Tecnología 1', 'Aula'),
            ('Artes Visuales', 2, 'Artes y Tecnología 2', 'Aula'),
            ('Educación Musical', 2, 'Música', 'Sala de Música'),
            ('Educación Física y Salud', 2, 'Ed. Física 3', 'Gimnasio'),
            ('Orientación', 1, 'Matemática 2', 'Aula'),
            ('Religión', 2, NR, 'Aula'),
        ]

        # ---------------------------------------------------------------------
        # 1° MEDIO A (40 horas)
        # ---------------------------------------------------------------------
        malla['1° MEDIO A'] = [
            ('Lenguaje y Comunicación', 6, 'Lenguaje 3', 'Aula'),
            ('Educación Matemática', 7, 'Matemática 3', 'Aula'),
            ('Idioma Extranjero Inglés', 4, 'Inglés 5', 'Aula'),
            ('English Skills', 2, ('Inglés 5', 'Inglés 4'), SK),
            ('Historia, Geografía y CC.SS.', 4, 'Historia 1', 'Aula'),
            ('Biología', 4, 'Biología', 'Aula'),
            ('Química', 2, 'Química', 'Aula'),
            ('Física', 2, 'Física', 'Aula'),
            ('Educación Tecnológica', 2, 'Artes y Tecnología 2', 'Aula'),
            ('Artes Visuales / Música', 2, ('Artes y Tecnología 1', 'Música'), AM),
            ('Educación Física y Salud', 2, 'Ed. Física 3', 'Gimnasio'),
            ('Orientación', 1, 'Química', 'Aula'),
            ('Religión', 2, NR, 'Aula'),
        ]

        # ---------------------------------------------------------------------
        # 1° MEDIO B (40 horas)
        # ---------------------------------------------------------------------
        malla['1° MEDIO B'] = [
            ('Lenguaje y Comunicación', 6, 'Lenguaje 3', 'Aula'),
            ('Educación Matemática', 7, 'Matemática 3', 'Aula'),
            ('Idioma Extranjero Inglés', 4, 'Inglés 5', 'Aula'),
            ('English Skills', 2, ('Inglés 5', 'Inglés 4'), SK),
            ('Historia, Geografía y CC.SS.', 4, 'Historia 1', 'Aula'),
            # El documento repite "1A" para Biología; se interpreta la segunda fila como 1° medio B
            ('Biología', 4, 'Biología', 'Aula'),
            ('Química', 2, 'Química', 'Aula'),
            ('Física', 2, 'Física', 'Aula'),
            ('Educación Tecnológica', 2, 'Artes y Tecnología 2', 'Aula'),
            ('Artes Visuales / Música', 2, ('Artes y Tecnología 1', 'Música'), AM),
            ('Educación Física y Salud', 2, 'Ed. Física 3', 'Gimnasio'),
            ('Orientación', 1, 'Inglés 5', 'Aula'),
            ('Religión', 2, NR, 'Aula'),
        ]

        # ---------------------------------------------------------------------
        # 2° MEDIO A (40 horas)
        # ---------------------------------------------------------------------
        malla['2° MEDIO A'] = [
            ('Lenguaje y Comunicación', 6, 'Lenguaje 4', 'Aula'),
            ('Educación Matemática', 7, 'Matemática 1', 'Aula'),
            ('Idioma Extranjero Inglés', 4, 'Inglés 4', 'Aula'),
            ('English Skills', 2, ('Inglés 4', 'Inglés 3'), SK),
            ('Historia, Geografía y CC.SS.', 4, 'Historia 1', 'Aula'),
            ('Biología', 4, 'Biología', 'Aula'),
            ('Química', 2, 'Química', 'Aula'),
            ('Física', 2, 'Física', 'Aula'),
            ('Educación Tecnológica', 2, 'Artes y Tecnología 1', 'Aula'),
            ('Artes Visuales / Música', 2, ('Artes y Tecnología 2', 'Música'), AM),
            ('Educación Física y Salud', 2, 'Ed. Física 3', 'Gimnasio'),
            ('Orientación', 1, 'Matemática 1', 'Aula'),
            ('Religión', 2, NR, 'Aula'),
        ]

        # ---------------------------------------------------------------------
        # 2° MEDIO B (40 horas)
        # ---------------------------------------------------------------------
        malla['2° MEDIO B'] = [
            ('Lenguaje y Comunicación', 6, 'Lenguaje 2', 'Aula'),
            ('Educación Matemática', 7, 'Matemática 1', 'Aula'),
            ('Idioma Extranjero Inglés', 4, 'Inglés 4', 'Aula'),
            ('English Skills', 2, ('Inglés 4', 'Inglés 3'), SK),
            ('Historia, Geografía y CC.SS.', 4, 'Historia 1', 'Aula'),
            ('Biología', 4, 'Biología', 'Aula'),
            ('Química', 2, 'Química', 'Aula'),
            ('Física', 2, 'Física', 'Aula'),
            ('Educación Tecnológica', 2, 'Artes y Tecnología 1', 'Aula'),
            ('Artes Visuales / Música', 2, ('Artes y Tecnología 2', 'Música'), AM),
            ('Educación Física y Salud', 2, 'Ed. Física 3', 'Gimnasio'),
            ('Orientación', 1, 'Lenguaje 4', 'Aula'),
            ('Religión', 2, NR, 'Aula'),
        ]

        # ---------------------------------------------------------------------
        # 3° MEDIO A (42 horas: 24 Plan Común + 18 en 3 franjas de electivos)
        # ---------------------------------------------------------------------
        malla['3° MEDIO A'] = [
            ('Lenguaje y Comunicación', 3, 'Lenguaje 1', 'Aula'),
            ('Educación Matemática', 3, 'Matemática 3', 'Aula'),
            ('Idioma Extranjero Inglés', 4, 'Inglés 5', 'Aula'),
            ('Educación Ciudadana', 2, 'Historia 2', 'Aula'),
            ('Ciencias para la Ciudadanía', 2, 'Biología', 'Aula'),
            ('Filosofía', 2, 'Lenguaje 5', 'Aula'),
            ('Física', 1, 'Física', 'Aula'),
            ('Artes Visuales / Música', 2, ('Artes y Tecnología 1', 'Música'), AM),
            ('Educación Física y Salud', 2, 'Ed. Física 3', 'Gimnasio'),
            ('Orientación', 1, 'Matemática 3', 'Aula'),
            ('Religión', 2, NR, 'Aula'),
        ]

        # ---------------------------------------------------------------------
        # 3° MEDIO B (42 horas: 24 Plan Común + 18 en 3 franjas de electivos)
        # ---------------------------------------------------------------------
        malla['3° MEDIO B'] = [
            ('Lenguaje y Comunicación', 3, 'Lenguaje 1', 'Aula'),
            ('Educación Matemática', 3, 'Matemática 3', 'Aula'),
            ('Idioma Extranjero Inglés', 4, 'Inglés 5', 'Aula'),
            ('Educación Ciudadana', 2, 'Historia 2', 'Aula'),
            ('Ciencias para la Ciudadanía', 2, 'Biología', 'Aula'),
            ('Filosofía', 2, 'Lenguaje 5', 'Aula'),
            ('Física', 1, 'Física', 'Aula'),
            ('Artes Visuales / Música', 2, ('Artes y Tecnología 1', 'Música'), AM),
            ('Educación Física y Salud', 2, 'Ed. Física 3', 'Gimnasio'),
            ('Orientación', 1, 'Lenguaje 1', 'Aula'),
            ('Religión', 2, NR, 'Aula'),
        ]

        # ---------------------------------------------------------------------
        # 4° MEDIO A (42 horas: 24 Plan Común + 18 en 3 franjas de electivos)
        # ---------------------------------------------------------------------
        malla['4° MEDIO A'] = [
            ('Lenguaje y Comunicación', 3, 'Lenguaje 3', 'Aula'),
            ('Educación Matemática', 3, 'Matemática 1', 'Aula'),
            ('Idioma Extranjero Inglés', 4, 'Inglés 2', 'Aula'),
            ('Educación Ciudadana', 2, 'Historia 3', 'Aula'),
            ('Ciencias para la Ciudadanía', 2, 'Química', 'Aula'),
            ('Filosofía', 2, 'Lenguaje 5', 'Aula'),
            ('Física', 1, 'Física', 'Aula'),
            ('Artes Visuales / Música', 2, ('Artes y Tecnología 1', 'Música'), AM),
            ('Educación Física y Salud', 2, 'Ed. Física 3', 'Gimnasio'),
            ('Orientación', 1, 'Lenguaje 3', 'Aula'),
            ('Religión', 2, NR, 'Aula'),
        ]

        # ---------------------------------------------------------------------
        # 4° MEDIO B (42 horas: 24 Plan Común + 18 en 3 franjas de electivos)
        # ---------------------------------------------------------------------
        malla['4° MEDIO B'] = [
            ('Lenguaje y Comunicación', 3, 'Lenguaje 1', 'Aula'),
            ('Educación Matemática', 3, 'Matemática 4', 'Aula'),
            ('Idioma Extranjero Inglés', 4, 'Inglés 2', 'Aula'),
            ('Educación Ciudadana', 2, 'Historia 3', 'Aula'),
            ('Ciencias para la Ciudadanía', 2, 'Química', 'Aula'),
            ('Filosofía', 2, 'Lenguaje 5', 'Aula'),
            ('Física', 1, 'Física', 'Aula'),
            ('Artes Visuales / Música', 2, ('Artes y Tecnología 2', 'Música'), AM),
            ('Educación Física y Salud', 2, 'Ed. Física 3', 'Gimnasio'),
            ('Orientación', 1, 'Inglés 2', 'Aula'),
            ('Religión', 2, NR, 'Aula'),
        ]

        # Franjas de electivos de 3° y 4° medio (6 horas cada una, docentes de todas sus secciones)
        for nivel, franjas in cls.FRANJAS_ELECTIVOS.items():
            for k, franja in enumerate(franjas, 1):
                docentes = tuple(dict.fromkeys(g[2] for g in franja['grupos']))
                for seccion in ('A', 'B'):
                    malla[f'{nivel} {seccion}'].append((cls.nombre_franja(k), 6, docentes, 'Salas electivos'))

        cls._malla_cache = malla
        return malla

    @classmethod
    def carga_docente(cls):
        """Horas de grilla por docente según la malla (los electivos se cuentan una vez por franja)."""
        carga = defaultdict(int)
        for curso, lecciones in cls.get_malla_curricular().items():
            for asig, horas, doc, _ in lecciones:
                if asig.startswith('Formación Diferenciada'):
                    continue
                for d in cls.docentes_de(doc):
                    carga[d] += horas
        for franjas in cls.FRANJAS_ELECTIVOS.values():
            for franja in franjas:
                for d in dict.fromkeys(g[2] for g in franja['grupos']):
                    carga[d] += 6
        return carga
