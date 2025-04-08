"""
Modulo per la creazione del manuale utente in PDF per SimPlanner.

Questo modulo genera un manuale utente completo con indice
e istruzioni dettagliate per l'utilizzo dell'applicazione SimPlanner.
"""

import io
import os
from datetime import datetime
import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import cm, inch

def create_user_manual():
    """
    Crea un manuale utente per SimPlanner in formato PDF, senza immagini e con indice.
    
    Returns:
        BytesIO contenente il file PDF
    """
    # Crea un oggetto in memoria per il PDF
    buffer = io.BytesIO()
    
    # Impostazioni del documento
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        leftMargin=1.5*cm,
        rightMargin=1.5*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Stili
    styles = getSampleStyleSheet()
    
    # Aggiungi stili personalizzati
    styles.add(ParagraphStyle(
        name='TitleBlue',
        parent=styles['Title'],
        textColor=colors.HexColor("#2e78c7")
    ))
    
    styles.add(ParagraphStyle(
        name='SectionBlue',
        parent=styles['Heading1'],
        textColor=colors.HexColor("#2e78c7"),
        fontSize=14,
        spaceAfter=6
    ))
    
    styles.add(ParagraphStyle(
        name='SubsectionBlue',
        parent=styles['Heading2'],
        textColor=colors.HexColor("#2e78c7"),
        fontSize=12,
        spaceAfter=6
    ))
    
    styles.add(ParagraphStyle(
        name='TOCHeading',
        parent=styles['Heading1'],
        fontSize=14,
        spaceAfter=10
    ))
    
    styles.add(ParagraphStyle(
        name='TOCEntry1',
        parent=styles['Normal'],
        fontSize=11,
        leftIndent=20,
        spaceAfter=3
    ))
    
    styles.add(ParagraphStyle(
        name='TOCEntry2',
        parent=styles['Normal'],
        fontSize=10,
        leftIndent=40,
        spaceAfter=3
    ))
    
    # Elementi per il documento
    elements = []
    
    # Titolo
    elements.append(Paragraph("Manuale Utente SimPlanner", styles['TitleBlue']))
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph("Sistema Avanzato di Programmazione Laboratori", styles['Heading4']))
    elements.append(Paragraph(f"Generato il {datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
    elements.append(Spacer(1, 1*cm))
    
    # Indice
    elements.append(Paragraph("Indice", styles['TOCHeading']))
    elements.append(Spacer(1, 0.3*cm))
    
    # Voci dell'indice
    toc_entries = [
        ("1. Introduzione", "TOCEntry1"),
        ("1.1 Requisiti di Sistema", "TOCEntry2"),
        ("2. Configurazione Iniziale", "TOCEntry1"),
        ("3. Gestione dei Gruppi", "TOCEntry1"),
        ("4. Gestione dei Laboratori", "TOCEntry1"),
        ("5. Programmazione Automatica", "TOCEntry1"),
        ("6. Visualizzazione del Calendario", "TOCEntry1"),
        ("7. Gestione Presenze", "TOCEntry1"),
        ("8. Gestione Inventario", "TOCEntry1"),
        ("9. Valutazione Laboratori", "TOCEntry1"),
        ("10. Backup e Ripristino", "TOCEntry1"),
        ("11. Esportazione Dati", "TOCEntry1"),
        ("12. Glossario", "TOCEntry1"),
        ("13. Risoluzione Problemi", "TOCEntry1")
    ]
    
    for entry, style in toc_entries:
        elements.append(Paragraph(entry, styles[style]))
    
    # Interruzione di pagina dopo l'indice
    elements.append(PageBreak())
    
    # Introduzione
    elements.append(Paragraph("1. Introduzione", styles['SectionBlue']))
    elements.append(Spacer(1, 0.3*cm))
    elements.append(Paragraph(
        "SimPlanner è un'applicazione avanzata per la gestione della programmazione dei laboratori " +
        "didattici in ambito universitario. È stata sviluppata specificamente per il Corso di Laurea " +
        "in Infermieristica dell'Università di Torino.", 
        styles['Normal']
    ))
    elements.append(Spacer(1, 0.2*cm))
    elements.append(Paragraph(
        "L'applicazione permette di gestire facilmente la creazione dei gruppi di studenti, la " +
        "programmazione dei laboratori, le presenze e le valutazioni, oltre a fornire funzionalità " +
        "avanzate per la gestione dell'inventario dei materiali didattici.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 0.5*cm))
    
    # Requisiti di sistema
    elements.append(Paragraph("1.1 Requisiti di Sistema", styles['SubsectionBlue']))
    elements.append(Spacer(1, 0.2*cm))
    elements.append(Paragraph(
        "Per utilizzare SimPlanner è necessario un browser web moderno (Chrome, Firefox, Edge, Safari) " +
        "aggiornato all'ultima versione. Non sono richieste installazioni aggiuntive sul computer dell'utente.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 0.5*cm))
    
    # Configurazione iniziale
    elements.append(Paragraph("2. Configurazione Iniziale", styles['SectionBlue']))
    elements.append(Spacer(1, 0.3*cm))
    elements.append(Paragraph(
        "La configurazione iniziale richiede l'inserimento delle informazioni di base relative " +
        "al corso di laurea, all'anno accademico e alla disponibilità delle aule. Questa configurazione " +
        "è necessaria solo al primo utilizzo o quando si desidera creare una nuova programmazione.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 0.5*cm))
    
    # Gestione gruppi
    elements.append(Paragraph("3. Gestione dei Gruppi", styles['SectionBlue']))
    elements.append(Spacer(1, 0.3*cm))
    elements.append(Paragraph(
        "La gestione dei gruppi permette di organizzare gli studenti in gruppi standard (A-E) e " +
        "in gruppi a capacità ridotta (1-8). Ogni studente appartiene contemporaneamente a un gruppo " +
        "standard e a un gruppo a capacità ridotta.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 0.2*cm))
    elements.append(Paragraph(
        "È possibile importare l'elenco degli studenti da un file Excel, generare i gruppi " +
        "automaticamente o modificarli manualmente.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 0.5*cm))
    
    # Laboratori
    elements.append(Paragraph("4. Gestione dei Laboratori", styles['SectionBlue']))
    elements.append(Spacer(1, 0.3*cm))
    elements.append(Paragraph(
        "La sezione di gestione dei laboratori permette di definire i laboratori didattici, " +
        "specificando nome, durata, capacità e altre caratteristiche.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 0.5*cm))
    
    # Programmazione
    elements.append(Paragraph("5. Programmazione Automatica", styles['SectionBlue']))
    elements.append(Spacer(1, 0.3*cm))
    elements.append(Paragraph(
        "La funzionalità di programmazione automatica permette di generare un calendario ottimizzato " +
        "per tutti i laboratori, tenendo conto dei vincoli di aule, orari e della disponibilità dei docenti.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 0.2*cm))
    elements.append(Paragraph(
        "L'algoritmo cerca di distribuire i laboratori in modo equilibrato, rispettando le regole " +
        "specifiche per particolari laboratori che devono essere programmati consecutivamente o in giorni specifici.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 0.5*cm))
    
    # Visualizzazione
    elements.append(Paragraph("6. Visualizzazione del Calendario", styles['SectionBlue']))
    elements.append(Spacer(1, 0.3*cm))
    elements.append(Paragraph(
        "La visualizzazione del calendario permette di vedere la programmazione generata in diverse " +
        "modalità: per data, per gruppo, per aula o per laboratorio. È possibile filtrare la visualizzazione " +
        "in base a vari criteri.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 0.5*cm))
    
    # Gestione presenze
    elements.append(Paragraph("7. Gestione Presenze", styles['SectionBlue']))
    elements.append(Spacer(1, 0.3*cm))
    elements.append(Paragraph(
        "La gestione delle presenze permette di registrare le presenze/assenze degli studenti ai " +
        "laboratori programmati. I dati possono essere utilizzati per generare report e valutazioni.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 0.5*cm))
    
    # Gestione inventario
    elements.append(Paragraph("8. Gestione Inventario", styles['SectionBlue']))
    elements.append(Spacer(1, 0.3*cm))
    elements.append(Paragraph(
        "La gestione dell'inventario permette di tenere traccia dei materiali disponibili per i " +
        "laboratori, gestire le giacenze e associare i materiali necessari a ciascun laboratorio.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 0.2*cm))
    elements.append(Paragraph(
        "Il sistema evidenzia automaticamente quando le giacenze scendono sotto una soglia minima " +
        "e permette di calcolare il fabbisogno complessivo di materiali per una programmazione.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 0.5*cm))
    
    # Valutazione
    elements.append(Paragraph("9. Valutazione Laboratori", styles['SectionBlue']))
    elements.append(Spacer(1, 0.3*cm))
    elements.append(Paragraph(
        "La sezione di valutazione permette di registrare e gestire le valutazioni degli studenti " +
        "per i diversi laboratori, con possibilità di upload di immagini e documenti.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 0.5*cm))
    
    # Backup e ripristino
    elements.append(Paragraph("10. Backup e Ripristino", styles['SectionBlue']))
    elements.append(Spacer(1, 0.3*cm))
    elements.append(Paragraph(
        "Il sistema di backup permette di salvare periodicamente tutti i dati dell'applicazione. " +
        "I backup vengono creati automaticamente a intervalli regolari e possono essere scaricati " +
        "o utilizzati per ripristinare i dati in caso di necessità.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 0.5*cm))
    
    # Esportazione dati
    elements.append(Paragraph("11. Esportazione Dati", styles['SectionBlue']))
    elements.append(Spacer(1, 0.3*cm))
    elements.append(Paragraph(
        "SimPlanner permette di esportare vari tipi di dati in formato Excel o PDF: " +
        "l'elenco degli studenti, i gruppi, la programmazione, le presenze, le valutazioni e l'inventario.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 0.5*cm))
    
    # Glossario
    elements.append(Paragraph("12. Glossario", styles['SectionBlue']))
    elements.append(Spacer(1, 0.3*cm))
    
    # Tabella per il glossario
    glossary_data = [
        ["Termine", "Definizione"],
        ["Gruppo Standard", "Gruppi identificati da lettere (A-E) con capacità di 12-15 studenti"],
        ["Gruppo Ridotto", "Gruppi identificati da numeri (1-8) con capacità di 7-8 studenti"],
        ["Laboratorio", "Attività didattica pratica svolta in aula con un gruppo di studenti"],
        ["Fascia Oraria", "Periodo di tempo in cui è programmato un laboratorio (es. 8:30-11:00)"],
        ["Giacenza", "Quantità disponibile di un materiale nell'inventario"]
    ]
    
    glossary_table = Table(glossary_data, colWidths=[4*cm, 11*cm])
    glossary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
        ('ALIGN', (0, 0), (1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (1, 0), 7),
        ('GRID', (0, 0), (1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 1), (1, -1), colors.white),
    ]))
    
    elements.append(glossary_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # Risoluzione problemi
    elements.append(Paragraph("13. Risoluzione Problemi", styles['SectionBlue']))
    elements.append(Spacer(1, 0.3*cm))
    elements.append(Paragraph(
        "In caso di problemi con l'applicazione, verificare innanzitutto la connessione internet " +
        "e provare a ricaricare la pagina. Se il problema persiste, controllare la sezione 'Log degli Eventi' " +
        "per eventuali messaggi di errore e contattare l'assistenza tecnica.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 0.3*cm))
    
    # Costruisci il PDF
    doc.build(elements)
    
    # Prepara l'output
    buffer.seek(0)
    return buffer

def add_manual_to_ui(sidebar=True):
    """
    Aggiunge i pulsanti per scaricare il manuale utente e altri documenti nell'interfaccia.
    
    Args:
        sidebar: Se True, aggiunge i pulsanti alla barra laterale, altrimenti all'interfaccia principale
    """
    # Scegli l'oggetto UI corretto (sidebar o main interface)
    ui = st.sidebar if sidebar else st
    
    ui.subheader("Documentazione")
    
    # Crea e scarica il manuale utente
    if ui.button("Genera Manuale Utente"):
        # Mostra messaggio di attesa
        ui.info("Generazione del manuale utente in corso...")
        
        # Crea il manuale
        pdf_buffer = create_user_manual()
        
        # Mostra pulsante per scaricare
        ui.download_button(
            label="Download Manuale Utente (PDF)",
            data=pdf_buffer,
            file_name="SimPlanner_Manuale_Utente.pdf",
            mime="application/pdf"
        )
        
        ui.success("Manuale utente generato con successo!")
    
    # Pulsante per esportare la programmazione dei laboratori in PDF con una tabella per pagina
    ui.markdown("---")
    if ui.button("Esporta PDF Programmazione (Tabella/Pagina)"):
        from pdf_export import export_schedule_pdf_reportlab
        import pandas as pd
        
        # Mostra messaggio di attesa
        ui.info("Generazione del PDF in corso...")
        
        # Verifica se c'è una programmazione salvata nella sessione
        if 'programmazione' in st.session_state and isinstance(st.session_state['programmazione'], pd.DataFrame) and not st.session_state['programmazione'].empty:
            # Recupera i dati della programmazione
            df_export = st.session_state['programmazione']
            
            # Ottieni informazioni aggiuntive dalla sessione
            sede_cdl = st.session_state.get('sede_cdl', None)
            anno_corso = st.session_state.get('anno_corso', None)
            anno_accademico = st.session_state.get('anno_accademico', None)
            
            # Ottieni anche i gruppi 
            gruppi_standard = st.session_state.get('gruppi_standard', {})
            gruppi_ridotti = st.session_state.get('gruppi_ridotti', {})
            
            # Unisci tutti i gruppi per passarli alla funzione di esportazione
            tutti_gruppi = {}
            tutti_gruppi.update(gruppi_standard)
            tutti_gruppi.update(gruppi_ridotti)
            
            # Crea il PDF con ReportLab (una tabella per pagina)
            pdf_buffer = export_schedule_pdf_reportlab(
                df_export,
                sede_cdl=sede_cdl,
                anno_corso=anno_corso,
                anno_accademico=anno_accademico,
                groups_data=tutti_gruppi
            )
            
            # Mostra il pulsante per scaricare
            ui.download_button(
                label="Download Programmazione (PDF)",
                data=pdf_buffer,
                file_name=f"SimPlanner_Programmazione_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )
            
            ui.success("PDF della programmazione generato con successo!")
        # Se programmazione è una lista, converti in DataFrame
        elif 'programmazione' in st.session_state and isinstance(st.session_state['programmazione'], list) and st.session_state['programmazione']:
            # Converti la lista in DataFrame
            try:
                df_export = pd.DataFrame(st.session_state['programmazione'])
                
                # Ottieni informazioni aggiuntive dalla sessione
                sede_cdl = st.session_state.get('sede_cdl', None)
                anno_corso = st.session_state.get('anno_corso', None)
                anno_accademico = st.session_state.get('anno_accademico', None)
                
                # Ottieni anche i gruppi 
                gruppi_standard = st.session_state.get('gruppi_standard', {})
                gruppi_ridotti = st.session_state.get('gruppi_ridotti', {})
                
                # Unisci tutti i gruppi per passarli alla funzione di esportazione
                tutti_gruppi = {}
                tutti_gruppi.update(gruppi_standard)
                tutti_gruppi.update(gruppi_ridotti)
                
                # Crea il PDF con ReportLab (una tabella per pagina)
                pdf_buffer = export_schedule_pdf_reportlab(
                    df_export,
                    sede_cdl=sede_cdl,
                    anno_corso=anno_corso,
                    anno_accademico=anno_accademico,
                    groups_data=tutti_gruppi
                )
                
                # Mostra il pulsante per scaricare
                ui.download_button(
                    label="Download Programmazione (PDF)",
                    data=pdf_buffer,
                    file_name=f"SimPlanner_Programmazione_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf"
                )
                
                ui.success("PDF della programmazione generato con successo!")
            except Exception as e:
                ui.error(f"Errore durante la generazione del PDF: {str(e)}")
        else:
            ui.warning("Nessuna programmazione disponibile da esportare. Genera prima una programmazione.")