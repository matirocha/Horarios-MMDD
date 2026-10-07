#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
PROTOTIPO 2 — EXPORTADOR DE DATOS PARA LA PLATAFORMA WEB DE HORARIOS MMDD
===============================================================================

Prepara los dos horarios que se eligen en el menú de inicio de la página:

  - 2026: el horario OFICIAL, leído tal cual de 'data/Data 2026/HORARIO CURSOS 2026.xlsx'
    (los docentes de cada clase salen de la distribución horaria 2026 del motor).
  - 2027: el horario GENERADO por el motor de 'notebooks/generador_horarios.py'.

Ambos se auditan con el mismo validador y se escriben con el mismo formato en
'datos/horarios_<año>.js', más un resumen liviano para el menú en 'datos/resumen_<año>.js':

  - Bloques, recreos y días de la semana.
  - Los 24 cursos regulares y los 3 niveles de párvulos (jornada, profesor/a jefe,
    tabla de horas y grilla semanal).
  - Los 37 docentes (departamento, jefatura, grilla semanal y distribución horaria).
  - Las salas de especialidad y los recintos deportivos (ocupación y bloqueos de pastoral).
  - Las franjas de electivos de 3° y 4° medio y el informe de auditoría.

Los datos se guardan como scripts (window.HORARIOS_MMDD = {...}) para que la página
funcione abriendo 'index.html' directamente, sin servidor.

Uso:
    python "Prototipos/Prototipo 2/exportar_datos.py"                     # 2026 y 2027 (semilla 3)
    python "Prototipos/Prototipo 2/exportar_datos.py" --anio 2027 --seed 7
    python "Prototipos/Prototipo 2/exportar_datos.py" --anio 2026
"""

import os
import sys
import json
import zipfile
import argparse
import unicodedata
from datetime import datetime
from collections import defaultdict

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.join(RAIZ, 'notebooks'))

from generador_horarios import (DatosColegio, ExportadorExcel, HorarioEscolar,  # noqa: E402
                                MotorHorarios, ValidadorRestricciones)

D = DatosColegio

ANIO_OFICIAL = 2026     # Horario vigente, leído del Excel del colegio
ANIO_GENERADO = 2027    # Horario propuesto por el motor
CURSO_MUESTRA = '3° MEDIO A'   # Curso cuya semana se dibuja en la tarjeta de cada año del menú

# Ciclos en los que se agrupan los cursos en el selector de la página
CICLOS = [
    ('parvulos', 'Educación Parvularia'),
    ('basica1', 'Primer ciclo básico'),
    ('basica2', 'Segundo ciclo básico'),
    ('media', 'Enseñanza media'),
]

# Salas y recintos que muestra la vista "Salas y gimnasios": (nombre, tipo, descripción)
ESPACIOS = [
    ('GIMNASIO A', 'recinto', 'Educación Física de 5° básico a 4° medio'),
    ('GIMNASIO B', 'recinto', 'Educación Física de 1° a 4° básico y párvulos'),
    ('PATIO SANTO DOMINGO', 'recinto', 'Recibe el desborde de los gimnasios'),
    ('ELECTIVO 1', 'sala', 'Inglés · English skills (un curso por bloque)'),
    ('ELECTIVO 2', 'sala', 'Asignaturas de profundización'),
    ('ELECTIVO 3', 'sala', 'Asignaturas de profundización'),
    ('SALA DE TECNOLOGÍA', 'sala', 'Asignaturas de profundización'),
    ('SALA DE ARTES', 'sala', 'Artes Visuales de enseñanza media'),
    ('SALA DE MÚSICA', 'sala', 'Música de 5° básico a 4° medio'),
    ('SALA DE 3°A', 'sala', 'Electivos de 3° medio'),
    ('SALA DE 3°B', 'sala', 'Electivos de 3° medio'),
    ('SALA DE 4°A', 'sala', 'Electivos de 4° medio'),
    ('SALA DE 4°B', 'sala', 'Electivos de 4° medio'),
    ('SALA PADRE CUETO', 'sala', 'Sala pastoral'),
    ('SALA MADRE PILAR', 'sala', 'Sala pastoral'),
]


def ciclo_de(curso):
    if D.es_parvulo(curso):
        return 'parvulos'
    if 'MEDIO' in curso:
        return 'media'
    return 'basica1' if curso[0] in '1234' else 'basica2'


def nombre_legible(curso):
    """'3° MEDIO A' -> '3° Medio A'; 'PREKINDER A' -> 'Prekínder A'."""
    especiales = {'PREKINDER A': 'Prekínder A', 'KINDER A': 'Kínder A', 'KINDER B': 'Kínder B'}
    if curso in especiales:
        return especiales[curso]
    return curso.replace('BÁSICO', 'Básico').replace('MEDIO', 'Medio')


def numero_franja(asignatura):
    """'Formación Diferenciada · Franja 2' -> 2."""
    return int(asignatura.rsplit(' ', 1)[1]) if asignatura.startswith('Formación Diferenciada') else None


def exportar_cursos(horario, jornadas=None):
    jornadas = jornadas or D.JORNADAS
    malla = D.get_malla_curricular()
    cursos = []
    for curso in D.todos_los_cursos():
        clases = []
        for dia in D.DIAS:
            for b, item in sorted(horario.asignaciones[curso][dia].items()):
                clases.append({
                    'dia': dia,
                    'bloque': b,
                    'asignatura': item['asignatura'],
                    'etiqueta': item['etiqueta'],
                    'docentes': list(item['docentes']),
                    'espacio': item['espacio'],
                    'franja': numero_franja(item['asignatura']),
                })
        tabla = []
        for tipo, asignatura, horas, profesor in ExportadorExcel._filas_tabla_curso(curso):
            tabla.append({'tipo': tipo, 'asignatura': asignatura, 'horas': horas, 'profesor': profesor})
        cursos.append({
            'id': curso,
            'nombre': nombre_legible(curso),
            'nivel': D.nivel(curso),
            'seccion': curso[-1],
            'ciclo': ciclo_de(curso),
            'parvulo': D.es_parvulo(curso),
            'codigo': D.codigo_corto(curso),
            'jefe': D.PROFESORES_JEFES.get(curso),
            'jornada': list(jornadas[curso]),
            'horas': sum(h for _, h, _, _ in malla[curso]),
            'gimnasio': D.zona_deportiva(curso),
            'malla': [{'asignatura': a, 'horas': h, 'docentes': list(D.docentes_de(d)), 'espacio': e}
                      for a, h, d, e in malla[curso]],
            'tabla': tabla,
            'clases': clases,
        })
    return cursos


def exportar_docentes(horario):
    jefaturas = {doc: curso for curso, doc in D.PROFESORES_JEFES.items()}
    docentes = []
    for depto, nombres in D.DEPARTAMENTOS:
        depto_corto = depto.split(' –')[0].split(' - ')[0].strip()
        for doc in nombres:
            ocupado = horario.docente_ocupado.get(doc, {})
            detalle = horario.docente_detalle.get(doc, {})
            clases = []
            for (dia, b), (curso, asig) in sorted(ocupado.items(),
                                                  key=lambda kv: (D.DIAS.index(kv[0][0]), kv[0][1])):
                if (dia, b) in detalle:
                    # Electivo de 3° o 4° medio: el docente atiende una sección mixta A+B
                    nivel = curso.replace(' A-B', '')
                    item = horario.asignaciones[f'{nivel} A'][dia][b]
                    clases.append({
                        'dia': dia, 'bloque': b,
                        'curso': None, 'grupo': f'{nombre_legible(nivel)} A-B',
                        'asignatura': asig, 'etiqueta': detalle[(dia, b)]['etiqueta'],
                        'sala': detalle[(dia, b)]['sala'],
                        'electivo': True, 'franja': numero_franja(item['asignatura']),
                        'nivel': nivel, 'codocentes': [],
                    })
                    continue
                item = horario.asignaciones[curso][dia][b]
                etiqueta = item['etiqueta']
                if asig == 'Artes Visuales / Música':
                    etiqueta = 'MÚSICA' if doc == 'Música' else 'ARTES'
                clases.append({
                    'dia': dia, 'bloque': b,
                    'curso': curso, 'grupo': nombre_legible(curso),
                    'asignatura': asig, 'etiqueta': etiqueta,
                    'sala': item['espacio'], 'electivo': False, 'franja': None, 'nivel': D.nivel(curso),
                    'codocentes': [d for d in item['docentes'] if d != doc],
                })
            filas, total = ExportadorExcel._resumen_docente(doc, horario)
            docentes.append({
                'nombre': doc,
                'departamento': depto_corto,
                'departamentoCompleto': depto,
                'jefatura': jefaturas.get(doc),
                'horasGrilla': len(ocupado),
                'horasTotales': total,
                'distribucion': filas,
                'clases': clases,
            })
    return docentes


def exportar_espacios(horario):
    """Ocupación de salas de especialidad y recintos deportivos (igual que las hojas del Excel)."""
    ocupacion = defaultdict(list)   # (espacio, dia, bloque) -> [{'texto', 'curso'}]
    for curso in D.CURSOS:
        for dia in D.DIAS:
            for b, item in horario.asignaciones[curso][dia].items():
                if item['asignatura'] == 'English Skills':
                    ocupacion[('ELECTIVO 1', dia, b)].append(
                        {'texto': f"{D.codigo_corto(curso)} English skills", 'curso': curso})
                elif item['asignatura'] == 'Artes Visuales / Música':
                    ocupacion[('SALA DE ARTES', dia, b)].append(
                        {'texto': f"{D.codigo_sala(curso)} Artes", 'curso': curso})
                    ocupacion[('SALA DE MÚSICA', dia, b)].append(
                        {'texto': f"{D.codigo_sala(curso)} Música", 'curso': curso})
                elif item['espacio'] == 'Sala de Música':
                    ocupacion[('SALA DE MÚSICA', dia, b)].append(
                        {'texto': f"{D.codigo_sala(curso)} Música", 'curso': curso})
    for nivel, franjas in D.FRANJAS_ELECTIVOS.items():
        for franja in franjas:
            for dia, b0 in franja['periodos']:
                for b in (b0, b0 + 1):
                    for asig, seccion, doc, sala, etiqueta in franja['grupos']:
                        ocupacion[(sala, dia, b)].append({'texto': etiqueta, 'curso': None, 'docente': doc,
                                                          'nivel': nivel, 'asignatura': asig,
                                                          'seccion': seccion})
    for (recinto, dia, b), cursos in horario.asignar_recintos().items():
        for curso in cursos:
            ocupacion[(recinto, dia, b)].append(
                {'texto': f"{D.codigo_corto(curso)} Ed. Física", 'curso': curso})

    espacios = []
    for nombre, tipo, descripcion in ESPACIOS:
        usos = []
        for (esp, dia, b), items in ocupacion.items():
            if esp == nombre:
                usos.append({'dia': dia, 'bloque': b, 'items': items})
        usos.sort(key=lambda u: (D.DIAS.index(u['dia']), u['bloque']))
        bloqueos = [{'dia': dia, 'bloque': b} for dia, b in D.BLOQUEOS_PASTORAL.get(nombre, [])]
        espacios.append({'nombre': nombre, 'tipo': tipo, 'descripcion': descripcion,
                         'usos': usos, 'pastoral': bloqueos})
    return espacios


def exportar_franjas():
    franjas = {}
    for nivel, lista in D.FRANJAS_ELECTIVOS.items():
        franjas[nivel] = [{
            'numero': k,
            'periodos': [{'dia': dia, 'bloque': b} for dia, b in franja['periodos']],
            'grupos': [{'asignatura': a, 'seccion': s, 'docente': doc, 'sala': sala, 'etiqueta': et}
                       for a, s, doc, sala, et in franja['grupos']],
        } for k, franja in enumerate(lista, 1)]
    return franjas


def exportar_auditoria(horario):
    reporte = ValidadorRestricciones.auditar(horario)
    m = reporte['metricas']
    criterios = [
        ('Sin choques de docentes', f"{m['colisiones_docentes']} colisiones", m['colisiones_docentes']),
        ('Cargas curriculares y jornadas completas',
         f"{m['total_bloques_asignados']} / {m['total_bloques_esperados']} bloques", m['errores_carga']),
        ('Orientación a cargo del profesor/a jefe', f"{m['errores_jefatura']} inconsistencias", m['errores_jefatura']),
        ('Electivos de 3° y 4° medio sincronizados', f"{m['errores_electivos']} diferencias A/B", m['errores_electivos']),
        ('Un curso por recinto deportivo', f"{m['errores_recintos']} excesos", m['errores_recintos']),
        ('Sala English skills y bloqueos de pastoral', f"{m['errores_salas']} conflictos", m['errores_salas']),
        ('Una sesión diaria por asignatura', f"{m['mismo_dia_violaciones']} repeticiones", m['mismo_dia_violaciones']),
        ('Troncales en bloques consecutivos', f"{m['core_no_consecutivo']} bloques separados", m['core_no_consecutivo']),
    ]
    return {
        'valido': reporte['valido'],
        'errores': reporte['errores_duros'][:300],
        'totalErrores': len(reporte['errores_duros']),
        'advertencias': reporte['advertencias'],
        'metricas': m,
        'criterios': [{'criterio': c, 'valor': v, 'errores': e} for c, v, e in criterios],
    }


# =============================================================================
# HORARIO OFICIAL 2026 (lectura del Excel del colegio)
# =============================================================================

def _normalizar(texto):
    """'C. NATURALES' / 'C.NATURALES' / 'c naturales' -> 'CNATURALES' (sin tildes, espacios ni puntos)."""
    texto = unicodedata.normalize('NFD', str(texto).upper())
    return ''.join(ch for ch in texto if ch.isalnum() or ch in '/-')


# Etiqueta normalizada de la grilla del Excel -> asignatura de la malla
ASIGNATURA_DE_ETIQUETA = {
    'LENGUAJE': 'Lenguaje y Comunicación',
    'LENGAUJE': 'Lenguaje y Comunicación',     # Errata del Excel (4° básico B)
    'MATEMATICA': 'Educación Matemática',
    'INGLES': 'Idioma Extranjero Inglés',
    'CSOCIALES': 'Ciencias Sociales',
    'HISTORIA': 'Historia, Geografía y CC.SS.',
    'CNATURALES': 'Ciencias Naturales',
    'BIOLOGIA': 'Biología',
    'QUIMICA': 'Química',
    'FISICA': 'Física',
    'TECNOLOGIA': 'Educación Tecnológica',
    'ARTES': 'Artes Visuales',
    'MUSICA': 'Educación Musical',
    'ARTES-MUSICA': 'Artes Visuales / Música',
    'EDFISICA': 'Educación Física y Salud',
    'ORIEN/TEC': 'Orientación / Tecnología',
    'ORIENTACION': 'Orientación',
    'RELIGION': 'Religión',
    'FILOSOFIA': 'Filosofía',
    'EDCIUDADANA': 'Educación Ciudadana',
    'CCCIUDADANA': 'Ciencias para la Ciudadanía',
    'CCIUDADANIA': 'Ciencias para la Ciudadanía',
    # Párvulos: su grilla muestra el código del curso en los bloques de Ed. Física
    'PK': 'Educación Física y Salud',
    'KA': 'Educación Física y Salud',
    'KB': 'Educación Física y Salud',
}

AMARILLO_SKILLS = 'FFFFFF00'   # Relleno de English skills en las grillas del Excel


def curso_de_codigo(codigo):
    """Códigos de las hojas de salas y gimnasios: '2a' = 2° básico A, '2A' = 2° medio A, '7B' = 7° básico B."""
    codigo = str(codigo or '').strip()
    parvulos = {'PK': 'PREKINDER A', 'KA': 'KINDER A', 'KB': 'KINDER B'}
    if codigo.upper() in parvulos:
        return parvulos[codigo.upper()]
    if len(codigo) != 2 or codigo[0] not in '12345678' or codigo[1].upper() not in 'AB':
        return None
    numero, seccion = codigo[0], codigo[1]
    tipo = 'MEDIO' if numero in '1234' and seccion.isupper() else 'BÁSICO'
    return f'{numero}° {tipo} {seccion.upper()}'


def _grilla_hoja(ws, fila_desde=1, columna=2):
    """
    Ubica la primera grilla semanal bajo 'fila_desde' (fila con 'HORAS' en la columna B).
    Retorna ([(fila, bloque)], columna del lunes).
    """
    fila = fila_desde
    while fila <= ws.max_row and str(ws.cell(fila, columna).value or '').strip() != 'HORAS':
        fila += 1
    filas = []
    for r in range(fila + 1, fila + 16):
        b = ws.cell(r, columna).value
        if isinstance(b, (int, float)) and 1 <= int(b) <= 10:
            filas.append((r, int(b)))
        elif b is None and filas:
            break
    return filas, columna + 2


def _skills_por_bloque(wb):
    """(curso, día, bloque) con English skills según la sala ELECTIVO 1 (hoja SALAS ELECTIVOS)."""
    ws = wb['SALAS ELECTIVOS']
    skills = set()
    filas, col0 = _grilla_hoja(ws)
    for r, b in filas:
        for i, dia in enumerate(D.DIAS):
            curso = curso_de_codigo(ws.cell(r, col0 + i).value)
            if curso:
                skills.add((curso, dia, b))
    return skills


def _recintos_por_bloque(wb):
    """(curso, día, bloque) -> recinto deportivo, según la hoja GIMNASIOS."""
    ws = wb['GIMNASIOS']
    recintos = {}
    for fila in range(1, ws.max_row + 1):
        titulo = str(ws.cell(fila, 4).value or '').strip().upper()
        if titulo not in D.RECINTOS_DEPORTIVOS:
            continue
        filas, col0 = _grilla_hoja(ws, fila)
        for r, b in filas:
            for i, dia in enumerate(D.DIAS):
                curso = curso_de_codigo(ws.cell(r, col0 + i).value)
                if curso:
                    recintos[(curso, dia, b)] = titulo
    return recintos


def leer_horario_oficial(ruta=None):
    """
    Construye un HorarioEscolar con el horario oficial 2026 tal como está en el Excel:
    la asignatura de cada bloque sale de la grilla de cada curso, English skills de la sala
    ELECTIVO 1 (o del relleno amarillo), las franjas de electivos de sus etiquetas y el recinto
    deportivo de la hoja GIMNASIOS. Los docentes se asignan con la distribución horaria 2026.
    Retorna (horario, jornadas, avisos).
    """
    import openpyxl
    wb = openpyxl.load_workbook(ruta or ExportadorExcel.RUTA_EXCEL_OFICIAL)
    hojas = {_normalizar(n): wb[n] for n in wb.sheetnames}
    malla = D.get_malla_curricular()
    skills = _skills_por_bloque(wb)
    recintos_reales = _recintos_por_bloque(wb)
    horario = HorarioEscolar()
    jornadas = {}
    avisos = []

    for curso in D.todos_los_cursos():
        ws = hojas.get(_normalizar(curso))
        if ws is None:
            avisos.append(f'No se encontró la hoja de {curso}')
            jornadas[curso] = D.JORNADAS[curso]
            continue
        lecciones = {a: (D.docentes_de(d), e) for a, _, d, e in malla[curso]}
        # Etiqueta de cada bloque de las franjas de electivos de este curso -> (n° de franja, franja)
        etiquetas_franja = {}
        for k, franja in enumerate(D.franjas_de(curso), 1):
            for etiqueta in D.etiquetas_franja(franja, curso):
                etiquetas_franja[_normalizar(etiqueta)] = (k, franja)

        ultimo = [0] * len(D.DIAS)
        filas, col0 = _grilla_hoja(ws)
        for r, b in filas:
            for i, dia in enumerate(D.DIAS):
                celda = ws.cell(r, col0 + i)
                texto = str(celda.value or '').strip()
                if not texto or texto.upper() == 'PASTORAL':
                    continue
                clave = _normalizar(texto)
                ultimo[i] = max(ultimo[i], b)

                if clave in etiquetas_franja:
                    k, franja = etiquetas_franja[clave]
                    detalle = {doc: (et, sala, f"{asig.capitalize()} ({seccion})")
                               for asig, seccion, doc, sala, et in franja['grupos']}
                    docentes = tuple(dict.fromkeys(g[2] for g in franja['grupos']))
                    horario.asignar(curso, dia, b, D.nombre_franja(k), docentes, 'Salas electivos',
                                    etiqueta=texto, clave=f'{D.nivel(curso)} A-B', detalle=detalle)
                    continue

                asignatura = ASIGNATURA_DE_ETIQUETA.get(clave)
                if asignatura is None:
                    avisos.append(f'{curso}: etiqueta desconocida "{texto}" el {dia} bloque {b}')
                    continue
                relleno = celda.fill.fgColor.rgb if celda.fill and celda.fill.fill_type else None
                if asignatura == 'Idioma Extranjero Inglés' and ((curso, dia, b) in skills or relleno == AMARILLO_SKILLS):
                    asignatura = 'English Skills'
                if asignatura not in lecciones:
                    avisos.append(f'{curso}: "{texto}" ({dia} bloque {b}) no está en la malla 2026')
                docentes, espacio = lecciones.get(asignatura, ((), 'Aula'))
                horario.asignar(curso, dia, b, asignatura, docentes, espacio)
        jornadas[curso] = D.JORNADAS[curso] if D.es_parvulo(curso) else tuple(ultimo)

    # Recintos deportivos según la hoja GIMNASIOS; si un bloque no aparece ahí, se usa la regla del motor
    def asignar_recintos():
        recintos = defaultdict(list)
        for (dia, b), cursos in horario.gimnasio_ocupado.items():
            for curso in cursos:
                destino = recintos_reales.get((curso, dia, b))
                if destino is None:
                    zona = D.zona_deportiva(curso)
                    destino = zona if not recintos[(zona, dia, b)] else 'PATIO SANTO DOMINGO'
                recintos[(destino, dia, b)].append(curso)
        return recintos

    horario.asignar_recintos = asignar_recintos
    return horario, jornadas, avisos


def exportar_escudo():
    """Copia el escudo del Excel oficial 2026 como PNG con fondo transparente."""
    ruta_excel = ExportadorExcel.RUTA_EXCEL_OFICIAL
    destino = os.path.join(AQUI, 'assets', 'escudo.png')
    try:
        with zipfile.ZipFile(ruta_excel) as z:
            medios = sorted(n for n in z.namelist() if n.startswith('xl/media/'))
            if not medios:
                return False
            crudo = z.read(medios[0])
    except (OSError, zipfile.BadZipFile):
        return False
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    try:
        import io
        from PIL import Image
    except ImportError:
        return False
    imagen = Image.open(io.BytesIO(crudo)).convert('L')
    # El escudo es negro sobre blanco: la luminancia se convierte en transparencia
    alfa = imagen.point(lambda v: 255 if v < 110 else (0 if v > 200 else int((200 - v) * 255 / 90)))
    negro = Image.new('LA', imagen.size, 0)
    negro.putalpha(alfa)
    negro.save(destino)
    return True


def construir_datos(horario, meta, jornadas=None):
    return {
        'meta': meta,
        'dias': D.DIAS,
        'bloques': [{'numero': b, 'inicio': ini, 'fin': fin} for b, (ini, fin) in D.HORARIOS_BLOQUES.items()],
        'pausas': [{'despues': b, 'nombre': nombre, 'rango': rango} for b, (nombre, rango) in D.RECREOS.items()],
        'pares': [list(p) for p in D.PARES],
        'ciclos': [{'id': i, 'nombre': n} for i, n in CICLOS],
        'cursos': exportar_cursos(horario, jornadas),
        'docentes': exportar_docentes(horario),
        'espacios': exportar_espacios(horario),
        'franjas': exportar_franjas(),
        'auditoria': exportar_auditoria(horario),
    }


def escribir_datos(datos):
    """Escribe datos/horarios_<año>.js (completo) y datos/resumen_<año>.js (tarjeta del menú)."""
    meta = datos['meta']
    anio = meta['anio']
    carpeta = os.path.join(AQUI, 'datos')
    os.makedirs(carpeta, exist_ok=True)
    origen = 'Excel oficial' if meta['fuente'] == 'oficial' else f"Semilla {meta['semilla']}"

    destino = os.path.join(carpeta, f'horarios_{anio}.js')
    with open(destino, 'w', encoding='utf-8') as f:
        f.write('// Archivo generado por exportar_datos.py — no editar a mano.\n')
        f.write(f"// Horario {anio} · {origen} · {meta['generado']}\n")
        f.write('window.HORARIOS_MMDD = ')
        json.dump(datos, f, ensure_ascii=False, separators=(',', ':'))
        f.write(';\n')

    a = datos['auditoria']
    m = a['metricas']
    # Semana de un curso para la mini-grilla de la tarjeta: asignatura por día y bloque (None si no hay clase)
    curso = next(c for c in datos['cursos'] if c['id'] == CURSO_MUESTRA)
    clases = {(k['dia'], k['bloque']): k['asignatura'] for k in curso['clases']}
    muestra = {'curso': curso['nombre'],
               'dias': [[clases.get((dia, b)) for b in range(1, max(curso['jornada']) + 1)] for dia in D.DIAS]}
    resumen = {
        **meta,
        'cursos': len(datos['cursos']),
        'docentes': len(datos['docentes']),
        'valido': a['valido'],
        'totalErrores': a['totalErrores'],
        'bloques': m['total_bloques_asignados'],
        'bloquesEsperados': m['total_bloques_esperados'],
        'dobles': m['porcentaje_bloques_dobles'],
        'ventanas': m['total_ventanas_docentes'],
        'patio': m['uso_patio'],
        'muestra': muestra,
    }
    with open(os.path.join(carpeta, f'resumen_{anio}.js'), 'w', encoding='utf-8') as f:
        f.write('// Archivo generado por exportar_datos.py — no editar a mano.\n')
        f.write(f'(window.HORARIOS_MMDD_RESUMEN = window.HORARIOS_MMDD_RESUMEN || {{}})[{anio}] = ')
        json.dump(resumen, f, ensure_ascii=False, separators=(',', ':'))
        f.write(';\n')

    estado = 'FACTIBLE' if a['valido'] else f"{a['totalErrores']} incumplimientos"
    print(f"Horario {anio} ({origen}) exportado en {os.path.relpath(destino, RAIZ)}")
    print(f"  {len(datos['cursos'])} cursos · {len(datos['docentes'])} docentes · {len(datos['espacios'])} espacios")
    print(f"  Auditoría: {estado} ({m['total_bloques_asignados']}/{m['total_bloques_esperados']} bloques, "
          f"{m['porcentaje_bloques_dobles']}% en bloques dobles)")


def meta_base(anio, fuente, **extra):
    return {
        'colegio': 'Colegio Madres Dominicas',
        'ciudad': 'Concepción',
        'anio': anio,
        'fuente': fuente,      # 'oficial' (Excel del colegio) o 'generado' (motor)
        'generado': datetime.now().strftime('%Y-%m-%d %H:%M'),
        **extra,
    }


def main():
    parser = argparse.ArgumentParser(description='Exporta los horarios 2026 (oficial) y 2027 (generado) '
                                                 'para la plataforma web (Prototipo 2)')
    parser.add_argument('--anio', type=int, choices=[ANIO_OFICIAL, ANIO_GENERADO],
                        help='Exporta solo ese año (por defecto, ambos)')
    parser.add_argument('--seed', type=int, default=3, help='Semilla del generador para 2027 (default: 3)')
    args = parser.parse_args()

    if args.anio in (None, ANIO_OFICIAL):
        horario, jornadas, avisos = leer_horario_oficial()
        archivo = os.path.relpath(ExportadorExcel.RUTA_EXCEL_OFICIAL, RAIZ).replace(os.sep, '/')
        escribir_datos(construir_datos(horario, meta_base(ANIO_OFICIAL, 'oficial', semilla=None, archivo=archivo),
                                       jornadas))
        for aviso in avisos:
            print(f'  Aviso: {aviso}')

    if args.anio in (None, ANIO_GENERADO):
        horario = MotorHorarios(seed=args.seed).generar()
        escribir_datos(construir_datos(horario, meta_base(ANIO_GENERADO, 'generado', semilla=args.seed)))

    escudo = exportar_escudo()
    print(f"Escudo: {'assets/escudo.png' if escudo else 'no disponible (se usa el monograma)'}")


if __name__ == '__main__':
    main()
