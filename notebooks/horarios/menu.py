# -*- coding: utf-8 -*-
"""
Menú interactivo y vista por consola de los horarios generados.
"""

import os

from .datos import DatosColegio
from .exportador_excel import ExportadorExcel
from .validador import ValidadorRestricciones

# Carpeta notebooks/ (los Excel se guardan en notebooks/Outputs Excel/)
CARPETA_NOTEBOOKS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class MenuInteractivo:
    """Consola interactiva para explorar los horarios generados y exportar."""

    def __init__(self, horario):
        self.horario = horario
        carpeta_outputs = os.path.join(CARPETA_NOTEBOOKS, "Outputs Excel")
        self.ruta_excel_cursos = os.path.join(carpeta_outputs, "Horario_Cursos_MMDD.xlsx")
        self.ruta_excel_docentes = os.path.join(carpeta_outputs, "Horarios_Docentes_Colegio_MMDD.xlsx")
        self.ruta_excel = self.ruta_excel_cursos

    @staticmethod
    def _recortar(texto, ancho):
        texto = str(texto)
        return texto if len(texto) <= ancho else texto[:ancho - 2] + '..'

    @staticmethod
    def _imprimir_recreo(b, col_w, header):
        nombre, rango = DatosColegio.RECREOS[b]
        barra = f"--- {nombre} {rango} ---".center(5 * (col_w + 3) - 3, '-')
        print(f"{'':<6} | {'':<13} | {barra}")
        print("-" * len(header))

    def mostrar_tabla_curso(self, curso):
        """Imprime en terminal el horario semanal formateado para un curso."""
        curso = curso.upper().strip()
        if curso not in DatosColegio.todos_los_cursos():
            print(f"\n❌ Error: El curso '{curso}' no existe.")
            return

        jefe = DatosColegio.PROFESORES_JEFES.get(curso, 'No asignado')
        col_w = 17
        ancho_total = 6 + 3 + 13 + 3 + 5 * (col_w + 3) - 1
        print("\n" + "=" * ancho_total)
        print(f"  COLEGIO MADRES DOMINICAS — HORARIO SEMANAL {DatosColegio.ANIO}: {curso}")
        print(f"  Profesor(a) Jefe: {jefe}")
        print("=" * ancho_total)

        header = f"{'BLOQUE':<6} | {'HORARIO':<13} | " + " | ".join(f"{d:<{col_w}}" for d in DatosColegio.DIAS)
        print(header)
        print("-" * len(header))

        max_bloques = 10 if max(DatosColegio.JORNADAS[curso]) > 8 else 8
        for b in range(1, max_bloques + 1):
            h_in, h_fi = DatosColegio.HORARIOS_BLOQUES[b]
            cols_asig = []
            cols_doc = []
            for d in DatosColegio.DIAS:
                if b not in DatosColegio.get_bloques_permitidos(curso, d):
                    cols_asig.append(f"{'---':<{col_w}}")
                    cols_doc.append(f"{' ':<{col_w}}")
                elif b in self.horario.asignaciones[curso][d]:
                    info = self.horario.asignaciones[curso][d][b]
                    docente = info['docente']
                    if info['asignatura'].startswith('Formación Diferenciada'):
                        docente = f"{len(info['docentes'])} docentes"
                    cols_asig.append(f"{self._recortar(info['etiqueta'], col_w):<{col_w}}")
                    cols_doc.append(f"{self._recortar('(' + docente + ')', col_w):<{col_w}}")
                else:
                    cols_asig.append(f"{'Libre':<{col_w}}")
                    cols_doc.append(f"{' ':<{col_w}}")

            print(f"{'B.' + str(b):<6} | {h_in + '-' + h_fi:<13} | " + " | ".join(cols_asig))
            print(f"{'':<6} | {'':<13} | " + " | ".join(cols_doc))
            if b in DatosColegio.RECREOS and b < max_bloques:
                self._imprimir_recreo(b, col_w, header)
            else:
                print("-" * len(header))

        print("=" * ancho_total)

    def mostrar_tabla_docente(self, docente_nombre):
        """Imprime la malla semanal de un docente específico."""
        coincidencias = sorted(d for d in self.horario.docente_ocupado if docente_nombre.lower() in d.lower())
        if not coincidencias:
            print(f"\n❌ No se encontró ningún docente con el nombre '{docente_nombre}'.")
            return

        exactos = [d for d in coincidencias if d.lower() == docente_nombre.lower()]
        doc = (exactos or coincidencias)[0]
        ocupado = self.horario.docente_ocupado[doc]
        detalle = self.horario.docente_detalle.get(doc, {})
        col_w = 17
        ancho_total = 6 + 3 + 13 + 3 + 5 * (col_w + 3) - 1
        print("\n" + "=" * ancho_total)
        print(f"  MALLA SEMANAL {DatosColegio.ANIO}: {doc} ({len(ocupado)} horas en grilla)")
        print("=" * ancho_total)

        header = f"{'BLOQUE':<6} | {'HORARIO':<13} | " + " | ".join(f"{d:<{col_w}}" for d in DatosColegio.DIAS)
        print(header)
        print("-" * len(header))

        max_bloques = 10 if any(b > 8 for (_, b) in ocupado) else 8
        for b in range(1, max_bloques + 1):
            h_in, h_fi = DatosColegio.HORARIOS_BLOQUES[b]
            cols_curso = []
            cols_asig = []
            for d in DatosColegio.DIAS:
                if (d, b) in ocupado:
                    c, asig = ocupado[(d, b)]
                    etiqueta = detalle[(d, b)]['etiqueta'] if (d, b) in detalle else DatosColegio.ETIQUETAS.get(asig, asig)
                    cols_curso.append(f"{self._recortar(c, col_w):<{col_w}}")
                    cols_asig.append(f"{self._recortar('(' + etiqueta + ')', col_w):<{col_w}}")
                else:
                    cols_curso.append(f"{'Libre':<{col_w}}")
                    cols_asig.append(f"{' ':<{col_w}}")

            print(f"{'B.' + str(b):<6} | {h_in + '-' + h_fi:<13} | " + " | ".join(cols_curso))
            print(f"{'':<6} | {'':<13} | " + " | ".join(cols_asig))
            if b in DatosColegio.RECREOS and b < max_bloques:
                self._imprimir_recreo(b, col_w, header)
            else:
                print("-" * len(header))
        print("=" * ancho_total)

    def exportar(self):
        """Genera ambos libros Excel en la carpeta Outputs Excel/."""
        print(f"\n⏳ Generando libros Excel en carpeta 'Outputs Excel/' ...")

        # 1. Horario de cursos
        ExportadorExcel.exportar_horario_cursos(self.horario, self.ruta_excel_cursos)
        print(f"✅ ¡Horario de Cursos generado exitosamente!")
        print(f"📁 [1] Cursos:   {self.ruta_excel_cursos}")

        # 2. Horario de docentes
        ExportadorExcel.exportar_horario_docentes(self.horario, self.ruta_excel_docentes)
        print(f"✅ ¡Horarios de Docentes generado exitosamente!")
        print(f"📁 [2] Docentes: {self.ruta_excel_docentes}\n")

    def mostrar_auditoria(self):
        """Muestra el reporte de verificación de restricciones."""
        auditoria = ValidadorRestricciones.auditar(self.horario)
        m = auditoria['metricas']
        print("\n" + "=" * 70)
        print(f"  AUDITORÍA DE RESTRICCIONES {DatosColegio.ANIO} — COLEGIO MADRES DOMINICAS")
        print("=" * 70)
        estado = "✅ FACTIBLE (100% Restricciones Duras Cumplidas)" if auditoria['valido'] else "❌ CONFLICTOS"
        print(f"  Estado Global: {estado}")
        print("-" * 70)
        print(f"  • Cursos programados:              {m['cursos_auditados']} (24 regulares + 3 párvulos)")
        print(f"  • Total bloques asignados:         {m['total_bloques_asignados']} / {m['total_bloques_esperados']}")
        print(f"  • Colisiones docentes:             {m['colisiones_docentes']}")
        print(f"  • Errores de carga o jornada:      {m['errores_carga']}")
        print(f"  • Jefaturas inconsistentes:        {m['errores_jefatura']}")
        print(f"  • Electivos desincronizados:       {m['errores_electivos']}")
        print(f"  • Recintos deportivos excedidos:   {m['errores_recintos']} (bloques en el patio: {m['uso_patio']})")
        print(f"  • Conflictos de salas/pastoral:    {m['errores_salas']}")
        print(f"  • Repeticiones diarias:            {m['mismo_dia_violaciones']}")
        print(f"  • Troncales no consecutivas:       {m['core_no_consecutivo']}")
        print(f"  • Porcentaje de Bloques Dobles:    {m['porcentaje_bloques_dobles']}% del total")
        print(f"  • Ventanas docentes acumuladas:    {m['total_ventanas_docentes']} horas libres intermedias")
        for error in auditoria['errores_duros'][:10]:
            print(f"    - {error}")
        print("=" * 70)

    def iniciar(self):
        """Bucle principal de interacción con el usuario."""
        cursos = DatosColegio.todos_los_cursos()
        while True:
            print("\n" + "╔" + "═" * 68 + "╗")
            print("║   SISTEMA DE ASIGNACIÓN DE HORARIOS - COLEGIO MMDD (TGOP) - 2026   ║")
            print("╚" + "═" * 68 + "╝")
            print("  1. Seleccionar curso para ver horario en pantalla")
            print("  2. Ver horario de todos los cursos (secuencial)")
            print("  3. Ver horario semanal de un docente")
            print("  4. Ver reporte de auditoría y verificación de restricciones")
            print("  5. Generar y exportar archivos Excel (Cursos y Docentes)")
            print("  0. Salir")
            print("-" * 70)

            opcion = input("Seleccione una opción (0-5): ").strip()

            if opcion == '1':
                print("\nLista de Cursos Disponibles:")
                for idx, c in enumerate(cursos, 1):
                    print(f"  [{idx:2d}] {c}")
                seleccion = input(f"\nIngrese el número (1-{len(cursos)}) o nombre exacto del curso: ").strip()
                if seleccion.isdigit() and 1 <= int(seleccion) <= len(cursos):
                    self.mostrar_tabla_curso(cursos[int(seleccion) - 1])
                else:
                    self.mostrar_tabla_curso(seleccion)

            elif opcion == '2':
                for c in cursos:
                    self.mostrar_tabla_curso(c)

            elif opcion == '3':
                doc_query = input("\nIngrese el nombre del docente (ej. 'Inglés 2', 'Básica 5'): ").strip()
                self.mostrar_tabla_docente(doc_query)

            elif opcion == '4':
                self.mostrar_auditoria()

            elif opcion == '5':
                self.exportar()

            elif opcion == '0':
                print("\n👋 Saliendo del sistema de horarios. ¡Hasta pronto!\n")
                break
            else:
                print("\n⚠️ Opción no válida. Intente nuevamente.")
