#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
MÓDULO DE MAQUETACIÓN EDITORIAL PARA IMPRENTA: "SOMBRA"
Ingeniero Editorial: Bill (Infraestructura y Sistemas Editoriales)
================================================================================
Especificaciones Técnicas de Producción Física:
- Formato de página: 150 mm × 210 mm (corte estándar novela europea).
- Márgenes simétricos/opuestos (recto/verso):
    * Lomo (interior): 22 mm
    * Corte (exterior): 15 mm
    * Cabeza (superior): 15 mm
    * Pie (inferior): 22 mm
- Caja tipográfica imprimible: 113 mm de ancho × 173 mm de alto.
- Tipografía del cuerpo: Garamond (TrueType incrustada al 100%), 11 pt / 13.5 pt leading.
- Alineación: Justificada con separación silábica automática (pyphen es_ES, soft-hyphens).
- Sangría de primera línea: 5 mm (párrafos de cuerpo, omitida tras títulos).
- Separata de Acto: Página impar (derecha) centrada en 24 pt, con reverso (par) en blanco,
  sin encabezados ni numeración.
- Inicio de Capítulo: Página impar (recto), drop inicial de 40 mm, título 18 pt negrita,
  separación de 15 mm al cuerpo, primer párrafo sin sangría.
- Apartados: En flujo continuo, espacio previo y posterior, keepWithNext para evitar viudas.
- Folios (numeración): 9.5 pt Garamond en margen exterior del pie.
- Encabezados vivos: Título de obra en páginas pares, título de capítulo en páginas impares,
  suprimidos en separatas, blancos y comienzos de capítulo.
================================================================================
"""

import os
import sys
import re
import html
import argparse
import pyphen

from reportlab.lib.units import mm
pt = 1
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, PageBreak, Flowable
)
from reportlab.pdfgen import canvas

# ==============================================================================
# 1. REGISTRO TIPOGRÁFICO: GARAMOND TRUETYPE
# ==============================================================================
FONT_DIR = r"C:\Windows\Fonts"
GARA_REG = os.path.join(FONT_DIR, "GARA.TTF")
GARA_BD  = os.path.join(FONT_DIR, "GARABD.TTF")
GARA_IT  = os.path.join(FONT_DIR, "GARAIT.TTF")

if not (os.path.exists(GARA_REG) and os.path.exists(GARA_BD) and os.path.exists(GARA_IT)):
    raise FileNotFoundError(
        f"Fuentes Garamond no encontradas en {FONT_DIR}. "
        "Asegúrese de que GARA.TTF, GARABD.TTF y GARAIT.TTF estén disponibles."
    )

pdfmetrics.registerFont(TTFont("Garamond", GARA_REG))
pdfmetrics.registerFont(TTFont("Garamond-Bold", GARA_BD))
pdfmetrics.registerFont(TTFont("Garamond-Italic", GARA_IT))
pdfmetrics.registerFont(TTFont("Garamond-BoldItalic", GARA_BD))  # Fallback a negrita

pdfmetrics.registerFontFamily(
    "Garamond",
    normal="Garamond",
    bold="Garamond-Bold",
    italic="Garamond-Italic",
    boldItalic="Garamond-BoldItalic"
)

# Inicializar motor de partición de palabras en español
dic_pyphen = pyphen.Pyphen(lang="es_ES")

def hyphenate_spanish_text(text: str) -> str:
    """
    Aplica soft-hyphen (\u00ad) a palabras en español preservando etiquetas HTML
    y caracteres de escape XML requeridos por ReportLab.
    """
    # Expresión regular que separa tags HTML de texto plano
    tokens = re.split(r"(<[^>]+>)", text)
    processed_tokens = []
    
    for token in tokens:
        if token.startswith("<") and token.endswith(">"):
            processed_tokens.append(token)
        else:
            # Separar palabras preservando puntuación
            words = re.split(r"(\s+|[—–\.,;:«»\(\)\[\]\"¿\?!]+)", token)
            hyphenated_words = []
            for w in words:
                # Partir solo palabras alfabéticas de 6 o más caracteres
                if len(w) >= 6 and w.isalpha():
                    w_hyphen = dic_pyphen.inserted(w, hyphen="\u00ad")
                    hyphenated_words.append(w_hyphen)
                else:
                    hyphenated_words.append(w)
            processed_tokens.append("".join(hyphenated_words))
            
    return "".join(processed_tokens)

def clean_markdown_inline(text: str) -> str:
    """
    Convierte marcas Markdown de cursiva y negrita en etiquetas XML de ReportLab,
    asegurando el correcto escape de entidades (&, <, >).
    """
    # 1. Sanitizar entidades ampersand
    text = re.sub(r"&(?!(?:amp|lt|gt|quot|apos);)", "&amp;", text)
    # 2. Negrita + Cursiva (***texto***)
    text = re.sub(r"\*\*\*(.*?)\*\*\*", r"<b><i>\1</i></b>", text)
    # 3. Negrita (**texto**)
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    # 4. Cursiva con asteriscos (*texto*)
    text = re.sub(r"\*([^\*]+)\*", r"<i>\1</i>", text)
    # 5. Cursiva con guiones bajos (_texto_)
    text = re.sub(r"(?<!\w)_([^_]+)_(?!\w)", r"<i>\1</i>", text)
    
    return text

# ==============================================================================
# 2. GEOMETRÍA Y CONTROL DE FLUJO EDITORIAL (REPORTLAB)
# ==============================================================================
PAGE_WIDTH  = 150 * mm
PAGE_HEIGHT = 210 * mm

# Márgenes matemáticos
MARGIN_LOMO    = 22 * mm   # Interior
MARGIN_CORTE   = 15 * mm   # Exterior
MARGIN_CABEZA  = 15 * mm   # Superior
MARGIN_PIE     = 22 * mm   # Inferior

BOX_WIDTH  = PAGE_WIDTH - MARGIN_LOMO - MARGIN_CORTE   # 113 mm
BOX_HEIGHT = PAGE_HEIGHT - MARGIN_CABEZA - MARGIN_PIE  # 173 mm

class PageBreakToOdd(Flowable):
    """
    Flowable de control de paginación que garantiza que el siguiente elemento
    comience rigurosamente en una página impar (recto).
    Si la página actual es impar y ya tiene contenido, salta al par (blanco) y
    luego al siguiente impar.
    Si la página actual es par, salta al siguiente impar.
    """
    def __init__(self):
        super().__init__()
        self.width = 0
        self.height = 0

    def wrap(self, availWidth, availHeight):
        return 0, 0

    def draw(self):
        pass

class PageMeta(Flowable):
    """
    Flowable mudo que inyecta metadatos a la página activa en el Canvas
    (tipo de página, título de capítulo, etc.).
    """
    def __init__(self, page_type="normal", title=""):
        super().__init__()
        self.page_type = page_type
        self.title = title
        self.width = 0
        self.height = 0

    def wrap(self, availWidth, availHeight):
        return 0, 0

    def draw(self):
        if not hasattr(self.canv, "page_meta"):
            self.canv.page_meta = {}
        # Asigna el estado a la página física en curso
        self.canv.page_meta[self.canv._pageNumber] = {
            "type": self.page_type,
            "title": self.title
        }

class EditorialPrintDocTemplate(BaseDocTemplate):
    """
    Plantilla de documento con soporte nativo para páginas opuestas
    (páginas pares e impares con márgenes de lomo y corte alternados).
    """
    def __init__(self, filename, **kwargs):
        super().__init__(filename, pagesize=(PAGE_WIDTH, PAGE_HEIGHT), **kwargs)

        # Marco Impar (Recto): Lomo a la izquierda (22 mm), Corte a la derecha (15 mm)
        odd_frame = Frame(
            MARGIN_LOMO,
            MARGIN_PIE,
            BOX_WIDTH,
            BOX_HEIGHT,
            id="odd_frame",
            topPadding=0,
            bottomPadding=0,
            leftPadding=0,
            rightPadding=0
        )

        # Marco Par (Verso): Corte a la izquierda (15 mm), Lomo a la derecha (22 mm)
        even_frame = Frame(
            MARGIN_CORTE,
            MARGIN_PIE,
            BOX_WIDTH,
            BOX_HEIGHT,
            id="even_frame",
            topPadding=0,
            bottomPadding=0,
            leftPadding=0,
            rightPadding=0
        )

        self.odd_template = PageTemplate(id="odd", frames=[odd_frame])
        self.even_template = PageTemplate(id="even", frames=[even_frame])
        self.addPageTemplates([self.odd_template, self.even_template])

    def handle_pageEnd(self):
        super().handle_pageEnd()
        next_page = self.page + 1
        if next_page % 2 == 0:
            self.pageTemplate = self.even_template
        else:
            self.pageTemplate = self.odd_template

    def filterFlowables(self, flowables):
        """
        Intercepta PageBreakToOdd antes de que el frame intente procesarlo,
        evaluando el número de página actual y si tiene contenido dibujado.
        """
        if flowables and isinstance(flowables[0], PageBreakToOdd):
            flowables.pop(0)
            has_content = (getattr(self, "_curPageFlowableCount", 0) > 0)
            if self.page % 2 == 1:  # Página impar
                if has_content:
                    # Forzar salto a página par (en blanco) y luego a impar
                    flowables.insert(0, PageBreak())
                    flowables.insert(0, PageBreak())
            else:  # Página par
                flowables.insert(0, PageBreak())

class PrintCanvas(canvas.Canvas):
    """
    Canvas de 2 pasadas para renderizado de alta fidelidad editorial:
    - Control de folios (números de página) en margen exterior inferior.
    - Encabezados vivos alternados (título de obra en verso, capítulo en recto).
    - Supresión estricta en portadillas, actos, blancos y cabeceras de capítulo.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []
        self.page_meta = {}

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        last_chapter_title = ""

        for state in self._saved_page_states:
            self.__dict__.update(state)
            p_num = self._pageNumber
            meta = self.page_meta.get(p_num, {"type": "normal", "title": ""})
            
            p_type = meta["type"]
            if meta["title"]:
                last_chapter_title = meta["title"]

            # Si es separata de acto, blanco o frontmatter, no dibujar nada
            if p_type in ("act", "blank", "frontmatter"):
                super().showPage()
                continue

            is_odd = (p_num % 2 == 1)

            # 1. FOLIOS (NUMERACIÓN INFERIOR A 9.5 PT)
            self.saveState()
            self.setFont("Garamond", 9.5)
            self.setFillColor(colors.black)

            folio_y = 13 * mm  # centrado en el margen de pie (0 a 22 mm)

            if is_odd:
                # Margen exterior derecho: PAGE_WIDTH - MARGIN_CORTE (135 mm)
                folio_x = PAGE_WIDTH - MARGIN_CORTE
                self.drawRightString(folio_x, folio_y, str(p_num))
            else:
                # Margen exterior izquierdo: MARGIN_CORTE (15 mm)
                folio_x = MARGIN_CORTE
                self.drawString(folio_x, folio_y, str(p_num))

            self.restoreState()

            # 2. ENCABEZADOS VIVOS (SUPRIMIDOS EN COMIENZO DE CAPÍTULO)
            if p_type != "chapter_start":
                self.saveState()
                self.setFont("Garamond-Italic", 8.5)
                self.setFillColor(colors.HexColor("#2B2B2B"))

                header_y = PAGE_HEIGHT - 11.5 * mm
                rule_y   = PAGE_HEIGHT - 13.5 * mm

                self.setLineWidth(0.3)
                self.setStrokeColor(colors.HexColor("#999999"))

                if is_odd:
                    # Página impar: Título de capítulo a la derecha
                    chap_str = last_chapter_title if last_chapter_title else "SOMBRA"
                    # Acortar si es excesivamente largo
                    if len(chap_str) > 45:
                        chap_str = chap_str[:42] + "..."
                    header_x = PAGE_WIDTH - MARGIN_CORTE
                    self.drawRightString(header_x, header_y, chap_str)
                    # Línea de caja: de 22 mm a 135 mm
                    self.line(MARGIN_LOMO, rule_y, PAGE_WIDTH - MARGIN_CORTE, rule_y)
                else:
                    # Página par: Título de la obra a la izquierda
                    header_x = MARGIN_CORTE
                    self.drawString(header_x, header_y, "SOMBRA")
                    # Línea de caja: de 15 mm a 128 mm
                    self.line(MARGIN_CORTE, rule_y, MARGIN_CORTE + BOX_WIDTH, rule_y)

                self.restoreState()

            super().showPage()

        super().save()

# ==============================================================================
# 3. ESTILOS TIPOGRÁFICOS EDITORIALES
# ==============================================================================
def create_editorial_styles():
    """
    Configura y devuelve el conjunto de estilos tipográficos con medidas exactas.
    """
    styles = {}

    # Separata de Acto: 24 pt Garamond versalitas/mayúsculas centradas
    styles["ActTitle"] = ParagraphStyle(
        "ActTitle",
        fontName="Garamond-Bold",
        fontSize=24,
        leading=30,
        alignment=TA_CENTER,
        textColor=colors.black,
        spaceAfter=0
    )

    # Título de Capítulo: 18 pt Garamond negrita
    styles["ChapterTitle"] = ParagraphStyle(
        "ChapterTitle",
        fontName="Garamond-Bold",
        fontSize=18,
        leading=22,
        alignment=TA_LEFT,
        textColor=colors.black,
        spaceAfter=0
    )

    # Apartado (###): 12.5 pt Garamond negrita, keepWithNext activo
    styles["SectionHeading"] = ParagraphStyle(
        "SectionHeading",
        fontName="Garamond-Bold",
        fontSize=12.5,
        leading=16,
        alignment=TA_LEFT,
        textColor=colors.black,
        spaceBefore=16,
        spaceAfter=8,
        keepWithNext=True
    )

    # Sub-apartado (####): 11.5 pt Garamond negrita cursiva
    styles["SubSectionHeading"] = ParagraphStyle(
        "SubSectionHeading",
        fontName="Garamond-BoldItalic",
        fontSize=11.5,
        leading=15,
        alignment=TA_LEFT,
        textColor=colors.black,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    # Metadatos de escena (hora, fecha, ubicación bajo título)
    styles["SceneMeta"] = ParagraphStyle(
        "SceneMeta",
        fontName="Garamond-Italic",
        fontSize=10,
        leading=13.5,
        alignment=TA_LEFT,
        textColor=colors.HexColor("#333333"),
        spaceBefore=0,
        spaceAfter=4,
        firstLineIndent=0,
        keepWithNext=True
    )

    # Párrafo normal con sangría de 5 mm
    styles["BodyText"] = ParagraphStyle(
        "BodyText",
        fontName="Garamond",
        fontSize=11,
        leading=13.5,
        alignment=TA_JUSTIFY,
        textColor=colors.black,
        firstLineIndent=5 * mm,
        spaceBefore=0,
        spaceAfter=0
    )

    # Primer párrafo tras título (sin sangría)
    styles["FirstParagraph"] = ParagraphStyle(
        "FirstParagraph",
        parent=styles["BodyText"],
        firstLineIndent=0
    )

    # Citas en bloque (Blockquotes >)
    styles["Blockquote"] = ParagraphStyle(
        "Blockquote",
        fontName="Garamond-Italic",
        fontSize=10,
        leading=13,
        alignment=TA_JUSTIFY,
        textColor=colors.HexColor("#222222"),
        leftIndent=12 * pt,
        rightIndent=12 * pt,
        firstLineIndent=0,
        spaceBefore=8,
        spaceAfter=8
    )

    # Asterismo / Separador de escena
    styles["Asterism"] = ParagraphStyle(
        "Asterism",
        fontName="Garamond",
        fontSize=11,
        leading=14,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#555555"),
        spaceBefore=12,
        spaceAfter=12
    )

    # Frontmatter styles
    styles["FalsaPortadilla"] = ParagraphStyle(
        "FalsaPortadilla",
        fontName="Garamond",
        fontSize=13,
        leading=18,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#222222")
    )

    styles["PortadaTitulo"] = ParagraphStyle(
        "PortadaTitulo",
        fontName="Garamond-Bold",
        fontSize=26,
        leading=32,
        alignment=TA_CENTER,
        textColor=colors.black
    )

    styles["PortadaAutor"] = ParagraphStyle(
        "PortadaAutor",
        fontName="Garamond",
        fontSize=14,
        leading=18,
        alignment=TA_CENTER,
        textColor=colors.black
    )

    styles["PortadaSubtitulo"] = ParagraphStyle(
        "PortadaSubtitulo",
        fontName="Garamond-Italic",
        fontSize=11,
        leading=15,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#444444")
    )

    styles["Colophon"] = ParagraphStyle(
        "Colophon",
        fontName="Garamond",
        fontSize=8.5,
        leading=12,
        alignment=TA_LEFT,
        textColor=colors.HexColor("#333333")
    )

    return styles

# ==============================================================================
# 4. COMPILADOR DE MARKDOWN A ELEMENTOS REPORTLAB (FLOWABLES)
# ==============================================================================
def parse_markdown_to_flowables(markdown_content: str, styles: dict) -> list:
    """
    Parsea el contenido Markdown jerárquico (# Actos, ## Capítulos, ### Apartados)
    y devuelve la secuencia exacta de Flowables respetando las reglas editoriales.
    """
    story = []
    lines = markdown_content.split("\n")

    # 1. FRONT MATTER EDITORIAL CLÁSICO
    # Página 1 (impar): Falsa portadilla
    story.append(PageMeta("frontmatter"))
    story.append(Spacer(1, 65 * mm))
    story.append(Paragraph("SOMBRA", styles["FalsaPortadilla"]))
    story.append(PageBreak())

    # Página 2 (par): Reverso en blanco
    story.append(PageMeta("blank"))
    story.append(PageBreak())

    # Página 3 (impar): Portada principal interior
    story.append(PageMeta("frontmatter"))
    story.append(Spacer(1, 30 * mm))
    story.append(Paragraph("PEDRO GARAT &amp; ANTIGRAVITY", styles["PortadaAutor"]))
    story.append(Spacer(1, 20 * mm))
    story.append(Paragraph("SOMBRA", styles["PortadaTitulo"]))
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph("Novela de Ciencia Ficción Dura", styles["PortadaSubtitulo"]))
    story.append(Spacer(1, 55 * mm))
    story.append(Paragraph("Edición Definitiva para Imprenta", styles["PortadaSubtitulo"]))
    story.append(PageBreak())

    # Página 4 (par): Página legal y créditos tipográficos
    story.append(PageMeta("frontmatter"))
    story.append(Spacer(1, 110 * mm))
    colophon_text = (
        "<b>SOMBRA</b><br/>"
        "© 2026 Pedro Garat &amp; Antigravity.<br/>"
        "Todos los derechos reservados.<br/><br/>"
        "<i>Dirección técnica y diseño editorial:</i> Bill (Editorial Engineering Systems)<br/>"
        "<i>Formato:</i> 150 × 210 mm (Papel ahuesado editorial de 90 g/m²)<br/>"
        "<i>Tipografía:</i> Garamond regular 11/13.5 pt, negrita y cursiva.<br/>"
        "<i>Separación silábica:</i> Motor lexicográfico pyphen (es_ES).<br/>"
        "Impreso en la Tierra antes del apagón."
    )
    story.append(Paragraph(colophon_text, styles["Colophon"]))
    story.append(PageBreak())

    # 2. CUERPO DE LA OBRA
    is_first_paragraph = False
    in_frontmatter_header = True
    current_chapter_title = ""

    idx = 0
    num_lines = len(lines)

    while idx < num_lines:
        line = lines[idx].strip()

        # Omitir cabecera inicial si ya procesamos el Front Matter
        if in_frontmatter_header:
            if line.startswith("# ") and "ACTO" in line.upper():
                in_frontmatter_header = False
            else:
                idx += 1
                continue

        if not line:
            idx += 1
            continue

        # NIVEL 1: ACTOS (# ...)
        if line.startswith("# "):
            act_title = line[2:].strip()
            # Salto riguroso a página impar
            story.append(PageBreakToOdd())
            # Marcador de separata (sin folio ni encabezado)
            story.append(PageMeta("act", act_title))
            # Separata: Centrado vertical (~65 mm de drop en caja de 173 mm)
            story.append(Spacer(1, 65 * mm))
            story.append(Paragraph(act_title.upper(), styles["ActTitle"]))
            # Reverso en blanco obligatorio (página par)
            story.append(PageBreak())
            story.append(PageMeta("blank"))
            story.append(PageBreak())
            idx += 1
            continue

        # NIVEL 2: CAPÍTULOS (## ...)
        if line.startswith("## "):
            raw_title = line[3:].strip()
            current_chapter_title = raw_title
            
            # Salto a página impar para inicio de capítulo
            story.append(PageBreakToOdd())
            # Marcador de inicio de capítulo (suprime encabezado vivo superior)
            story.append(PageMeta("chapter_start", current_chapter_title))
            
            # Drop inicial de 40 mm desde el margen superior
            story.append(Spacer(1, 40 * mm))
            story.append(Paragraph(current_chapter_title, styles["ChapterTitle"]))
            
            # Separación de 15 mm antes del texto
            story.append(Spacer(1, 15 * mm))
            
            is_first_paragraph = True
            idx += 1
            continue

        # NIVEL 3: APARTADOS (### ...)
        if line.startswith("### "):
            sec_title = line[4:].strip()
            # Marca de metadatos de página normal
            story.append(PageMeta("normal", current_chapter_title))
            story.append(Paragraph(sec_title, styles["SectionHeading"]))
            is_first_paragraph = True
            idx += 1
            continue

        # SUB-APARTADOS (#### ...)
        if line.startswith("#### "):
            subsec_title = line[5:].strip()
            story.append(Paragraph(subsec_title, styles["SubSectionHeading"]))
            is_first_paragraph = True
            idx += 1
            continue

        # SEPARADORES DE ESCENA (--- o ***)
        if line in ("---", "***", "* * *", "___"):
            story.append(Paragraph("*&nbsp;&nbsp;&nbsp;&nbsp;*&nbsp;&nbsp;&nbsp;&nbsp;*", styles["Asterism"]))
            is_first_paragraph = True
            idx += 1
            continue

        # CITAS EN BLOQUE (> ...)
        if line.startswith(">"):
            quote_lines = []
            while idx < num_lines and lines[idx].strip().startswith(">"):
                quote_lines.append(lines[idx].strip()[1:].strip())
                idx += 1
            quote_text = " ".join(quote_lines)
            quote_text = clean_markdown_inline(quote_text)
            quote_text = hyphenate_spanish_text(quote_text)
            story.append(Paragraph(quote_text, styles["Blockquote"]))
            is_first_paragraph = True
            continue

        # PÁRRAFOS REGULARES Y METADATOS EN CURSIVA
        # Revisar si es metadato de fecha/hora bajo título: *02:35 AM — 16 de julio de 1945*
        if line.startswith("*") and line.endswith("*") and not line.startswith("***") and is_first_paragraph:
            meta_text = line[1:-1].strip()
            meta_text = clean_markdown_inline(meta_text)
            story.append(Paragraph(f"<i>{meta_text}</i>", styles["SceneMeta"]))
            idx += 1
            continue

        # Acumular párrafo continuo si abarca múltiples líneas
        p_lines = [line]
        idx += 1
        while idx < num_lines:
            next_l = lines[idx].strip()
            if not next_l or next_l.startswith("#") or next_l in ("---", "***", "* * *") or next_l.startswith(">"):
                break
            p_lines.append(next_l)
            idx += 1

        p_raw = " ".join(p_lines)
        p_cleaned = clean_markdown_inline(p_raw)
        p_hyphenated = hyphenate_spanish_text(p_cleaned)

        chosen_style = styles["FirstParagraph"] if is_first_paragraph else styles["BodyText"]
        story.append(Paragraph(p_hyphenated, chosen_style))
        is_first_paragraph = False

    return story

# ==============================================================================
# 5. PIPELINE PRINCIPAL DE COMPILACIÓN EDITORIAL
# ==============================================================================
def build_print_pdf(input_md_path: str, output_pdf_path: str):
    """
    Ejecuta el pipeline completo de renderizado y compilación de la novela.
    """
    print("=" * 78)
    print("INICIANDO COMPILACIÓN EDITORIAL PARA IMPRENTA")
    print(f"Archivo de entrada: {input_md_path}")
    print(f"Archivo de salida:  {output_pdf_path}")
    print(f"Formato: 150 mm × 210 mm | Lomo: {MARGIN_LOMO/mm:.0f} mm | Corte: {MARGIN_CORTE/mm:.0f} mm")
    print("=" * 78)

    if not os.path.exists(input_md_path):
        raise FileNotFoundError(f"No se encontró el archivo markdown: {input_md_path}")

    with open(input_md_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    print("Configurando estilos tipográficos Garamond...")
    styles = create_editorial_styles()

    print("Parseando estructura jerárquica y aplicando silabeo pyphen...")
    story = parse_markdown_to_flowables(md_content, styles)
    print(f"Total de flowables generados para la maqueta: {len(story)}")

    print("Iniciando maquetación en ReportLab (EditorialPrintDocTemplate + PrintCanvas)...")
    doc = EditorialPrintDocTemplate(output_pdf_path)
    doc.build(story, canvasmaker=PrintCanvas)

    print("Verificando integridad del PDF compilado...")
    if os.path.exists(output_pdf_path):
        size_kb = os.path.getsize(output_pdf_path) / 1024
        print(f"¡Compilación finalizada con éxito!")
        print(f"PDF generado: {output_pdf_path} ({size_kb:.1f} KB)")
        
        # Sincronizar copia en novela/ si se compiló en la raíz
        novela_copy = os.path.join("novela", os.path.basename(output_pdf_path))
        if os.path.abspath(output_pdf_path) != os.path.abspath(novela_copy):
            import shutil
            shutil.copyfile(output_pdf_path, novela_copy)
            print(f"Copia sincronizada en: {novela_copy}")
    else:
        raise RuntimeError("Error: No se encontró el archivo de salida tras la compilación.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generador editorial para imprenta de La Canción del Silencio.")
    parser.add_argument("--input", default="novela/la_cancion_del_silencio_completa.md", help="Ruta al archivo Markdown completo.")
    parser.add_argument("--output", default="La_Cancion_del_Silencio_Edicion_Imprenta_150x210.pdf", help="Ruta al PDF de salida.")
    args = parser.parse_args()

    build_print_pdf(args.input, args.output)
