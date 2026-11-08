import os
import re
import shutil
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

PAGE_WIDTH = A4[0]
PAGE_HEIGHT = A4[1]
USABLE_WIDTH = PAGE_WIDTH - 108  # 487.27 pt (54 pt margins)

class LocationsCanvas(canvas.Canvas):
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
        self.setFont("Helvetica-Bold", 7.5)
        self.setFillColor(colors.HexColor("#0369A1"))  # Azul zafiro / cartográfico
        
        # Encabezado (páginas > 1)
        if self._pageNumber > 1:
            self.drawString(54, PAGE_HEIGHT - 36, "SOMBRA • ATLAS Y CÓDEX DE LOCALIZACIONES")
            self.setFont("Helvetica", 7.5)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawRightString(PAGE_WIDTH - 54, PAGE_HEIGHT - 36, "ESCENARIOS, TEATROS DE OPERACIONES Y BASTIONES")
            self.setStrokeColor(colors.HexColor("#0EA5E9"))
            self.setLineWidth(0.75)
            self.line(54, PAGE_HEIGHT - 40, PAGE_WIDTH - 54, PAGE_HEIGHT - 40)
        
        # Pie de página
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(54, 45, PAGE_WIDTH - 54, 45)
        
        self.setFont("Helvetica", 7.8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(54, 32, "Atlas Canónico de Localizaciones • La Guerra de la Herencia")
        page_str = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(PAGE_WIDTH - 54, 32, page_str)
        self.restoreState()

def strip_emojis(text):
    """Elimina emojis y selectores de variación que no existen en fuentes Type1 estándar."""
    pattern = re.compile(
        r'[\U00010000-\U0010ffff]'
        r'|[\u2600-\u27bf]'
        r'|[\u2300-\u23ff]'
        r'|[\u2b50-\u2b55]'
        r'|[\ufe00-\ufe0f]'
        r'|[\u200d]'
    )
    cleaned = pattern.sub('', text)
    # Limpieza de caracteres tipográficos conflictivos
    cleaned = cleaned.replace("«", '"').replace("»", '"')
    cleaned = cleaned.replace("“", '"').replace("”", '"')
    cleaned = cleaned.replace("‘", "'").replace("’", "'")
    cleaned = cleaned.replace("—", " - ")
    cleaned = cleaned.replace("•", " - ")
    return cleaned.strip()

def format_inline_markdown(text):
    """Convierte negritas y cursivas en etiquetas compatibles con ReportLab."""
    text = strip_emojis(text)
    # Reemplazo de markdown
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    return text

def parse_locations_markdown(filepath):
    """Lee y estructura el archivo localizaciones.md por esferas, fichas y tabla sinóptica."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    
    sections = []
    current_sphere = None
    current_loc = None
    table_lines = []
    in_table = False
    
    for line in lines:
        stripped = line.strip()
        
        # Detectar tabla sinóptica al final
        if stripped.startswith('| Cap.') or stripped.startswith('| :---:'):
            in_table = True
            table_lines.append(stripped)
            continue
        elif in_table:
            if stripped.startswith('|'):
                table_lines.append(stripped)
                continue
            else:
                in_table = False

        # Detectar esferas (## ESFERA X: ...)
        if stripped.startswith('## '):
            if current_loc and current_sphere:
                current_sphere['locations'].append(current_loc)
                current_loc = None
            if current_sphere:
                sections.append(current_sphere)
            
            title = stripped[3:].strip()
            if 'MATRIZ SINÓPTICA' in title.upper():
                current_sphere = None
                continue
                
            current_sphere = {
                'title': title,
                'locations': []
            }
            continue
            
        # Detectar fichas de localizaciones (### 1. ...)
        if stripped.startswith('### ') and current_sphere:
            sub_title = stripped[4:].strip()
            if current_loc:
                current_sphere['locations'].append(current_loc)
                current_loc = None
            
            current_loc = {
                'name': sub_title,
                'items': []
            }
            continue
            
        # Líneas de propiedades o listas
        if stripped.startswith('- ') or stripped.startswith('* '):
            if current_loc:
                current_loc['items'].append(stripped[2:].strip())
            continue
        elif stripped.startswith('  - ') or stripped.startswith('  * '):
            if current_loc:
                current_loc['items'].append('    ' + stripped[4:].strip())
            continue
        elif stripped and not stripped.startswith('#') and not stripped.startswith('---') and not stripped.startswith('>'):
            if current_loc:
                current_loc['items'].append(stripped)
                
    if current_loc and current_sphere:
        current_sphere['locations'].append(current_loc)
    if current_sphere:
        sections.append(current_sphere)
        
    return sections, table_lines

def generate_pdf():
    input_file = os.path.join("novela", "localizaciones.md")
    output_filename = "Localizaciones_La_Cancion_del_Silencio.pdf"
    
    sections, table_lines = parse_locations_markdown(input_file)
    
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'MainTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=4
    )
    
    sub_title_style = ParagraphStyle(
        'MainSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#0284C7"),
        spaceAfter=15,
        textTransform='uppercase'
    )
    
    intro_style = ParagraphStyle(
        'IntroText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9.2,
        leading=13.5,
        textColor=colors.HexColor("#334155")
    )
    
    sphere_heading_style = ParagraphStyle(
        'SphereHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12.5,
        leading=16.5,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )
    
    loc_name_style = ParagraphStyle(
        'LocName',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=13.5,
        textColor=colors.HexColor("#0369A1"),
        spaceBefore=7,
        spaceAfter=3,
        keepWithNext=True
    )
    
    prop_key_style = ParagraphStyle(
        'PropText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.8,
        leading=12.5,
        textColor=colors.HexColor("#1E293B"),
        spaceAfter=3
    )
    
    subprop_style = ParagraphStyle(
        'SubPropText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.4,
        leading=11.8,
        textColor=colors.HexColor("#334155"),
        leftIndent=14,
        spaceAfter=2
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.2,
        leading=10.5,
        textColor=colors.HexColor("#FFFFFF"),
        alignment=1  # Centrado
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.8,
        leading=10.5,
        textColor=colors.HexColor("#1E293B")
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.8,
        leading=10.5,
        textColor=colors.HexColor("#0F172A"),
        alignment=1
    )

    story = []
    
    # Portada / Cabecera
    story.append(Paragraph("ATLAS DE LOCALIZACIONES", title_style))
    story.append(Paragraph("SOMBRA • LA GUERRA DE LA HERENCIA", sub_title_style))
    
    # Cuadro de introducción
    intro_p = Paragraph(
        "<b>Atlas Cartográfico y Códex de Escenarios:</b> Registro canónico de todos los "
        "enclaves cósmicos, sedes de mando supremo, laboratorios originarios, bastiones industriales de guerra "
        "y hogares civiles de la retaguardia que articulan los acontecimientos de la novela, "
        "estructurados por esferas operacionales y niveles de intervención estratégica.",
        intro_style
    )
    intro_table = Table([[intro_p]], colWidths=[USABLE_WIDTH])
    intro_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('LINEBEFORE', (0, 0), (0, -1), 3, colors.HexColor("#0284C7")),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
    ]))
    story.append(intro_table)
    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1"), spaceBefore=2, spaceAfter=10))

    # Paleta de colores para las esferas
    sphere_colors = {
        "ESFERA 1": colors.HexColor("#7C3AED"), # Violeta cósmico / espacio profundo
        "ESFERA 2": colors.HexColor("#0284C7"), # Azul ONU / político
        "ESFERA 3": colors.HexColor("#0D9488"), # Verde azulado científico
        "ESFERA 4": colors.HexColor("#D97706"), # Ámbar militar / defensivo
        "ESFERA 5": colors.HexColor("#059669"), # Esmeralda familiar / civil
        "ESFERA 6": colors.HexColor("#DC2626"), # Rojo histórico Trinity
    }

    for sec in sections:
        sphere_raw_title = format_inline_markdown(sec['title'])
        if not sphere_raw_title:
            continue
            
        # Determinar color de acento de la esfera
        accent_color = colors.HexColor("#0369A1")
        for key, col in sphere_colors.items():
            if key in sphere_raw_title:
                accent_color = col
                break

        # Título de esfera con barra decorativa
        sphere_table = Table([[
            Paragraph(f"<b>{sphere_raw_title.upper()}</b>", ParagraphStyle(
                'STitle', parent=sphere_heading_style, textColor=accent_color, spaceBefore=0, spaceAfter=0
            ))
        ]], colWidths=[USABLE_WIDTH])
        sphere_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
            ('LINELEFT', (0, 0), (0, -1), 3.5, accent_color),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(KeepTogether([
            Spacer(1, 10),
            sphere_table,
            Spacer(1, 8)
        ]))

        # Renderizar cada localización de la esfera
        for loc in sec['locations']:
            loc_elements = []
            l_name = format_inline_markdown(loc['name'])
            loc_elements.append(Paragraph(f"{l_name}", loc_name_style))
                
            for item in loc['items']:
                formatted_item = format_inline_markdown(item)
                if item.startswith('    '):
                    loc_elements.append(Paragraph(f"&bull; {formatted_item.strip()}", subprop_style))
                else:
                    loc_elements.append(Paragraph(f"&bull; {formatted_item}", prop_key_style))
                    
            loc_elements.append(Spacer(1, 6))
            
            # Envolver en caja KeepTogether para no partir localizaciones
            story.append(KeepTogether(loc_elements))
            
        story.append(Spacer(1, 8))

    # Matriz Sinóptica de Localizaciones por Capítulo
    if table_lines:
        story.append(Spacer(1, 10))
        table_title_table = Table([[
            Paragraph("<b>MATRIZ SINÓPTICA DE LOCALIZACIONES POR CAPÍTULO</b>", ParagraphStyle(
                'MTitle', parent=sphere_heading_style, textColor=colors.HexColor("#1E3A8A"), spaceBefore=0, spaceAfter=0
            ))
        ]], colWidths=[USABLE_WIDTH])
        table_title_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
            ('LINELEFT', (0, 0), (0, -1), 3.5, colors.HexColor("#1E3A8A")),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(KeepTogether([table_title_table, Spacer(1, 8)]))

        table_data = []
        # Cabecera de tabla
        table_data.append([
            Paragraph("<b>Cap.</b>", table_header_style),
            Paragraph("<b>Título del Capítulo</b>", table_header_style),
            Paragraph("<b>Localizaciones Principales</b>", table_header_style),
            Paragraph("<b>Relevancia Operativa y Dramática</b>", table_header_style),
        ])

        # Procesar filas
        for row in table_lines[2:]: # Omitir cabecera y separador de markdown
            parts = [p.strip() for p in row.split('|')[1:-1]]
            if len(parts) >= 4:
                cap_num = format_inline_markdown(parts[0])
                cap_title = format_inline_markdown(parts[1])
                cap_locs = format_inline_markdown(parts[2])
                cap_rel = format_inline_markdown(parts[3])

                table_data.append([
                    Paragraph(cap_num, table_cell_bold),
                    Paragraph(cap_title, table_cell_style),
                    Paragraph(cap_locs, table_cell_style),
                    Paragraph(cap_rel, table_cell_style),
                ])

        synoptic_table = Table(
            table_data,
            colWidths=[32, 105, 155, 195]
        )
        
        t_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ]

        # Alternar color de fondo en filas
        for i in range(1, len(table_data)):
            if i % 2 == 0:
                t_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor("#F8FAFC")))
            else:
                t_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor("#FFFFFF")))

        synoptic_table.setStyle(TableStyle(t_style))
        story.append(synoptic_table)
        story.append(Spacer(1, 14))

    doc.build(story, canvasmaker=LocationsCanvas)
    print(f"PDF generado con éxito: {output_filename}")

    # Copiar también en la carpeta novela/ para mantener orden
    dest_novela = os.path.join("novela", output_filename)
    shutil.copy2(output_filename, dest_novela)
    print(f"Copia archivada en: {dest_novela}")

if __name__ == '__main__':
    generate_pdf()
