# -*- coding: utf-8 -*-
"""
Documentos Word (.docx) y PDF de los horarios.

- Horario de cursos: una página por curso con el diseño de las hojas de
  'data/Data 2026/HORARIO CURSOS 2026.xlsx' (escudo, curso y profesor/a jefe, grilla con
  recreos y tabla de horas). El contenido sale de ExportadorExcel, así que Word, PDF y Excel
  muestran exactamente lo mismo.
- Distribución horaria docente: el formato de 'data/Data 2026/DISTRIBUCIÓN HORARIA 2026.docx'
  (una tabla por departamento: profesor, cursos, n° de horas, asignatura y horas lectivas).

Word usa python-docx y PDF usa reportlab (y Pillow para el escudo). Se importan al usarlos:
el motor funciona sin ellos.
"""

import io
from datetime import datetime

from ..datos import DatosColegio
from .exportador_excel import ExportadorExcel as X


def _hex(argb):
    """'FFFFE598' -> 'FFE598' (los colores de ExportadorExcel vienen con canal alfa)."""
    return argb[-6:] if argb else None


# =============================================================================
# Contenido (común a Word y PDF)
# =============================================================================
def paginas_cursos(horario):
    """Una página por curso: títulos, filas de la grilla y tabla de horas, como en el Excel."""
    paginas = []
    malla = DatosColegio.get_malla_curricular()
    for curso in DatosColegio.todos_los_cursos():
        max_b, contenido = X.contenido_curso(curso, horario)
        grilla = []
        for b in range(1, max_b + 1):
            inicio, fin = DatosColegio.HORARIOS_BLOQUES[b]
            celdas = []
            for dia in DatosColegio.DIAS:
                texto, relleno = contenido(dia, b)
                celdas.append((texto or '', _hex(relleno or X.BLANCO)))
            grilla.append(('bloque', str(b), f'{inicio} - {fin}', celdas))
            if b in DatosColegio.RECREOS and b < max_b:
                nombre, rango = DatosColegio.RECREOS[b]
                celdas = []
                for dia in DatosColegio.DIAS:
                    texto, relleno = contenido(dia, 'C') if nombre == 'COLACIÓN' else (None, None)
                    celdas.append((texto or '', _hex(relleno or X.AMARILLO)))
                grilla.append(('pausa', nombre, rango, celdas))
        en_media = DatosColegio.nivel(curso) in DatosColegio.FRANJAS_ELECTIVOS
        paginas.append({
            'curso': curso,
            'titulos': [('CURSO', curso), ('PROFESOR/A JEFE', DatosColegio.PROFESORES_JEFES.get(curso, '') or '')],
            'grilla': grilla,
            'tabla': X._filas_tabla_curso(curso),
            'borde_etiquetas': _hex(X.BORDE_MEDIA) if en_media else None,
            'skills': any(a == 'English Skills' for a, _, _, _ in malla[curso]),
        })
    return paginas


def distribucion_desde_datos(docentes):
    """
    Departamentos de la distribución horaria a partir de la lista 'docentes' de
    datos/horarios_<año>.js (cada docente trae sus filas en 'distribucion').
    Retorna [(departamento, [(docente, filas, total)])]; los docentes sin horas no aparecen.
    """
    deptos = {}
    for d in docentes:
        filas = d.get('distribucion') or []
        if not filas:
            continue
        total = d.get('horasTotales')
        if not isinstance(total, (int, float)):
            total = sum(f.get('horas') or 0 for f in filas)
        deptos.setdefault(d.get('departamentoCompleto') or d.get('departamento') or '', []).append(
            (d['nombre'], filas, total))
    return list(deptos.items())


def _texto_asignatura(fila):
    # Como en el documento 2026: English skills es "Inglés" en verde (con la leyenda bajo la tabla)
    return 'Inglés' if fila.get('tipo') == 'skills' else str(fila.get('asignatura') or '')


def _numero(valor):
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)
    return '' if valor is None else str(valor)


# Profesor, cursos, n° de horas, asignatura y horas lectivas (twips). El documento 2026 usa
# 2120/1240/1400/1520/1240; aquí cursos y asignatura son más anchos para los nombres de los electivos
ANCHOS_DISTRIBUCION = [1900, 1500, 1300, 2600, 1240]
RELLENOS_DISTRIBUCION = {'jefatura': _hex(X.CELESTE), 'skills': _hex(X.VERDE), 'orientec': _hex(X.AZUL)}
TITULO_DISTRIBUCION = 'DISTRIBUCIÓN DE HORAS POR ASIGNATURAS – AÑO ACADÉMICO {anio}.'
LEYENDA_SKILLS = 'Verdes : English skills   2 docentes'
PIE_DISTRIBUCION = 'UNIDAD TÉCNICA PEDAGÓGICA'


# =============================================================================
# Word (python-docx)
# =============================================================================
def _docx():
    try:
        import docx  # noqa: F401
    except ImportError as error:
        raise RuntimeError('Los documentos Word requieren python-docx (pip install python-docx).') from error
    import docx
    return docx


# Orden de los hijos de w:tcPr, w:trPr y w:tblPr que exige Word (si no, dice que el archivo está dañado)
_ORDEN_TCPR = ['cnfStyle', 'tcW', 'gridSpan', 'hMerge', 'vMerge', 'tcBorders', 'shd', 'noWrap', 'tcMar',
               'textDirection', 'tcFitText', 'vAlign', 'hideMark']
_ORDEN_TRPR = ['cnfStyle', 'divId', 'gridBefore', 'gridAfter', 'wBefore', 'wAfter', 'cantSplit', 'trHeight',
               'tblHeader', 'tblCellSpacing', 'jc', 'hidden']
_ORDEN_TBLPR = ['tblStyle', 'tblpPr', 'tblOverlap', 'bidiVisual', 'tblStyleRowBandSize', 'tblStyleColBandSize',
                'tblW', 'jc', 'tblCellSpacing', 'tblInd', 'tblBorders', 'shd', 'tblLayout', 'tblCellMar', 'tblLook']


def _w(etiqueta, **atributos):
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    e = OxmlElement(f'w:{etiqueta}')
    for k, v in atributos.items():
        e.set(qn(f'w:{k}'), str(v))
    return e


def _poner(padre, elemento, orden):
    """Reemplaza (o agrega) un hijo de padre respetando el orden del esquema de Word."""
    from docx.oxml.ns import qn
    nombre = elemento.tag.split('}')[1]
    for viejo in padre.findall(qn(f'w:{nombre}')):
        padre.remove(viejo)
    posicion = orden.index(nombre)
    for hijo in padre:
        local = hijo.tag.split('}')[1]
        if local in orden and orden.index(local) > posicion:
            hijo.addprevious(elemento)
            return elemento
    padre.append(elemento)
    return elemento


def _bordes_celda(celda, color='000000', sz=4, lados=None, ninguno=()):
    """lados: {'top': (sz, color), ...} para sobrescribir; ninguno: lados sin borde."""
    bordes = _w('tcBorders')
    for lado in ('top', 'left', 'bottom', 'right'):
        if lado in ninguno:
            bordes.append(_w(lado, val='nil'))
            continue
        tam, col = (lados or {}).get(lado, (sz, color))
        bordes.append(_w(lado, val='single', sz=tam, space=0, color=col))
    _poner(celda._tc.get_or_add_tcPr(), bordes, _ORDEN_TCPR)


def _relleno(celda, color):
    if color:
        _poner(celda._tc.get_or_add_tcPr(), _w('shd', val='clear', color='auto', fill=color), _ORDEN_TCPR)


def _valign(celda, valor='center'):
    _poner(celda._tc.get_or_add_tcPr(), _w('vAlign', val=valor), _ORDEN_TCPR)


def _ancho_celda(celda, twips):
    _poner(celda._tc.get_or_add_tcPr(), _w('tcW', w=int(twips), type='dxa'), _ORDEN_TCPR)


def _fila(tabla_docx, i, alto=None, sin_partir=True, encabezado=False):
    from docx.enum.table import WD_ROW_HEIGHT_RULE
    from docx.shared import Twips
    fila = tabla_docx.rows[i]
    if alto:
        fila.height = Twips(alto)
        fila.height_rule = WD_ROW_HEIGHT_RULE.AT_LEAST
    trPr = fila._tr.get_or_add_trPr()
    if sin_partir:
        _poner(trPr, _w('cantSplit'), _ORDEN_TRPR)
    if encabezado:
        _poner(trPr, _w('tblHeader'), _ORDEN_TRPR)
    return fila


def _tabla(documento, filas, anchos, bordes=None, centrada=False):
    """Tabla de ancho fijo (anchos en twips). bordes: (sz exterior, sz interior, color) o None."""
    from docx.shared import Twips
    t = documento.add_table(rows=filas, cols=len(anchos))
    t.autofit = False
    tblPr = t._tbl.tblPr
    _poner(tblPr, _w('tblW', w=int(sum(anchos)), type='dxa'), _ORDEN_TBLPR)
    if centrada:
        _poner(tblPr, _w('jc', val='center'), _ORDEN_TBLPR)
    _poner(tblPr, _w('tblLayout', type='fixed'), _ORDEN_TBLPR)
    margenes = _w('tblCellMar')
    margenes.append(_w('left', w=70, type='dxa'))
    margenes.append(_w('right', w=70, type='dxa'))
    _poner(tblPr, margenes, _ORDEN_TBLPR)
    if bordes:
        exterior, interior, color = bordes
        b = _w('tblBorders')
        for lado in ('top', 'left', 'bottom', 'right'):
            b.append(_w(lado, val='single', sz=exterior, space=0, color=color))
        for lado in ('insideH', 'insideV'):
            b.append(_w(lado, val='single', sz=interior, space=0, color=color))
        _poner(tblPr, b, _ORDEN_TBLPR)
    for i, ancho in enumerate(anchos):
        t.columns[i].width = Twips(ancho)
        for celda in t.columns[i].cells:
            _ancho_celda(celda, ancho)
    return t


def _matriz(tabla_docx):
    """
    Celdas de la tabla por fila y columna (las combinadas se repiten). Se calcula una vez después de
    combinar: tabla.cell() recorre la tabla entera en cada llamada y vuelve muy lento el documento.
    """
    celdas = tabla_docx._cells
    n = len(tabla_docx.columns)
    return [celdas[i:i + n] for i in range(0, len(celdas), n)]


def _escribir(celda, texto, fuente, tam, negrita=False, alineacion='center', subrayado=False):
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Pt
    p = celda.paragraphs[0]
    for extra in celda.paragraphs[1:]:   # restos de celdas combinadas
        extra._p.getparent().remove(extra._p)
    p.alignment = {'center': WD_ALIGN_PARAGRAPH.CENTER, 'left': WD_ALIGN_PARAGRAPH.LEFT,
                   'right': WD_ALIGN_PARAGRAPH.RIGHT}[alineacion]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.0
    run = p.add_run(str(texto))
    _fuente(run, fuente, tam, negrita, subrayado)
    return p


def _fuente(run, fuente, tam, negrita=False, subrayado=False):
    from docx.oxml.ns import qn
    from docx.shared import Pt
    run.font.name = fuente
    rFonts = run._element.get_or_add_rPr().get_or_add_rFonts()
    rFonts.set(qn('w:cs'), 'Calibri')
    rFonts.set(qn('w:eastAsia'), fuente)
    run.font.size = Pt(tam)
    run.font.bold = negrita
    if subrayado:
        run.font.underline = True


def _pagina_carta(documento, arriba, derecha, abajo, izquierda, pie=None):
    from docx.shared import Twips
    s = documento.sections[0]
    s.page_width, s.page_height = Twips(12240), Twips(15840)
    s.top_margin, s.right_margin, s.bottom_margin, s.left_margin = (Twips(arriba), Twips(derecha),
                                                                     Twips(abajo), Twips(izquierda))
    if pie is not None:
        s.footer_distance = Twips(pie)
    return s


def _documento_base(titulo, fuente='Calibri', tam=11):
    from docx.shared import Pt
    docx = _docx()
    documento = docx.Document()
    normal = documento.styles['Normal']
    normal.font.name = fuente
    normal.font.size = Pt(tam)
    normal.paragraph_format.space_after = Pt(8)
    normal.paragraph_format.line_spacing = 1.08
    props = documento.core_properties
    props.title = titulo
    props.author = 'Horarios MMDD'
    props.created = datetime.now()
    return documento


def _campo(parrafo, instruccion, fuente, tam):
    """Campo de Word (PAGE o NUMPAGES) dentro de un párrafo."""
    for tipo, texto in (('begin', None), (None, instruccion), ('separate', None), (None, '1'), ('end', None)):
        run = parrafo.add_run()
        _fuente(run, fuente, tam)
        if tipo:
            run._r.append(_w('fldChar', fldCharType=tipo))
        elif texto == instruccion:
            instr = _w('instrText')
            instr.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
            instr.text = f' {instruccion} \\* MERGEFORMAT '
            run._r.append(instr)
        else:
            run.add_text(texto)


def _guardar_docx(documento):
    salida = io.BytesIO()
    documento.save(salida)
    return salida.getvalue()


# ----------------------------------------------------------------------------- distribución
def distribucion_docx(departamentos, anio):
    """DISTRIBUCIÓN HORARIA con el formato del documento Word 2026. Retorna los bytes del .docx."""
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
    from docx.shared import Pt, Twips
    documento = _documento_base(f'Distribución horaria docente {anio}')
    seccion = _pagina_carta(documento, 851, 900, 1440, 1080, pie=1117)

    # Pie: UNIDAD TÉCNICA PEDAGÓGICA ............ Página X de Y
    pie = seccion.footer.paragraphs[0]
    paradas = pie.paragraph_format.tab_stops
    for posicion in (4680, 9360):   # tabulaciones del estilo Pie de página de la plantilla
        paradas.add_tab_stop(Twips(posicion), WD_TAB_ALIGNMENT.CLEAR)
    paradas.add_tab_stop(Twips(12240 - 1080 - 900), WD_TAB_ALIGNMENT.RIGHT)
    _fuente(pie.add_run(f'{PIE_DISTRIBUCION}\tPágina '), 'Calibri', 11)
    _campo(pie, 'PAGE', 'Calibri', 11)
    _fuente(pie.add_run(' de '), 'Calibri', 11)
    _campo(pie, 'NUMPAGES', 'Calibri', 11)

    documento.add_paragraph()   # el documento 2026 deja una línea en blanco sobre el título
    titulo = documento.add_paragraph()
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _fuente(titulo.add_run(TITULO_DISTRIBUCION.format(anio=anio)), 'Calibri', 14, negrita=True, subrayado=True)

    anchos = ANCHOS_DISTRIBUCION
    fuente, tam = 'Abadi', 11
    for depto, docentes in departamentos:
        p = documento.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.keep_with_next = True
        _fuente(p.add_run(f'ASIGNATURAS: {depto}'), 'Calibri', 14, negrita=True)

        n = 1 + sum(len(filas) for _, filas, _ in docentes)
        t = _tabla(documento, n, anchos, bordes=(8, 4, '000000'))
        bloques, i = [], 1
        for docente, filas, total in docentes:   # profesor y horas lectivas abarcan las filas del docente
            bloques.append((i, docente, filas, total))
            if len(filas) > 1:
                for j in (0, 4):
                    t.cell(i, j).merge(t.cell(i + len(filas) - 1, j))
            i += len(filas)
        m = _matriz(t)

        for j, texto in enumerate(['PROFESOR', 'CURSOS', 'Nº DE HORAS', 'Asignatura', 'HORAS LECTIVAS']):
            celda = m[0][j]
            _escribir(celda, texto, fuente, tam).paragraph_format.keep_with_next = True
            _relleno(celda, _hex(X.GRIS))
            _valign(celda, 'bottom')
        _fila(t, 0, alto=564, encabezado=True)

        hay_skills = False
        for inicio, docente, filas, total in bloques:
            for k, f in enumerate(filas):
                i = inicio + k
                _fila(t, i, alto=276)
                relleno = RELLENOS_DISTRIBUCION.get(f.get('tipo'))
                hay_skills |= f.get('tipo') == 'skills'
                for j, texto in ((1, f.get('cursos') or ''), (2, _numero(f.get('horas'))), (3, _texto_asignatura(f))):
                    celda = m[i][j]
                    p = _escribir(celda, texto, fuente, tam if len(str(texto)) <= 22 else 9)
                    p.paragraph_format.keep_with_next = k < len(filas) - 1   # el bloque de un docente no se parte
                    _relleno(celda, relleno)
                    _valign(celda, 'bottom')
                    # Borde grueso al terminar el bloque de cada docente
                    _bordes_celda(celda, lados={'bottom': (8 if k == len(filas) - 1 else 4, '000000')})
            for j, texto in ((0, docente), (4, _numero(total))):
                celda = m[inicio][j]
                _escribir(celda, texto, fuente, tam)
                _valign(celda, 'center')
                _bordes_celda(celda, sz=8)
        if hay_skills:
            p = documento.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            _fuente(p.add_run(LEYENDA_SKILLS), 'Calibri', 14, negrita=True)
        documento.add_paragraph()
    return _guardar_docx(documento)


# ----------------------------------------------------------------------------- horarios
# Anchos de las columnas B a H del Excel 2026 (en caracteres) y su equivalente en twips
_COLUMNAS_GRILLA = [8.66, 12.66, 13.89, 14.44, 14.44, 14.44, 14.44]
_TWIPS_POR_COLUMNA = 10260 / sum(_COLUMNAS_GRILLA)   # ancho útil de la carta con márgenes de 0,63"
_FUENTE_HORARIO = 'Cavolini'


def _twips(columnas):
    return [round(c * _TWIPS_POR_COLUMNA) for c in columnas]


def horarios_docx(paginas, anio, descripcion=''):
    """Horario de cursos en Word: una página por curso, con el diseño del Excel 2026."""
    from docx.enum.text import WD_BREAK
    from docx.shared import Pt
    documento = _documento_base(f'Horario de cursos {anio} {descripcion}'.strip(), fuente=_FUENTE_HORARIO, tam=8)
    _pagina_carta(documento, 720, 907, 720, 907)
    naranjo = _hex(X.BORDE)
    fuente = _FUENTE_HORARIO
    escudo = X.escudo()
    anchos = _twips(_COLUMNAS_GRILLA)

    for n, pagina in enumerate(paginas):
        if n:
            salto = documento.add_paragraph()
            salto.paragraph_format.space_after = Pt(0)
            salto.add_run().add_break(WD_BREAK.PAGE)

        # Encabezado: escudo y año | rótulos | valores (sin bordes)
        cab = _tabla(documento, 3, [anchos[0] + anchos[1], anchos[2] + anchos[3], sum(anchos[4:])])
        izquierda = cab.cell(0, 0).merge(cab.cell(2, 0))
        mc = _matriz(cab)
        p = izquierda.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        if escudo:
            try:
                p.add_run().add_picture(io.BytesIO(escudo), height=Pt(66))
            except Exception:   # noqa: BLE001 — imagen ilegible: el encabezado va sin escudo
                pass
        anio_p = izquierda.add_paragraph()
        anio_p.paragraph_format.space_after = Pt(0)
        _fuente(anio_p.add_run(str(anio)), 'Calibri', 11, negrita=True)
        for r, (rotulo, valor) in enumerate(pagina['titulos'][:3]):
            _escribir(mc[r][1], rotulo, fuente, 8, negrita=True)
            _escribir(mc[r][2], valor, fuente, 9, negrita=True)
            for j in (1, 2):
                _valign(mc[r][j], 'center')
        for r in range(3):
            _fila(cab, r, alto=380)
        separador = documento.add_paragraph()
        separador.paragraph_format.space_after = Pt(4)

        # Grilla
        filas = pagina['grilla']
        t = _tabla(documento, len(filas) + 1, anchos, bordes=(4, 4, naranjo))
        t.cell(0, 0).merge(t.cell(0, 1))
        m = _matriz(t)
        _escribir(m[0][0], 'HORAS', fuente, 8, negrita=True)
        _relleno(m[0][0], _hex(X.AMARILLO))
        for i, dia in enumerate(DatosColegio.DIAS):
            celda = m[0][2 + i]
            _escribir(celda, dia.upper(), fuente, 8, negrita=True)
            _relleno(celda, _hex(X.AMARILLO))
        _fila(t, 0, alto=285)
        for r, (tipo, rotulo, rango, celdas) in enumerate(filas, 1):
            _fila(t, r, alto=285)
            fondo = _hex(X.CREMA) if tipo == 'bloque' else _hex(X.AMARILLO)
            for j, texto in ((0, rotulo), (1, rango)):
                _escribir(m[r][j], texto, fuente, 8 if len(texto) <= 7 or j else 6.5, negrita=True)   # "COLACIÓN"
                _relleno(m[r][j], fondo)
            for i, (texto, relleno) in enumerate(celdas):
                celda = m[r][2 + i]
                _escribir(celda, texto, fuente, 8 if len(texto) <= 16 else 7)
                _relleno(celda, relleno)
            for j in range(7):
                _valign(m[r][j], 'center')

        # Tabla de horas: ASIGNATURAS (B:D) | N° DE HORAS (E) | PROFESOR/A (F:G)
        espacio = documento.add_paragraph()
        espacio.paragraph_format.space_after = Pt(6)
        tabla = _filas_tabla_documento(pagina['tabla'])
        th = _tabla(documento, len(tabla), [sum(anchos[0:3]), anchos[3], anchos[4] + anchos[5]])
        for r, (tipo, *_resto) in enumerate(tabla):   # Artes visuales y Música comparten las horas
            if tipo == 'artes' and r + 1 < len(tabla):
                th.cell(r, 1).merge(th.cell(r + 1, 1))
        m = _matriz(th)
        borde_etiqueta = pagina['borde_etiquetas'] or naranjo
        for r, (tipo, etiqueta, horas, texto) in enumerate(tabla):
            _fila(th, r, alto=285)
            if tipo == 'total':
                _escribir(m[r][1], _numero(horas), fuente, 8)
                _relleno(m[r][1], _hex(X.AMARILLO))
                _bordes_celda(m[r][1], color=naranjo)
                for j in (0, 2):
                    _bordes_celda(m[r][j], ninguno=('top', 'left', 'bottom', 'right'))
                continue
            celda = m[r][0]
            _escribir(celda, etiqueta, fuente, 8, negrita=tipo != 'subtitulo',
                      alineacion='center' if tipo == 'encabezado' else 'left')
            _relleno(celda, _hex(X.AMARILLO))
            _bordes_celda(celda, color=borde_etiqueta)
            _valign(celda, 'center')
            if tipo == 'encabezado':
                for j, texto_j in ((1, 'N° DE HORAS'), (2, texto or 'PROFESOR/A')):
                    _escribir(m[r][j], texto_j, fuente, 8, negrita=True)
                    _relleno(m[r][j], _hex(X.AMARILLO))
                    _bordes_celda(m[r][j], color=naranjo)
                    _valign(m[r][j], 'center')
                continue
            if tipo != 'musica':
                _escribir(m[r][1], _numero(horas), fuente, 8)
                _bordes_celda(m[r][1], color=naranjo)
                _valign(m[r][1], 'center')
            _escribir(m[r][2], texto or '', fuente, 8 if len(texto or '') <= 34 else 7)
            _bordes_celda(m[r][2], color=naranjo)
            _valign(m[r][2], 'center')
        if pagina['skills']:
            # Un párrafo entre tablas: sin él, Word las une en una sola
            documento.add_paragraph().paragraph_format.space_after = Pt(4)
            leyenda = _tabla(documento, 1, [anchos[0], anchos[1] * 2])
            ml = _matriz(leyenda)
            _relleno(ml[0][0], _hex(X.SKILLS))
            _escribir(ml[0][1], 'English skills', 'Arial', 10, negrita=True, alineacion='left')
            _fila(leyenda, 0, alto=285)
    return _guardar_docx(documento)


def _filas_tabla_documento(filas):
    """Las filas de _filas_tabla_curso con los textos listos para Word y PDF."""
    return [(tipo, etiqueta or '', horas, texto) for tipo, etiqueta, horas, texto in filas]


# =============================================================================
# PDF (reportlab)
# =============================================================================
def _reportlab():
    try:
        import reportlab  # noqa: F401
    except ImportError as error:
        raise RuntimeError('Los documentos PDF requieren reportlab (pip install reportlab).') from error


def _color(hexa):
    from reportlab.lib import colors
    return colors.HexColor(f'#{hexa}') if hexa else None


def _estilo_parrafo(tam, negrita=False, alineacion=1, fuente='Helvetica'):
    from reportlab.lib.styles import ParagraphStyle
    return ParagraphStyle('p', fontName=f'{fuente}-Bold' if negrita else fuente, fontSize=tam,
                          leading=tam * 1.18, alignment=alineacion, textColor='#000000')


def _p(texto, tam, negrita=False, alineacion=1):
    from reportlab.platypus import Paragraph
    from xml.sax.saxutils import escape
    return Paragraph(escape(str(texto)), _estilo_parrafo(tam, negrita, alineacion))


def _lienzo_numerado(pie_izquierda=None):
    """Clase de canvas que escribe 'Página X de Y' (y un texto a la izquierda) al pie de cada página."""
    from reportlab.pdfgen import canvas

    class Lienzo(canvas.Canvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._estados = []

        def showPage(self):   # noqa: N802 — nombre de reportlab
            self._estados.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            total = len(self._estados)
            for estado in self._estados:
                self.__dict__.update(estado)
                if pie_izquierda is not None:
                    ancho, _ = self._pagesize
                    self.setFont('Helvetica', 10)
                    self.drawString(54, 40, pie_izquierda)
                    self.drawRightString(ancho - 45, 40, f'Página {self._pageNumber} de {total}')
                super().showPage()
            super().save()

    return Lienzo


def _documento_pdf(salida, titulo, margenes):
    from reportlab.lib.pagesizes import LETTER
    from reportlab.platypus import SimpleDocTemplate
    arriba, derecha, abajo, izquierda = margenes
    return SimpleDocTemplate(salida, pagesize=LETTER, topMargin=arriba, rightMargin=derecha,
                             bottomMargin=abajo, leftMargin=izquierda, title=titulo, author='Horarios MMDD',
                             creator='Horarios MMDD')


def distribucion_pdf(departamentos, anio):
    """DISTRIBUCIÓN HORARIA en PDF, con el formato del documento Word 2026."""
    _reportlab()
    from reportlab.lib import colors
    from reportlab.platypus import KeepTogether, Paragraph, Spacer, Table, TableStyle
    from xml.sax.saxutils import escape
    salida = io.BytesIO()
    doc = _documento_pdf(salida, f'Distribución horaria docente {anio}', (42, 45, 72, 54))
    titulo = Paragraph(f'<u>{TITULO_DISTRIBUCION.format(anio=anio)}</u>', _estilo_parrafo(14, True, 1))
    historia = [Spacer(1, 14), titulo, Spacer(1, 12)]
    anchos = [c / 20 for c in ANCHOS_DISTRIBUCION]   # twips -> puntos
    tam = 9.5
    for depto, docentes in departamentos:
        encabezado = Table([[_p(t, tam) for t in ('PROFESOR', 'CURSOS', 'Nº DE HORAS', 'Asignatura', 'HORAS LECTIVAS')]],
                           colWidths=anchos, rowHeights=[28])
        encabezado.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(f'#{_hex(X.GRIS)}')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
            ('TOPPADDING', (0, 0), (-1, -1), 1), ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        bloques = []
        hay_skills = False
        for docente, filas, total in docentes:
            datos = []
            estilo = [
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('BOX', (0, 0), (0, -1), 1, colors.black),
                ('BOX', (4, 0), (4, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 1), ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
                ('SPAN', (0, 0), (0, len(filas) - 1)), ('SPAN', (4, 0), (4, len(filas) - 1)),
            ]
            for r, f in enumerate(filas):
                hay_skills |= f.get('tipo') == 'skills'
                datos.append([_p(docente, tam) if r == 0 else '', _p(f.get('cursos') or '', tam),
                              _p(_numero(f.get('horas')), tam), _p(_texto_asignatura(f), tam if len(_texto_asignatura(f)) <= 24 else 8),
                              _p(_numero(total), tam) if r == 0 else ''])
                relleno = RELLENOS_DISTRIBUCION.get(f.get('tipo'))
                if relleno:
                    estilo.append(('BACKGROUND', (1, r), (3, r), colors.HexColor(f'#{relleno}')))
            tabla = Table(datos, colWidths=anchos)   # alto automático: los nombres largos ocupan dos líneas
            tabla.setStyle(TableStyle(estilo))
            bloques.append(tabla)
        titulo_depto = Paragraph(f'ASIGNATURAS: {escape(depto)}', _estilo_parrafo(13, True, 0))
        historia.append(KeepTogether([titulo_depto, Spacer(1, 8), encabezado, bloques[0]]))
        historia.extend(KeepTogether([b]) for b in bloques[1:])
        if hay_skills:
            historia += [Spacer(1, 8), Paragraph(LEYENDA_SKILLS.replace('   ', ' &nbsp; '), _estilo_parrafo(12, True, 0))]
        historia.append(Spacer(1, 18))
    doc.build(historia, canvasmaker=_lienzo_numerado(PIE_DISTRIBUCION))
    return salida.getvalue()


def horarios_pdf(paginas, anio, descripcion=''):
    """Horario de cursos en PDF: una página por curso, con el diseño del Excel 2026."""
    _reportlab()
    from reportlab.lib import colors
    from reportlab.platypus import Image, PageBreak, Spacer, Table, TableStyle
    salida = io.BytesIO()
    doc = _documento_pdf(salida, f'Horario de cursos {anio} {descripcion}'.strip(), (36, 45, 36, 45))
    ancho_util = 612 - 90
    escala = ancho_util / sum(_COLUMNAS_GRILLA)
    anchos = [c * escala for c in _COLUMNAS_GRILLA]
    naranjo = colors.HexColor(f'#{_hex(X.BORDE)}')
    amarillo = colors.HexColor(f'#{_hex(X.AMARILLO)}')
    crema = colors.HexColor(f'#{_hex(X.CREMA)}')
    escudo = X.escudo()
    tam = 7

    historia = []
    for n, pagina in enumerate(paginas):
        if n:
            historia.append(PageBreak())
        # Encabezado
        imagen = ''
        if escudo:
            try:
                imagen = Image(io.BytesIO(escudo), width=38, height=50)   # proporción del escudo (226 x 300)
            except Exception:   # noqa: BLE001 — sin Pillow o imagen ilegible: sin escudo
                imagen = ''
        titulos = list(pagina['titulos'][:3]) + [('', '')] * (3 - len(pagina['titulos'][:3]))
        cab = Table([[imagen, _p(titulos[0][0], 7.5, True), _p(titulos[0][1], 9, True)],
                     ['', _p(titulos[1][0], 7.5, True), _p(titulos[1][1], 9, True)],
                     [_p(str(anio), 10.5, True, 0), _p(titulos[2][0], 7.5, True), _p(titulos[2][1], 9, True)]],
                    colWidths=[anchos[0] + anchos[1], anchos[2] + anchos[3], sum(anchos[4:])],
                    rowHeights=[26, 26, 18], hAlign='LEFT')
        cab.setStyle(TableStyle([('SPAN', (0, 0), (0, 1)), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                 ('LEFTPADDING', (0, 0), (0, -1), 2)]))
        historia += [cab, Spacer(1, 8)]

        # Grilla
        datos = [[_p('HORAS', tam, True), ''] + [_p(d.upper(), tam, True) for d in DatosColegio.DIAS]]
        estilo = [('SPAN', (0, 0), (1, 0)), ('BACKGROUND', (0, 0), (-1, 0), amarillo),
                  ('GRID', (0, 0), (-1, -1), 0.5, naranjo), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                  ('TOPPADDING', (0, 0), (-1, -1), 1), ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
                  ('LEFTPADDING', (0, 0), (-1, -1), 2), ('RIGHTPADDING', (0, 0), (-1, -1), 2)]
        for r, (tipo, rotulo, rango, celdas) in enumerate(pagina['grilla'], 1):
            fila = [_p(rotulo, tam, True), _p(rango, tam, True)]
            estilo.append(('BACKGROUND', (0, r), (1, r), crema if tipo == 'bloque' else amarillo))
            for i, (texto, relleno) in enumerate(celdas):
                fila.append(_p(texto, tam if len(texto) <= 18 else 6))
                estilo.append(('BACKGROUND', (2 + i, r), (2 + i, r), _color(relleno)))
            datos.append(fila)
        grilla = Table(datos, colWidths=anchos, rowHeights=[14.5] * len(datos), hAlign='LEFT')
        grilla.setStyle(TableStyle(estilo))
        historia += [grilla, Spacer(1, 14)]

        # Tabla de horas
        tabla = _filas_tabla_documento(pagina['tabla'])
        anchos_t = [sum(anchos[0:3]), anchos[3], anchos[4] + anchos[5]]
        datos, estilo, altos = [], [('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                    ('TOPPADDING', (0, 0), (-1, -1), 1), ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
                                    ('LEFTPADDING', (0, 0), (-1, -1), 3)], []
        borde_etiquetas = _color(pagina['borde_etiquetas']) or naranjo
        for r, (tipo, etiqueta, horas, texto) in enumerate(tabla):
            if tipo == 'total':
                datos.append(['', _p(_numero(horas), tam), ''])
                estilo += [('BACKGROUND', (1, r), (1, r), amarillo), ('BOX', (1, r), (1, r), 0.5, naranjo)]
                altos.append(14.5)
                continue
            largo = len(etiqueta) > 30 or len(texto or '') > 40
            altos.append(24 if largo else 14.5)
            alineacion = 1 if tipo == 'encabezado' else 0
            celda_etiqueta = _p(etiqueta, tam, tipo != 'subtitulo', alineacion)
            if tipo == 'encabezado':
                datos.append([celda_etiqueta, _p('N° DE HORAS', tam, True), _p(texto or 'PROFESOR/A', tam, True)])
                estilo += [('BACKGROUND', (0, r), (-1, r), amarillo), ('GRID', (1, r), (2, r), 0.5, naranjo)]
            else:
                horas_txt = '' if tipo == 'musica' else _numero(horas)
                datos.append([celda_etiqueta, _p(horas_txt, tam), _p(texto or '', tam if len(texto or '') <= 40 else 6)])
                estilo += [('BACKGROUND', (0, r), (0, r), amarillo), ('BOX', (2, r), (2, r), 0.5, naranjo)]
                if tipo == 'artes' and r + 1 < len(tabla):
                    estilo += [('SPAN', (1, r), (1, r + 1)), ('BOX', (1, r), (1, r + 1), 0.5, naranjo)]
                elif tipo != 'musica':
                    estilo.append(('BOX', (1, r), (1, r), 0.5, naranjo))
            estilo.append(('BOX', (0, r), (0, r), 0.5, borde_etiquetas))
        horas_t = Table(datos, colWidths=anchos_t, rowHeights=altos, hAlign='LEFT')
        horas_t.setStyle(TableStyle(estilo))
        historia.append(horas_t)
        if pagina['skills']:
            leyenda = Table([['', _p('English skills', 8.5, True, 0)]], colWidths=[anchos[0], anchos[1] * 2],
                            rowHeights=[14], hAlign='LEFT')
            leyenda.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, 0), _color(_hex(X.SKILLS))),
                                         ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
            historia += [Spacer(1, 10), leyenda]
    doc.build(historia)
    return salida.getvalue()
