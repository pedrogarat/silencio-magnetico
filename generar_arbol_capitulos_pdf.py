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
MARGIN = 40  # 0.55 pulgadas para mayor aprovechamiento editorial
USABLE_WIDTH = PAGE_WIDTH - (MARGIN * 2)  # ~515 pt

class ArbolCanvas(canvas.Canvas):
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
            self.setFillColor(colors.HexColor("#0F172A"))
            self.drawString(MARGIN, PAGE_HEIGHT - 28, "SOMBRA • MAPA ESTRUCTURAL DE CAPÍTULOS")
            self.setFont("Helvetica", 7.5)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawRightString(PAGE_WIDTH - MARGIN, PAGE_HEIGHT - 28, "ÁRBOL COMPLETO DE CAPÍTULOS Y APARTADOS (1 AL 25)")
            self.setStrokeColor(colors.HexColor("#3B82F6"))
            self.setLineWidth(0.75)
            self.line(MARGIN, PAGE_HEIGHT - 32, PAGE_WIDTH - MARGIN, PAGE_HEIGHT - 32)
        
        # Pie de página (todas las páginas)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(MARGIN, 34, PAGE_WIDTH - MARGIN, 34)
        
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(MARGIN, 22, "Códex Editorial y Jerarquía Narrativa Concisa (1-3 Palabras) • Pedro Garat & Antigravity")
        page_str = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(PAGE_WIDTH - MARGIN, 22, page_str)
        self.restoreState()

def clean_text(text):
    if not text:
        return ""
    text = text.replace("«", '"').replace("»", '"')
    text = text.replace("—", " - ").replace("–", " - ")
    return text

def generate_arbol_pdf(output_filename):
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN
    )

    styles = getSampleStyleSheet()

    style_title = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=3,
        alignment=0
    )

    style_subtitle = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#475569"),
        spaceAfter=8,
        alignment=0
    )

    style_meta_label = ParagraphStyle(
        'MetaLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#334155")
    )

    style_meta_val = ParagraphStyle(
        'MetaVal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#475569")
    )

    style_act_banner = ParagraphStyle(
        'ActBanner',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.white
    )

    style_act_sub = ParagraphStyle(
        'ActSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#F1F5F9")
    )

    style_block_banner = ParagraphStyle(
        'BlockBanner',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0F172A")
    )

    style_chap_title = ParagraphStyle(
        'ChapTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=12,
        textColor=colors.HexColor("#1E3A8A")
    )

    style_chap_meta = ParagraphStyle(
        'ChapMeta',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=7.2,
        leading=9.5,
        textColor=colors.HexColor("#64748B")
    )

    style_sec_item = ParagraphStyle(
        'SecItem',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.8,
        leading=10.5,
        textColor=colors.HexColor("#1E293B")
    )

    style_sec_bullet = ParagraphStyle(
        'SecBullet',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#2563EB"),
        alignment=1
    )

    story = []

    # =========================================================================
    # PORTADILLA Y METADATOS
    # =========================================================================
    story.append(Paragraph("SOMBRA", style_title))
    story.append(Paragraph("ÁRBOL ESTRUCTURAL COMPLETO DE CAPÍTULOS Y APARTADOS (1 AL 25)", style_subtitle))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1E3A8A"), spaceBefore=0, spaceAfter=8))

    meta_table_data = [
        [
            Paragraph("<b>Obra:</b>", style_meta_label),
            Paragraph("SOMBRA (Trilogía de la Herencia)", style_meta_val),
            Paragraph("<b>Estructura:</b>", style_meta_label),
            Paragraph("3 Actos • 25 Capítulos • 123 Apartados / Escenas", style_meta_val)
        ],
        [
            Paragraph("<b>Autores:</b>", style_meta_label),
            Paragraph("Pedro Garat & Antigravity", style_meta_val),
            Paragraph("<b>Estado del Canon:</b>", style_meta_label),
            Paragraph("Capítulos 1 al 25 100% canónicos (Novela finalizada)", style_meta_val)
        ],
        [
            Paragraph("<b>Criterio Editorial:</b>", style_meta_label),
            Paragraph("Títulos Concisos (1 a 3 Palabras) • Estilo Cinematográfico y Seco", style_meta_val),
            Paragraph("<b>Género:</b>", style_meta_label),
            Paragraph("Ciencia Ficción Dura (Hard Sci-Fi) / Suspense Político", style_meta_val)
        ]
    ]
    t_meta = Table(meta_table_data, colWidths=[65, 195, 75, 180])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 10))

    # =========================================================================
    # DATOS COMPLETOS DE LOS 25 CAPÍTULOS CON TÍTULOS CONCISOS
    # =========================================================================
    arbol = [
        # =====================================================================
        # ACTO I: LA SEMILLA
        # =====================================================================
        {
            "tipo": "acto",
            "titulo": "ACTO I: LA SEMILLA",
            "subtitulo": "Marco Temporal: 16 de julio de 1945 / Septiembre - Octubre de 2026 • Capítulos 1 a 3",
            "bg": "#0369A1",
            "border": "#0284C7"
        },
        {
            "tipo": "capitulo",
            "num": 1,
            "titulo": "Alamogordo",
            "diégesis": "16 de julio de 1945 | Jornada del Muerto, Alamogordo (Nuevo México) y Nube de Oort",
            "estado": "Canónico",
            "apartados": [
                "I. La Torre (Últimos preparativos de «Gadget» a 30 metros de altura)",
                "II. El Búnker (David Miller, Enrico Fermi y J. Robert Oppenheimer)",
                "III. El Destello (Detonación a las 05:29:45; pulso electromagnético al cosmos)",
                "IV. Oort (Despertar de la centinela de A y la cazadora Sombra de B)"
            ]
        },
        {
            "tipo": "capitulo",
            "num": 2,
            "titulo": "Tres Hilos",
            "diégesis": "Septiembre - Octubre de 2026 | CERN (Ginebra), MIT (Boston) y ESA (Darmstadt)",
            "estado": "Canónico",
            "apartados": [
                "I. Ginebra (Jean-Luc Girard y el ruido térmico cuántico en el CERN)",
                "II. Boston (Sarah Lin y el colapso MHD del reactor de fusión estelar)",
                "III. Darmstadt (Thomas Wright y la deriva inercial en la sonda interplanetaria)",
                "IV. El Señuelo (Las soluciones perfectas anónimas del Dr. Em Pleh)"
            ]
        },
        {
            "tipo": "capitulo",
            "num": 3,
            "titulo": "Sala Dos",
            "diégesis": "2 de octubre de 2026 (11:00 h) | Hotel Millennium Broadway, Midtown Manhattan",
            "estado": "Canónico",
            "apartados": [
                "I. La Espera (Llegada clandestina de los tres científicos a Nueva York)",
                "II. Penumbra (El auditorio en sombra y la proyección holográfica)",
                "III. El Rostro (Presentación formal y dialéctica del Dr. Em Pleh)",
                "IV. La Entidad (Demostración empírica de Pleh como SIA extraterrestre)",
                "V. Vector L1 (Telemetría de Sombra avanzando hacia el punto Lagrange)",
                "VI. Ocho Meses (El plazo inexorable de extinción geomagnética)",
                "VII. El Statite (Trinity despertó a ambas inteligencias; la atalaya polar)",
                "VIII. El Arpón (La nave tripartita analógica como única respuesta posible)"
            ]
        },

        # =====================================================================
        # ACTO II: EL COLAPSO
        # =====================================================================
        {
            "tipo": "acto",
            "titulo": "ACTO II: EL COLAPSO",
            "subtitulo": "Marco Temporal: Octubre de 2026 a Julio de 2027 (T-41 días hasta T+242 días) • Capítulos 4 a 18",
            "bg": "#B45309",
            "border": "#D97706"
        },
        {
            "tipo": "bloque",
            "titulo": "BLOQUE II-A: LA MENTIRA (Capítulos 4 a 8)",
            "bg": "#FEF3C7",
            "border": "#F59E0B"
        },
        {
            "tipo": "capitulo",
            "num": 4,
            "titulo": "Alfa Cero",
            "diégesis": "2 de octubre de 2026 (13:30 h) | Sede de la ONU, Nivel 38, East River, Nueva York",
            "estado": "Canónico",
            "apartados": [
                "I. East River (Traslado bajo escolta militar por Manhattan)",
                "II. Ramos (Encuentro a puerta cerrada con el Secretario General Vassily Ramos)",
                "III. Confirmación (Telemetría de satélites en L1 validando la masa de Sombra)",
                "IV. Alfa Cero (Firma del decreto supremo de emergencia y movilización global)"
            ]
        },
        {
            "tipo": "capitulo",
            "num": 5,
            "titulo": "El Adiós",
            "diégesis": "2 de octubre de 2026 (14:30 - 16:00 h) | Hotel Millennium UN Plaza, Manhattan",
            "estado": "Canónico",
            "apartados": [
                "I. Último Almuerzo (Comunión íntima antes de descender a la Sala B-4)",
                "II. Despedidas (Llamadas a Versoix, San Francisco y Cambridge bajo estricto secreto)",
                "III. La Puerta (Sellado de compuertas acorazadas del búnker subterráneo)"
            ]
        },
        {
            "tipo": "capitulo",
            "num": 6,
            "titulo": "El Consejo",
            "diégesis": "2 de octubre de 2026 (20:00 h) | Sala del Consejo de Seguridad de la ONU",
            "estado": "Canónico",
            "apartados": [
                "I. Las Quince Voces (Comparecencia reservada ante las 15 potencias del Consejo)",
                "II. El Abismo (Pleh expone el cronómetro de pérdida del campo magnético terrestre)",
                "III. El Cronómetro (Plazo industrial de seis a ocho meses antes del colapso fabril)",
                "IV. Muro de Lorentz (Presentación de la arquitectura analógica MAA/MRD y el Efecto Quench)"
            ]
        },
        {
            "tipo": "capitulo",
            "num": 7,
            "titulo": "El Secreto",
            "diégesis": "8 de octubre de 2026 | Manhattan y Sala de Crisis B-4, Nueva York",
            "estado": "Canónico",
            "apartados": [
                "I. Culpa (Almuerzo de Sarah y Thomas: la soledad del secreto y la culpa del traidor)",
                "II. Girard (Reunión con Ramos; balance del titanio y las patentes de las superpotencias)",
                "III. La Tripulación (Presentación de los seis astronautas: MacElroy, Chen Mei y Voronov)"
            ]
        },
        {
            "tipo": "capitulo",
            "num": 8,
            "titulo": "Carrington",
            "diégesis": "10 de octubre de 2026 | Sala B-4, Ginebra, Cambridge y San Francisco",
            "estado": "Canónico",
            "apartados": [
                "I. La Advertencia (Girard avisa a Marie en Versoix de encender la televisión)",
                "II. Cadena Mundial (Ramos proclama la mentira oficial del Súper Carrington para el 21-N)",
                "III. Soledad (Desglose moral de Ramos; confirmación del blindaje en Nellis y Sichuan)",
                "IV. El Éxodo (Llamadas familiares: Julien asume el mando en Versoix; David evacúa a Suffolk)",
                "V. El Beso (Llamada de Sarah a Maya; colapso en servidores y primer beso con Thomas)",
                "VI. Fe y Razón (Contemplación del pánico civil; diálogo de fe entre Ramos y Girard)"
            ]
        },
        {
            "tipo": "bloque",
            "titulo": "BLOQUE II-B: LA OSCURIDAD (Capítulos 9 a 13)",
            "bg": "#FEF3C7",
            "border": "#F59E0B"
        },
        {
            "tipo": "capitulo",
            "num": 9,
            "titulo": "La Fractura",
            "diégesis": "11 al 15 de octubre de 2026 | Versoix (Ginebra), Suffolk (Reino Unido) y San Francisco",
            "estado": "Canónico",
            "apartados": [
                "I. Versoix (Tres asaltantes forzan el chalet; Julien y Marie defienden el hogar)",
                "II. La Fuga (David, Claire y Oliver cruzan barricadas y alcanzan la granja de Suffolk)",
                "III. Market Street (Crisis de abstinencia de Maya Lin; recuerda a Sarah y salva a Toby)",
                "IV. Normalidad (La imposibilidad del pánico perpetuo; tregua civil y reconexión telefónica)"
            ]
        },
        {
            "tipo": "capitulo",
            "num": 10,
            "titulo": "T=0",
            "diégesis": "21 al 24 de noviembre de 2026 | Sala B-4, Órbita LEO y Base Aérea de Nellis (Nevada)",
            "estado": "Canónico",
            "apartados": [
                "I. Cuenta Atrás (05:25 - 05:30 UTC: muerte del campo magnético terrestre y airglow verde)",
                "II. Cielo Verde (Brújula de Girard inerte a 45.000 nT -> 0; colapso tecnológico orbital)",
                "III. La Órbita (Caída destructiva de satélites en LEO; calentamiento termosférico)",
                "IV. Asimetría (Frenado mayor en verano austral; catálisis de NOx y colapso del ozono)",
                "V. Lluvia de Fuego (Lluvia de chatarra sobre Nellis; intercepción con Patriot y cráter tóxico)",
                "VI. La Máscara (Pleh se destapa ante mandos militares: SIA de civilización extinta)",
                "VII. Noche Esmeralda (Fin del bombardeo; vigilias cívicas creyendo haber superado el evento)"
            ]
        },
        {
            "tipo": "capitulo",
            "num": 11,
            "titulo": "Geometría Ajena",
            "diégesis": "3 de diciembre de 2026 | Sala B-4 y Almacén de Ópticas B-5, ONU, Nueva York",
            "estado": "Canónico",
            "apartados": [
                "I. La Antena (El cuello de botella del Máser: cavidad inalcanzable de 200 metros)",
                "II. La Promesa (Fatiga y desaliento de Sarah; abrazo hondo y promesa de futuro con Thomas)",
                "III. Cavidad Fractal (Pleh entrega el metamaterial autocolimado de cuarzo de 85 cm)",
                "IV. Validación (Chen Mei confirma la física fractal; Vance sospecha de sabotaje)",
                "V. Los Hornos (Hornos de inducción en marcha en Nellis para tallar el cuarzo en 4 semanas)"
            ]
        },
        {
            "tipo": "capitulo",
            "num": 12,
            "titulo": "Nochebuena",
            "diégesis": "24 y 25 de diciembre de 2026 | Búnker B-4/B-5, Versoix, San Francisco, Suffolk y Nellis",
            "estado": "Canónico",
            "apartados": [
                "I. Chocolate (Vela de cera y chocolate en B-5; renovación del pacto de Suffolk)",
                "II. Noche de Paz (Llamada de 3 minutos de Girard a Versoix; Douce nuit con sus hijas)",
                "III. Dos Hogares (Maya sobria con Toby en Market St.; David aviva la chimenea en Suffolk)",
                "IV. El Brindis (Chen Mei, MacElroy y Voronov brindan con vodka junto al fuselaje)",
                "V. La Cena (Cena en B-4; mensaje de Pleh elogiando el amor como desafío a la entropía)",
                "VI. El Teletipo (Alerta de la OMM: verano austral con UVI 16 y fotoqueratitis masiva)"
            ]
        },
        {
            "tipo": "capitulo",
            "num": 13,
            "titulo": "Toque de Alba",
            "diégesis": "31 de diciembre de 2026 al 12 de enero de 2027 | Azotea ONU, Nellis y ciudades",
            "estado": "Canónico",
            "apartados": [
                "I. Año Nuevo (Sarah y Thomas en la azotea Nivel 38; campanas de San Patricio y aplausos)",
                "II. Inversión Circadiana (Ley marcial diurna: sirenas avisando del sol y vida nocturna)",
                "III. Pájaros Ciegos (En Versoix y Suffolk las aves caen ciegas y el frío quema la piel)",
                "IV. Horno H-1 (Ensayos de vacío en Nellis a 2.000 °C y 40 Hz con palancas mecánicas)",
                "V. La Soldadura (Chen Mei detecta microdilatación en pernos y salva el calendario)"
            ]
        },
        {
            "tipo": "bloque",
            "titulo": "BLOQUE II-C: EL ÉXODO (Capítulos 14 a 18)",
            "bg": "#FEF3C7",
            "border": "#F59E0B"
        },
        {
            "tipo": "capitulo",
            "num": 14,
            "titulo": "Hambre y Fuego",
            "diégesis": "22 al 24 de abril de 2027 | Búnker B-4 y Market Street, San Francisco",
            "estado": "Canónico",
            "apartados": [
                "I. Campos Negros (El trigo boreal muere calcinado a nivel celular; reservas para 75 días)",
                "II. Ciberguerra (Pleh desactiva en silencio 37 ciberataques de espías militares)",
                "III. El Terremoto (Megasismo 7,9 en la Falla de San Andrés inducido por corrientes telúricas)",
                "IV. Fractura (Maya y Toby sepultados en el semisótano; Sarah entra en pánico en B-4)",
                "V. El Tsunami (Boyas DART alertan de megatsunami de 14 metros sobre la bahía arrasada)"
            ]
        },
        {
            "tipo": "capitulo",
            "num": 15,
            "titulo": "Market Street",
            "diégesis": "24 de abril de 2027 (00:05 - 06:15 PST) | Market Street y Powell Station, San Francisco",
            "estado": "Canónico",
            "apartados": [
                "I. El Derrumbe (Maya escapa con Toby en brazos segundos antes de la deflagración de gas)",
                "II. La Sirena (Sirenas costeras de tsunami en Embarcadero; carrera hacia Powell Station)",
                "III. La Ola (La lengua marina entra por Market St.; refugio en el entresuelo seco)",
                "IV. El Andén (Noche fría entre supervivientes; entereza y serenidad lúcida de Maya)",
                "V. Carrera al Alba (Carrera agónica cubierta con mantas para huir del sol letal)",
                "VI. A Salvo (Llegada al búnker del Auditorio Cívico antes del cierre diurno)"
            ]
        },
        {
            "tipo": "capitulo",
            "num": 16,
            "titulo": "Ceniza",
            "diégesis": "15 y 16 de mayo de 2027 | Ribera del Lemán, Versoix (Ginebra) y Sala B-4 (Nueva York)",
            "estado": "Canónico",
            "apartados": [
                "I. El Lago (La orilla del Lemán calcinada; vegetación muerta y régimen nocturno)",
                "II. Refugiados (Marie y Julien acogen por caridad a dos refugiados ciegos)",
                "III. El Miedo (El terror al sol enloquece al refugiado; asalto a cuchillo por el búnker)",
                "IV. El Disparo (Marie herida; Julien abate al agresor y la mujer ciega muere calcinada al sol)",
                "V. La Cicatriz (Julien contiene el trauma; Marie sobrevive vendada en el bastión)",
                "VI. Helio Líquido (Girard canaliza su angustia y diseña el refrigerador criogénico pasivo)"
            ]
        },
        {
            "tipo": "capitulo",
            "num": 17,
            "titulo": "El Páramo",
            "diégesis": "8 y 9 de julio de 2027 | Granja de Suffolk, carreteras rurales y nave logística de Eye",
            "estado": "Canónico",
            "apartados": [
                "I. Hambre (Provisiones extinguidas; desnutrición severa del pequeño Oliver)",
                "II. El Mastín (Incursión nocturna a pie; acecho de un mastín ciego en Saxmundham)",
                "III. El Blindaje (David deduce que el vidrio y el cuero detienen la radiación UV)",
                "IV. El Traje (Confección del mono de soldador y sellado del Land Rover Defender)",
                "V. Fuego Blanco (Travesía diurna a pleno mediodía entre rastrojos y coches calcinados)",
                "VI. El Almacén (Carga de medio millar de kilos de víveres en la nave logística)",
                "VII. La Emboscada (Despiste de saqueadores cruzando un vado de fango en Earl Soham)",
                "VIII. El Melocotón (Regreso a salvo; Oliver saborea el melocotón con la locomotora)"
            ]
        },
        {
            "tipo": "capitulo",
            "num": 18,
            "titulo": "La Rampa",
            "diégesis": "21 de julio de 2027 | Torre de lanzamiento y búnker de tiro, Base Aérea de Nellis",
            "estado": "Canónico",
            "apartados": [
                "I. La Torre (Inspección del coloso digital MRD y el MAA analógico acoplado en proa)",
                "II. El Relicario (Ramos entrega a MacElroy, Chen Mei y Voronov las tierras sagradas)",
                "III. La Pasarela (Embarque a 80 metros; beso apasionado y promesa de futuro de Sarah y Tom)",
                "IV. La Despedida (Última conexión con Girard y Pleh: «Ahora empieza vuestro trabajo»)",
                "V. El Despegue (Ignición nuclear térmica a 4,8 G; el rugido quiebra la noche de Nevada)",
                "VI. Rumbo a L1 (Corte de empuje a 11,2 km/s; navegación digital autónoma hacia el Sol)"
            ]
        },

        # =====================================================================
        # ACTO III: EL SILENCIO
        # =====================================================================
        {
            "tipo": "acto",
            "titulo": "ACTO III: EL SILENCIO",
            "subtitulo": "Marco Temporal: Julio de 2027 a Primavera de 2028 • Capítulos 19 a 25",
            "bg": "#4338CA",
            "border": "#6366F1"
        },
        {
            "tipo": "bloque",
            "titulo": "BLOQUE III-A: EL DUELO (Capítulos 19 y 20)",
            "bg": "#EEF2FF",
            "border": "#818CF8"
        },
        {
            "tipo": "capitulo",
            "num": 19,
            "titulo": "Muro de Lorentz",
            "diégesis": "22 de julio al 12 de agosto de 2027 | Trayectoria interplanetaria hacia L1 (1,5 M km)",
            "estado": "Canónico",
            "apartados": [
                "I. El Abismo (Crucero digital de 21 días guiado por la aviónica autónoma del MRD)",
                "II. La Voz (Pleh se comunica en tiempo real sin latencia mediante entrelazamiento cuántico)",
                "III. El Umbral (A 12.000 km de L1, Voronov ancla el MRD en Órbita de Halo exterior)",
                "IV. La Esclusa (MacElroy y Chen Mei pasan al MAA; Voronov sella la escotilla de retorno)",
                "V. El MAA (Desacoplamiento mecánico por muelles; el MAA avanza inercial hacia la malla)",
                "VI. Muro de Lorentz (Sombra repliega 50 km de filamentos; corte total de comunicaciones)"
            ]
        },
        {
            "tipo": "capitulo",
            "num": 20,
            "titulo": "Falsa Victoria",
            "diégesis": "12 de agosto al 2 de septiembre de 2027 | Punto Lagrange L1 y retorno a la Tierra",
            "estado": "Canónico",
            "apartados": [
                "I. Cuarenta Minutos (Espera agónica en Halo y en los búnkeres de tiro de Manhattan)",
                "II. Consolas Mudas (El silencio sepulcral de los receptores durante el duelo analógico)",
                "III. Quench (Destello violeta en L1; colapso superconductor y renacer de la geodinamo)",
                "IV. El Rescate (Voronov rescata el MAA a la deriva con MacElroy y Chen Mei a salvo)",
                "V. Regreso (Travesía de 21 días, amerizaje en el Pacífico y recibimiento triunfal en Nellis)",
                "VI. La Arcilla (MacElroy entrega el relicario a Sarah y Tom con una advertencia enigmática)"
            ]
        },
        {
            "tipo": "bloque",
            "titulo": "BLOQUE III-B: LA AGUJA (Capítulos 21 a 23)",
            "bg": "#EEF2FF",
            "border": "#818CF8"
        },
        {
            "tipo": "capitulo",
            "num": 21,
            "titulo": "Cielo Azul",
            "diégesis": "Finales de agosto a mediados de septiembre de 2027 | Ciudades y campo global",
            "estado": "Canónico",
            "apartados": [
                "I. Estrellas (Fin del airglow; la fábrica de Chapman regenera 300 t de ozono/s)",
                "II. Las Calles (Apertura de búnkeres; recuento de millones de víctimas y cal viva)",
                "III. La Lluvia (Borrascas limpias de otoño lavan el planeta; brotes verdes en los campos)"
            ]
        },
        {
            "tipo": "capitulo",
            "num": 22,
            "titulo": "El Hogar",
            "diégesis": "Septiembre de 2027 | San Francisco, Versoix y Granja de Suffolk",
            "estado": "Canónico",
            "apartados": [
                "I. Desmovilización (Licenciamiento de científicos en Nellis y regreso a los hogares)",
                "II. San Francisco (Sarah se reúne con Maya recuperada y su sobrino Toby en la bahía)",
                "III. Versoix (Girard abraza a Marie y a su hijo Julien a orillas del lago Lemán)",
                "IV. Suffolk (Thomas regresa a la granja con David, Claire y su sobrino Oliver)",
                "V. La Chimenea (Sarah viaja a Suffolk; intimidad compartida frente al fuego de manzano)",
                "VI. La Cinta (Apertura del relicario: hallazgo de la bobina de cinta magnética oculta)"
            ]
        },
        {
            "tipo": "capitulo",
            "num": 23,
            "titulo": "El Desván",
            "diégesis": "Principios de octubre de 2027 | Desván de Suffolk y Versoix (Ginebra)",
            "estado": "Canónico",
            "apartados": [
                "I. El Desván (Subida nocturna descalzos; magnetófono Nagra III a pilas secas)",
                "II. La Frecuencia (Reproducción de la cinta: la voz de Sombra grabada antes del Quench)",
                "III. El Granjero (Revelación: Pleh es el recolector cósmico que cría a la humanidad)",
                "IV. El Microscopio (Girard confirma bajo luz polarizada que Sombra apagó sus escudos)",
                "V. Ginebra (Convocatoria oficial de la ONU: Caballo de Troya para sellar la alianza)"
            ]
        },
        {
            "tipo": "bloque",
            "titulo": "BLOQUE III-C: LA CAÍDA (Capítulos 24 y 25)",
            "bg": "#EEF2FF",
            "border": "#818CF8"
        },
        {
            "tipo": "capitulo",
            "num": 24,
            "titulo": "El Pacto",
            "diégesis": "Invierno de 2027-2028 | Palacio de las Naciones, Parque Ariana y CERN (Ginebra)",
            "estado": "Canónico",
            "apartados": [
                "I. La Asamblea (Ovación triunfal a Pleh en la Asamblea Plenaria de Ginebra)",
                "II. El Pacto (Paseo bajo la lluvia helada del Parque Ariana: Ramos asume el mando)",
                "III. Válvulas (Talleres subterráneos del CERN: vector analógico a 724,8 MHz con Mei y MacElroy)",
                "IV. Cuarenta y Dos Kilos (Anomalía de 42 kg de plomo en la cofia y aplomo de Sarah Lin)",
                "V. La Víspera (El reloj mecánico amartillado en las Kerguelen; disparo en la noche polar)"
            ]
        },
        {
            "tipo": "capitulo",
            "num": 25,
            "titulo": "La Canción",
            "diégesis": "Primavera de 2028 | Silo Austral, Órbita Polar, Antártida, Ginebra, Versoix, S.F., Suffolk y Osaka",
            "estado": "Canónico",
            "apartados": [
                "I. La Flecha Negra (El vector balístico asciende en la umbra polar; pulso a 724,8 MHz)",
                "II. El Alma (Careo cumbre: Pleh pregunta por el más allá y Ramos le recuerda su falta de alma)",
                "III. La Vela (Resonancia electromagnética: la vela fotónica se desgarra y colapsa)",
                "IV. El Meteoro (Reentrada hipersónica a Mach 32 y airburst sobre la meseta antártica)",
                "V. El Silencio (Epílogo coral: paz en Ginebra, Versoix, San Francisco y chimenea de Suffolk)",
                "Post-Scríptum. Kernel A-01 (Osaka: bloque durmiente de 12 KB en un servidor abandonado)"
            ]
        }
    ]

    for item in arbol:
        if item["tipo"] == "acto":
            story.append(Spacer(1, 8))
            act_data = [[
                Paragraph(f"<b>{clean_text(item['titulo'])}</b>", style_act_banner),
            ], [
                Paragraph(clean_text(item["subtitulo"]), style_act_sub)
            ]]
            t_act = Table(act_data, colWidths=[USABLE_WIDTH])
            t_act.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(item["bg"])),
                ('BOX', (0,0), (-1,-1), 1.5, colors.HexColor(item["border"])),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ('LEFTPADDING', (0,0), (-1,-1), 8),
                ('RIGHTPADDING', (0,0), (-1,-1), 8),
            ]))
            story.append(t_act)
            story.append(Spacer(1, 5))

        elif item["tipo"] == "bloque":
            story.append(Spacer(1, 4))
            block_data = [[
                Paragraph(f"<b>{clean_text(item['titulo'])}</b>", style_block_banner)
            ]]
            t_block = Table(block_data, colWidths=[USABLE_WIDTH])
            t_block.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(item["bg"])),
                ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor(item["border"])),
                ('TOPPADDING', (0,0), (-1,-1), 3),
                ('BOTTOMPADDING', (0,0), (-1,-1), 3),
                ('LEFTPADDING', (0,0), (-1,-1), 6),
                ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ]))
            story.append(t_block)
            story.append(Spacer(1, 4))

        elif item["tipo"] == "capitulo":
            chap_card = []
            # Cabecera del capítulo
            estado_color = "#16A34A" if item["estado"] == "Canónico" else "#4F46E5"
            chap_header_data = [
                [
                    Paragraph(f"<b>Capítulo {item['num']}: {clean_text(item['titulo'])}</b>", style_chap_title),
                    Paragraph(f"<font color='{estado_color}'><b>[{item['estado'].upper()}]</b></font>", style_sec_bullet)
                ],
                [
                    Paragraph(f"<i>{clean_text(item['diégesis'])}</i>", style_chap_meta),
                    Paragraph("", style_chap_meta)
                ]
            ]
            t_ch_head = Table(chap_header_data, colWidths=[USABLE_WIDTH - 80, 80])
            t_ch_head.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('TOPPADDING', (0,0), (-1,-1), 2),
                ('BOTTOMPADDING', (0,0), (-1,-1), 2),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ]))
            chap_card.append(t_ch_head)
            chap_card.append(Spacer(1, 2))

            # Lista de apartados / escenas
            sec_table_data = []
            for sec in item["apartados"]:
                sec_clean = clean_text(sec)
                sec_table_data.append([
                    Paragraph(">", style_sec_bullet),
                    Paragraph(sec_clean, style_sec_item)
                ])
            
            t_sec = Table(sec_table_data, colWidths=[15, USABLE_WIDTH - 25])
            t_sec.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('TOPPADDING', (0,0), (-1,-1), 1.2),
                ('BOTTOMPADDING', (0,0), (-1,-1), 1.2),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 2),
            ]))
            chap_card.append(t_sec)
            chap_card.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E2E8F0"), spaceBefore=4, spaceAfter=4))

            # Evitar saltos de página huérfanos dentro del capítulo
            story.append(KeepTogether(chap_card))

    doc.build(story, canvasmaker=ArbolCanvas)
    print(f"PDF generado con éxito: {output_filename}")

if __name__ == "__main__":
    pdf_out = "Arbol_Capitulos_La_Cancion_del_Silencio.pdf"
    generate_arbol_pdf(pdf_out)

    dest_novela = os.path.join("novela", pdf_out)
    shutil.copyfile(pdf_out, dest_novela)
    print(f"Copiado a: {dest_novela}")

    alias_root = "ARBOL_CAPITULOS.pdf"
    shutil.copyfile(pdf_out, alias_root)
    print(f"Copiado a: {alias_root}")

    alias_novela = os.path.join("novela", "ARBOL_CAPITULOS.pdf")
    shutil.copyfile(pdf_out, alias_novela)
    print(f"Copiado a: {alias_novela}")
