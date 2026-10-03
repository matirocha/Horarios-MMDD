#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
PROTOTIPO 2 — EXPORTADOR DE DATOS PARA LA PLATAFORMA WEB DE HORARIOS MMDD
===============================================================================

Ejecuta el motor de 'notebooks/generador_horarios.py', audita el horario obtenido
y escribe todo lo que necesita la página web en 'datos/horarios.js':

  - Bloques, recreos y días de la semana.
  - Los 24 cursos regulares y los 3 niveles de párvulos (jornada, profesor/a jefe,
    tabla de horas y grilla semanal).
  - Los 37 docentes (departamento, jefatura, grilla semanal y distribución horaria).
  - Las salas de especialidad y los recintos deportivos (ocupación y bloqueos de pastoral).
  - Las franjas de electivos de 3° y 4° medio y el informe de auditoría.

Los datos se guardan como un script (window.HORARIOS_MMDD = {...}) para que la página
funcione abriendo 'index.html' directamente, sin servidor.

Uso:
    python "Prototipos/Prototipo 2/exportar_datos.py"            # semilla por defecto (3)
    python "Prototipos/Prototipo 2/exportar_datos.py" --seed 7
"""

import os
import sys
import json
import zipfile
import argparse
from datetime import datetime
from collections import defaultdict

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.join(RAIZ, 'notebooks'))

from generador_horarios import (DatosColegio, ExportadorExcel, MotorHorarios,  # noqa: E402
                                ValidadorRestricciones)

D = DatosColegio

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


def exportar_cursos(horario):
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
            'jornada': list(D.JORNADAS[curso]),
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


def main():
    parser = argparse.ArgumentParser(description='Exporta los horarios generados para la plataforma web (Prototipo 2)')
    parser.add_argument('--seed', type=int, default=3, help='Semilla del generador (default: 3)')
    args = parser.parse_args()

    horario = MotorHorarios(seed=args.seed).generar()
    datos = {
        'meta': {
            'colegio': 'Colegio Madres Dominicas',
            'ciudad': 'Concepción',
            'anio': D.ANIO,
            'semilla': args.seed,
            'generado': datetime.now().strftime('%Y-%m-%d %H:%M'),
        },
        'dias': D.DIAS,
        'bloques': [{'numero': b, 'inicio': ini, 'fin': fin} for b, (ini, fin) in D.HORARIOS_BLOQUES.items()],
        'pausas': [{'despues': b, 'nombre': nombre, 'rango': rango} for b, (nombre, rango) in D.RECREOS.items()],
        'pares': [list(p) for p in D.PARES],
        'ciclos': [{'id': i, 'nombre': n} for i, n in CICLOS],
        'cursos': exportar_cursos(horario),
        'docentes': exportar_docentes(horario),
        'espacios': exportar_espacios(horario),
        'franjas': exportar_franjas(),
        'auditoria': exportar_auditoria(horario),
    }

    destino = os.path.join(AQUI, 'datos', 'horarios.js')
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, 'w', encoding='utf-8') as f:
        f.write('// Archivo generado por exportar_datos.py — no editar a mano.\n')
        f.write(f"// Semilla {args.seed} · {datos['meta']['generado']}\n")
        f.write('window.HORARIOS_MMDD = ')
        json.dump(datos, f, ensure_ascii=False, separators=(',', ':'))
        f.write(';\n')

    escudo = exportar_escudo()
    a = datos['auditoria']
    print(f"Datos exportados en {os.path.relpath(destino, RAIZ)}")
    print(f"  {len(datos['cursos'])} cursos · {len(datos['docentes'])} docentes · {len(datos['espacios'])} espacios")
    print(f"  Auditoría: {'FACTIBLE' if a['valido'] else 'NO FACTIBLE'} "
          f"({a['metricas']['total_bloques_asignados']}/{a['metricas']['total_bloques_esperados']} bloques, "
          f"{a['metricas']['porcentaje_bloques_dobles']}% en bloques dobles)")
    print(f"  Escudo: {'assets/escudo.png' if escudo else 'no disponible (se usa el monograma)'}")


if __name__ == '__main__':
    main()
