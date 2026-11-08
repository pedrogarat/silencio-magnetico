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

PAGE_WIDTH = A4[0]
PAGE_HEIGHT = A4[1]
USABLE_WIDTH = PAGE_WIDTH - 108  # 487.27 pt (54 pt margins)

class ReportCanvas(canvas.Canvas):
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
        self.setFillColor(colors.HexColor("#0284C7"))
        
        # Encabezado (páginas > 1)
        if self._pageNumber > 1:
            self.drawString(54, PAGE_HEIGHT - 36, "SOMBRA • CÓDICE EDITORIAL Y AUDITORÍA DE CONTINUIDAD")
            self.setFont("Helvetica", 7.5)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawRightString(PAGE_WIDTH - 54, PAGE_HEIGHT - 36, "RECAPITULACIÓN OFICIAL • CAPÍTULOS 1 AL 10")
            self.setStrokeColor(colors.HexColor("#0284C7"))
            self.setLineWidth(0.75)
            self.line(54, PAGE_HEIGHT - 40, PAGE_WIDTH - 54, PAGE_HEIGHT - 40)
        
        # Pie de página
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(54, 45, PAGE_WIDTH - 54, 45)
        
        self.setFont("Helvetica", 7.8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(54, 32, "Códice Rector y Control de Coherencia Editorial • Capítulos 1 al 10 (T=0 a T+72h)")
        page_str = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(PAGE_WIDTH - 54, 32, page_str)
        self.restoreState()

def create_alert_box(title, text_paragraphs, styles, border_color="#D97706", bg_color="#FFFBEB", width=USABLE_WIDTH):
    t_style = ParagraphStyle(
        'AlertTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#92400E") if border_color == "#D97706" else colors.HexColor("#0369A1") if border_color == "#0284C7" else colors.HexColor("#166534"),
        spaceAfter=3
    )
    b_style = ParagraphStyle(
        'AlertBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#78350F") if border_color == "#D97706" else colors.HexColor("#0C4A6E") if border_color == "#0284C7" else colors.HexColor("#14532D"),
        spaceAfter=3
    )
    content = [Paragraph(f"<b>{title}</b>", t_style)]
    for p in text_paragraphs:
        content.append(Paragraph(p, b_style))
    t = Table([[content]], colWidths=[width])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(bg_color)),
        ('LINELEFT', (0,0), (-1,-1), 3.5, colors.HexColor(border_color)),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    return t

def generate_report_pdf(output_filename):
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    super_title = ParagraphStyle(
        'SuperTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#0284C7"),
        alignment=1,
        spaceAfter=4
    )
    main_title = ParagraphStyle(
        'MainTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0F172A"),
        alignment=1,
        spaceAfter=6
    )
    subtitle = ParagraphStyle(
        'SubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#475569"),
        alignment=1,
        spaceAfter=14
    )
    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12.5,
        leading=16,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.2,
        leading=13.5,
        textColor=colors.HexColor("#0369A1"),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'ReportBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.8,
        leading=12.5,
        textColor=colors.HexColor("#1E293B"),
        spaceAfter=5
    )
    bullet_style = ParagraphStyle(
        'ReportBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12.2,
        textColor=colors.HexColor("#1E293B"),
        leftIndent=10,
        spaceAfter=3.5
    )
    tbl_header = ParagraphStyle(
        'TblHdr',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.2,
        leading=11,
        textColor=colors.white,
        alignment=0
    )
    tbl_cell = ParagraphStyle(
        'TblCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.6,
        leading=10.4,
        textColor=colors.HexColor("#1E293B")
    )
    tbl_cell_bold = ParagraphStyle(
        'TblCellB',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.8,
        leading=10.6,
        textColor=colors.HexColor("#0F172A")
    )

    story = []
    
    # ---------------- PORTADA / ENCABEZADO ----------------
    story.append(Spacer(1, 8))
    story.append(Paragraph("SOMBRA • CÓDICE RECTOR Y AUDITORÍA EDITORIAL", super_title))
    story.append(Paragraph("Informe de Recapitulación General de la Obra", main_title))
    story.append(Paragraph("Control de Continuidad, Arcos Psicológicos, Flujo de Información y Fases del Colapso (Capítulos 1 al 10)", subtitle))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284C7"), spaceBefore=2, spaceAfter=12))
    
    # ---------------- 1. REGLAS DE ORO EDITORIALES ----------------
    story.append(Paragraph("1. Principios Rectores y Reglas de Oro Editoriales", h1_style))
    story.append(Paragraph(
        "Antes de redactar, continuar o modificar cualquier capítulo, escena o diálogo, es preceptivo contrastar el texto propuesto con las siguientes normas canónicas:",
        body_style
    ))
    
    reglas = [
        ("Regla 1: Coherencia Absoluta con lo Ya Escrito", "Prohibición tajante de filtraciones de omnisciencia. Cada personaje solo actúa y siente en función de los datos que ha asimilado experimentalmente."),
        ("Regla 2: Dosificación del Lenguaje Científico", "Economía técnica estricta (*hard sci-fi* al servicio del drama humano). Para pasajes matemáticos o físicos densos, es obligatorio solicitar confirmación previa al Autor."),
        ("Regla 3: Coherencia de Voces y Psicología", "Registro léxico único: Girard (cartesiano y familiar), Sarah (vehemente y volcánica, herida pero tierna), Wright (templado, operacional y protector), Pleh (aritmético e implacable), Ramos (estadista compasivo y católico)."),
        ("Regla 4: Rigor Argumental y Pruebas Irrefutables", "Cero 'suposiciones ligeras'. Toda alerta o decisión estratégica se sustenta en evidencias empíricas (espectrometría, cinemática, efecto Zeeman, firmas de RF)."),
        ("Regla 5: Ritmo Cinematográfico ('Show, Don't Tell')", "Comenzar las escenas en el punto más tardío y salir tras entregar el giro dramático; la tensión fluye del choque de caracteres y los datos en monitor."),
        ("Regla 6: Protocolo de Identidad de Em Pleh", "Para el Consejo de Seguridad, gobiernos y militares, Pleh es estrictamente un astrofísico civil humano independiente. Desconocen por completo su naturaleza de SIA extraterrestre."),
        ("Regla 7: Calendario Canónico y Cuenta Atrás", "Sobreimpresión obligatoria al inicio de cada capítulo de fecha, hora y cuenta atrás exacta de días u horas hacia la siguiente fase de la catástrofe.")
    ]
    for r_title, r_desc in reglas:
        story.append(Paragraph(f"• <b>{r_title}:</b> {r_desc}", bullet_style))
        
    story.append(Spacer(1, 8))
    
    # ---------------- 2. CRONOLOGÍA E HITOS (CAPS 1 AL 10) ----------------
    story.append(Paragraph("2. Recapitulación Argumental y Cronológica (Capítulos 1 al 10)", h1_style))
    story.append(Paragraph(
        "La línea temporal cubre desde la génesis atómica en 1945 hasta la consumación del colapso magnético y la batalla cinética en la mesosfera (T+72h):",
        body_style
    ))
    
    hitos = [
        ("Cap. 1: El Amanecer de Alamogordo (16 julio 1945)",
         "La detonación <i>Trinity</i> emite un pulso electromagnético al cosmos. En la Nube de Oort (1 año luz), despiertan la sonda nodriza de la Civilización A (creadora de la SIA Pleh) y la sonda cazadora de la Civilización B (ejecutora del Teorema del Exterminio Preventivo)."),
        ("Cap. 2: Los Tres Hilos del Ilusionista (Septiembre 2026)",
         "Ochenta y un años después, tres científicos en crisis reciben soluciones anónimas e impecables firmadas por el Dr. Em Pleh: Girard (CERN, ruido cuántico), Sarah Lin (MIT, MHD en tokamak) y Thomas Wright (ESA, rescate orbital). Son citados en Manhattan."),
        ("Cap. 3: La Sala Dos (24 septiembre 2026, 10:00 EDT)",
         "Pleh se revela como una SIA extraterrestre en órbita polar (100.000 km). Demuestra que la máquina de B (<i>Sombra</i>) frena en Lagrange L1 para anular la magnetosfera por interferencia destructiva. Expone la necesidad del contraataque analógico."),
        ("Cap. 4: El Vértigo de las Naciones (24 septiembre 2026, mediodía)",
         "Pleh y los científicos se reúnen con el Secretario General de la ONU, Vassily Ramos. Tras verificar satelitalmente la firma electromagnética en L1, Ramos decreta el secreto supremo <b>Alfa Cero</b> y crea el Comité Científico Director."),
        ("Cap. 5: El Ancla Humana (24 septiembre 2026, 13:00 - 16:00 EDT)",
         "Llamadas telefónicas bajo secreto de Estado: Girard con su familia en Ginebra; Sarah asumiendo la ruptura con Mark; Wright añorando a su hermano y fascinado por Sarah. A las 16:00 h ingresan en el búnker subterráneo Sala de Crisis B-4."),
        ("Cap. 6: La Cámara del Silencio (24 septiembre 2026, 20:00 EDT | T - 58 días)",
         "Sesión extraordinaria secreta del Consejo de Seguridad. Pleh comparece como consultor civil y desmonta los recelos militares con datos de satélites espías. Presenta el <b>Calendario Canónico de Fases</b> (Fases 1 a 6) y la arquitectura del doble módulo (MAA/MRD, efecto Quench y máser)."),
        ("Cap. 7: La Condición Immedible (8 octubre 2026, 13:20 EDT | T - 44 días)",
         "Salto de 10 días. Almuerzo íntimo de Sarah y Thomas en Manhattan (culpa del traidor frente a los civiles inocentes). Girard llega conmovido por los planes de su hijo Julien. Reunión con Ramos en B-4: balance industrial favorable, rapiña geopolítica por patentes, selección de los 6 astronautas (MacElroy, Chen Mei, Voronov) y recelos hacia el anonimato de Pleh."),
        ("Cap. 8: La Gran Mentira (10 octubre 2026 | T - 42 días)",
         "Girard rompe Alfa Cero para alertar a Marie en Versoix. Rueda de prensa mundial de Ramos: proclama la 'Gran Mentira' del Súper Evento Carrington para el 21 de noviembre, justificando el futuro <i>airglow</i> y la caída de satélites, e impone la ley marcial energética. Blindaje Faraday en Nellis y Sichuan. Llamadas familiares de Girard (Julien toma el mando del hogar) y Wright (David, Claire y Oliver evacúan a Suffolk). Desgarradora llamada de Sarah con su hermana Maya en San Francisco; catarsis, primer beso entre Sarah y Thomas en la sala de servidores. Ramos reflexiona con Girard entre fe y razón."),
        ("Cap. 9: La Fractura del Orden (11 al 15 octubre 2026 | T - 37 días)",
         "Capítulo coral sobre los frentes familiares: 1) Versoix: Julien (17 años) electrifica la cancela con condensadores y Marie repele a maleantes con escopeta. 2) Suffolk: David, Claire y Oliver (3 años) esquivan saqueos en Land Rover y llegan a la granja con agua de pozo y leña. 3) San Francisco: Maya Lin resiste una crisis de abstinencia recordando su promesa a Sarah y abraza a Toby (4 años). 4) Normalización psicológica del miedo en una rutina cívica ordenada y reconexión telefónica al 75% con el búnker B-4."),
        ("Cap. 10: T = 0 / El Colapso Tecnológico Orbital (21 al 24 noviembre 2026 | T=0 a T+72h)",
         "1) T=0 (21 nov, 05:30 UTC): <i>Airglow</i> verdoso global; la magnetosfera cae a 0 nT; la brújula marina de Girard enloquece y muere. 2) T+24 a 72h: Radiación solar causa SEU masivos en chips y calentamiento atmosférico que expande la termosfera (densidad x50); satélites LEO entran en giro caótico (*tumbling*); lluvia torrencial de chatarra cósmica. 3) El Escudo Defensivo: Misiles antibalísticos/ASAT destruyen fragmentos críticos; Pleh y Ramos orquestan una salva desde el <i>USS Lake Erie</i> para volatilizar un satélite espía Keyhole de 18 t que amenazaba Nellis. La órbita baja queda barrida. Comienza la cuenta atrás hacia la Fase 3 (NOx y destrucción de ozono).")
    ]
    
    for title, desc in hitos:
        story.append(Paragraph(f"• <b>{title}:</b> {desc}", bullet_style))
        
    story.append(Spacer(1, 8))
    
    # ---------------- 3. AUDITORÍA DE PERSONAJES PRINCIPALES ----------------
    story.append(KeepTogether([
        Paragraph("3. Auditoría Psicológica y Coherencia de Personajes Principales", h1_style),
        Paragraph("Evaluación de coherencia interna, registro léxico y arcos dramáticos tras 10 capítulos:", body_style)
    ]))
    
    personajes_data = [
        [
            Paragraph("Personaje", tbl_header),
            Paragraph("Perfil Canónico", tbl_header),
            Paragraph("Evolución Observada (Caps. 1-10)", tbl_header),
            Paragraph("Diagnóstico", tbl_header)
        ],
        [
            Paragraph("<b>Dr. Em Pleh</b><br/><i>(SIA / Avatar de A)</i>", tbl_cell_bold),
            Paragraph("Aritmético, riguroso, conciso, melancolía ética hacia lo humano, imperturbable.", tbl_cell),
            Paragraph("Mantiene una frialdad operativa perfecta. Revela la amenaza (Cap. 3), domina la diplomacia (Cap. 4 y 6), coordina la defensa cinética mesosférica con el <i>USS Lake Erie</i> (Cap. 10) y recuerda implacable el plazo biológico a Fase 3.", tbl_cell),
            Paragraph("<font color='#059669'><b>100% Coherente</b></font><br/>Sin fisuras de registro ni modismos.", tbl_cell)
        ],
        [
            Paragraph("<b>Dra. Sarah Lin</b><br/><i>(MIT - Fusión)</i>", tbl_cell_bold),
            Paragraph("Competitiva, vehemente, volcánica, gran resistencia al estrés pero heridas afectivas.", tbl_cell),
            Paragraph("Gran profundización humana. Supera su ruptura con Mark, perdona y salva a su hermana Maya (Cap. 8), consolida su romance con Thomas con un primer beso y mantiene su entereza técnica en el búnker durante T=0 (Cap. 10).", tbl_cell),
            Paragraph("<font color='#059669'><b>Sobresaliente</b></font><br/>Arco dramático rico y conmovedor.", tbl_cell)
        ],
        [
            Paragraph("<b>Dr. Jean-Luc Girard</b><br/><i>(CERN - Criogenia)</i>", tbl_cell_bold),
            Paragraph("Cartesiano puro, escéptico radical, formal, formalista ético y padre ejemplar.", tbl_cell),
            Paragraph("Conflicto moral desgarrador. Rompe Alfa Cero por amor familiar (Cap. 8) y llora en privado antes de recobrar la templanza. En Cap. 10 contempla con dolor científico la muerte de su brújula marina al llegar el Silencio Magnético.", tbl_cell),
            Paragraph("<font color='#059669'><b>Sobresaliente</b></font><br/>Pilar ético y metodológico indiscutible.", tbl_cell)
        ],
        [
            Paragraph("<b>Dr. Thomas Wright</b><br/><i>(ESA - Navegación)</i>", tbl_cell_bold),
            Paragraph("Templanza veterana (52 años), pragmático operacional, empático, protector del equipo.", tbl_cell),
            Paragraph("El ancla emocional de la obra. Modera crisis diplomáticas, criba a los 6 astronautas (Cap. 7), protege a Sarah sosteniéndola en su llanto (Cap. 8) y asume con serenidad militar el monitoreo de la reentrada orbital en Cap. 10.", tbl_cell),
            Paragraph("<font color='#059669'><b>100% Coherente</b></font><br/>El pilar más sólido de la expedición.", tbl_cell)
        ],
        [
            Paragraph("<b>Vassily Ramos</b><br/><i>(Secretario General ONU)</i>", tbl_cell_bold),
            Paragraph("Estadista íntegro, exhausto por el deber, de profundas convicciones católicas y compasivas.", tbl_cell),
            Paragraph("Crecimiento colosal. Asume la culpa moral de la 'Gran Mentira' de Carrington (Cap. 8), defiende el consuelo de la fe popular ante Girard, y en Cap. 10 ordena con determinación los disparos de intercepción antibalística.", tbl_cell),
            Paragraph("<font color='#059669'><b>Excelente</b></font><br/>Líder trágico de dimensión humana universal.", tbl_cell)
        ]
    ]
    
    t_pers = Table(personajes_data, colWidths=[85, 115, 195, 92])
    t_pers.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 4.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4.5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_pers)
    story.append(Spacer(1, 10))
    
    # ---------------- 4. AUDITORÍA DE FAMILIARES Y ANCLAS HUMANAS ----------------
    story.append(KeepTogether([
        Paragraph("4. Auditoría de Arcos Familiares y Anclas Humanas (Caps. 8 y 9)", h1_style),
        Paragraph("El factor civil aporta tensión real y verosimilitud sociológica ante el colapso global:", body_style)
    ]))
    
    fam_data = [
        [
            Paragraph("Familiar / Vínculo", tbl_header),
            Paragraph("Ubicación y Entorno", tbl_header),
            Paragraph("Arco y Acontecimientos Clave (Caps. 8-10)", tbl_header),
            Paragraph("Estado Canónico", tbl_header)
        ],
        [
            Paragraph("<b>Marie y Julien Girard</b><br/><i>(Familia de Jean-Luc)</i>", tbl_cell_bold),
            Paragraph("Chalet familiar en Versoix, Ginebra (Suiza).", tbl_cell),
            Paragraph("Julien (17 años) demuestra liderazgo técnico improvisando una trampa eléctrica con condensadores; Marie encara con escopeta a maleantes (Cap. 9). Se refugian en el sótano blindado durante T=0 (Cap. 10).", tbl_cell),
            Paragraph("<font color='#059669'><b>A salvo</b></font><br/>Seguros en búnker doméstico.", tbl_cell)
        ],
        [
            Paragraph("<b>David, Claire y Oliver</b><br/><i>(Familia de Thomas)</i>", tbl_cell_bold),
            Paragraph("Casa de campo en Suffolk (Reino Unido).", tbl_cell),
            Paragraph("Evacúan Cambridge en Land Rover esquivando saqueos en la A14; aseguran la granja con agua de pozo artesiano y leña seca (Cap. 9). Pasan el T=0 protegidos en la campiña inglesa (Cap. 10).", tbl_cell),
            Paragraph("<font color='#059669'><b>A salvo</b></font><br/>Aislados y abastecidos.", tbl_cell)
        ],
        [
            Paragraph("<b>Maya Lin y Toby</b><br/><i>(Familia de Sarah)</i>", tbl_cell_bold),
            Paragraph("Apartamento modesto en Market St., San Francisco.", tbl_cell),
            Paragraph("Maya (14 meses limpia) sufre una crisis de abstinencia bajo toque de queda pero vence la tentación al recordar a Sarah; protege a su hijo Toby (4 años) y se refugia en el sótano durante el T=0 (Cap. 9 y 10).", tbl_cell),
            Paragraph("<font color='#059669'><b>A salvo</b></font><br/>Sobria y protegida.", tbl_cell)
        ]
    ]
    
    t_fam = Table(fam_data, colWidths=[95, 115, 185, 92])
    t_fam.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0369A1")),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 4.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4.5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_fam)
    story.append(Spacer(1, 10))
    
    # ---------------- 5. FLUJO DE INFORMACIÓN TRAS CAPÍTULO 10 ----------------
    story.append(KeepTogether([
        Paragraph("5. Auditoría del Flujo de Información (Quién sabe qué tras Cap. 10)", h1_style),
        Paragraph("Control estricto de compartimentación informativa tras el Silencio Magnético:", body_style)
    ]))
    
    info_data = [
        [
            Paragraph("Estamento / Grupo", tbl_header),
            Paragraph("Lo que SABEN (alcanzado Cap. 10)", tbl_header),
            Paragraph("Lo que IGNORAN", tbl_header),
            Paragraph("Estado Canónico", tbl_header)
        ],
        [
            Paragraph("<b>Comité Científico</b><br/>(Wright, Lin, Girard)", tbl_cell_bold),
            Paragraph("Pleh es una SIA alienígena; Sombra en L1; colapso magnético a 0 nT; órbita LEO barrida; talleres MAA en Nellis y Sichuan protegidos por Faraday; inicio inminente de Fase 3.", tbl_cell),
            Paragraph("Ignoran si la psique de los 6 astronautas soportará el confinamiento manual y el comportamiento exacto del plasma en L1.", tbl_cell),
            Paragraph("<font color='#059669'><b>Blindado</b></font>", tbl_cell)
        ],
        [
            Paragraph("<b>Secretario General</b><br/>(Vassily Ramos)", tbl_cell_bold),
            Paragraph("Origen extraterrestre de Pleh; que la tormenta Carrington fue una coartada calculada; autorizó los disparos de misiles antibalísticos para salvar Nellis.", tbl_cell),
            Paragraph("Ignora los pormenores mecánicos del MAA/MRD y cómo evitar la histeria global cuando el ozono comience a destruirse en Fase 3.", tbl_cell),
            Paragraph("<font color='#059669'><b>Blindado</b></font>", tbl_cell)
        ],
        [
            Paragraph("<b>Superpotencias</b><br/>(Consejo de Seguridad, Pentágono, Pekín, Moscú)", tbl_cell_bold),
            Paragraph("Verificaron el pulso magnético en L1; aceptaron la coartada de Carrington para ordenar a sus tropas; emplearon sus arsenales ASAT (Aegis, S-500, Dong Neng-3).", tbl_cell),
            Paragraph("<b>IGNORAN que Pleh es una SIA o alienígena.</b> Creen que es un consultor humano clandestino y temen que sea un agente de ciberguerra enemigo.", tbl_cell),
            Paragraph("<font color='#059669'><b>Conforme a Regla 6</b></font>", tbl_cell)
        ],
        [
            Paragraph("<b>Opinión Pública y Familias</b><br/>(Sociedad civil global)", tbl_cell_bold),
            Paragraph("Creen que sufren las secuelas de un 'Súper Evento Solar Carrington' natural; se disciplinan ante la ley marcial y los cortes rotatorios.", tbl_cell),
            Paragraph("<b>Ignoran absolutamente la presencia de Sombra en L1</b>, la existencia de Pleh y que la verdadera extinción vendrá por radiación UV.", tbl_cell),
            Paragraph("<font color='#059669'><b>Blindado</b></font>", tbl_cell)
        ]
    ]
    
    t_info = Table(info_data, colWidths=[95, 150, 155, 87])
    t_info.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 4.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4.5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_info)
    story.append(Spacer(1, 10))
    
    # ---------------- 6. CALENDARIO CANÓNICO DE FASES ----------------
    story.append(KeepTogether([
        Paragraph("6. Calendario Canónico de Fases del Colapso (Control de Tiempos)", h1_style),
        Paragraph("Cronograma matemático expuesto por Pleh en Cap. 6 y contrastado en Cap. 10:", body_style)
    ]))
    
    fases_data = [
        [
            Paragraph("Fase y Fecha Canónica", tbl_header),
            Paragraph("Fenómeno Físico / Orbital", tbl_header),
            Paragraph("Impacto Biosférico e Industrial", tbl_header),
            Paragraph("Estado", tbl_header)
        ],
        [
            Paragraph("<b>Fase 1: T = 0</b><br/>21 nov 2026 (05:30 UTC)", tbl_cell_bold),
            Paragraph("Despliegue de los 50 km completado en L1; anulación del dipolo (45.000 nT → 0).", tbl_cell),
            Paragraph("<i>Airglow</i> verdoso global; brújulas erráticas; fallo de sistemas magnetosféricos.", tbl_cell),
            Paragraph("<font color='#059669'><b>Cumplida</b></font><br/>(Cap. 10)", tbl_cell)
        ],
        [
            Paragraph("<b>Fase 2: T + 24-72 h</b><br/>22 al 24 nov 2026", tbl_cell_bold),
            Paragraph("Radiación ionizante directa causa SEU; termosfera x50; *tumbling* y reentrada masiva.", tbl_cell),
            Paragraph("Destrucción de satélites GPS y telecomunicaciones; defensa con misiles ASAT; órbita LEO barrida.", tbl_cell),
            Paragraph("<font color='#059669'><b>Cumplida</b></font><br/>(Cap. 10)", tbl_cell)
        ],
        [
            Paragraph("<b>Fase 3: T + 30-90 d</b><br/>21 dic 2026 a feb 2027", tbl_cell_bold),
            Paragraph("Penetración de protones solares sin deflexión; catálisis masiva de óxidos de nitrógeno (NOx).", tbl_cell),
            Paragraph("Pérdida acelerada del 4% diario de la capa de ozono estratosférico hasta su aniquilación.", tbl_cell),
            Paragraph("<font color='#D97706'><b>Próxima</b></font><br/>(Cap. 11+)", tbl_cell)
        ],
        [
            Paragraph("<b>Fase 4: T + 6 meses</b><br/>21 mayo 2027", tbl_cell_bold),
            Paragraph("Radiación UVC y UVB incide directamente sobre la superficie y la capa fótica marina.", tbl_cell),
            Paragraph("Abrasión de cosechas continentales; extinción del fitoplancton (muerte del 50% del oxígeno biológico).", tbl_cell),
            Paragraph("<font color='#64748B'><b>Pendiente</b></font>", tbl_cell)
        ],
        [
            Paragraph("<b>Fase 5: T + 8 meses</b><br/>21 julio 2027", tbl_cell_bold),
            Paragraph("Hambre masiva, colapso de cadenas logísticas y desarticulación de refinerías.", tbl_cell),
            Paragraph("<b>Cierre de la ventana operativa industrial:</b> Imposibilidad física de ensamblar o lanzar cohetes.", tbl_cell),
            Paragraph("<font color='#DC2626'><b>Límite Fatal</b></font>", tbl_cell)
        ],
        [
            Paragraph("<b>Fase 6: T + 3 años</b><br/>Noviembre 2029", tbl_cell_bold),
            Paragraph("Atmósfera anóxica y esterilizada por radiación ionizante continua.", tbl_cell),
            Paragraph("Extinción biológica total e irreversible de los vertebrados terrestres y marinos.", tbl_cell),
            Paragraph("<font color='#64748B'><b>Final</b></font>", tbl_cell)
        ]
    ]
    
    t_fases = Table(fases_data, colWidths=[110, 175, 140, 62])
    t_fases.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0369A1")),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_fases)
    story.append(Spacer(1, 10))
    
    # ---------------- 7. RESOLUCIÓN DE FRICCIONES Y ALERTAS ----------------
    story.append(KeepTogether([
        Paragraph("7. Auditoría de Puntos de Fricción y Estado de Alertas", h1_style),
        Paragraph("Dictámenes sobre los aspectos sensibles de la narrativa y la continuidad:", body_style)
    ]))
    
    # Alert Box 1: Sincronización
    box1 = create_alert_box(
        "A. Unificación Canónica de Archivos de Recapitulación",
        [
            "Se consolidó <code>recapitulacion.md</code> (22.8 KB) como la única fuente canónica y fidedigna del Códice Rector, sincronizando cualquier copia obsoleta (como el antiguo <code>recapitulación.md</code> con tilde).",
            "<b>Resultado:</b> Cero riesgo de discrepancia de lectura por parte de agentes o scripts en futuros capítulos."
        ],
        styles,
        border_color="#059669",
        bg_color="#F0FDF4"
    )
    story.append(box1)
    story.append(Spacer(1, 5))
    
    # Alert Box 2: Edades y nombres familiares
    box2 = create_alert_box(
        "B. Rigor en Nombres, Vínculos y Edades Familiares",
        [
            "Se fijaron canónicamente: <b>Julien Girard</b> (17 años, liderazgo práctico y resolutivo en Versoix); <b>Oliver Wright</b> (3 años, hijo de David y Claire en Suffolk); <b>Toby</b> (4 años, hijo de Maya Lin en San Francisco; Maya limpia 14 meses).",
            "<b>Continuidad:</b> Queda prohibido variar edades o lazos en futuros capítulos corales."
        ],
        styles,
        border_color="#0284C7",
        bg_color="#F0F9FF"
    )
    story.append(box2)
    story.append(Spacer(1, 5))
    
    # Alert Box 3: Salto al Capítulo 11
    box3 = create_alert_box(
        "C. Transición al Capítulo 11: Entrenamiento Manual y la Sombra del Ozono",
        [
            "Con la órbita baja despejada de satélites tras el Capítulo 10, el foco dramático se desplaza a los búnkeres de Nevada y Sichuan: el ensamblaje bajo Faraday del MAA y el entrenamiento de los 6 astronautas con instrumental analógico y telémetros ópticos bajo la guía de Wright.",
            "<b>Urgencia temporal:</b> Faltan escasas semanas para el 21 de diciembre de 2026 (inicio de Fase 3: colapso de la capa de ozono)."
        ],
        styles,
        border_color="#D97706",
        bg_color="#FFFBEB"
    )
    story.append(box3)
    story.append(Spacer(1, 10))
    
    # ---------------- 8. CHECKLIST PREVIO Y CONCLUSIONES ----------------
    story.append(KeepTogether([
        Paragraph("8. Checklist Previo a la Redacción y Conclusiones", h1_style),
        Paragraph(
            "<b>Checklist Obligatorio de 8 Puntos (Códice Rector):</b><br/>"
            "1. [ ] ¿Contradice algún evento o dato de los capítulos anteriores?<br/>"
            "2. [ ] ¿Se han contrastado los nombres canónicos y edades de familiares (Julien 17, Oliver 3, Toby 4)?<br/>"
            "3. [ ] ¿Algún personaje sabe algo que todavía ignora en ese instante?<br/>"
            "4. [ ] ¿El lenguaje técnico es comprensible y ágil, o se está volviendo farragoso?<br/>"
            "5. [ ] Si hay una explicación técnica profunda, ¿se ha pedido antes confirmación al Autor?<br/>"
            "6. [ ] ¿Las voces suenan diferenciadas (Girard cartesiano, Sarah vehemente, Wright operacional, Pleh aritmético, Ramos estadista empático y católico)?<br/>"
            "7. [ ] ¿Se respeta la dimensión espiritual y ética de los personajes sin deslices antirreligiosos ni cinismo?<br/>"
            "8. [ ] ¿Las afirmaciones críticas se sostienen con pruebas empíricas sólidas?<br/><br/>"
            "<b>Conclusión de Auditoría:</b> La obra goza de una salud narrativa y editorial excepcional. La combinación de rigor astrofísico y calidez humana convierte a <i>SOMBRA</i> en una obra cumbre de la ciencia ficción dura en lengua española.",
            body_style
        )
    ]))
    
    doc.build(story, canvasmaker=ReportCanvas)
    print(f"Informe PDF generado con éxito: {output_filename}")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    out_root = os.path.join(base_dir, "Informe_Recapitulacion_y_Auditoria_Coherencia.pdf")
    out_novela = os.path.join(base_dir, "novela", "Informe_Recapitulacion_y_Auditoria_Coherencia.pdf")
    
    generate_report_pdf(out_root)
    shutil.copyfile(out_root, out_novela)
    print(f"Copia sincronizada en: {out_novela}")
