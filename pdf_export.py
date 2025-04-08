"""
Modulo per la generazione e l'esportazione in PDF della programmazione dei laboratori
e dei gruppi di studenti, con opzioni di formattazione avanzate tramite ReportLab.
"""

import io
from datetime import datetime
import tempfile
import os
# from weasyprint import HTML, CSS  # Disabilitato: non si usa più WeasyPrint
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

"""
def export_schedule_pdf_weasyprint(schedule_data, filename="programmazione_laboratori.pdf", sede_cdl=None, anno_corso=None, num_macrogruppi=None, anno_accademico=None):
    \"""
    Esporta la programmazione dei laboratori in un file PDF utilizzando WeasyPrint.
    
    Args:
        schedule_data: DataFrame con la programmazione
        filename: Nome del file PDF
        sede_cdl: Sede del Corso di Laurea
        anno_corso: Anno di corso
        num_macrogruppi: Numero di macrogruppi
        anno_accademico: Anno accademico (es. "2024/2025")
    
    Returns:
        BytesIO contenente il file PDF
    \"""
    # Crea l'HTML
    html_content = create_html_from_schedule(
        schedule_data, 
        sede_cdl=sede_cdl, 
        anno_corso=anno_corso, 
        num_macrogruppi=num_macrogruppi,
        anno_accademico=anno_accademico
    )
    
    # Crea temporaneo per l'HTML
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as temp_html:
        temp_html.write(html_content.encode('utf-8'))
        temp_html_path = temp_html.name
    
    # Output PDF
    output = io.BytesIO()
    
    try:
        # Converti HTML in PDF
        html = HTML(filename=temp_html_path)
        css = create_css()
        html.write_pdf(target=output, stylesheets=[css])
        
        # Reset il puntatore
        output.seek(0)
    finally:
        # Pulisci i file temporanei
        if os.path.exists(temp_html_path):
            os.unlink(temp_html_path)
    
    return output
"""

def export_student_groups_pdf(student_groups, filename="gruppi_studenti.pdf", channel_info=None):
    """
    Esporta i gruppi di studenti in un PDF utilizzando ReportLab
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from io import BytesIO

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []

    # Stili
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']

    # Titolo
    if channel_info:
        elements.append(Paragraph(f"Elenco Gruppi Studenti - {channel_info}", title_style))
    else:
        elements.append(Paragraph("Elenco Gruppi Studenti", title_style))

    elements.append(Spacer(1, 20))

    # Per ogni gruppo
    for group_name, students in student_groups.items():
        elements.append(Paragraph(f"Gruppo {group_name}", subtitle_style))

        # Tabella studenti
        data = [["Cognome", "Nome", "Matricola"]]
        for student in students:
            data.append([
                student.get('cognome', ''),
                student.get('nome', ''),
                student.get('matricola', '')
            ])

        t = Table(data, colWidths=[200, 200, 100])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(t)
        elements.append(Spacer(1, 20))

    # Costruisci il documento
    doc.build(elements)
    buffer.seek(0)
    return buffer
