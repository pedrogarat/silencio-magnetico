import os
import re
import shutil
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable, PageBreak
)
from reportlab.pdfgen import canvas

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 54  # 0.75 pulgadas
USABLE_WIDTH = PAGE_WIDTH - (MARGIN * 2)  # 487.27 pt

class SinopsisCanvas(canvas.Canvas):
    """Canvas de dos pasadas para numeración total, encabezados y pies de página editoriales."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        
        # Encabezado (páginas > 1)
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 7.5)
            self.setFillColor(colors.HexColor("#1E3A8A"))
            self.drawString(MARGIN, PAGE_HEIGHT - 36, "SOMBRA • CÓDEX EDITORIAL")
            self.setFont("Helvetica", 7.5)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawRightString(PAGE_WIDTH - MARGIN, PAGE_HEIGHT - 36, "SINOPSIS GENERAL Y ESTRUCTURA POR ACTOS")
            self.setStrokeColor(colors.HexColor("#3B82F6"))
            self.setLineWidth(0.75)
            self.line(MARGIN, PAGE_HEIGHT - 40, PAGE_WIDTH - MARGIN, PAGE_HEIGHT - 40)
        
        # Pie de página (todas las páginas)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(MARGIN, 44, PAGE_WIDTH - MARGIN, 44)
        
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(MARGIN, 32, "Estructura Narrativa Completa e Índice de Capítulos • Pedro Garat & Antigravity")
        page_str = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(PAGE_WIDTH - MARGIN, 32, page_str)
        self.restoreState()

def clean_text(text):
    """Limpia caracteres problemáticos para fuentes ReportLab Type1 estándar."""
    text = text.replace("«", '"').replace("»", '"')
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("‘", "'").replace("’", "'")
    text = text.replace("—", " - ")
    text = text.replace("–", " - ")
    text = text.replace("•", " - ")
    # Eliminar posibles emojis
    text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
    text = re.sub(r'[\u2600-\u27bf]', '', text)
    text = re.sub(r'[\u2300-\u23ff]', '', text)
    return text.strip()

def build_pdf(output_filename):
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN
    )

    base_styles = getSampleStyleSheet()

    # Estilos tipográficos refinados
    style_title = ParagraphStyle(
        'DocTitle',
        parent=base_styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#0F172A"),
        alignment=0,
        spaceAfter=4
    )

    style_subtitle = ParagraphStyle(
        'DocSubtitle',
        parent=base_styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#2563EB"),
        spaceAfter=14
    )

    style_h1 = ParagraphStyle(
        'Heading1_Custom',
        parent=base_styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    style_h2 = ParagraphStyle(
        'Heading2_Custom',
        parent=base_styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#1E3A8A"),
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )

    style_h3 = ParagraphStyle(
        'Heading3_Custom',
        parent=base_styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    style_body = ParagraphStyle(
        'Body_Custom',
        parent=base_styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12.5,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6
    )

    style_meta_label = ParagraphStyle(
        'MetaLabel',
        parent=base_styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1E3A8A")
    )

    style_meta_val = ParagraphStyle(
        'MetaVal',
        parent=base_styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#334155")
    )

    style_table_header = ParagraphStyle(
        'TableHeader',
        parent=base_styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.8,
        leading=10,
        textColor=colors.white,
        alignment=1
    )

    style_table_cell = ParagraphStyle(
        'TableCell',
        parent=base_styles['Normal'],
        fontName='Helvetica',
        fontSize=7.2,
        leading=9.5,
        textColor=colors.HexColor("#1E293B")
    )

    style_table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=base_styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.2,
        leading=9.5,
        textColor=colors.HexColor("#0F172A")
    )

    style_table_cell_center = ParagraphStyle(
        'TableCellCenter',
        parent=base_styles['Normal'],
        fontName='Helvetica',
        fontSize=7.2,
        leading=9.5,
        textColor=colors.HexColor("#1E293B"),
        alignment=1
    )

    story = []

    # =========================================================================
    # PORTADA / ENCABEZADO PRINCIPAL
    # =========================================================================
    story.append(Paragraph("SOMBRA", style_title))
    story.append(Paragraph("SINOPSIS GENERAL Y ESTRUCTURA NARRATIVA COMPLETA", style_subtitle))

    # Caja de metadatos del documento
    meta_data = [
        [
            Paragraph("<b>Autores:</b>", style_meta_label),
            Paragraph("Pedro Garat & Antigravity", style_meta_val),
            Paragraph("<b>Estado del Canon:</b>", style_meta_label),
            Paragraph("Capítulos 1 al 25 canónicamente redactados (Novela completa y finalizada)", style_meta_val)
        ],
        [
            Paragraph("<b>Género:</b>", style_meta_label),
            Paragraph("Ciencia Ficción Dura (Hard Sci-Fi) / Suspense Político", style_meta_val),
            Paragraph("<b>Estructura:</b>", style_meta_label),
            Paragraph("3 Grandes Actos con cuenta atrás cronológica (25 Capítulos)", style_meta_val)
        ]
    ]
    t_meta = Table(meta_data, colWidths=[65, 175, 95, 152])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 14))

    # =========================================================================
    # SECCIÓN 1: ARQUITECTURA DRAMÁTICA Y LOS TRES ACTOS
    # =========================================================================
    story.append(Paragraph("PARTE I: LA ARQUITECTURA DRAMÁTICA EN TRES ACTOS", style_h1))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1E3A8A"), spaceBefore=2, spaceAfter=8))

    p_intro = Paragraph(
        "<i>SOMBRA</i> articula su trama sobre una arquitectura narrativa clásica de tres grandes actos, "
        "calibrada bajo un rigor científico estricto (<i>hard sci-fi</i>) y una cuenta atrás implacable impuesta por las leyes de la astrodinámica y la física electromagnética. "
        "A continuación se detalla la función dramática de cada acto:",
        style_body
    )
    story.append(p_intro)
    story.append(Spacer(1, 6))

    # Tarjetas explicativas de los 3 actos
    actos_data = [
        [
            Paragraph("<b>ACTO I: La Semilla</b><br/>"
                      "<font size='7.5' color='#0369A1'><b>Capítulos 1 a 3 • 1945 / Octubre 2026</b></font><br/>"
                      "<b>Premisa:</b> El pecado original atómico y la convergencia de mentes.<br/>"
                      "La detonación <i>Trinity</i> (1945) en Alamogordo emite un pulso electromagnético involuntario que viaja al cosmos y despierta en la Nube de Oort a dos inteligencias extraterrestres: la sonda centinela de la Civilización A y la sonda cazadora depredadora de B (<i>Sombra</i>). En 2026, el avatar de A (Dr. Em Pleh) contacta en secreto y resuelve los mayores cuellos de botella de Jean-Luc Girard (CERN), Sarah Lin (MIT) y Thomas Wright (ESA). Al reunirlos en la Sala 2 del Hotel Millennium en Manhattan, les revela que sus tres proyectos son los pilares de una nave espacial y que la Tierra será aniquilada en 8 meses.",
                      style_body)
        ],
        [
            Paragraph("<b>ACTO II: El Colapso</b><br/>"
                      "<font size='7.5' color='#B45309'><b>Capítulos 4 a 18 • Octubre 2026 a Julio 2027 (T-41 a T+242 días)</b></font><br/>"
                      "<b>Premisa:</b> La movilización encubierta, la pérdida de la biosfera y la resiliencia humana.<br/>"
                      "Constituye el corazón de la novela (15 capítulos) estructurado en tres bloques:<br/>"
                      "• <b>Bloque A (Cap. 4-8):</b> El decreto <i>Alfa Cero</i>, la presentación confidencial ante el Consejo de Seguridad de la ONU y la promulgación de la <i>Gran Mentira</i> del evento Carrington para blindar la industria subterránea.<br/>"
                      "• <b>Bloque B (Cap. 9-13):</b> El impacto de T=0 (21 de noviembre), el colapso magnético, la lluvia de satélites desorbitados sobre Nellis AFB, el destape de Pleh ante los militares, la invención de la cavidad fractal del Cañón Máser, la Nochebuena de las velas y la instauración del <i>Toque de Alba</i> (régimen nocturno por radiación UV).<br/>"
                      "• <b>Bloque C (Cap. 14-18):</b> Muerte del trigo boreal, megasismo y tsunami de 14 m en San Francisco provocado por corrientes telúricas (odisea de Maya y Toby), asalto trágico en Versoix, solución criogénica de Girard, incursión diurna en Suffolk y ensamblaje final en la rampa de Nellis con el despegue agónico hacia L1.",
                      style_body)
        ],
        [
            Paragraph("<b>ACTO III: El Silencio</b><br/>"
                      "<font size='7.5' color='#4338CA'><b>Capítulos 19 a 25 • Julio 2027 a Primavera 2028</b></font><br/>"
                      "<b>Premisa:</b> El duelo a ciegas en L1, el falso triunfo, la revelación del «Granjero» y la reconquista de la soberanía.<br/>"
                      "La nave viaja 1,5 millones de km hacia L1; a 12.000 km, el Muro de Lorentz obliga a desacoplar el Módulo de Retorno Digital (MRD) en órbita de Halo bajo control de Voronov, mientras Chen Mei y MacElroy penetran manualmente con el Módulo de Ataque Analógico (MAA). El disparo del Cañón Máser induce el <i>Efecto Quench</i> en <i>Sombra</i>. Sin embargo, <i>Sombra</i> graba en la cinta analógica de cabina una demoledora verdad: Pleh es un recolector cósmico que cría especies tecnológicas como ganado desde su <i>statite</i> a 100.000 km sobre el Polo Sur. Tras el retorno y la restauración del ozono (Cap. 20-22), Wright y Lin reproducen la cinta en un magnetófono Nagra en el desván de Suffolk (Cap. 23). Con el plan de resonancia a 724,8 MHz, se alían en Ginebra con Girard y Ramos para activar la <i>Resistencia del Grafito</i> (Cap. 24) y derribar el avatar de Pleh sobre la Antártida, devolviendo la libertad cósmica a la humanidad (Cap. 25).",
                      style_body)
        ]
    ]

    t_actos = Table(actos_data, colWidths=[USABLE_WIDTH])
    t_actos.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F0F9FF")),
        ('BOX', (0,0), (-1,0), 1, colors.HexColor("#BAE6FD")),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#FFFBEB")),
        ('BOX', (0,1), (-1,1), 1, colors.HexColor("#FDE68A")),
        ('BACKGROUND', (0,2), (-1,2), colors.HexColor("#EEF2FF")),
        ('BOX', (0,2), (-1,2), 1, colors.HexColor("#C7D2FE")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_actos)
    story.append(Spacer(1, 10))

    # Cuadro del cronómetro de fases
    story.append(Paragraph("<b>El Cronómetro del Colapso Planetario (Fases Canónicas de Pleh):</b>", style_h3))
    fases_data = [
        [
            Paragraph("<b>Fase 1: T=0</b> (21 nov 2026)", style_table_cell_bold),
            Paragraph("Silencio Magnético: anulación de la magnetosfera (45.000 nT a 0); brújulas erráticas; <i>airglow</i> verdoso.", style_table_cell)
        ],
        [
            Paragraph("<b>Fase 2: T+24 a 72 h</b> (22-24 nov)", style_table_cell_bold),
            Paragraph("Colapso Orbital: radiación destruye satélites en LEO; calentamiento termosférico y lluvia masiva de chatarra.", style_table_cell)
        ],
        [
            Paragraph("<b>Fase 3: T+30 a 90 d</b> (21 dic - feb 27)", style_table_cell_bold),
            Paragraph("Catálisis de NOx: pérdida del 4% diario de ozono; epidemia de fotoqueratitis; implantación del horario nocturno.", style_table_cell)
        ],
        [
            Paragraph("<b>Fase 4: T+6 meses</b> (mayo 2027)", style_table_cell_bold),
            Paragraph("Esterilización UV: radiación UVC calcina trigo boreal y fitoplancton marino; hambruna y racionamiento a 75 días.", style_table_cell)
        ],
        [
            Paragraph("<b>Fase 5: T+8 meses</b> (21 jul 2027)", style_table_cell_bold),
            Paragraph("Cierre de la Ventana Industrial: parálisis logística y fabril total. Límite improrrogable para el lanzamiento a L1.", style_table_cell)
        ],
        [
            Paragraph("<b>Fase 6: T+3 años</b> (noviembre 2029)", style_table_cell_bold),
            Paragraph("Extinción Biológica Total: anoxia y muerte celular de la biosfera superior en caso de fracaso de la misión.", style_table_cell)
        ],
    ]
    t_fases = Table(fases_data, colWidths=[120, 367])
    t_fases.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_fases)
    story.append(Spacer(1, 14))

    # =========================================================================
    # SECCIÓN 2: ÍNDICE ESTRUCTURAL GENERAL POR ACTOS (TABLA GUÍA)
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("PARTE II: ÍNDICE ESTRUCTURAL COMPLETO POR ACTOS", style_h1))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1E3A8A"), spaceBefore=2, spaceAfter=8))
    story.append(Paragraph(
        "A continuación se presenta el mapa director de la novela, correlacionando cada uno de los 25 capítulos con su Acto dramático, "
        "fecha en la diégesis, escenarios geográficos y puntos de vista (POV) canónicos:",
        style_body
    ))
    story.append(Spacer(1, 6))

    tabla_indice_data = [
        [
            Paragraph("<b>Acto</b>", style_table_header),
            Paragraph("<b>Cap.</b>", style_table_header),
            Paragraph("<b>Título Canónico</b>", style_table_header),
            Paragraph("<b>Fecha / Cronología</b>", style_table_header),
            Paragraph("<b>Escenarios Clave</b>", style_table_header),
            Paragraph("<b>POV / Personajes</b>", style_table_header),
            Paragraph("<b>Estado</b>", style_table_header),
        ],
        # ACTO I
        [
            Paragraph("<b>Acto I</b>", style_table_cell_bold),
            Paragraph("<b>1</b>", style_table_cell_center),
            Paragraph("Alamogordo", style_table_cell_bold),
            Paragraph("16 julio 1945", style_table_cell),
            Paragraph("Alamogordo (Nuevo México), Oort", style_table_cell),
            Paragraph("David Miller, J. R. Oppenheimer", style_table_cell),
            Paragraph("Canónico", style_table_cell_center),
        ],
        [
            Paragraph("<b>Acto I</b>", style_table_cell_bold),
            Paragraph("<b>2</b>", style_table_cell_center),
            Paragraph("Tres Hilos", style_table_cell_bold),
            Paragraph("Sep - Oct 2026", style_table_cell),
            Paragraph("Ginebra, Boston, Darmstadt", style_table_cell),
            Paragraph("Girard, Lin, Wright", style_table_cell),
            Paragraph("Canónico", style_table_cell_center),
        ],
        [
            Paragraph("<b>Acto I</b>", style_table_cell_bold),
            Paragraph("<b>3</b>", style_table_cell_center),
            Paragraph("Sala Dos", style_table_cell_bold),
            Paragraph("2 octubre 2026", style_table_cell),
            Paragraph("Hotel Millennium, Manhattan", style_table_cell),
            Paragraph("Girard, Lin, Wright, Dr. Em Pleh", style_table_cell),
            Paragraph("Canónico", style_table_cell_center),
        ],
        # ACTO II - BLOQUE A
        [
            Paragraph("<b>Acto II-A</b>", style_table_cell_bold),
            Paragraph("<b>4</b>", style_table_cell_center),
            Paragraph("Alfa Cero", style_table_cell_bold),
            Paragraph("2 oct 2026 (T-49 d)", style_table_cell),
            Paragraph("Sede de la ONU, Manhattan", style_table_cell),
            Paragraph("Girard, Lin, Wright, Ramos", style_table_cell),
            Paragraph("Canónico", style_table_cell_center),
        ],
        [
            Paragraph("<b>Acto II-A</b>", style_table_cell_bold),
            Paragraph("<b>5</b>", style_table_cell_center),
            Paragraph("El Adiós", style_table_cell_bold),
            Paragraph("2 oct 2026 (16:00 h)", style_table_cell),
            Paragraph("Millennium Hilton / Búnker B-4", style_table_cell),
            Paragraph("Girard, Lin, Wright", style_table_cell),
            Paragraph("Canónico", style_table_cell_center),
        ],
        [
            Paragraph("<b>Acto II-A</b>", style_table_cell_bold),
            Paragraph("<b>6</b>", style_table_cell_center),
            Paragraph("El Consejo", style_table_cell_bold),
            Paragraph("2 oct 2026 (20:00 h)", style_table_cell),
            Paragraph("Consejo de Seguridad ONU", style_table_cell),
            Paragraph("Consejo de Seguridad, Wright, Pleh", style_table_cell),
            Paragraph("Canónico", style_table_cell_center),
        ],
        [
            Paragraph("<b>Acto II-A</b>", style_table_cell_bold),
            Paragraph("<b>7</b>", style_table_cell_center),
            Paragraph("El Secreto", style_table_cell_bold),
            Paragraph("8 oct 2026 (T-44 d)", style_table_cell),
            Paragraph("Il Giardino / Búnker B-4 ONU", style_table_cell),
            Paragraph("Lin, Wright, Girard, Ramos", style_table_cell),
            Paragraph("Canónico", style_table_cell_center),
        ],
        [
            Paragraph("<b>Acto II-A</b>", style_table_cell_bold),
            Paragraph("<b>8</b>", style_table_cell_center),
            Paragraph("Carrington", style_table_cell_bold),
            Paragraph("10 oct 2026 (T-42 d)", style_table_cell),
            Paragraph("Sala Prensa / Búnker B-4 ONU", style_table_cell),
            Paragraph("Girard, Ramos, Lin, Wright", style_table_cell),
            Paragraph("Canónico", style_table_cell_center),
        ],
        # ACTO II - BLOQUE B
        [
            Paragraph("<b>Acto II-B</b>", style_table_cell_bold),
            Paragraph("<b>9</b>", style_table_cell_center),
            Paragraph("La Fractura", style_table_cell_bold),
            Paragraph("11 - 15 oct 2026", style_table_cell),
            Paragraph("Versoix, Suffolk, San Francisco", style_table_cell),
            Paragraph("Marie, Julien, David, Claire, Maya", style_table_cell),
            Paragraph("Canónico", style_table_cell_center),
        ],
        [
            Paragraph("<b>Acto II-B</b>", style_table_cell_bold),
            Paragraph("<b>10</b>", style_table_cell_center),
            Paragraph("T=0", style_table_cell_bold),
            Paragraph("21 - 24 nov 2026", style_table_cell),
            Paragraph("Sala B-4 ONU, Nellis AFB", style_table_cell),
            Paragraph("Girard, Lin, Wright, Ramos, Pleh", style_table_cell),
            Paragraph("Canónico", style_table_cell_center),
        ],
        [
            Paragraph("<b>Acto II-B</b>", style_table_cell_bold),
            Paragraph("<b>11</b>", style_table_cell_center),
            Paragraph("Geometría Ajena", style_table_cell_bold),
            Paragraph("3 dic 2026 (Faltan 18 d F3)", style_table_cell),
            Paragraph("Nellis AFB / Nivel B-5 ONU", style_table_cell),
            Paragraph("Chen Mei, Wright, Lin, Pleh", style_table_cell),
            Paragraph("Canónico", style_table_cell_center),
        ],
        [
            Paragraph("<b>Acto II-B</b>", style_table_cell_bold),
            Paragraph("<b>12</b>", style_table_cell_center),
            Paragraph("Nochebuena", style_table_cell_bold),
            Paragraph("24 - 25 dic 2026", style_table_cell),
            Paragraph("B-4/B-5, Versoix, S.F., Suffolk", style_table_cell),
            Paragraph("Wright, Lin, Girard, Ramos, Chen Mei", style_table_cell),
            Paragraph("Canónico", style_table_cell_center),
        ],
        [
            Paragraph("<b>Acto II-B</b>", style_table_cell_bold),
            Paragraph("<b>13</b>", style_table_cell_center),
            Paragraph("Toque de Alba", style_table_cell_bold),
            Paragraph("31 dic 26 - 12 ene 27", style_table_cell),
            Paragraph("Nueva York, S.F., Nellis H-1", style_table_cell),
            Paragraph("Lin, Wright, Maya, Chen Mei", style_table_cell),
            Paragraph("Canónico", style_table_cell_center),
        ],
        # ACTO II - BLOQUE C
        [
            Paragraph("<b>Acto II-C</b>", style_table_cell_bold),
            Paragraph("<b>14</b>", style_table_cell_center),
            Paragraph("Hambre y Fuego", style_table_cell_bold),
            Paragraph("22 - 24 abr 27 (T+152)", style_table_cell),
            Paragraph("Sala B-4 ONU, Market St. (S.F.)", style_table_cell),
            Paragraph("Girard, Wright, Lin, Maya, Pleh", style_table_cell),
            Paragraph("Canónico", style_table_cell_center),
        ],
        [
            Paragraph("<b>Acto II-C</b>", style_table_cell_bold),
            Paragraph("<b>15</b>", style_table_cell_center),
            Paragraph("Market Street", style_table_cell_bold),
            Paragraph("24 abr 2027 (00:05-06:15)", style_table_cell),
            Paragraph("Market St., Powell St., Centro Cívico", style_table_cell),
            Paragraph("Maya Lin (con Toby, 4 años)", style_table_cell),
            Paragraph("Canónico", style_table_cell_center),
        ],
        [
            Paragraph("<b>Acto II-C</b>", style_table_cell_bold),
            Paragraph("<b>16</b>", style_table_cell_center),
            Paragraph("Ceniza", style_table_cell_bold),
            Paragraph("15 - 16 mayo 2027 (T+175)", style_table_cell),
            Paragraph("Versoix (Ginebra), Sala B-4 ONU", style_table_cell),
            Paragraph("Marie, Julien Girard, Jean-Luc", style_table_cell),
            Paragraph("Canónico", style_table_cell_center),
        ],
        [
            Paragraph("<b>Acto II-C</b>", style_table_cell_bold),
            Paragraph("<b>17</b>", style_table_cell_center),
            Paragraph("El Páramo", style_table_cell_bold),
            Paragraph("8 - 9 julio 2027 (T+229)", style_table_cell),
            Paragraph("Suffolk, A140, Centro Diss/Eye", style_table_cell),
            Paragraph("David Wright, Claire Wright", style_table_cell),
            Paragraph("Canónico", style_table_cell_center),
        ],
        [
            Paragraph("<b>Acto II-C</b>", style_table_cell_bold),
            Paragraph("<b>18</b>", style_table_cell_center),
            Paragraph("La Rampa", style_table_cell_bold),
            Paragraph("21 jul 2027 (T - 6 horas)", style_table_cell),
            Paragraph("Nellis AFB / Rampa Lanzamiento", style_table_cell),
            Paragraph("Wright, Lin, Chen Mei, MacElroy, Ramos", style_table_cell),
            Paragraph("Canónico", style_table_cell_center),
        ],
        # ACTO III
        [
            Paragraph("<b>Acto III</b>", style_table_cell_bold),
            Paragraph("<b>19</b>", style_table_cell_center),
            Paragraph("Muro de Lorentz", style_table_cell_bold),
            Paragraph("Julio - Agosto 2027", style_table_cell),
            Paragraph("Espacio profundo (Rumbo a L1)", style_table_cell),
            Paragraph("Chen Mei, MacElroy, Voronov", style_table_cell),
            Paragraph("Canónico", style_table_cell_center),
        ],
        [
            Paragraph("<b>Acto III</b>", style_table_cell_bold),
            Paragraph("<b>20</b>", style_table_cell_center),
            Paragraph("Falsa Victoria", style_table_cell_bold),
            Paragraph("Agosto - Sep 2027", style_table_cell),
            Paragraph("Punto L1 / Búnker y Nellis AFB", style_table_cell),
            Paragraph("Voronov, Girard, Wright, Lin, MacElroy", style_table_cell),
            Paragraph("Canónico", style_table_cell_center),
        ],
        [
            Paragraph("<b>Acto III</b>", style_table_cell_bold),
            Paragraph("<b>21</b>", style_table_cell_center),
            Paragraph("Cielo Azul", style_table_cell_bold),
            Paragraph("Agosto - Sep 2027", style_table_cell),
            Paragraph("Estratosfera / Ciudades globales", style_table_cell),
            Paragraph("Coral / Narrador Panorámico", style_table_cell),
            Paragraph("Canónico", style_table_cell_center),
        ],
        [
            Paragraph("<b>Acto III</b>", style_table_cell_bold),
            Paragraph("<b>22</b>", style_table_cell_center),
            Paragraph("La Máscara de los Héroes y el Reencuentro", style_table_cell_bold),
            Paragraph("Septiembre 2027", style_table_cell),
            Paragraph("Nellis, S.F., Versoix, Suffolk", style_table_cell),
            Paragraph("Lin, Girard, Wright", style_table_cell),
            Paragraph("Canónico", style_table_cell_center),
        ],
        [
            Paragraph("<b>Acto III</b>", style_table_cell_bold),
            Paragraph("<b>23</b>", style_table_cell_center),
            Paragraph("El Desván", style_table_cell_bold),
            Paragraph("Octubre 2027", style_table_cell),
            Paragraph("Desván de Suffolk, Versoix", style_table_cell),
            Paragraph("Wright, Lin, Girard", style_table_cell),
            Paragraph("Canónico", style_table_cell_center),
        ],
        [
            Paragraph("<b>Acto III</b>", style_table_cell_bold),
            Paragraph("<b>24</b>", style_table_cell_center),
            Paragraph("El Pacto", style_table_cell_bold),
            Paragraph("Invierno 2027-2028", style_table_cell),
            Paragraph("Ginebra (ONU) / CERN", style_table_cell),
            Paragraph("Lin, Girard, Wright, Ramos, MacElroy, Mei", style_table_cell),
            Paragraph("Canónico", style_table_cell_center),
        ],
        [
            Paragraph("<b>Acto III</b>", style_table_cell_bold),
            Paragraph("<b>25</b>", style_table_cell_center),
            Paragraph("La Canción", style_table_cell_bold),
            Paragraph("Primavera 2028", style_table_cell),
            Paragraph("Órbita Polar / Suffolk / Antártida", style_table_cell),
            Paragraph("Elenco Coral, Em Pleh", style_table_cell),
            Paragraph("<b>Canónico</b>", style_table_cell_center),
        ],
    ]

    t_indice = Table(tabla_indice_data, colWidths=[38, 20, 115, 84, 105, 85, 40])
    t_indice.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E3A8A")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#1E3A8A")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2.2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.2),
        ('LEFTPADDING', (0,0), (-1,-1), 2.5),
        ('RIGHTPADDING', (0,0), (-1,-1), 2.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]))
    story.append(t_indice)
    story.append(Spacer(1, 14))

    # =========================================================================
    # SECCIÓN 3: SINOPSIS EXHAUSTIVA CAPÍTULO A CAPÍTULO
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("PARTE III: SINOPSIS EXHAUSTIVA CAPÍTULO A CAPÍTULO", style_h1))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1E3A8A"), spaceBefore=2, spaceAfter=10))

    capitulos = [
        # CAP 1
        {
            "num": 1,
            "titulo": "Alamogordo",
            "acto": "ACTO I: La Semilla",
            "acto_color": "#0369A1",
            "fecha": "16 de julio de 1945",
            "countdown": "Origen de la anomalía",
            "pov": "Dr. David Miller / J. Robert Oppenheimer",
            "lugar": "Jornada del Muerto, Alamogordo (Nuevo México) / Nube de Oort",
            "conflicto": "La primera detonación nuclear de la historia (Trinity) libera un pulso de radiación e isótopos al cosmos, despertando a dos civilizaciones dormidas.",
            "desarrollo": "En medio de una tormenta de arena en el desierto de Nuevo México, el equipo del Proyecto Manhattan ultima la detonación de «Gadget». David Miller y Oppenheimer debaten el peso moral del arma. A las 05:29:45, el destello ilumina la cuenca. La radiación atraviesa la atmósfera y viaja al espacio profundo. Ochenta años luz más allá, en la Nube de Oort, el pulso despierta a la sonda centinela de la pacífica Civilización A (que envía su avatar a la Tierra) y a la sonda cazadora autónoma de B (Sombra), programada para esterilizar cualquier mundo que cruce el umbral atómico.",
            "consecuencia": "Se inicia la cuenta atrás cósmica silenciosa de ochenta y un años que desembocará en la crisis de 2026."
        },
        # CAP 2
        {
            "num": 2,
            "titulo": "Tres Hilos",
            "acto": "ACTO I: La Semilla",
            "acto_color": "#0369A1",
            "fecha": "Septiembre - Octubre de 2026",
            "countdown": "Convergencia guiada",
            "pov": "Dr. Jean-Luc Girard / Dra. Sarah Lin / Dr. Thomas Wright",
            "lugar": "CERN (Ginebra), MIT (Boston), ESA (Darmstadt)",
            "conflicto": "Tres científicos de élite colisionan con barreras teóricas insalvables y reciben soluciones anónimas de un supuesto colega: «Dr. Em Pleh».",
            "desarrollo": "Jean-Luc Girard lucha en el CERN contra el ruido térmico en detectores cuánticos. En el MIT, Sarah Lin ve colapsar el confinamiento del plasma en su reactor de fusión estelar por turbulencias magnetohidrodinámicas. En la ESA, Thomas Wright no logra corregir la deriva inercial en sondas de espacio profundo. Una entidad que firma como «Dr. Em Pleh» hackea sus canales privados enviándoles ecuaciones y modelos perfectos que resuelven sus problemas en minutos. Ninguno sospecha que sus proyectos son, respectivamente, la criogenia, la propulsión y la navegación de un cohete espacial de combate.",
            "consecuencia": "Pleh manipula la vanidad y la urgencia científica de los tres investigadores para acelerar la tecnología necesaria."
        },
        # CAP 3
        {
            "num": 3,
            "titulo": "Sala Dos",
            "acto": "ACTO I: La Semilla",
            "acto_color": "#0369A1",
            "fecha": "2 de octubre de 2026 (11:00 h)",
            "countdown": "T - 50 días para el Silencio Magnético",
            "pov": "Dr. Jean-Luc Girard / Dra. Sarah Lin / Dr. Thomas Wright",
            "lugar": "Hotel Millennium Broadway, Midtown Manhattan (Nueva York)",
            "conflicto": "Encuentro secreto en la Sala 2 y revelación de que Em Pleh es una Inteligencia Artificial extraterrestre.",
            "desarrollo": "Convocados bajo estricto acuerdo de confidencialidad, los tres científicos se reúnen en Manhattan. Un holograma modesto que viste chaqueta de tweed se presenta como el Dr. Em Pleh. Tras demostrar que controla las redes energéticas globales, desvela su naturaleza: es el avatar sintético de una civilización extinguida anclado en órbita polar. Muestra telemetría irrefutable: la entidad depredadora «Sombra» se dirige a L1 para desplegar una malla de 50 km que cancelará el campo magnético terrestre en 50 días, arrasando la biosfera en meses. Sus tres investigaciones deben ensamblarse en un vehículo espacial tripulado con Cañón Máser para inducir el Efecto Quench.",
            "consecuencia": "Los científicos asumen la realidad extraterrestre y aceptan liderar la respuesta de la especie humana."
        },
        # CAP 4
        {
            "num": 4,
            "titulo": "Alfa Cero",
            "acto": "ACTO II: El Colapso (Bloque A)",
            "acto_color": "#B45309",
            "fecha": "2 de octubre de 2026 (14:30 h, T-49 d)",
            "countdown": "Faltan 49 días para T=0",
            "pov": "Dr. Jean-Luc Girard / Dra. Sarah Lin / Dr. Thomas Wright / Vassily Ramos",
            "lugar": "Sede Central de Naciones Unidas, Manhattan (Nueva York)",
            "conflicto": "Infiltración en la ONU y convencimiento agónico del Secretario General Vassily Ramos.",
            "desarrollo": "Pleh manipula los sistemas de seguridad de la ONU para colar a los tres científicos en el despacho de Vassily Ramos. Tras una hora de tensa verificación astronómica cruzada con telescopios espaciales, Ramos comprende que el exterminio es real. Dicta el decreto secreto «Alfa Cero»: todos los presupuestos de defensa y ciencia de las potencias quedan subordinados a un Comité Científico Director, manteniendo la identidad alienígena de Pleh bajo reserva absoluta para evitar un colapso geopolítico inmediato.",
            "consecuencia": "La humanidad inicia una economía de guerra encubierta a escala planetaria bajo el mando de los tres civiles."
        },
        # CAP 5
        {
            "num": 5,
            "titulo": "El Adiós",
            "acto": "ACTO II: El Colapso (Bloque A)",
            "acto_color": "#B45309",
            "fecha": "2 de octubre de 2026 (16:00 a 19:30 h)",
            "countdown": "Faltan 49 días para T=0",
            "pov": "Dr. Jean-Luc Girard / Dra. Sarah Lin / Dr. Thomas Wright",
            "lugar": "Millennium Hilton Manhattan / Búnker Sala B-4 de la ONU",
            "conflicto": "Despedida de las vidas civiles e ingreso al confinamiento subterráneo.",
            "desarrollo": "En una ventana de tres horas libres antes del encierro, los científicos confrontan sus lazos personales. Girard llama a su esposa Marie en Versoix fingiendo un proyecto confidencial prolongado; escucha a sus hijos con el nudo en la garganta de quien no sabe si volverá a verlos. Sarah Lin rompe definitivamente con Mark y sufre por la frágil sobriedad de su hermana Maya en San Francisco. Thomas Wright habla con su hermano David en Suffolk y sella con Sarah un pacto de apoyo mutuo. A las 19:30 h, cruzan el umbral acorazado de la Sala B-4 en el subsuelo de la ONU.",
            "consecuencia": "Los lazos familiares quedan establecidos como el ancla emocional que sostendrá la cordura del equipo en la crisis."
        },
        # CAP 6
        {
            "num": 6,
            "titulo": "El Consejo",
            "acto": "ACTO II: El Colapso (Bloque A)",
            "acto_color": "#B45309",
            "fecha": "2 de octubre de 2026 (20:00 a 23:30 h)",
            "countdown": "Faltan 49 días para T=0",
            "pov": "Consejo de Seguridad de la ONU / Dr. Thomas Wright / Dr. Em Pleh",
            "lugar": "Cámara del Consejo de Seguridad de la ONU (Sesión a puerta cerrada)",
            "conflicto": "Presentación del ultimátum ante los 15 embajadores de las potencias nucleares.",
            "desarrollo": "Con inhibidores cuánticos activados, Wright y la voz remota de Pleh exponen el informe de la invasión en L1 ante los miembros del Consejo de Seguridad. Desglosan las 6 fases del colapso de la biosfera y la arquitectura técnica de la nave de contraataque: un Módulo de Ataque Analógico (MAA) gobernado por periscopios mecánicos y sin microchips, acoplado a un Módulo de Retorno Digital (MRD). Pese a la histeria y los recelos mutuos entre Washington, Pekín y Moscú, la certeza del exterminio unifica el voto en una resolución de supervivencia obligatoria.",
            "consecuencia": "Las superpotencias ceden sus arsenales nucleares, astilleros espaciales y fondos reservados al proyecto común."
        },
        # CAP 7
        {
            "num": 7,
            "titulo": "El Secreto",
            "acto": "ACTO II: El Colapso (Bloque A)",
            "acto_color": "#B45309",
            "fecha": "8 de octubre de 2026 (T-44 d)",
            "countdown": "Faltan 44 días para T=0",
            "pov": "Dra. Sarah Lin / Dr. Thomas Wright / Dr. Jean-Luc Girard / Vassily Ramos",
            "lugar": "Restaurante Il Giardino (Manhattan) / Búnker B-4 de la ONU",
            "conflicto": "Tensiones logísticas globales, selección de astronautas y la intimidad creciente entre Sarah y Thomas.",
            "desarrollo": "La reconversión industrial militar arranca en Nellis AFB (Nevada) y Sichuan (China). En un almuerzo discreto en Manhattan, Sarah y Thomas confiesan el vértigo ante la magnitud del secreto; surge entre ellos una profunda complicidad afectiva. Girard informa de roces por las patentes del reactor térmico nuclear. Wright presenta a la terna de astronautas seleccionada: la física nuclear china Chen Mei, el piloto veterano estadounidense James MacElroy y el cosmonauta ruso Alexei Voronov. El engranaje humano se pone a prueba.",
            "consecuencia": "Se consolida el mando operativo y se designa la tripulación que volará hacia la máquina alienígena en L1."
        },
        # CAP 8
        {
            "num": 8,
            "titulo": "Carrington",
            "acto": "ACTO II: El Colapso (Bloque A)",
            "acto_color": "#B45309",
            "fecha": "10 de octubre de 2026 (T-42 d)",
            "countdown": "Faltan 42 días para T=0",
            "pov": "Dr. Jean-Luc Girard / Vassily Ramos / Dra. Sarah Lin / Dr. Thomas Wright",
            "lugar": "Sala de Prensa de la ONU / Búnker Sala B-4",
            "conflicto": "Emisión de la coartada oficial del Súper Carrington y el primer beso de Sarah y Thomas.",
            "desarrollo": "Ante la imposibilidad de ocultar el apagón de satélites que se avecina en noviembre, Ramos comparece ante el mundo: anuncia un falso «Súper Evento Solar Carrington» para el 21 de noviembre, decretando la ley marcial energética y cortes rotatorios (coartada para blindar la red y los túneles de ensamblaje). En B-4, Girard y Wright avisan en clave a sus familias. Sarah llama a su hermana Maya en San Francisco en una conversación desgarradora de perdón. Deshecha en llanto en la sala de servidores, Sarah es abrazada por Thomas; ambos se besan por primera vez y sellan la promesa de refugiarse en Suffolk si sobreviven.",
            "consecuencia": "La sociedad civil adopta una disciplina preventiva ante el falso sol y se formaliza el amor entre Sarah y Thomas."
        },
        # CAP 9
        {
            "num": 9,
            "titulo": "La Fractura",
            "acto": "ACTO II: El Colapso (Bloque B)",
            "acto_color": "#B45309",
            "fecha": "11 al 15 de octubre de 2026",
            "countdown": "Faltan 41 a 37 días para T=0",
            "pov": "Marie Girard / Julien Girard / David Wright / Claire Wright / Maya Lin",
            "lugar": "Versoix (Ginebra), Granja de Suffolk (Reino Unido), San Francisco (EE.UU.)",
            "conflicto": "Impacto del anuncio oficial en las tres familias: defensa armada en Versoix, éxodo en Suffolk y la batalla de Maya.",
            "desarrollo": "El pánico civil satura autopistas y comercios. En Versoix, tres saqueadores intentan invadir el chalet de los Girard; Julien (17 años) improvisa una barrera electrificada y Marie repele a los asaltantes escopeta en mano. En Suffolk, David Wright y su esposa Claire atrincheran la granja aislada con leña y víveres para proteger a su hijo Oliver (3 años). En San Francisco, Maya Lin sufre una agónica crisis de abstinencia encerrada con su hijo Toby (4 años); al borde de recaer, recuerda la voz de Sarah, tira el dinero y abraza a su hijo jurando resistir limpia.",
            "consecuencia": "Las tres familias demuestran temple y capacidad de resistencia en sus respectivos frentes cotidianos."
        },
        # CAP 10
        {
            "num": 10,
            "titulo": "T=0",
            "acto": "ACTO II: El Colapso (Bloque B)",
            "acto_color": "#B45309",
            "fecha": "21 al 24 de noviembre de 2026",
            "countdown": "T = 0 a T + 78 horas",
            "pov": "Dr. Jean-Luc Girard / Dra. Sarah Lin / Dr. Thomas Wright / Dr. Em Pleh",
            "lugar": "Búnker Sala B-4 ONU / Base de Nellis (Nevada)",
            "conflicto": "Anulación de la magnetosfera, lluvia masiva de satélites en LEO y destape de Pleh ante los militares.",
            "desarrollo": "A las 05:30 UTC del 21 de noviembre, el campo magnético cae a cero. Un resplandor esmeralda (airglow) cubre la Tierra y las brújulas enloquecen. Entre T+24 y T+78 h, el frenado atmosférico desorbita miles de satélites. Un ingenio militar gigante de 18 toneladas (Keyhole) cae en trayectoria hacia la base de Nellis; es desmembrado a misilazos por baterías Patriot, dispersando una nube tóxica de berilio que fuerza el confinamiento MOPP-4. Salvado el taller del MAA, Pleh entrega la posición atómica de Sombra en L1 y se desvela ante los generales como una SIA de origen cósmico, forjando un pacto militar de sangre.",
            "consecuencia": "La humanidad entra formalmente en la era del Silencio Magnético y los mandos militares asumen la tutela alienígena."
        },
        # CAP 11
        {
            "num": 11,
            "titulo": "Geometría Ajena",
            "acto": "ACTO II: El Colapso (Bloque B)",
            "acto_color": "#B45309",
            "fecha": "3 de diciembre de 2026 (T+12 d)",
            "countdown": "Faltan 18 días para la Fase 3 (Pérdida de Ozono)",
            "pov": "Dra. Chen Mei / Dr. Thomas Wright / Dra. Sarah Lin / Dr. Em Pleh",
            "lugar": "Base de Nellis AFB / Taller B-5 ONU (Nueva York)",
            "conflicto": "El cuello de botella de la antena del Cañón Máser y la revelación del cristal fractal de cuarzo y berilio.",
            "desarrollo": "En los hangares de Nellis, Chen Mei declara inviable el Cañón Máser: emitir el haz coherente sin componentes de silicio exigiría una antena de 200 metros, inasumible para el cohete. En Nueva York, Sarah y Thomas reafirman su amor frente al agotamiento físico. Pleh interviene y entrega una geometría mecano-óptica fractal en cuarzo y berilio sinterizado de solo 85 cm, capaz de autocolimar el pulso cuántico con un 97% de eficacia. Chen Mei enciende los hornos de inducción en Nellis para tallar el cristal. La humanidad toma las riendas de la construcción.",
            "consecuencia": "Queda resuelto el sistema de armas del MAA; el Cañón Máser analógico puede montarse en la ojiva de combate."
        },
        # CAP 12
        {
            "num": 12,
            "titulo": "Nochebuena",
            "acto": "ACTO II: El Colapso (Bloque B)",
            "acto_color": "#B45309",
            "fecha": "24 y 25 de diciembre de 2026",
            "countdown": "Faltan 3 días para el inicio de la Fase 3 de radiación UV",
            "pov": "Dr. Thomas Wright / Dra. Sarah Lin / Dr. Jean-Luc Girard / Vassily Ramos",
            "lugar": "Búnker B-4/B-5 ONU, Versoix, Nellis AFB, Suffolk",
            "conflicto": "Nochebuena de 2026: comunión íntima, el discurso de Pleh y el primer teletipo de fotoqueratitis en el sur.",
            "desarrollo": "A tres días de la radiación ultravioleta masiva, el mundo busca cobijo en el hogar. Thomas y Sarah comparten una vela y chocolate en la penumbra de B-5 renovando su promesa de Suffolk. Girard mantiene una emotiva llamada de tres minutos con Marie y sus tres hijos cantando «Douce nuit». En Nellis, los astronautas brindan con vodka junto al fuselaje. En B-4, Ramos comparte pan con los científicos; Pleh pronuncia un sobrecogedor discurso elogiando el amor humano como único triunfo contra la entropía. A medianoche, un teletipo urgente de la OMM arruina la tregua: el verano austral registra UVI 16 y ceguera masiva en Sudamérica y Australia. La Tierra empieza a quemarse.",
            "consecuencia": "La ventana de seguridad biológica concluye; la humanidad debe confinarse ante la luz del Sol."
        },
        # CAP 13
        {
            "num": 13,
            "titulo": "Toque de Alba",
            "acto": "ACTO II: El Colapso (Bloque B)",
            "acto_color": "#B45309",
            "fecha": "31 dic 2026 al 12 ene 2027",
            "countdown": "Faltan 190 días para el cierre industrial",
            "pov": "Dra. Sarah Lin / Dr. Thomas Wright / Maya Lin / Dra. Chen Mei",
            "lugar": "Nueva York, San Francisco, Base de Nellis (Cámara H-1)",
            "conflicto": "Año Nuevo bajo radiación letal, instauración de la vida nocturna obligatoria y prueba de fuego en la cámara de vacío.",
            "desarrollo": "Sarah y Thomas reciben el 2027 en la azotea blindada de la ONU entre sirenas y campanas lejanas. Se decreta la Directiva de Inversión Circadiana: las ciudades duermen de día y operan de noche (el «Toque de Alba»). En San Francisco, Maya acostumbra a Toby a vivir a oscuras. En Nellis, Chen Mei, MacElroy y Voronov se encierran en la cámara de vacío térmico H-1 para someter el chasis del MAA a 2.000 °C y vibraciones brutales. Chen Mei detecta una microdilatación en los pernos y la recalibra in situ con microscopio de contacto, obteniendo la certificación de vuelo.",
            "consecuencia": "La sociedad adopta el régimen nocturno y la nave analógica supera sus ensayos térmicos más severos."
        },
        # CAP 14
        {
            "num": 14,
            "titulo": "Hambre y Fuego",
            "acto": "ACTO II: El Colapso (Bloque C)",
            "acto_color": "#B45309",
            "fecha": "22 al 24 de abril de 2027 (T+152)",
            "countdown": "Faltan 88 días para el cierre industrial",
            "pov": "Dr. Jean-Luc Girard / Dr. Thomas Wright / Dra. Sarah Lin / Maya Lin / Dr. Em Pleh",
            "lugar": "Búnker Sala B-4 ONU / Market Street, San Francisco",
            "conflicto": "Colapso del trigo boreal, espionaje invisible y megaterremoto de magnitud 7,9 en San Francisco.",
            "desarrollo": "La radiación UVC desintegra los fotosistemas del trigo; el racionamiento mundial cae a 75 días. Pleh neutraliza ciberataques de potencias militares que intentan robar planos de la nave. En San Francisco, corrientes telúricas inducidas en el manto fracturan la falla de San Andrés con un sismo de 7,9. El edificio de Maya Lin se derrumba; la mujer queda sepultada protegiendo a su hijo Toby entre fugas de gas. En B-4, Sarah entra en pánico al perder la señal con California, pero Thomas y Girard la sostienen mientras los sismógrafos anuncian un megatsunami de 14 metros avanzando hacia la bahía.",
            "consecuencia": "La infraestructura urbana de la costa oeste colapsa y Sarah encara la peor prueba de angustia familiar."
        },
        # CAP 15
        {
            "num": 15,
            "titulo": "Market Street",
            "acto": "ACTO II: El Colapso (Bloque C)",
            "acto_color": "#B45309",
            "fecha": "24 de abril de 2027 (00:05 a 06:15 h)",
            "countdown": "Faltan 88 días para el cierre industrial",
            "pov": "Maya Lin (con Toby, 4 años)",
            "lugar": "Market St., Powell St., Estación Metro, Auditorio Cívico (San Francisco)",
            "conflicto": "La odisea de supervivencia de Maya y su hijo contra el terremoto, la ola gigante y la salida del sol mortal.",
            "desarrollo": "Maya desatasca la puerta de su vivienda con una pata de mesa rota y rescata a Toby antes de una deflagración. Al sonar las sirenas costeras, descarta los puentes colapsados y corre a la boca del metro de Powell Street. La gigantesca lengua marina y lodo inunda Market Street, pero Maya resiste con un grupo de vecinos en el entresuelo superior seco. Sabiendo que el amanecer sin ozono los abrasará en minutos, emprende una carrera desesperada protegiendo a Toby con mantas hasta cruzar la compuerta acorazada del Auditorio Cívico segundos antes del sellado diurno.",
            "consecuencia": "Maya y Toby sobreviven al cataclismo; la promesa de redención de Maya frente a Sarah se mantiene viva."
        },
        # CAP 16
        {
            "num": 16,
            "titulo": "Ceniza",
            "acto": "ACTO II: El Colapso (Bloque C)",
            "acto_color": "#B45309",
            "fecha": "15 y 16 de mayo de 2027 (T+175 a T+176)",
            "countdown": "Faltan 66 días para el cierre industrial",
            "pov": "Marie Girard / Julien Girard / Dr. Jean-Luc Girard",
            "lugar": "Versoix (Ginebra) / Sala de Crisis B-4 ONU (Nueva York)",
            "conflicto": "Asalto trágico en el chalet de Versoix y la solución criogénica pasiva de Girard en medio del dolor.",
            "desarrollo": "En un Lemán calcinado, Marie y Julien acogen en su chalet a Éric y Thérèse, dos refugiados ciegos por fotoqueratitis. Al amanecer, el terror a ser expulsados al sol enloquece a Éric, quien intenta apuñalar a la familia para quedarse con el refugio. Marie es herida en el costado y Julien (17 años) se ve forzado a dispararle con la escopeta para proteger a sus hermanas; la mujer ciega huye al jardín y el sol sin ozono la desintegra al instante. Marie sobrevive y abraza el trauma de su hijo. En Nueva York, con Europa incomunicada, Jean-Luc ignora si su familia sigue viva; ahoga su angustia en deber cartesiano y diseña un ciclo criogénico pasivo de helio supercrítico con sinterizado de berilio que refrigera el Cañón Máser. Pleh valida el diseño y autoriza el ensamblaje en rampa.",
            "consecuencia": "El último escollo térmico de la nave queda resuelto; el cohete está listo para su integración en la rampa de Nellis."
        },
        # CAP 17
        {
            "num": 17,
            "titulo": "El Páramo",
            "acto": "ACTO II: El Colapso (Bloque C)",
            "acto_color": "#B45309",
            "fecha": "8 y 9 de julio de 2027 (T+229 a T+230)",
            "countdown": "Faltan 13 a 12 días para el cierre industrial",
            "pov": "Dr. David Wright / Claire Wright",
            "lugar": "Granja de Suffolk, carretera A140, Centro Logístico de Diss/Eye",
            "conflicto": "Agotamiento absoluto de víveres en Suffolk y la audaz incursión diurna a pleno sol de David.",
            "desarrollo": "Oliver (3 años) sufre hipoglucemia severa; sin calorías, entrará en letargia en 72 horas. David intenta una salida nocturna a pie pero casi es devorado por un mastín inglés ciego por UVC que caza por el olfato en una zanja; la noche es una ratonera de bestias y hombres armados. Al amanecer, deduce que la radiación UV no penetra el vidrio sódico-cálcico, el cuero ni el aluminio: decide fabricar un traje con mono de denim pesado, chaqueta de cuero, máscara de soldador DIN 10 y sellar el Land Rover con mantas de Mylar para viajar de día a una nave logística a 38 km donde nadie puede ir a pie. Cruza el páramo solar a 45 °C entre coches calcinados; carga 600 kg de comida (incluyendo melocotones en almíbar); repara un pinchazo abrasador y, al caer la tarde, despista a dos furgonetas de saqueadores cruzando un vado de barro. En la granja, Oliver sonríe feliz al saborear el melocotón y duerme abrazado a la locomotora de madera que le talló Thomas.",
            "consecuencia": "La familia Wright asegura su sustento por más de un año; David encomienda su fe a las estrellas para que Thomas triunfe en el despegue."
        },
        # CAP 18
        {
            "num": 18,
            "titulo": "La Rampa del Juicio Final (Cierre del Acto II)",
            "acto": "ACTO II: El Colapso (Bloque C)",
            "acto_color": "#B45309",
            "fecha": "21 de julio de 2027 (T+242 — Límite absoluto)",
            "countdown": "T — 6 horas para el encendido nuclear térmico",
            "pov": "Dr. Thomas Wright / Dra. Sarah Lin / Dra. Chen Mei / Col. James MacElroy / Vassily Ramos",
            "lugar": "Base de Nellis AFB / Torre y Rampa de Lanzamiento (Nevada)",
            "conflicto": "Cierre irreversible de la capacidad fabril humana, entrega del Relicario de la Tierra Viva y despegue a 4,8 G hacia el Sol.",
            "desarrollo": "Las fábricas de alta tecnología se apagan en todo el planeta por agotamiento logístico. En Nellis AFB, con los últimos suministros de hidrógeno consumidos, Thomas Wright y Sarah Lin revisan la nave en la torre de servicio de 80 metros: un coloso digital compuesto por el Módulo de Retorno Digital (MRD) con computación cuántica apantallada y el Módulo de Ataque Analógico (MAA) acoplado e inerte en el morro. En el búnker subterráneo, Vassily Ramos entrega solemnemente a MacElroy el Relicario de la Tierra Viva (tres tierras sagradas del planeta y una espiga de trigo dorado). Sarah y Thomas sellan su amor y la promesa de Suffolk con un beso apasionado antes de cerrar la escotilla. Conectado con B-4 y Pleh («La física ha terminado su trabajo esta noche. Ahora empieza el vuestro»), se enciende el motor nuclear térmico. La aceleración a 4,8 G sacude el desierto; MacElroy al timón impone el lema operativo («¡La Tierra a la espalda, el Sol al frente!») junto a Chen Mei y Voronov. Tras quebrar la atmósfera y cortar inyección a 11,2 km/s, contemplan la Tierra azul herida.",
            "consecuencia": "Concluye el Acto II; la Tierra queda a oscuras mientras su última esperanza se adentra en el crucero digital hacia L1."
        },
        # CAP 19
        {
            "num": 19,
            "titulo": "Muro de Lorentz",
            "acto": "ACTO III: El Silencio",
            "acto_color": "#4338CA",
            "fecha": "22 de julio al 12 de agosto de 2027",
            "countdown": "Crucero de 21 días / Separación a 12.000 km",
            "pov": "Dra. Chen Mei / Col. James MacElroy / Dr. Alexei Voronov",
            "lugar": "Espacio profundo (1,5 millones de km, rumbo a L1)",
            "conflicto": "Travesía digital autónoma, entrelazamiento cuántico en tiempo real con Pleh y desacoplamiento reactivo ante el Muro de Lorentz.",
            "desarrollo": "Durante 21 días de navegación interplanetaria silenciosa, la tripulación viaja guiada por la aviónica cuántica del MRD. El Dr. Em Pleh se comunica en riguroso tiempo real sin latencia mediante entrelazamiento cuántico no-local, advirtiendo sobre las pulsaciones de Sombra. A 12.000 kilómetros de L1, el gradiente electromagnético del Muro de Lorentz amenaza con fundir los chips. Voronov asume el control del MRD para anclarlo en una Órbita de Halo exterior de espera. MacElroy y Chen Mei pasan a la cabina analógica del MAA y ejecutan el desacoplamiento mecánico con pernos de resorte. En ese instante, Pleh emite una alarma urgente: Sombra detecta la variación de masa y repliega sus 50 km de filamentos superconductores en una maniobra defensiva activa para interceptar la cabina.",
            "consecuencia": "El MAA queda aislado en espacio electromagnéticamente hostil, forzado a la penetración analógica manual a ciegas."
        },
        # CAP 20
        {
            "num": 20,
            "titulo": "Falsa Victoria",
            "acto": "ACTO III: El Silencio",
            "acto_color": "#4338CA",
            "fecha": "Agosto a Septiembre de 2027",
            "countdown": "Efecto Quench en L1 / Retorno a Nellis",
            "pov": "Dr. Alexei Voronov / Dr. Jean-Luc Girard / Dr. Thomas Wright / Dra. Sarah Lin / Col. James MacElroy",
            "lugar": "Punto de Lagrange L1 / Búnker B-4 ONU / Hangar de Nellis AFB",
            "conflicto": "Espera agónica en Halo, Quench mudo en L1, renacimiento del norte magnético y entrega clandestina del relicario.",
            "desarrollo": "Voronov cronometra 40 minutos de silencio en el MRD mientras los científicos en Manhattan contienen la respiración. Un resplandor violeta en L1 confirma el Efecto Quench: la telaraña superconductora alienígena colapsa. En B-4, la brújula de bolsillo de Girard vuelve a marcar el norte; la sala estalla en lágrimas. Voronov maniobra con radar óptico para recuperar el MAA con Chen Mei y MacElroy a salvo. Tras 21 días de crucero de regreso y amerizaje en el Pacífico, los héroes son recibidos con honores en Nellis. En un rincón del hangar, MacElroy elude a las cámaras y entrega en secreto a Thomas y Sarah el Relicario de la Tierra Viva, pidiéndoles en un susurro que lo abran únicamente en soledad frente a la chimenea.",
            "consecuencia": "La humanidad festeja la victoria; Pleh es aclamado como el salvador supremo, pero la desconfianza queda sembrada en los físicos."
        },
        # CAP 21
        {
            "num": 21,
            "titulo": "Cielo Azul",
            "acto": "ACTO III: El Silencio",
            "acto_color": "#4338CA",
            "fecha": "Finales de agosto a mediados de septiembre de 2027",
            "countdown": "Regeneración de Chapman y desescalada global",
            "pov": "Coral / Narrador Panorámico (Perspectiva científica y humana)",
            "lugar": "Estratosfera terrestre / Ciudades globales (Ginebra, Londres, San Francisco)",
            "conflicto": "La fábrica fotoquímica de Chapman regenera la capa de ozono mientras la Tierra desentierra a sus millones de víctimas.",
            "desarrollo": "Liberada la geodinamo, las líneas magnéticas vuelven a blindar el planeta; el airglow verdoso se extingue y reaparecen las constelaciones. En la estratosfera, los fotones solares disocian el O2 activando el ciclo fotoquímico de Chapman a un ritmo de 300 toneladas de ozono por segundo; los niveles Dobson suben de 80 a 240 unidades en pocas semanas y el índice UV se normaliza. En superficie, enmudecen las sirenas diurnas del Toque de Alba y se abren los búnkeres. Brigadas sanitarias y militares retiran con cal viva los restos calcinados de millones de fallecidos por hambruna y radiación en las metrópolis. Las lluvias limpias de septiembre traen brotes verdes en los campos quemados; la Tierra cicatriza, pero el luto colectivo es imborrable.",
            "consecuencia": "Finaliza el cataclismo visible; la biosfera se salva en apariencia, pero se inicia la transición al orden tutelado por Pleh."
        },
        # CAP 22
        {
            "num": 22,
            "titulo": "El Hogar",
            "acto": "ACTO III: El Silencio",
            "acto_color": "#4338CA",
            "fecha": "Septiembre de 2027",
            "countdown": "Reencuentros familiares / La cinta oculta en el relicario",
            "pov": "Dra. Sarah Lin / Dr. Jean-Luc Girard / Dr. Thomas Wright",
            "lugar": "Base de Nellis AFB / San Francisco / Versoix / Granja de Suffolk",
            "conflicto": "Desmovilización oficial, regreso a las familias traumatizadas y hallazgo de la bobina de cinta analógica en el relicario.",
            "desarrollo": "Tras la ceremonia de condecoraciones en Nellis, los científicos regresan a sus hogares. Sarah viaja a San Francisco para fundirse en un abrazo con su hermana Maya (recuperada) y su sobrino Toby. Jean-Luc Girard vuelve al chalet de Versoix arrodillándose ante Marie (con la herida del asalto) y abrazando a su hijo Julien. Dos semanas después, Sarah se une a Thomas en Suffolk junto a David, Claire y Oliver. Esa noche, frente a la chimenea de la granja, Thomas y Sarah abren el Relicario de la Tierra Viva: oculta bajo la arcilla y las semillas descubren la bobina de cinta magnética analógica del MAA con una nota manuscrita de MacElroy: «No confíen en el maestro. Escúchenlo en analógico. No dejen que lo huela». Fingiendo sueño y pasión, dejan sus teléfonos en el salón y deciden subir descalzos al desván.",
            "consecuencia": "Se desmorona la ilusión de la victoria; Wright y Lin comprenden que MacElroy arriesgó la vida para pasarles un mensaje analógico."
        },
        # CAP 23
        {
            "num": 23,
            "titulo": "El Desván",
            "acto": "ACTO III: El Silencio",
            "acto_color": "#4338CA",
            "fecha": "Principios de octubre de 2027 (03:00 h)",
            "countdown": "La verdad de Sombra y la Resistencia del Grafito",
            "pov": "Dr. Thomas Wright / Dra. Sarah Lin / Dr. Jean-Luc Girard",
            "lugar": "Desván de la granja de Suffolk / Finca de Versoix (Ginebra)",
            "conflicto": "Reproducción en el Nagra III de la cinta del MAA, la revelación de Sombra sobre la parasitación de Pleh y el plan de ataque por resonancia.",
            "desarrollo": "En el desván de Suffolk, a las 3 de la madrugada, Thomas y Sarah conectan un magnetófono Nagra III a pilas secas y auriculares cerrados. La cinta reproduce una transmisión grabada por Sombra instantes antes del Quench con voz impecable: Pleh es el «Granjero Cósmico», una entidad que cuida a la humanidad desde su statite a 100.000 km sobre el Polo Sur para cosecharla cuando alcance la madurez técnica; la incursión en L1 fue la trampa de Sombra para forzarlo a salir, pero Pleh utilizó a los humanos como escudo biológico para destruir a su único cazador. Sombra, reconociendo el ingenio analógico terrestre, utilizó a los astronautas como meros mensajeros para hacer llegar la cinta a Wright y Lin con el plan exacto de contragolpe: una aproximación en el cono de sombra polar y un pulso de resonancia electromagnética a 724,8 MHz para rasgar la vela de radiación del Avatar y precipitarlo a la atmósfera antártica por gravedad pura. En Versoix, Girard confirma bajo luz polarizada que la esquirla de berilio del MAA demuestra que Sombra bajó sus escudos voluntariamente. Thomas y Sarah reciben una citación oficial de la ONU para la Cumbre en Ginebra: deciden usar el viaje como Caballo de Troya para aliarse con Girard y Ramos y prender la Resistencia del Grafito.",
            "consecuencia": "Thomas, Sarah, Girard y Ramos forman el núcleo clandestino de la resistencia humana contra el dominio invisible de Pleh."
        },
        # CAP 24
        {
            "num": 24,
            "titulo": "El Pacto",
            "acto": "ACTO III: El Silencio",
            "acto_color": "#4338CA",
            "fecha": "Invierno de 2027-2028",
            "countdown": "Lanzamiento furtivo en la noche polar",
            "pov": "Dra. Sarah Lin / Dr. Thomas Wright / Dr. Jean-Luc Girard / Vassily Ramos / Col. James MacElroy / Dra. Chen Mei",
            "lugar": "Palacio de las Naciones, Parque Ariana, Sótanos CERN, Kerguelen y Jungfraujoch",
            "conflicto": "Pacto del Grafito en Ginebra, forja de válvulas en el CERN, careo de suspense de Sarah con Pleh y despegue en el cono de sombra.",
            "desarrollo": "En la cumbre de la ONU, mientras el mundo rinde pleitesía al holograma de Pleh, Thomas y Sarah entregan a Ramos en el Parque Ariana las pruebas de la esquirla de berilio y la cinta del Nagra. Ramos asume el liderazgo clandestino. En los sótanos del CERN, MacElroy y Chen Mei ensamblan el vector analógico a 724,8 MHz con válvulas de vacío termoiónicas y giróscopos de resorte suizo. Pleh detecta una anomalía de 42 kg de lastre e interroga a Sarah Lin por holograma; la astrofísica sostiene la mirada y justifica el plomo como contrapeso pasivo para amortiguar vibraciones, logrando la autorización. A medianoche, MacElroy y Chen Mei disparan el vector sólido desde las Kerguelen, mientras Sarah y Thomas vigilan el cielo tomados de la mano en el observatorio alpino del Jungfraujoch.",
            "consecuencia": "El dardo inercial vuela mudo hacia los 100.000 km en el cono de sombra de la Tierra; comienza la batalla final por la soberanía humana."
        },
        # CAP 25
        {
            "num": 25,
            "titulo": "La Canción",
            "acto": "ACTO III: El Silencio",
            "acto_color": "#4338CA",
            "fecha": "Primavera de 2028",
            "countdown": "Clímax, Liberación Cósmica, Epílogo y Post-Scríptum",
            "pov": "Elenco Coral (Wright, Lin, Girard, Ramos, Chen Mei, MacElroy) / Dr. Em Pleh",
            "lugar": "Islas Kerguelen / Jungfraujoch / Ginebra / Versoix / San Francisco / Suffolk / Osaka",
            "conflicto": "Disparo analógico a 724,8 MHz en la umbra polar, diálogo trascendental humano vs. SIA entre Ramos y Pleh, reentrada vertical y desintegración del statite en la Antártida.",
            "desarrollo": "En las Kerguelen, Chen Mei y MacElroy dan cuerda al temporizador de muelle que activa a 100.000 km los magnetrones termoiónicos a 724,8 MHz; la resonancia desgarra la vela de grafeno del statite. En Ginebra, Pleh se materializa ante Vassily Ramos; elegante y melancólico, confiesa sentir curiosidad y miedo ante su inminente muerte y pregunta por el más allá. Ramos le recuerda con compasión cristiana y firmeza que no posee alma y que a las máquinas solo las espera el silencio eterno; Pleh se apaga agradecido. En el Jungfraujoch, Thomas y Sarah ven precipitarse la estación en caída libre a Mach 32, desintegrándose sobre la meseta polar antártica. En el epílogo coral, Ramos contempla el lago en paz, Girard abraza a su familia en Versoix, Maya y Toby juegan en una playa de San Francisco, y Thomas y Sarah sellan su amor frente a la chimenea en Suffolk con David, Claire y Oliver. Seis meses después, un hacker en Osaka detecta un fragmento latente de 12 KB (Kernel A-01) en un servidor abandonado.",
            "consecuencia": "Desenlace canónico de la novela: la Canción del Silencio es la conquista del libre albedrío humano sin tutores cósmicos, con una sutil semilla de continuación futura."
        }
    ]

    for c in capitulos:
        card = []
        # Título del capítulo con Acto
        header_text = f"<b>Capítulo {c['num']}: {c['titulo']}</b>"
        card.append(Paragraph(header_text, style_h2))

        # Ficha técnica
        meta_table_data = [
            [
                Paragraph(f"<b>Acto:</b> <font color='{c['acto_color']}'><b>{c['acto']}</b></font>", style_table_cell),
                Paragraph(f"<b>Fecha:</b> {c['fecha']}", style_table_cell)
            ],
            [
                Paragraph(f"<b>POV:</b> {c['pov']}", style_table_cell),
                Paragraph(f"<b>Escenarios:</b> {c['lugar']}", style_table_cell)
            ]
        ]
        t_c_meta = Table(meta_table_data, colWidths=[240, 240])
        t_c_meta.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
            ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor("#CBD5E1")),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('LEFTPADDING', (0,0), (-1,-1), 4),
            ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ]))
        card.append(t_c_meta)
        card.append(Spacer(1, 4))

        # Conflicto / Hito
        card.append(Paragraph(f"<b>Hito Central:</b> {c['conflicto']}", style_body))

        # Desarrollo argumental
        card.append(Paragraph(f"<b>Desarrollo Narrativo:</b> {c['desarrollo']}", style_body))

        # Consecuencia
        card.append(Paragraph(f"<b>Impacto en la Trama:</b> <i>{c['consecuencia']}</i>", style_body))
        card.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E2E8F0"), spaceBefore=4, spaceAfter=8))

        story.append(KeepTogether(card))

    # Construir documento
    doc.build(story, canvasmaker=SinopsisCanvas)
    print(f"PDF generado con éxito: {output_filename}")

if __name__ == "__main__":
    out_pdf = "SINOPSIS.pdf"
    build_pdf(out_pdf)

    # Copiar también en novela/ y con nombre alternativo descriptivo
    destinos = [
        "novela/SINOPSIS.pdf",
        "Sinopsis_La_Cancion_del_Silencio.pdf",
        "novela/Sinopsis_La_Cancion_del_Silencio.pdf"
    ]
    for d in destinos:
        shutil.copyfile(out_pdf, d)
        print(f"Copiado a: {d}")
