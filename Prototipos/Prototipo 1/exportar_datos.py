#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
EXPORTADOR DE DATOS PARA LA PÁGINA WEB (PROTOTIPO 1)
Colegio Madres Dominicas (MMDD) - Taller de Gestión de Operaciones, UdeC
===============================================================================

Ejecuta el motor de `notebooks/generador_horarios.py`, audita el resultado y
escribe `datos_horarios.js`, el archivo que lee `index.html`.

Se usa un archivo .js (y no .json) para que la página funcione abriendo
index.html con doble clic, sin necesidad de levantar un servidor.

Uso:
    python exportar_datos.py                 # semilla por defecto (3)
    python exportar_datos.py --seed 7        # otra semilla
    python exportar_datos.py --salida horario_semilla7.js
"""

import os
import re
import sys
import json
import argparse
from datetime import datetime

CARPETA = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(CARPETA, '..', 'notebooks'))
sys.dont_write_bytecode = True  # no dejar __pycache__ dentro de notebooks/

from generador_horarios import DatosColegio, MotorHorarios, ValidadorRestricciones  # noqa: E402

# Restricciones duras que audita ValidadorRestricciones, con los fragmentos de sus mensajes de error
RESTRICCIONES_DURAS = [
    ('HC2', 'No solapamiento docente',
     'Ningún docente atiende a dos cursos o grupos en el mismo bloque.',
     ('Colisión Docente',)),
    ('HC3', 'Clases dentro de la jornada',
     'Cada curso recibe clases solo en los bloques de su jornada diaria.',
     ('Bloque fuera de jornada', 'Colisión de Curso')),
    ('HC4', 'Cargas horarias exactas',
     'Cada asignatura recibe exactamente las horas que exige el plan de estudios.',
     ('Carga horaria incorrecta', 'no coincide con su jornada', ' horas esperadas ')),
    ('HC5', 'Orientación con profesor jefe',
     'La hora de Orientación la dicta el profesor jefe del curso.',
     ('Orientación/Jefatura',)),
    ('HC6', 'Electivos sincronizados (3° y 4° medio)',
     'Las franjas de formación diferenciada coinciden entre las secciones A y B.',
     ('Desincronización de electivos',)),
    ('HC7', 'Recintos deportivos',
     'Gimnasio A, Gimnasio B y Patio Santo Domingo reciben un curso por bloque.',
     ('Capacidad de',)),
    ('HC8', 'Salas limitadas y co-docencia',
     'English Skills se dicta con dos docentes y su sala no se comparte.',
     ('sin co-docencia', ' ocupada por ')),
    ('HC9–10', 'Una sesión diaria por asignatura',
     'Cada asignatura se dicta en una sola sesión por día; las troncales en pares de 90 min.',
     ('Asignatura repetida', 'Asignatura fragmentada', 'Bloque no consecutivo')),
    ('HC11', 'Bloqueos de pastoral',
     'Los electivos no usan salas reservadas para actividades pastorales.',
     ('bloqueada por pastoral',)),
]

NOMBRES_PARVULOS = {'PREKINDER': 'Prekínder', 'KINDER': 'Kínder'}
PALABRAS_MENORES = {'de', 'del', 'la', 'las', 'los', 'y', 'e', 'en'}


def bonito(texto):
    """'SALA DE 3°A' -> 'Sala de 3°A'; 'PATIO SANTO DOMINGO' -> 'Patio Santo Domingo'."""
    if not texto or texto != texto.upper():
        return texto
    palabras = []
    for i, p in enumerate(texto.split()):
        if any(ch.isdigit() for ch in p) or (i > 0 and len(p) == 1):
            palabras.append(p)
        elif i > 0 and p.lower() in PALABRAS_MENORES:
            palabras.append(p.lower())
        else:
            palabras.append(p.capitalize())
    return ' '.join(palabras)


def nombre_departamento(nombre):
    """'ARTES VISUALES – MÚSICA – TECNOLOGÍA - ASIGNATURAS DE PROFUNDIZACIÓN' -> 'Artes visuales – Música – Tecnología'."""
    partes = [p.strip() for p in re.split(r'\s[–-]\s', nombre)]
    partes = [p for p in partes if 'PROFUNDIZACIÓN' not in p.upper()]
    texto = ' – '.join(p[:1].upper() + p[1:].lower() for p in partes)
    return re.sub(r'\b(\w)\.', lambda m: m.group(1).upper() + '.', texto)   # 'c. sociales' -> 'C. sociales'


def docentes_de(item_o_docente):
    """Normaliza a lista: el generador usa un str o una tupla (co-docencia)."""
    if isinstance(item_o_docente, dict):
        return list(item_o_docente.get('docentes') or [item_o_docente['docente']])
    if isinstance(item_o_docente, (list, tuple)):
        return list(item_o_docente)
    return [item_o_docente]


def describir_curso(curso, es_parvulo):
    partes = curso.split()
    seccion = partes[-1]
    if es_parvulo:
        nivel = NOMBRES_PARVULOS.get(partes[0], partes[0].capitalize())
        return {'nombre': f'{nivel} {seccion}', 'nivel': nivel, 'seccion': seccion,
                'ciclo': 'Párvulos · solo Ed. Física', 'parvulo': True}
    numero = int(partes[0].rstrip('°'))
    tipo = partes[1].capitalize()
    if tipo == 'Básico':
        ciclo = '1° a 4° Básico' if numero <= 4 else '5° a 8° Básico'
    else:
        ciclo = '1° a 4° Medio'
    nivel = f'{partes[0]} {tipo}'
    return {'nombre': f'{nivel} {seccion}', 'nivel': nivel, 'seccion': seccion, 'ciclo': ciclo, 'parvulo': False}


def texto_recreo(valor):
    """El generador usa ('RECREO', '09:30 - 09:45') o '09:30 - 09:40 (Recreo 1)'."""
    if isinstance(valor, (list, tuple)):
        nombre, rango = valor
    else:
        m = re.match(r'^(.*?)\s*\((.*)\)$', valor)
        rango, nombre = (m.group(1), m.group(2)) if m else (valor, 'Recreo')
    return {'nombre': nombre.capitalize(), 'horario': rango.replace(' - ', '–')}


def construir_datos(horario, semilla):
    malla = DatosColegio.get_malla_curricular()
    auditoria = ValidadorRestricciones.auditar(horario)
    parvulos = list(getattr(DatosColegio, 'CURSOS_PARVULOS', []))
    todos = list(DatosColegio.CURSOS) + parvulos   # cursos regulares primero
    nombres = {c: describir_curso(c, c in parvulos)['nombre'] for c in todos}

    def nombre_grupo(clave):
        if clave in nombres:
            return nombres[clave]
        if clave.endswith(' A-B'):
            return nombres.get(f'{clave[:-4]} A', clave)[:-2] + ' A-B'
        return clave

    def cursos_del_grupo(clave):
        if clave in nombres:
            return [clave]
        if clave.endswith(' A-B'):
            return [f'{clave[:-4]} A', f'{clave[:-4]} B']
        return []

    # Recinto deportivo que ocupa cada curso en cada bloque de Ed. Física
    if hasattr(horario, 'asignar_recintos'):
        uso = horario.asignar_recintos()
        nombres_recintos = list(getattr(DatosColegio, 'RECINTOS_DEPORTIVOS', sorted({r for r, _, _ in uso})))
        capacidad = {bonito(r): 1 for r in nombres_recintos}
    else:
        uso = {('RECINTOS DEPORTIVOS', d, b): list(cs) for (d, b), cs in horario.gimnasio_ocupado.items() if cs}
        nombres_recintos = ['RECINTOS DEPORTIVOS']
        capacidad = {'Recintos Deportivos': 3}
    recinto_de = {}
    uso_recintos = {dia: {} for dia in DatosColegio.DIAS}
    for (recinto, dia, b), cursos in uso.items():
        for c in cursos:
            recinto_de[(c, dia, b)] = bonito(recinto)
        if cursos:
            uso_recintos[dia].setdefault(str(b), {})[bonito(recinto)] = list(cursos)

    # Cursos
    cursos = []
    for c in todos:
        jefe = DatosColegio.PROFESORES_JEFES.get(c, '')
        cursos.append({
            'id': c,
            **describir_curso(c, c in parvulos),
            'jefe': jefe,
            'carga': sum(h for _, h, _, _ in malla[c]),
            'bloquesPermitidos': {dia: DatosColegio.get_bloques_permitidos(c, dia) for dia in DatosColegio.DIAS},
            'malla': [
                {'asignatura': a, 'horas': h, 'docentes': docentes_de(d), 'espacio': e}
                for a, h, d, e in malla[c]
            ],
        })

    # Asignaciones por curso
    asignaciones = {}
    for c in todos:
        asignaciones[c] = {}
        for dia in DatosColegio.DIAS:
            del_dia = {}
            for b in sorted(horario.asignaciones[c][dia]):
                item = horario.asignaciones[c][dia][b]
                fila = {
                    'asignatura': item['asignatura'],
                    'docentes': docentes_de(item),
                    'espacio': item.get('espacio', 'Aula'),
                }
                if item.get('etiqueta'):
                    fila['etiqueta'] = item['etiqueta']
                if (c, dia, b) in recinto_de:
                    fila['recinto'] = recinto_de[(c, dia, b)]
                del_dia[str(b)] = fila
            asignaciones[c][dia] = del_dia

    # Horario de cada docente (incluye qué electivo y en qué sala atiende)
    departamento_de = {}
    departamentos = []
    for dep, miembros in getattr(DatosColegio, 'DEPARTAMENTOS', []):
        nombre = nombre_departamento(dep)
        departamentos.append(nombre)
        for d in miembros:
            departamento_de[d] = nombre
    detalle = getattr(horario, 'docente_detalle', {})
    no_lectivas = getattr(DatosColegio, 'HORAS_NO_LECTIVAS', {})

    docentes = []
    for doc in sorted(horario.docente_ocupado):
        clases = {dia: {} for dia in DatosColegio.DIAS}
        for (dia, b), (clave, asig) in horario.docente_ocupado[doc].items():
            relacionados = cursos_del_grupo(clave)
            item = horario.asignaciones[relacionados[0]][dia].get(b, {}) if relacionados else {}
            clase = {
                'grupo': clave,
                'grupoNombre': nombre_grupo(clave),
                'cursos': relacionados,
                'asignatura': asig,
                'base': item.get('asignatura', asig),
            }
            extra = detalle.get(doc, {}).get((dia, b))
            if extra:
                clase['sala'] = bonito(extra.get('sala', ''))
            else:
                otros = [d for d in docentes_de(item) if d != doc] if item else []
                if otros:
                    clase['coDocentes'] = otros
                lugar = recinto_de.get((relacionados[0], dia, b)) if relacionados else None
                lugar = lugar or item.get('espacio')
                if lugar and lugar != 'Aula':
                    clase['sala'] = lugar
            clases[dia][str(b)] = clase
        docentes.append({
            'id': doc,
            'departamento': departamento_de.get(doc, 'Otros'),
            'clases': clases,
            'horasNoLectivas': [
                {'cursos': cs, 'actividad': act, 'horas': h} for cs, act, h in no_lectivas.get(doc, [])
            ],
        })

    # Franjas de electivos de 3° y 4° medio
    franjas = {}
    for nivel, lista in getattr(DatosColegio, 'FRANJAS_ELECTIVOS', {}).items():
        franjas[nivel] = [{
            'nombre': DatosColegio.nombre_franja(k),
            'grupos': [
                {'asignatura': a.capitalize(), 'seccion': s, 'docente': d, 'sala': bonito(sala)}
                for a, s, d, sala, _ in f['grupos']
            ],
        } for k, f in enumerate(lista, 1)]

    # Auditoría agrupada por restricción
    restricciones = []
    clasificados = set()
    for codigo, nombre, descripcion, fragmentos in RESTRICCIONES_DURAS:
        errores = [e for e in auditoria['errores_duros'] if any(f in e for f in fragmentos)]
        clasificados.update(errores)
        restricciones.append({'codigo': codigo, 'nombre': nombre, 'descripcion': descripcion, 'errores': errores})

    return {
        'meta': {
            'colegio': 'Colegio Madres Dominicas - Concepción',
            'anio': getattr(DatosColegio, 'ANIO', None),
            'semilla': semilla,
            'generado': datetime.now().strftime('%Y-%m-%d %H:%M'),
        },
        'dias': DatosColegio.DIAS,
        'bloques': {str(b): list(h) for b, h in DatosColegio.HORARIOS_BLOQUES.items()},
        'recreos': {str(b): texto_recreo(v) for b, v in DatosColegio.RECREOS.items()},
        'cursos': cursos,
        'asignaciones': asignaciones,
        'docentes': docentes,
        'departamentos': departamentos,
        'franjas': franjas,
        'recintos': {
            'nombres': [bonito(r) for r in nombres_recintos],
            'capacidad': capacidad,
            'uso': uso_recintos,
        },
        'auditoria': {
            'valido': auditoria['valido'],
            'metricas': auditoria['metricas'],
            'restricciones': restricciones,
            'advertencias': auditoria.get('advertencias', []),
            'otrosErrores': [e for e in auditoria['errores_duros'] if e not in clasificados],
        },
    }


def main():
    parser = argparse.ArgumentParser(description='Exporta el horario generado para la página web')
    parser.add_argument('--seed', type=int, default=3, help='Semilla del generador (default: 3)')
    parser.add_argument('--salida', default='datos_horarios.js',
                        help='Archivo de salida dentro de Prototipo 1 (default: datos_horarios.js)')
    args = parser.parse_args()

    horario = MotorHorarios(seed=args.seed).generar()
    datos = construir_datos(horario, args.seed)

    ruta = os.path.join(CARPETA, args.salida)
    with open(ruta, 'w', encoding='utf-8') as f:
        f.write('// Archivo generado por exportar_datos.py - no editar a mano.\n')
        f.write('window.DATOS_HORARIOS = ')
        json.dump(datos, f, ensure_ascii=False, separators=(',', ':'))
        f.write(';\n')

    estado = 'FACTIBLE' if datos['auditoria']['valido'] else 'CON CONFLICTOS'
    print(f'Horario exportado (semilla {args.seed}, {estado}): {ruta}')


if __name__ == '__main__':
    main()
