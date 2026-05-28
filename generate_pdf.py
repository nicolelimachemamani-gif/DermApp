import os
import sys
import re
import subprocess

# Asegurar la instalación de reportlab
try:
    import reportlab
except ImportError:
    print("Instalando reportlab para generación de PDF...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"])

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MD_PATH = os.path.join(BASE_DIR, "reporte_tecnico.md")
PDF_PATH = os.path.join(BASE_DIR, "reporte_tecnico.pdf")

def md_to_pdf_html(text):
    """Convierte marcas básicas de Markdown a etiquetas HTML compatibles con Paragraph de ReportLab."""
    # Negrita (**text** -> <b>text</b>)
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    # Cursiva (*text* -> <i>text</i>)
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    # Código en línea (`code` -> <font face="Courier">code</font>)
    text = re.sub(r'`(.*?)`', r'<font face="Courier" color="#e06c75"><b>\1</b></font>', text)
    return text

def parse_markdown_to_story(md_path, styles):
    story = []
    
    if not os.path.exists(md_path):
        print(f"Error: No se encontró el archivo {md_path}")
        return None
        
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Separar por líneas
    lines = content.split("\n")
    
    in_code_block = False
    code_lines = []
    
    for line in lines:
        stripped = line.strip()
        
        # Manejo de bloques de código (```)
        if stripped.startswith("```"):
            if in_code_block:
                # Terminar bloque de código
                code_text = "<br/>".join(code_lines)
                code_p = Paragraph(code_text, styles['CodeBlock'])
                
                # Envolver en tabla con fondo gris para estilizar el contenedor de código
                t = Table([[code_p]], colWidths=[468])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#0f141c')),
                    ('PADDING', (0,0), (-1,-1), 10),
                    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 12),
                    ('TOPPADDING', (0,0), (-1,-1), 12),
                    ('LEFTPADDING', (0,0), (-1,-1), 12),
                    ('RIGHTPADDING', (0,0), (-1,-1), 12),
                ]))
                story.append(t)
                story.append(Spacer(1, 10))
                in_code_block = False
                code_lines = []
            else:
                in_code_block = True
            continue
            
        if in_code_block:
            # Reemplazar espacios y caracteres especiales de código para ReportLab HTML Paragraph
            safe_code = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            # Preservar tabulaciones/indentación básica usando espacios no rompibles
            safe_code = safe_code.replace('    ', '&nbsp;&nbsp;&nbsp;&nbsp;').replace('  ', '&nbsp;&nbsp;')
            code_lines.append(safe_code)
            continue
            
        # Manejo de líneas horizontales (---)
        if stripped == "---":
            story.append(Spacer(1, 8))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#d1d5db'), spaceBefore=5, spaceAfter=15))
            continue
            
        # Manejo de títulos y encabezados
        if stripped.startswith("# "):
            title_text = md_to_pdf_html(stripped[2:])
            story.append(Paragraph(title_text, styles['DocTitle']))
            story.append(Spacer(1, 15))
            continue
            
        if stripped.startswith("## "):
            h2_text = md_to_pdf_html(stripped[3:])
            story.append(Paragraph(h2_text, styles['DocH2']))
            story.append(Spacer(1, 10))
            continue
            
        if stripped.startswith("### "):
            h3_text = md_to_pdf_html(stripped[4:])
            story.append(Paragraph(h3_text, styles['DocH3']))
            story.append(Spacer(1, 8))
            continue
            
        # Manejo de citas / Notas (> [!NOTE])
        if stripped.startswith(">"):
            note_content = stripped[1:].strip()
            if note_content.startswith("[!NOTE]") or note_content.startswith("[!TIP]") or note_content.startswith("[!IMPORTANT]"):
                note_content = note_content.replace("[!NOTE]", "<b>NOTA:</b>").replace("[!TIP]", "<b>CONSEJO:</b>").replace("[!IMPORTANT]", "<b>IMPORTANTE:</b>")
            
            note_html = md_to_pdf_html(note_content)
            note_p = Paragraph(note_html, styles['NoteText'])
            t = Table([[note_p]], colWidths=[468])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f3f4f6')),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#9ca3af')),
                ('LINEBEFORE', (0,0), (0,-1), 4, colors.HexColor('#1f2937')), # Borde izquierdo grueso
                ('PADDING', (0,0), (-1,-1), 8),
            ]))
            story.append(t)
            story.append(Spacer(1, 12))
            continue
            
        # Manejo de listas con viñetas (bullet points: - o *)
        if stripped.startswith("- ") or stripped.startswith("* "):
            bullet_text = md_to_pdf_html(stripped[2:])
            story.append(Paragraph(bullet_text, styles['DocBullet']))
            story.append(Spacer(1, 4))
            continue
            
        # Párrafos regulares
        if stripped:
            para_html = md_to_pdf_html(stripped)
            story.append(Paragraph(para_html, styles['DocBody']))
            story.append(Spacer(1, 10))
        else:
            # Doble salto de línea genera un pequeño espaciador
            story.append(Spacer(1, 4))
            
    return story

def build_pdf():
    print(f"Compilando {MD_PATH} a PDF...")
    
    # Crear el documento PDF
    # Márgenes de 0.75 pulgadas (54 puntos)
    doc = SimpleDocTemplate(
        PDF_PATH,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    # Inicializar hojas de estilo
    styles = getSampleStyleSheet()
    
    # Agregar estilos personalizados profesionales
    styles.add(ParagraphStyle(
        name='DocTitle',
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor('#1e3a8a'), # Azul oscuro elegante
        alignment=TA_CENTER,
        spaceAfter=15
    ))
    
    styles.add(ParagraphStyle(
        name='DocH2',
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=colors.HexColor('#0f172a'), # Casi negro
        spaceBefore=15,
        spaceAfter=10,
        keepWithNext=True
    ))
    
    styles.add(ParagraphStyle(
        name='DocH3',
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor('#2563eb'), # Azul medio brillante
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    ))
    
    styles.add(ParagraphStyle(
        name='DocBody',
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155'), # Gris pizarra oscuro legible
        alignment=TA_JUSTIFY,
        spaceAfter=8
    ))
    
    styles.add(ParagraphStyle(
        name='DocBullet',
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155'),
        leftIndent=20,
        firstLineIndent=-10,
        spaceAfter=4
    ))
    
    styles.add(ParagraphStyle(
        name='NoteText',
        fontName='Helvetica-Oblique',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#1e293b')
    ))
    
    styles.add(ParagraphStyle(
        name='CodeBlock',
        fontName='Courier',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#abb2bf') # Color gris claro tipo Atom One Dark
    ))
    
    # Convertir el markdown en objetos ReportLab (story)
    story = parse_markdown_to_story(MD_PATH, styles)
    
    if story:
        # Función para pie de página y encabezado en cada hoja
        def add_header_footer(canvas, doc):
            canvas.saveState()
            
            # Pie de página
            canvas.setFont('Helvetica', 8)
            canvas.setFillColor(colors.HexColor('#64748b'))
            canvas.drawString(54, 30, "Manual Técnico DermalAI - Primera Unidad")
            canvas.drawRightString(doc.pagesize[0] - 54, 30, f"Página {doc.page}")
            
            # Línea decorativa pie de página
            canvas.setStrokeColor(colors.HexColor('#cbd5e1'))
            canvas.setLineWidth(0.5)
            canvas.line(54, 42, doc.pagesize[0] - 54, 42)
            
            # Encabezado (solo a partir de la página 2)
            if doc.page > 1:
                canvas.setFont('Helvetica-Oblique', 8)
                canvas.setFillColor(colors.HexColor('#64748b'))
                canvas.drawString(54, doc.pagesize[1] - 35, "DermalAI: Inteligencia Artificial y MLOps")
                canvas.line(54, doc.pagesize[1] - 40, doc.pagesize[0] - 54, doc.pagesize[1] - 40)
                
            canvas.restoreState()
            
        # Compilar el PDF
        doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
        print(f"\n[ÉXITO] ¡PDF generado exitosamente en: {PDF_PATH}!")
        return True
    else:
        print("Fallo en la generación de la historia del documento.")
        return False

if __name__ == "__main__":
    build_pdf()
