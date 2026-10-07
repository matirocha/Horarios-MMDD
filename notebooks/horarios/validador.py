# -*- coding: utf-8 -*-
"""
Auditoría exhaustiva de las restricciones duras y de los criterios de calidad
de un horario ya construido.
"""

from collections import defaultdict

from .datos import DatosColegio


class ValidadorRestricciones:
    """Verifica el estricto cumplimiento de las restricciones duras y los criterios de calidad."""

    @staticmethod
    def auditar(horario):
        malla = DatosColegio.get_malla_curricular()
        reporte = {
            'valido': True,
            'errores_duros': [],
            'advertencias': [],
            'metricas': {}
        }
        errores = reporte['errores_duros']
        conteo = defaultdict(int)

        # HC 1, 2: Choques docentes (Clash-Free Teacher). Un electivo compartido por A y B
        # cuenta como un solo grupo.
        colisiones_docentes = 0
        for doc, bloques in horario.docente_claves.items():
            for (dia, bloque), claves in bloques.items():
                if len(claves) > 1:
                    colisiones_docentes += 1
                    errores.append(f"Colisión Docente: {doc} atiende {sorted(claves)} el {dia} bloque {bloque}")
        conteo['colisiones_docentes'] = colisiones_docentes

        # HC 3: Ocupación única de cada curso dentro de su jornada
        for curso in DatosColegio.todos_los_cursos():
            for dia in DatosColegio.DIAS:
                permitidos = DatosColegio.get_bloques_permitidos(curso, dia)
                for bloque in horario.asignaciones[curso][dia]:
                    if bloque not in permitidos:
                        errores.append(f"Bloque fuera de jornada: {curso} el {dia} bloque {bloque}")
                        conteo['fuera_jornada'] += 1

        # HC 4: Cumplimiento estricto de cargas horarias (y jornada completa sin huecos)
        horas_por_materia = defaultdict(lambda: defaultdict(int))
        total_asignados = defaultdict(int)
        for curso in DatosColegio.todos_los_cursos():
            for dia in DatosColegio.DIAS:
                for bloque, item in horario.asignaciones[curso][dia].items():
                    horas_por_materia[curso][item['asignatura']] += 1
                    total_asignados[curso] += 1
        esperado_global = 0
        for curso, materias in malla.items():
            esperado = sum(h for _, h, _, _ in materias)
            esperado_global += esperado
            if total_asignados[curso] != esperado:
                errores.append(f"Carga horaria incorrecta en {curso}: requerida={esperado}, asignada={total_asignados[curso]}")
                conteo['cargas'] += 1
            if not DatosColegio.es_parvulo(curso) and esperado != DatosColegio.get_total_bloques_semanal(curso):
                errores.append(f"La malla de {curso} ({esperado} h) no coincide con su jornada "
                               f"({DatosColegio.get_total_bloques_semanal(curso)} bloques)")
                conteo['cargas'] += 1
            for asig, hrs, _, _ in materias:
                if horas_por_materia[curso][asig] != hrs:
                    errores.append(f"{curso} - {asig}: horas esperadas {hrs} != asignadas {horas_por_materia[curso][asig]}")
                    conteo['cargas'] += 1

        # HC 5: Orientación y jefatura a cargo del profesor jefe de cada curso
        for curso in DatosColegio.CURSOS:
            jefe = DatosColegio.PROFESORES_JEFES[curso]
            for dia in DatosColegio.DIAS:
                for bloque, item in horario.asignaciones[curso][dia].items():
                    if item['asignatura'] in ('Orientación', 'Orientación / Tecnología') and jefe not in item['docentes']:
                        errores.append(f"Orientación/Jefatura en {curso} no está a cargo de {jefe}")
                        conteo['jefaturas'] += 1

        # HC 6: Sincronización de las franjas de electivos (3° y 4° medio A y B)
        for nivel in DatosColegio.FRANJAS_ELECTIVOS:
            ocupacion = []
            for seccion in ('A', 'B'):
                curso = f"{nivel} {seccion}"
                ocupacion.append({
                    (dia, b, item['asignatura'])
                    for dia in DatosColegio.DIAS
                    for b, item in horario.asignaciones[curso][dia].items()
                    if item['asignatura'].startswith('Formación Diferenciada')
                })
            if ocupacion[0] != ocupacion[1]:
                errores.append(f"Desincronización de electivos en {nivel}: {sorted(ocupacion[0] ^ ocupacion[1])}")
                conteo['electivos'] += 1

        # HC 7: Recintos deportivos (Gimnasio A, Gimnasio B y Patio Santo Domingo, un curso cada uno)
        uso_patio = 0
        for (recinto, dia, bloque), cursos in horario.asignar_recintos().items():
            if recinto == 'PATIO SANTO DOMINGO':
                uso_patio += 1
            if len(cursos) > 1:
                errores.append(f"Capacidad de {recinto} excedida el {dia} bloque {bloque}: {cursos}")
                conteo['recintos'] += 1

        # HC 8: Salas de capacidad limitada (English skills) y co-docencia completa
        uso_salas = defaultdict(list)
        for curso in DatosColegio.CURSOS:
            for dia in DatosColegio.DIAS:
                for bloque, item in horario.asignaciones[curso][dia].items():
                    if item['espacio'] in DatosColegio.RECURSOS_CAPACIDAD:
                        uso_salas[(item['espacio'], dia, bloque)].append(curso)
                    if item['asignatura'] == 'English Skills' and len(item['docentes']) < 2:
                        errores.append(f"English skills sin co-docencia en {curso} el {dia} bloque {bloque}")
                        conteo['salas'] += 1
        for (sala, dia, bloque), cursos in uso_salas.items():
            if len(cursos) > DatosColegio.RECURSOS_CAPACIDAD[sala]:
                errores.append(f"{sala} ocupada por {cursos} el {dia} bloque {bloque}")
                conteo['salas'] += 1

        # HC 9: Una sola sesión diaria por asignatura (una sesión = 1 bloque o un par consecutivo)
        # HC 10: Las troncales nunca quedan en bloques separados del mismo día
        same_day_violations = 0
        core_non_consecutive = 0
        for curso in DatosColegio.todos_los_cursos():
            por_dia = defaultdict(list)
            for dia in DatosColegio.DIAS:
                for bloque, item in horario.asignaciones[curso][dia].items():
                    if not item['asignatura'].startswith('Formación Diferenciada'):
                        por_dia[(dia, DatosColegio.familia(item['asignatura']))].append(bloque)
            for (dia, fam), bloques in por_dia.items():
                bl = sorted(bloques)
                es_par = len(bl) == 2 and (bl[0], bl[1]) in DatosColegio.PARES
                if len(bl) > 2 or (len(bl) == 2 and not es_par):
                    same_day_violations += 1
                    errores.append(f"Asignatura repetida en {curso} el {dia}: '{fam}' en bloques {bl}")
                    if any(t.lower() in fam.lower() for t in DatosColegio.ASIGNATURAS_TRONCALES):
                        core_non_consecutive += 1

        # HC 11: Las salas usadas no coinciden con los bloqueos de pastoral
        for nivel, franjas in DatosColegio.FRANJAS_ELECTIVOS.items():
            for franja in franjas:
                for dia, b0 in franja['periodos']:
                    for grupo in franja['grupos']:
                        bloqueos = DatosColegio.BLOQUEOS_PASTORAL.get(grupo[3], [])
                        if (dia, b0) in bloqueos or (dia, b0 + 1) in bloqueos:
                            errores.append(f"{grupo[3]} bloqueada por pastoral el {dia} ({grupo[4]})")
                            conteo['pastoral'] += 1

        # MÉTRICAS BLANDAS: Ventanas docentes y bloques dobles
        total_ventanas = 0
        for doc, bloques in horario.docente_ocupado.items():
            for dia in DatosColegio.DIAS:
                ocupados = sorted(b for (d, b) in bloques if d == dia)
                for i in range(len(ocupados) - 1):
                    total_ventanas += ocupados[i + 1] - ocupados[i] - 1

        total_sesiones = 0
        bloques_dobles_logrados = 0
        for curso in DatosColegio.CURSOS:
            for dia in DatosColegio.DIAS:
                asig = horario.asignaciones[curso][dia]
                bloques = sorted(asig)
                i = 0
                while i < len(bloques):
                    b = bloques[i]
                    if i + 1 < len(bloques) and bloques[i + 1] == b + 1 and asig[b]['asignatura'] == asig[b + 1]['asignatura']:
                        bloques_dobles_logrados += 2
                        total_sesiones += 2
                        i += 2
                        continue
                    total_sesiones += 1
                    i += 1

        pct_dobles = (bloques_dobles_logrados / total_sesiones * 100) if total_sesiones > 0 else 0
        if uso_patio:
            reporte['advertencias'].append(f"Se usa el Patio Santo Domingo en {uso_patio} bloques de Ed. Física")

        reporte['valido'] = len(errores) == 0
        reporte['metricas'] = {
            'total_bloques_asignados': sum(total_asignados.values()),
            'total_bloques_esperados': esperado_global,
            'total_ventanas_docentes': total_ventanas,
            'porcentaje_bloques_dobles': round(pct_dobles, 1),
            'cursos_auditados': len(DatosColegio.todos_los_cursos()),
            'docentes_auditados': len(horario.docente_ocupado),
            'colisiones_docentes': conteo['colisiones_docentes'],
            'errores_carga': conteo['cargas'] + conteo['fuera_jornada'],
            'errores_jefatura': conteo['jefaturas'],
            'errores_electivos': conteo['electivos'],
            'errores_recintos': conteo['recintos'],
            'errores_salas': conteo['salas'] + conteo['pastoral'],
            'uso_patio': uso_patio,
            'mismo_dia_violaciones': same_day_violations,
            'core_no_consecutivo': core_non_consecutive
        }

        return reporte
