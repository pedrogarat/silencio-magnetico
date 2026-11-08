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

class CharactersCanvas(canvas.Canvas):
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
        self.setFillColor(colors.HexColor("#1E3A8A"))
        
        # Encabezado (páginas > 1)
        if self._pageNumber > 1:
            self.drawString(54, PAGE_HEIGHT - 36, "SOMBRA • CÓDEX EDITORIAL")
            self.setFont("Helvetica", 7.5)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawRightString(PAGE_WIDTH - 54, PAGE_HEIGHT - 36, "ELENCO COMPLETO Y DRAMATIS PERSONAE")
            self.setStrokeColor(colors.HexColor("#3B82F6"))
            self.setLineWidth(0.75)
            self.line(54, PAGE_HEIGHT - 40, PAGE_WIDTH - 54, PAGE_HEIGHT - 40)
        
        # Pie de página
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(54, 45, PAGE_WIDTH - 54, 45)
        
        self.setFont("Helvetica", 7.8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(54, 32, "Códex Exhaustivo de Personajes • Ordenados por Jerarquía e Importancia")
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
    # Limpieza de caracteres problemáticos
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

def parse_characters_markdown(filepath):
    """Lee y estructura el archivo personajes.md por niveles y fichas de personajes."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    
    sections = []
    current_level = None
    current_char = None
    
    for line in lines:
        stripped = line.strip()
        
        # Detectar niveles (## NIVEL X: ...)
        if stripped.startswith('## '):
            if current_char and current_level:
                current_level['characters'].append(current_char)
                current_char = None
            if current_level:
                sections.append(current_level)
            
            title = stripped[3:].strip()
            current_level = {
                'title': title,
                'characters': []
            }
            continue
            
        # Detectar subsecciones dentro de un nivel (ej: ### bastión de versoix)
        if stripped.startswith('### ') and current_level:
            sub_title = stripped[4:].strip()
            # Si empieza con número o nombre de personaje
            if current_char:
                current_level['characters'].append(current_char)
                current_char = None
            
            current_char = {
                'name': sub_title,
                'items': [],
                'is_group': not any(c.isdigit() for c in sub_title[:4]) and not 'Dr.' in sub_title and not 'Dra.' in sub_title and not 'Col.' in sub_title
            }
            continue
            
        # Líneas de propiedades o listas
        if stripped.startswith('- ') or stripped.startswith('* '):
            if current_char:
                current_char['items'].append(stripped[2:].strip())
            continue
        elif stripped.startswith('  - ') or stripped.startswith('  * '):
            if current_char:
                current_char['items'].append('    ' + stripped[4:].strip())
            continue
        elif stripped and not stripped.startswith('#') and not stripped.startswith('---') and not stripped.startswith('>'):
            if current_char:
                current_char['items'].append(stripped)
                
    if current_char and current_level:
        current_level['characters'].append(current_char)
    if current_level:
        sections.append(current_level)
        
    return sections

def generate_pdf():
    input_file = os.path.join("novela", "personajes.md")
    output_filename = "Personajes_La_Cancion_del_Silencio.pdf"
    
    sections = parse_characters_markdown(input_file)
    
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
        textColor=colors.HexColor("#2563EB"),
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
    
    level_heading_style = ParagraphStyle(
        'LevelHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )
    
    char_name_style = ParagraphStyle(
        'CharName',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=13.5,
        textColor=colors.HexColor("#1E3A8A"),
        spaceBefore=6,
        spaceAfter=3,
        keepWithNext=True
    )
    
    group_header_style = ParagraphStyle(
        'GroupHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#047857"),
        spaceBefore=8,
        spaceAfter=4,
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

    story = []
    
    # Portada / Cabecera
    story.append(Paragraph("CÓDEX DE PERSONAJES", title_style))
    story.append(Paragraph("SOMBRA • LA GUERRA DE LA HERENCIA", sub_title_style))
    
    # Cuadro de introducción
    intro_p = Paragraph(
        "<b>Guía Oficial de Personajes y Dramatis Personae:</b> Registro canónico de todas las "
        "entidades, líderes, científicos, tripulantes y figuras civiles que componen la trama de la novela, "
        "ordenados rigurosamente por su nivel de protagonismo, relevancia dramática y peso operacional.",
        intro_style
    )
    intro_table = Table([[intro_p]], colWidths=[USABLE_WIDTH])
    intro_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('LINEBEFORE', (0, 0), (0, -1), 3, colors.HexColor("#2563EB")),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
    ]))
    story.append(intro_table)
    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1"), spaceBefore=2, spaceAfter=10))

    # Paleta de colores para los niveles
    level_colors = {
        "NIVEL 1": colors.HexColor("#2563EB"), # Azul real
        "NIVEL 2": colors.HexColor("#0284C7"), # Azul cielo oscuro
        "NIVEL 3": colors.HexColor("#7C3AED"), # Violeta cósmico
        "NIVEL 4": colors.HexColor("#D97706"), # Ámbar cohete
        "NIVEL 5": colors.HexColor("#475569"), # Pizarra militar
        "NIVEL 6": colors.HexColor("#059669"), # Esmeralda familiar
        "NIVEL 7": colors.HexColor("#0D9488"), # Verde azulado ciencia
        "NIVEL 8": colors.HexColor("#DC2626"), # Rojo Trinity
        "NIVEL 9": colors.HexColor("#64748B"), # Gris civil
    }

    for sec in sections:
        level_raw_title = format_inline_markdown(sec['title'])
        if not level_raw_title:
            continue
            
        # Determinar color de acento del nivel
        accent_color = colors.HexColor("#1E3A8A")
        for key, col in level_colors.items():
            if key in level_raw_title:
                accent_color = col
                break

        # Título de nivel con barra decorativa
        level_table = Table([[
            Paragraph(f"<b>{level_raw_title.upper()}</b>", ParagraphStyle(
                'LTitle', parent=level_heading_style, textColor=accent_color, spaceBefore=0, spaceAfter=0
            ))
        ]], colWidths=[USABLE_WIDTH])
        level_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
            ('LINELEFT', (0, 0), (0, -1), 3.5, accent_color),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(KeepTogether([
            Spacer(1, 10),
            level_table,
            Spacer(1, 8)
        ]))

        # Renderizar cada personaje del nivel
        for ch in sec['characters']:
            char_elements = []
            
            c_name = format_inline_markdown(ch['name'])
            is_group = ch.get('is_group', False)
            
            if is_group:
                char_elements.append(Paragraph(f"<b>{c_name}</b>", group_header_style))
            else:
                # Nombre del personaje con pequeña caja o acento
                char_elements.append(Paragraph(f"{c_name}", char_name_style))
                
            for item in ch['items']:
                formatted_item = format_inline_markdown(item)
                if item.startswith('    '):
                    char_elements.append(Paragraph(f"&bull; {formatted_item.strip()}", subprop_style))
                else:
                    char_elements.append(Paragraph(f"&bull; {formatted_item}", prop_key_style))
                    
            char_elements.append(Spacer(1, 6))
            
            # Envolver en caja KeepTogether para no partir personajes a la mitad si es posible
            story.append(KeepTogether(char_elements))
            
        story.append(Spacer(1, 8))

    doc.build(story, canvasmaker=CharactersCanvas)
    print(f"PDF generado con éxito: {output_filename}")

    # Copiar también en la carpeta novela/ para mantener orden
    dest_novela = os.path.join("novela", "Personajes_La_Cancion_del_Silencio.pdf")
    shutil.copy2(output_filename, dest_novela)
    print(f"Copia archivada en: {dest_novela}")

if __name__ == '__main__':
    generate_pdf()
