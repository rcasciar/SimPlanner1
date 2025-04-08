"""
Modulo per l'esportazione dell'elenco aule in formato PDF.
"""

import io
from datetime import datetime
import pandas as pd
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def export_rooms_pdf(rooms_data, filename="aule_laboratori.pdf", sede_cdl=None, anno_corso=None, anno_accademico=None):
    """
    Esporta l'elenco delle aule in un file PDF utilizzando ReportLab.
    
    Args:
        rooms_data: DataFrame o lista di dizionari con le aule configurate
        filename: Nome del file PDF
        sede_cdl: Sede del Corso di Laurea
        anno_corso: Anno di corso
        anno_accademico: Anno accademico (es. "2024/2025")
    
    Returns:
        BytesIO contenente il file PDF
    """
    # Prepara l'output
    output = io.BytesIO()
    
    # Converti in DataFrame se necessario
    if not isinstance(rooms_data, pd.DataFrame):
        rooms_data = pd.DataFrame(rooms_data)
    
    # Crea il documento
    doc = SimpleDocTemplate(output, pagesize=landscape(A4), 
                         rightMargin=30, leftMargin=30,
                         topMargin=30, bottomMargin=30)
    
    # Stili
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    heading_style = styles["Heading2"]
    normal_style = styles["Normal"]
    
    # Stile personalizzato per le intestazioni di tabella
    table_header_style = ParagraphStyle(
        name='TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=colors.darkblue,
        alignment=1,  # Centrato
        spaceAfter=6
    )
    
    # Stile per le celle normali
    table_cell_style = ParagraphStyle(
        name='TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        spaceAfter=3
    )
    
    # Elementi da aggiungere al documento
    elements = []
    
    # Titolo
    elements.append(Paragraph("Aule Configurate per Laboratori", title_style))
    elements.append(Spacer(1, 10))
    
    # Informazioni aggiuntive
    elements.append(Paragraph(f"Generato il {datetime.now().strftime('%d/%m/%Y %H:%M')}", normal_style))
    
    # Aggiungi informazioni sulla sede, anno di corso e anno accademico
    if sede_cdl:
        elements.append(Paragraph(f"Sede: {sede_cdl}", normal_style))
    if anno_corso:
        elements.append(Paragraph(f"Anno di corso: {anno_corso}", normal_style))
    if anno_accademico:
        elements.append(Paragraph(f"Anno accademico: {anno_accademico}", normal_style))
    
    elements.append(Spacer(1, 20))
    
    # Prepara i dati della tabella
    table_headers = ["Nome Aula", "Capacità", "Laboratori Consentiti"]
    
    # Converti le intestazioni in Paragraph
    header_row = [Paragraph(h, table_header_style) for h in table_headers]
    
    # Prepara le righe
    table_data = [header_row]
    for index, row in rooms_data.iterrows():
        # Converti la lista di laboratori consentiti in una stringa
        if isinstance(row.get("laboratori_consentiti"), list):
            laboratori = ", ".join(row["laboratori_consentiti"]) if row["laboratori_consentiti"] else "Tutti"
        else:
            laboratori = "Tutti"
        
        row_data = [
            Paragraph(str(row["nome"]), table_cell_style),
            Paragraph(str(row["capacita"]), table_cell_style),
            Paragraph(laboratori, table_cell_style)
        ]
        table_data.append(row_data)
    
    # Crea la tabella
    table = Table(table_data, colWidths=[120, 80, 400])
    
    # Stile della tabella
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.darkblue),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 7),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ])
    
    # Alterna i colori di sfondo per le righe
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            table_style.add('BACKGROUND', (0, i), (-1, i), colors.whitesmoke)
    
    table.setStyle(table_style)
    
    # Aggiungi la tabella al documento
    elements.append(table)
    
    # Aggiungi piè di pagina
    elements.append(Spacer(1, 15))
    footer_text = "SimPlanner - Sistema di Programmazione Laboratori"
    footer_style = ParagraphStyle(
        name='Footer',
        parent=styles['Normal'],
        fontSize=8,
        alignment=1,  # Centrato
    )
    elements.append(Paragraph(footer_text, footer_style))
    
    # Costruisci il documento
    doc.build(elements)
    
    # Reset il puntatore
    output.seek(0)
    
    return output