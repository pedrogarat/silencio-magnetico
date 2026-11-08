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

class TechDocCanvas(canvas.Canvas):
    """Canvas de dos pasadas para numeración total, encabezados y pies de página técnicos."""
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
        self.setFillColor(colors.HexColor("#0284C7"))
        
        # Encabezado (páginas > 1)
        if self._pageNumber > 1:
            self.drawString(54, PAGE_HEIGHT - 36, "SOMBRA • FUENTE TÉCNICA Y ASTROFÍSICA")
            self.setFont("Helvetica", 7.5)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawRightString(PAGE_WIDTH - 54, PAGE_HEIGHT - 36, "HARD SCIENCE FICTION REFERENCE")
            self.setStrokeColor(colors.HexColor("#0284C7"))
            self.setLineWidth(0.75)
            self.line(54, PAGE_HEIGHT - 40, PAGE_WIDTH - 54, PAGE_HEIGHT - 40)
        
        # Pie de página
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(54, 45, PAGE_WIDTH - 54, 45)
        
        self.setFont("Helvetica", 7.8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(54, 32, "Notas Científicas y Biblia Técnica: La Llegada del Avatar y la Misión L1")
        page_str = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(PAGE_WIDTH - 54, 32, page_str)
        self.restoreState()

def strip_emojis(text):
    """Elimina emojis y selectores de variación que no existen en fuentes Type1 estándar."""
    # Rango de emojis y símbolos suplementarios
    pattern = re.compile(
        r'[\U00010000-\U0010ffff]'
        r'|[\u2600-\u27bf]'
        r'|[\u2300-\u23ff]'
        r'|[\u2b50-\u2b55]'
        r'|[\ufe00-\ufe0f]'
        r'|[\u200d]'
    )
    cleaned = pattern.sub('', text)
    return cleaned.strip()

def clean_inline_formatting(text):
    """Limpia markdown inline, elimina emojis y convierte a tags seguros de ReportLab."""
    text = strip_emojis(text)
    
    # Limpieza general y específica de LaTeX
    text = text.replace(r"\dots", "…")
    text = re.sub(r'\\mathbf\{([^}]+)\}', r'<b>\1</b>', text)
    text = re.sub(r'\\textbf\{([^}]+)\}', r'<b>\1</b>', text)
    text = re.sub(r'\\textit\{([^}]+)\}', r'<i>\1</i>', text)
    text = re.sub(r'\\text\{([^}]+)\}', r'\1', text)
    text = text.replace(r"$\vec{F} = I (\vec{L} \times \vec{B})$", "<b>F</b> = I (<b>L</b> × <b>B</b>)")
    text = re.sub(r'\\vec\{([^}]+)\}', r'<b>\1</b>', text)
    text = text.replace(r"$T=0$", "T = 0").replace(r"$T = 0$", "T = 0")
    text = text.replace(r"$NO_x$", "NO<sub>x</sub>").replace(r"NO_x", "NO<sub>x</sub>")
    text = text.replace(r"$O_3$", "O<sub>3</sub>").replace(r"O_3", "O<sub>3</sub>")
    text = text.replace(r"$N_2$", "N<sub>2</sub>").replace(r"N_2", "N<sub>2</sub>")
    text = text.replace(r"$O_2$", "O<sub>2</sub>").replace(r"O_2", "O<sub>2</sub>")
    text = text.replace(r"$CO_2$", "CO<sub>2</sub>").replace(r"CO_2", "CO<sub>2</sub>")
    text = text.replace(r"$T_c, J_c$", "T<sub>c</sub>, J<sub>c</sub>").replace(r"T_c, J_c", "T<sub>c</sub>, J<sub>c</sub>")
    text = text.replace(r"$90^\circ$", "90°")
    text = text.replace(r"$100.000 \text{ km}$", "100.000 km")
    text = text.replace(r"$\sim 1 \text{ AL}$", "~1 AL")
    text = text.replace(r"$2^\circ$", "2°")
    text = re.sub(r'\^\\circ\s*C?', '°C', text)
    text = text.replace(r'^\circ', '°')
    text = text.replace(r'\times', '×')
    text = text.replace(r'\approx', '≈')
    text = text.replace(r'\to', '→')
    text = text.replace(r'\sim', '~')
    
    # Limpiar cualquier $...$ remanente sin dejar el símbolo $
    text = re.sub(r'\$(.*?)\$', r'\1', text)
    
    # Negritas y cursivas
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    
    # Flechas
    text = text.replace("->", "→").replace("<-", "←")
    
    return text

def create_ascii_box(code_text, styles):
    p_style = ParagraphStyle(
        'AsciiCode',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=6.8,
        leading=8.2,
        textColor=colors.HexColor("#0F172A"),
    )
    lines = code_text.strip('\n').split('\n')
    flowables = []
    for line in lines:
        safe_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace(' ', '&nbsp;')
        flowables.append(Paragraph(safe_line, p_style))
        
    t = Table([[flowables]], colWidths=[USABLE_WIDTH])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F1F5F9")),
        ('BOX', (0,0), (-1,-1), 0.8, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING', (0,0), (-1,-1), 9),
        ('RIGHTPADDING', (0,0), (-1,-1), 9),
    ]))
    return t

def create_timeline_table(timeline_items, styles):
    table_data = []
    for phase_badge, title, desc in timeline_items:
        clean_title = clean_inline_formatting(title)
        clean_desc = clean_inline_formatting(desc)
        p_badge = Paragraph(f"<b>{phase_badge}</b>", styles['TimelineBadge'])
        p_desc = Paragraph(f"<b>{clean_title}</b><br/><font color='#475569'>{clean_desc}</font>", styles['TimelineDesc'])
        table_data.append([p_badge, p_desc])
        
    t = Table(table_data, colWidths=[70, USABLE_WIDTH - 70])
    t.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#F8FAFC")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    return t

def create_glossary_table(rows, styles):
    table_data = []
    # Header
    h_term = Paragraph("<b>Término Técnico</b>", styles['TableHeader'])
    h_def = Paragraph("<b>Definición Rigurosa para la Trama</b>", styles['TableHeader'])
    h_app = Paragraph("<b>Aplicación en Diálogos / Narrativa</b>", styles['TableHeader'])
    table_data.append([h_term, h_def, h_app])
    
    col_w = [115, 185, USABLE_WIDTH - 300]
    
    for i, (t, d, a) in enumerate(rows):
        term_p = Paragraph(f"<b>{clean_inline_formatting(t)}</b>", styles['TableBodyBold'])
        def_p = Paragraph(clean_inline_formatting(d), styles['TableBody'])
        app_p = Paragraph(f"<i>{clean_inline_formatting(a)}</i>", styles['TableBodyOblique'])
        table_data.append([term_p, def_p, app_p])
        
    t = Table(table_data, colWidths=col_w, repeatRows=1)
    
    t_style = [
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]
    for r in range(1, len(table_data)):
        if r % 2 == 0:
            t_style.append(('BACKGROUND', (0, r), (-1, r), colors.HexColor("#F8FAFC")))
            
    t.setStyle(TableStyle(t_style))
    return t

def generate_science_notes_pdf(md_path, output_filename):
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    base_styles = getSampleStyleSheet()
    
    styles = {
        'Normal': base_styles['Normal'],
        'SuperTitle': ParagraphStyle(
            'TechSuperTitle',
            parent=base_styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9.5,
            leading=12.5,
            textColor=colors.HexColor("#0284C7"),
            alignment=1,
            spaceAfter=4
        ),
        'DocTitle': ParagraphStyle(
            'TechTitle',
            parent=base_styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=17,
            leading=21,
            textColor=colors.HexColor("#0F172A"),
            alignment=1,
            spaceAfter=10
        ),
        'DocSubTitle': ParagraphStyle(
            'TechSubTitle',
            parent=base_styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=9.3,
            leading=14,
            textColor=colors.HexColor("#334155"),
            alignment=4,
            spaceAfter=10
        ),
        'SectionH2': ParagraphStyle(
            'TechH2',
            parent=base_styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=15.5,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=14,
            spaceAfter=5,
            keepWithNext=True
        ),
        'SectionH3': ParagraphStyle(
            'TechH3',
            parent=base_styles['Heading3'],
            fontName='Helvetica-Bold',
            fontSize=10.2,
            leading=13.5,
            textColor=colors.HexColor("#0369A1"),
            spaceBefore=9,
            spaceAfter=4,
            keepWithNext=True
        ),
        'Body': ParagraphStyle(
            'TechBody',
            parent=base_styles['Normal'],
            fontName='Helvetica',
            fontSize=9.0,
            leading=13.5,
            textColor=colors.HexColor("#1E293B"),
            spaceAfter=5,
            alignment=4
        ),
        'Bullet': ParagraphStyle(
            'TechBullet',
            parent=base_styles['Normal'],
            fontName='Helvetica',
            fontSize=9.0,
            leading=13.5,
            textColor=colors.HexColor("#1E293B"),
            leftIndent=14,
            spaceAfter=3,
            alignment=4
        ),
        'TableHeader': ParagraphStyle(
            'TableHeader',
            parent=base_styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=11.5,
            textColor=colors.white
        ),
        'TableBody': ParagraphStyle(
            'TableBody',
            parent=base_styles['Normal'],
            fontName='Helvetica',
            fontSize=8.2,
            leading=11.5,
            textColor=colors.HexColor("#1E293B")
        ),
        'TableBodyBold': ParagraphStyle(
            'TableBodyBold',
            parent=base_styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8.2,
            leading=11.5,
            textColor=colors.HexColor("#0F172A")
        ),
        'TableBodyOblique': ParagraphStyle(
            'TableBodyOblique',
            parent=base_styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=8.0,
            leading=11.2,
            textColor=colors.HexColor("#334155")
        ),
        'TimelineBadge': ParagraphStyle(
            'TimelineBadge',
            parent=base_styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#0284C7")
        ),
        'TimelineDesc': ParagraphStyle(
            'TimelineDesc',
            parent=base_styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#0F172A")
        )
    }
    
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    lines = content.split('\n')
    story = []
    
    # 1. Cabecera y Título
    story.append(Paragraph("SOMBRA • DOCUMENTACIÓN TÉCNICA", styles['SuperTitle']))
    story.append(Paragraph("Fuente Técnica y Notas Científicas: La Llegada del Avatar y la Misión L1", styles['DocTitle']))
    
    # Párrafo introductorio
    intro_text = (
        "Este documento constituye la <b>enciclopedia técnica, biblia de astrofísica y guía de verosimilitud</b> "
        "para la redacción de la novela. Define la lógica científica real, la tecnología exoplanetaria, las tácticas de "
        "sigilo termodinámico, el mecanismo del ataque magnético de la Civilización B, la física del contraataque "
        "analógico y la arquitectura astrodinámica de salvación de la Tierra."
    )
    story.append(Paragraph(intro_text, styles['DocSubTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284C7"), spaceBefore=2, spaceAfter=12))
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Omitir el título ya renderizado y el primer separador
        if line.startswith("# ") or (i < 6 and line == "---"):
            i += 1
            continue
            
        if not line:
            i += 1
            continue
            
        # Separadores
        if line == "---":
            story.append(Spacer(1, 4))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1"), spaceBefore=6, spaceAfter=10))
            i += 1
            continue
            
        # Bloque de código o Mermaid o ASCII diagram
        if line.startswith("```"):
            code_type = line.replace("```", "").strip()
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1 # saltar cierre ```
            
            if code_type == "mermaid":
                # Parsear timeline de mermaid
                timeline_items = []
                for cl in code_lines:
                    cl_s = cl.strip()
                    if cl_s.startswith("Fase "):
                        # Formato: Fase 1 : Título : Descripción
                        parts = cl_s.split(":")
                        if len(parts) >= 3:
                            badge = parts[0].strip()
                            t_title = parts[1].strip()
                            t_desc = ":".join(parts[2:]).strip()
                            timeline_items.append((badge, t_title, t_desc))
                if timeline_items:
                    story.append(Spacer(1, 4))
                    story.append(create_timeline_table(timeline_items, styles))
                    story.append(Spacer(1, 6))
            else:
                # ASCII Diagram / Code
                raw_code = "\n".join(code_lines)
                story.append(Spacer(1, 4))
                story.append(create_ascii_box(raw_code, styles))
                story.append(Spacer(1, 6))
            continue
            
        # Encabezados de Sección Nivel 2 (## ...)
        if line.startswith("## "):
            sec_title = clean_inline_formatting(line.replace("## ", "").strip())
            story.append(Spacer(1, 8))
            story.append(Paragraph(sec_title, styles['SectionH2']))
            story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#0284C7"), spaceBefore=2, spaceAfter=8))
            i += 1
            continue
            
        # Encabezados Nivel 3 (### ...)
        if line.startswith("### "):
            sub_title = clean_inline_formatting(line.replace("### ", "").strip())
            story.append(Spacer(1, 5))
            story.append(Paragraph(sub_title, styles['SectionH3']))
            i += 1
            continue
            
        # Tablas de Markdown (| ...)
        if line.startswith("|") and line.endswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            if len(table_lines) >= 3:
                # Separar cabecera, divisor y filas
                rows_data = []
                for row_idx, r_line in enumerate(table_lines):
                    if row_idx == 1 and ("---" in r_line or ":---" in r_line):
                        continue
                    cols = [c.strip() for c in r_line.strip('|').split('|')]
                    if row_idx == 0:
                        continue
                    if len(cols) >= 3:
                        rows_data.append((cols[0], cols[1], cols[2]))
                story.append(Spacer(1, 4))
                story.append(create_glossary_table(rows_data, styles))
                story.append(Spacer(1, 6))
            continue
            
        # Viñetas (* o -)
        if line.startswith("* ") or line.startswith("- "):
            bullet_text = line[2:].strip()
            clean_b = clean_inline_formatting(bullet_text)
            story.append(Paragraph(f"&bull;&nbsp;&nbsp;{clean_b}", styles['Bullet']))
            i += 1
            continue
            
        # Listas numeradas (1. , 2. ...)
        match_num = re.match(r'^(\d+)\.\s+(.*)', line)
        if match_num:
            num_idx = match_num.group(1)
            num_text = clean_inline_formatting(match_num.group(2))
            story.append(Paragraph(f"<b>{num_idx}.</b>&nbsp;&nbsp;{num_text}", styles['Bullet']))
            i += 1
            continue
            
        # Texto normal
        clean_text = clean_inline_formatting(line)
        story.append(Paragraph(clean_text, styles['Body']))
        i += 1

    doc.build(story, canvasmaker=TechDocCanvas)
    print(f"PDF generado con éxito: {output_filename}")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    md_file = os.path.join(base_dir, "novela", "notas_cientificas.md")
    
    # Guardar en novela/ y en raíz
    out_file_novela = os.path.join(base_dir, "novela", "Notas_Cientificas_La_Cancion_del_Silencio.pdf")
    out_file_root = os.path.join(base_dir, "Notas_Cientificas_La_Cancion_del_Silencio.pdf")
    
    generate_science_notes_pdf(md_file, out_file_novela)
    shutil.copyfile(out_file_novela, out_file_root)
    print(f"Copia creada en la raíz: {out_file_root}")
