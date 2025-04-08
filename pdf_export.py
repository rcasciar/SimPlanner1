"""
Modulo per l'esportazione delle programmazioni e gruppi di studenti in formato PDF.
"""

import io
from datetime import datetime
import tempfile
import os
from weasyprint import HTML, CSS
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def create_css():
    """
    Crea il CSS per il documento PDF
    """
    return CSS(string='''
        @page {
            size: A4 landscape;
            margin: 1cm;
        }
        body {
            font-family: sans-serif;
            font-size: 9pt;
        }
        h1 {
            font-size: 16pt;
            margin-bottom: 10pt;
            color: #1e88e5;
        }
        h2 {
            font-size: 14pt;
            margin-top: 20pt;
            margin-bottom: 8pt;
            color: #1e88e5;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 15pt;
        }
        th {
            background-color: #e3f2fd;
            padding: 5pt;
            text-align: left;
            font-weight: bold;
            border: 1px solid #ccc;
        }
        td {
            padding: 4pt;
            border: 1px solid #ccc;
        }
        .odd-row {
            background-color: #f8f9fa;
        }
        .even-row {
            background-color: #ffffff;
        }
        .footer {
            font-size: 8pt;
            text-align: center;
            margin-top: 10pt;
            color: #666;
        }
    ''')

def create_html_from_schedule(schedule_data, title="Programmazione Laboratori", sede_cdl=None, anno_corso=None, num_macrogruppi=None, anno_accademico=None):
    """
    Crea un documento HTML dalla programmazione dei laboratori.
    
    Args:
        schedule_data: DataFrame con la programmazione
        title: Titolo del documento
        sede_cdl: Sede del Corso di Laurea
        anno_corso: Anno di corso
        num_macrogruppi: Numero di macrogruppi
        anno_accademico: Anno accademico (es. "2024/2025")
    
    Returns:
        HTML per la visualizzazione o esportazione
    """
    # Ordina i dati per data e ora
    schedule_data = schedule_data.sort_values(by=["data", "ora_inizio", "aula"])
    
    # Informazioni aggiuntive per l'intestazione
    info_aggiuntive = ""
    if sede_cdl:
        info_aggiuntive += f"<p><strong>Sede:</strong> {sede_cdl}</p>"
    if anno_corso:
        info_aggiuntive += f"<p><strong>Anno di corso:</strong> {anno_corso}</p>"
    if anno_accademico:
        info_aggiuntive += f"<p><strong>Anno accademico:</strong> {anno_accademico}</p>"
    if num_macrogruppi and num_macrogruppi > 1:
        info_aggiuntive += f"<p><strong>Macrogruppi configurati:</strong> {num_macrogruppi}</p>"
    
    # Crea l'HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{title}</title>
    </head>
    <body>
        <h1>{title}</h1>
        <p>Generato il {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        {info_aggiuntive}
    """
    
    # Raggruppa per data
    for data in sorted(schedule_data["data"].unique()):
        html += f"<h2>Data: {data}</h2>"
        
        df_giorno = schedule_data[schedule_data["data"] == data]
        df_giorno = df_giorno.sort_values(by=["ora_inizio", "aula"])
        
        # Tabella per questa data
        html += """
        <table>
            <thead>
                <tr>
                    <th>Orario</th>
                    <th>Laboratorio</th>
                    <th>Aula</th>
                    <th>Gruppo</th>
                    <th>Tipo Gruppo</th>
                </tr>
            </thead>
            <tbody>
        """
        
        # Righe per ogni evento
        for i, (_, row) in enumerate(df_giorno.iterrows()):
            row_class = "odd-row" if i % 2 == 0 else "even-row"
            tipo_gruppo = "Standard" if row["tipo_gruppo"] == "standard" else "Ridotto"
            
            html += f"""
            <tr class="{row_class}">
                <td>{row["ora_inizio"]}-{row["ora_fine"]}</td>
                <td>{row["laboratorio"]}</td>
                <td>{row["aula"]}</td>
                <td>{row["gruppo"]}</td>
                <td>{tipo_gruppo}</td>
            </tr>
            """
        
        html += """
            </tbody>
        </table>
        """
    
    # Chiudi il documento
    html += """
        <div class="footer">
            SimPlanner - Sistema di Programmazione Laboratori
        </div>
    </body>
    </html>
    """
    
    return html

def export_schedule_pdf_weasyprint(schedule_data, filename="programmazione_laboratori.pdf", sede_cdl=None, anno_corso=None, num_macrogruppi=None, anno_accademico=None):
    """
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
    """
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

def export_student_groups_pdf(groups_data, laboratori_per_gruppo=None, sede_cdl=None, anno_corso=None, anno_accademico=None):
    """
    Esporta i gruppi di studenti in un file PDF.
    Include prima la programmazione completa dei laboratori e poi gli elenchi di studenti per gruppo.
    
    Args:
        groups_data: Dizionario con i gruppi di studenti {'Gruppo A': [{'cognome': 'Rossi', 'nome': 'Mario'}, ...]}
        laboratori_per_gruppo: Dizionario con i laboratori assegnati a ciascun gruppo (opzionale)
        sede_cdl: Sede del Corso di Laurea
        anno_corso: Anno di corso
        anno_accademico: Anno accademico (es. "2024/2025")
    
    Returns:
        BytesIO contenente il file PDF
    """
    # Prepara l'output
    output = io.BytesIO()
    
    # Crea il documento (utilizziamo pagina orizzontale per avere più spazio)
    doc = SimpleDocTemplate(output, pagesize=landscape(A4), 
                         rightMargin=30, leftMargin=30,
                         topMargin=30, bottomMargin=30)
    
    # Stili
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name='CustomTitle',
        parent=styles["Title"],
        fontName='Helvetica-Bold',
        fontSize=14,
        alignment=1,  # Centrato
        spaceAfter=20
    )
    heading_style = ParagraphStyle(
        name='CustomHeading',
        parent=styles["Heading1"],
        fontName='Helvetica-Bold',
        fontSize=12,
        alignment=1,  # Centrato
        spaceAfter=10
    )
    subheading_style = ParagraphStyle(
        name='CustomSubheading',
        parent=styles["Heading2"],
        fontName='Helvetica-Bold',
        fontSize=10,
        alignment=0,  # Allineato a sinistra
        spaceAfter=6
    )
    normal_style = styles["Normal"]
    
    # Stile personalizzato per le intestazioni di tabella
    table_header_style = ParagraphStyle(
        name='TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        alignment=1,  # Centrato
        spaceAfter=6
    )
    
    # Elementi da aggiungere al documento
    elements = []
    
    # Titolo principale
    if anno_accademico:
        title_text = f"GRUPPI LABORATORI - ANNO ACCADEMICO {anno_accademico}"
    else:
        title_text = "GRUPPI LABORATORI"
        
    if anno_corso:
        title_text += f" - {anno_corso}° ANNO"
    
    if sede_cdl:
        title_text += f"\n{sede_cdl.upper()}"
        
    elements.append(Paragraph(title_text, title_style))
    elements.append(Spacer(1, 10))
    
    # Informazioni aggiuntive
    info_text = f"Generato il {datetime.now().strftime('%d/%m/%Y')}"
    elements.append(Paragraph(info_text, normal_style))
    elements.append(Spacer(1, 20))
    
    # PARTE 1: PROGRAMMAZIONE DEI LABORATORI
    elements.append(Paragraph("PROGRAMMAZIONE LABORATORI", heading_style))
    elements.append(Spacer(1, 10))
    
    # Verifica se ci sono laboratori programmati
    if laboratori_per_gruppo:
        # Raccogliamo tutti i laboratori in un formato unificato per ordinarli per data
        tutti_i_laboratori = []
        
        for gruppo, labs in laboratori_per_gruppo.items():
            if isinstance(labs, list):
                for lab in labs:
                    tutti_i_laboratori.append({
                        'data': lab.get('data', ''),
                        'orario': lab.get('orario', ''),
                        'ora_inizio': lab.get('orario', '').split('-')[0] if '-' in lab.get('orario', '') else '',
                        'ora_fine': lab.get('orario', '').split('-')[1] if '-' in lab.get('orario', '') else '',
                        'laboratorio': lab.get('nome', ''),
                        'aula': lab.get('aula', ''),
                        'gruppo': gruppo
                    })
        
        # Ordina per data e orario inizio
        tutti_i_laboratori = sorted(tutti_i_laboratori, key=lambda x: (x['data'], x['ora_inizio']))
        
        # Raggruppa per data
        date_uniche = sorted(set(lab['data'] for lab in tutti_i_laboratori))
        
        for data in date_uniche:
            labs_del_giorno = [lab for lab in tutti_i_laboratori if lab['data'] == data]
            
            # Titolo del giorno
            elements.append(Paragraph(f"Data: {data}", subheading_style))
            
            # Crea tabella per questa data
            table_data = [["Orario", "Laboratorio", "Aula", "Gruppo"]]
            
            # Aggiungi i laboratori di questo giorno
            for lab in labs_del_giorno:
                orario = lab.get('orario', '')
                laboratorio = lab.get('laboratorio', '').upper()
                aula = lab.get('aula', '').upper()
                gruppo = lab.get('gruppo', '')
                
                table_data.append([orario, laboratorio, aula, gruppo])
            
            # Crea la tabella
            table = Table(table_data, repeatRows=1, colWidths=[doc.width*0.2, doc.width*0.3, doc.width*0.3, doc.width*0.2])
            
            # Stile tabella
            table_style = TableStyle([
                # Intestazioni
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 7),
                ('TOPPADDING', (0, 0), (-1, 0), 7),
                
                # Dati
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('TOPPADDING', (0, 1), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                
                # Griglia
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ])
            
            # Alterna colori delle righe
            for i in range(1, len(table_data)):
                if i % 2 == 0:
                    table_style.add('BACKGROUND', (0, i), (-1, i), colors.whitesmoke)
            
            table.setStyle(table_style)
            elements.append(table)
            elements.append(Spacer(1, 10))
    else:
        elements.append(Paragraph("Nessun laboratorio programmato", normal_style))
        
    elements.append(Spacer(1, 20))
    
    # PARTE 2: ELENCHI STUDENTI PER GRUPPO
    elements.append(Paragraph("ELENCHI STUDENTI PER GRUPPO", heading_style))
    elements.append(Spacer(1, 10))
    
    # Raggruppa i gruppi per tipo (standard/ridotto)
    gruppi_standard = {}
    gruppi_ridotti = {}
    
    for nome_gruppo, studenti in groups_data.items():
        if nome_gruppo.startswith('Gruppo'):
            gruppi_standard[nome_gruppo] = studenti
        elif nome_gruppo.isdigit() or nome_gruppo.startswith('Gruppo'):
            gruppi_ridotti[nome_gruppo] = studenti
        else:
            # Se non riusciamo a classificare, mettiamo nei gruppi standard
            gruppi_standard[nome_gruppo] = studenti
    
    # Funzione per creare una tabella di gruppo
    def crea_tabella_gruppo(nome_gruppo, studenti, is_header=False):
        # Titolo del gruppo
        if is_header:
            elements.append(Paragraph(f"GRUPPO {nome_gruppo.upper()}", subheading_style))
        
        # Dati tabella
        group_table_data = [["COGNOME", "NOME"]]
        
        # Aggiungi studenti ordinati per cognome
        studenti_ordinati = sorted(studenti, key=lambda s: s.get("cognome", "").upper())
        for studente in studenti_ordinati:
            cognome = studente.get("cognome", "").upper()
            nome = studente.get("nome", "").upper()
            group_table_data.append([cognome, nome])
            
        # Crea la tabella
        table = Table(group_table_data, colWidths=[doc.width/2*0.5, doc.width/2*0.5])
        
        # Stile della tabella
        table_style = TableStyle([
            # Intestazione
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
            ('TOPPADDING', (0, 0), (-1, 0), 5),
            
            # Dati studenti
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('TOPPADDING', (0, 1), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
            
            # Griglia
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ])
        
        # Alterna colori delle righe
        for i in range(1, len(group_table_data)):
            if i % 2 == 0:
                table_style.add('BACKGROUND', (0, i), (-1, i), colors.whitesmoke)
        
        table.setStyle(table_style)
        return table
    
    # Mostra i gruppi standard
    if gruppi_standard:
        elements.append(Paragraph("GRUPPI STANDARD", subheading_style))
        elements.append(Spacer(1, 5))
        
        # Un gruppo per pagina
        gruppi_items = list(gruppi_standard.items())
        for i, (nome_gruppo, studenti) in enumerate(gruppi_items):
            # Crea intestazione del gruppo
            elements.append(Paragraph(f"GRUPPO {nome_gruppo.upper()}", subheading_style))
            elements.append(Spacer(1, 5))
            
            # Crea tabella
            table = crea_tabella_gruppo(nome_gruppo, studenti)
            elements.append(table)
            
            # Aggiungi un PageBreak se non è l'ultimo gruppo
            if i < len(gruppi_items) - 1 or gruppi_ridotti:
                elements.append(PageBreak())
                if i < len(gruppi_items) - 1:
                    # Ripeti l'intestazione principale nella nuova pagina
                    elements.append(Paragraph("GRUPPI STANDARD", subheading_style))
                    elements.append(Spacer(1, 5))
    
    # Poi i gruppi ridotti
    if gruppi_ridotti:
        elements.append(Paragraph("GRUPPI A CAPACITÀ RIDOTTA", subheading_style))
        elements.append(Spacer(1, 5))
        
        # Un gruppo per pagina
        gruppi_items = list(gruppi_ridotti.items())
        for i, (nome_gruppo, studenti) in enumerate(gruppi_items):
            # Crea intestazione del gruppo
            elements.append(Paragraph(f"GRUPPO {nome_gruppo.upper()}", subheading_style))
            elements.append(Spacer(1, 5))
            
            # Crea tabella
            table = crea_tabella_gruppo(nome_gruppo, studenti)
            elements.append(table)
            
            # Aggiungi un PageBreak se non è l'ultimo gruppo
            if i < len(gruppi_items) - 1:
                elements.append(PageBreak())
                if i < len(gruppi_items) - 1:
                    # Ripeti l'intestazione principale nella nuova pagina
                    elements.append(Paragraph("GRUPPI A CAPACITÀ RIDOTTA", subheading_style))
                    elements.append(Spacer(1, 5))
    
    # Aggiungi piè di pagina
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

def export_schedule_pdf_reportlab(schedule_data, filename="programmazione_laboratori.pdf", sede_cdl=None, anno_corso=None, num_macrogruppi=None, anno_accademico=None, groups_data=None):
    """
    Esporta la programmazione dei laboratori in un file PDF utilizzando ReportLab.
    
    Args:
        schedule_data: DataFrame con la programmazione
        filename: Nome del file PDF
        sede_cdl: Sede del Corso di Laurea
        anno_corso: Anno di corso
        num_macrogruppi: Numero di macrogruppi
        anno_accademico: Anno accademico (es. "2024/2025")
        groups_data: Dizionario con i gruppi di studenti (opzionale)
    
    Returns:
        BytesIO contenente il file PDF
    """
    # Prepara l'output
    output = io.BytesIO()
    
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
    elements.append(Paragraph("Programmazione Laboratori", title_style))
    elements.append(Spacer(1, 10))
    
    # Informazioni aggiuntive
    elements.append(Paragraph(f"Generato il {datetime.now().strftime('%d/%m/%Y %H:%M')}", normal_style))
    
    # Aggiungi informazioni sulla sede, anno di corso, anno accademico e macrogruppi
    if sede_cdl:
        elements.append(Paragraph(f"Sede: {sede_cdl}", normal_style))
    if anno_corso:
        elements.append(Paragraph(f"Anno di corso: {anno_corso}", normal_style))
    if anno_accademico:
        elements.append(Paragraph(f"Anno accademico: {anno_accademico}", normal_style))
    if num_macrogruppi and num_macrogruppi > 1:
        elements.append(Paragraph(f"Macrogruppi configurati: {num_macrogruppi}", normal_style))
    
    elements.append(Spacer(1, 20))
    
    # Ordina i dati
    schedule_data = schedule_data.sort_values(by=["data", "ora_inizio", "aula"])
    
    # Raggruppa per data
    for data in sorted(schedule_data["data"].unique()):
        elements.append(Paragraph(f"Data: {data}", heading_style))
        elements.append(Spacer(1, 5))
        
        df_giorno = schedule_data[schedule_data["data"] == data]
        df_giorno = df_giorno.sort_values(by=["ora_inizio", "aula"])
        
        # Prepara i dati della tabella
        table_data = [["Orario", "Laboratorio", "Aula", "Gruppo", "Tipo Gruppo"]]
        
        # Converti le intestazioni in Paragraph
        table_data[0] = [Paragraph(h, table_header_style) for h in table_data[0]]
        
        # Aggiungi le righe dei dati
        for _, row in df_giorno.iterrows():
            tipo_gruppo = "Standard" if row["tipo_gruppo"] == "standard" else "Ridotto"
            table_row = [
                Paragraph(f"{row['ora_inizio']}-{row['ora_fine']}", table_cell_style),
                Paragraph(f"{row['laboratorio']}", table_cell_style),
                Paragraph(f"{row['aula']}", table_cell_style),
                Paragraph(f"{row['gruppo']}", table_cell_style),
                Paragraph(f"{tipo_gruppo}", table_cell_style)
            ]
            table_data.append(table_row)
        
        # Crea la tabella
        table = Table(table_data, repeatRows=1)
        
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
        
        # Aggiungi un'interruzione di pagina dopo ogni tabella (eccetto l'ultima)
        if data != sorted(schedule_data["data"].unique())[-1]:
            elements.append(PageBreak())
        else:
            elements.append(Spacer(1, 15))
    
    # Aggiungi pagina con elenchi dei gruppi se disponibili
    if groups_data and len(groups_data) > 0:
        elements.append(PageBreak())
        elements.append(Paragraph("ELENCHI STUDENTI PER GRUPPO", heading_style))
        elements.append(Spacer(1, 10))
        
        # Funzione per creare una tabella per un gruppo
        def crea_tabella_gruppo(nome_gruppo, studenti):
            # Titolo del gruppo
            elements.append(Paragraph(f"GRUPPO {nome_gruppo.upper()}", heading_style))
            elements.append(Spacer(1, 5))
            
            # Dati tabella
            group_table_data = [["COGNOME", "NOME"]]
            group_table_data[0] = [Paragraph(h, table_header_style) for h in group_table_data[0]]
            
            # Aggiungi studenti ordinati per cognome
            studenti_ordinati = sorted(studenti, key=lambda s: s.get("cognome", "").upper() if isinstance(s, dict) else s)
            for studente in studenti_ordinati:
                if isinstance(studente, dict):
                    cognome = studente.get("cognome", "").upper()
                    nome = studente.get("nome", "").upper()
                    group_table_data.append([
                        Paragraph(cognome, table_cell_style),
                        Paragraph(nome, table_cell_style)
                    ])
            
            # Crea tabella
            table = Table(group_table_data, repeatRows=1)
            
            # Stile tabella
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
            
            # Alterna colori righe
            for i in range(1, len(group_table_data)):
                if i % 2 == 0:
                    table_style.add('BACKGROUND', (0, i), (-1, i), colors.whitesmoke)
            
            table.setStyle(table_style)
            
            elements.append(table)
            elements.append(Spacer(1, 10))
        
        # Separa i gruppi standard e ridotti
        gruppi_standard = {}
        gruppi_ridotti = {}
        
        for nome_gruppo, studenti in groups_data.items():
            if nome_gruppo.startswith('Gruppo') or nome_gruppo[0].isalpha():
                gruppi_standard[nome_gruppo] = studenti
            elif nome_gruppo.isdigit() or nome_gruppo[0].isdigit():
                gruppi_ridotti[nome_gruppo] = studenti
        
        # Aggiungi gruppi standard
        if gruppi_standard:
            elements.append(Paragraph("GRUPPI STANDARD", heading_style))
            elements.append(Spacer(1, 5))
            
            for nome, studenti in sorted(gruppi_standard.items()):
                crea_tabella_gruppo(nome, studenti)
                elements.append(PageBreak())
        
        # Aggiungi gruppi ridotti
        if gruppi_ridotti:
            elements.append(Paragraph("GRUPPI A CAPACITÀ RIDOTTA", heading_style))
            elements.append(Spacer(1, 5))
            
            for nome, studenti in sorted(gruppi_ridotti.items()):
                crea_tabella_gruppo(nome, studenti)
                if nome != list(sorted(gruppi_ridotti.keys()))[-1]:  # Se non è l'ultimo gruppo
                    elements.append(PageBreak())
    
    # Costruisci il documento
    doc.build(elements)
    
    # Reset il puntatore
    output.seek(0)
    
    return output