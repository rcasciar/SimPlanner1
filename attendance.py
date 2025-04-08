"""
Modulo per la gestione delle presenze degli studenti ai laboratori.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
import os

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import cm

def initialize_attendance():
    """
    Inizializza il sistema di gestione delle presenze.
    """
    if 'presenze_studenti' not in st.session_state:
        st.session_state.presenze_studenti = {}

def mark_attendance(data, laboratorio, aula, gruppo, student_id, present=True):
    """
    Segna una presenza o assenza per uno studente a un laboratorio.
    
    Args:
        data: Data del laboratorio (formato stringa dd/mm/yyyy)
        laboratorio: Nome del laboratorio
        aula: Nome dell'aula
        gruppo: Gruppo dello studente
        student_id: ID dello studente
        present: True se presente, False se assente
    """
    # Crea un ID unico per l'evento
    event_id = f"{data}_{laboratorio}_{aula}_{gruppo}"
    
    # Assicurati che la struttura dati esista
    if 'presenze_studenti' not in st.session_state:
        st.session_state.presenze_studenti = {}
    
    # Crea l'evento se non esiste
    if event_id not in st.session_state.presenze_studenti:
        st.session_state.presenze_studenti[event_id] = {}
    
    # Gestisci diversi formati di ID studente
    if isinstance(student_id, dict):
        # Se è un oggetto, usa l'ID se disponibile, altrimenti crea una chiave univoca
        if 'id' in student_id:
            id_key = student_id['id']
        else:
            # Genera una chiave basata sul nome/cognome
            id_key = f"dict_{hash(str(student_id))}"
        
        # Aggiungi informazioni dello studente nel dizionario presenze
        # In questo modo possiamo recuperare nome e cognome in seguito
        st.session_state.presenze_studenti[event_id][id_key] = {
            'presente': present,
            'cognome': student_id.get('cognome', ''),
            'nome': student_id.get('nome', '')
        }
    elif isinstance(student_id, str) and student_id.startswith(("STD_", "dict_")):
        # Se l'ID è già nel nuovo formato, usalo direttamente
        id_key = student_id
        # Se ci sono dati sullo studente nella sessione
        if 'studenti' in st.session_state:
            # Cerca lo studente per ID
            student_info = None
            for s in st.session_state.studenti:
                if s.get('id', '') == student_id:
                    student_info = s
                    break
            
            if student_info:
                st.session_state.presenze_studenti[event_id][id_key] = {
                    'presente': present,
                    'cognome': student_info.get('cognome', ''),
                    'nome': student_info.get('nome', '')
                }
            else:
                # Se non troviamo lo studente, salviamo solo la presenza
                st.session_state.presenze_studenti[event_id][id_key] = {
                    'presente': present,
                    'cognome': '',
                    'nome': ''
                }
        else:
            # Non ci sono dati sugli studenti, salviamo solo la presenza
            st.session_state.presenze_studenti[event_id][id_key] = {
                'presente': present,
                'cognome': '',
                'nome': ''
            }
    else:
        # Per altri casi, converti in stringa
        id_key = str(student_id)
        # Se ci sono dati sullo studente nella sessione
        if 'studenti' in st.session_state:
            # Cerca lo studente per indice/ID
            student_info = None
            try:
                idx = int(student_id) if isinstance(student_id, str) else student_id
                if 0 <= idx < len(st.session_state.studenti):
                    student_info = st.session_state.studenti[idx]
            except (ValueError, TypeError):
                # Fallback: cerchiamo in altri modi
                for i, s in enumerate(st.session_state.studenti):
                    if str(i) == str(student_id):
                        student_info = s
                        break
            
            if student_info:
                st.session_state.presenze_studenti[event_id][id_key] = {
                    'presente': present,
                    'cognome': student_info.get('cognome', ''),
                    'nome': student_info.get('nome', '')
                }
            else:
                # Se non troviamo lo studente, salviamo solo la presenza
                st.session_state.presenze_studenti[event_id][id_key] = {
                    'presente': present,
                    'cognome': '',
                    'nome': ''
                }
        else:
            # Non ci sono dati sugli studenti, salviamo solo la presenza
            st.session_state.presenze_studenti[event_id][id_key] = {
                'presente': present,
                'cognome': '',
                'nome': ''
            }

def get_student_attendance(student_id):
    """
    Ottiene l'elenco delle presenze per uno studente.
    
    Args:
        student_id: ID dello studente
        
    Returns:
        Lista di tuple (data, laboratorio, aula, gruppo, presente)
    """
    if 'presenze_studenti' not in st.session_state:
        return []
    
    attendance_list = []
    
    for event_id, presenze in st.session_state.presenze_studenti.items():
        if student_id in presenze:
            # Estrai le informazioni dall'ID dell'evento
            data, laboratorio, aula, gruppo = event_id.split('_', 3)
            attendance_list.append((data, laboratorio, aula, gruppo, presenze[student_id]))
    
    return attendance_list

def get_lab_attendance(data, laboratorio, aula, gruppo):
    """
    Ottiene l'elenco delle presenze per un laboratorio specifico.
    
    Args:
        data: Data del laboratorio
        laboratorio: Nome del laboratorio
        aula: Nome dell'aula
        gruppo: Gruppo del laboratorio
        
    Returns:
        Dizionario {student_id: presente} o {student_id: {presente, nome, cognome}}
    """
    event_id = f"{data}_{laboratorio}_{aula}_{gruppo}"
    
    if 'presenze_studenti' not in st.session_state or event_id not in st.session_state.presenze_studenti:
        return {}
    
    # Prepara il dizionario risultante
    risultato = {}
    
    # Converti dati nel nuovo formato
    for student_id, presenza in st.session_state.presenze_studenti[event_id].items():
        # Se è già nel nuovo formato (dizionario), mantienilo così
        if isinstance(presenza, dict) and 'presente' in presenza:
            risultato[student_id] = presenza['presente']  # Estrai solo il valore booleano presente
        else:
            # Altrimenti usa direttamente il valore booleano
            risultato[student_id] = presenza
    
    return risultato

def get_all_attendance():
    """
    Ottiene tutte le presenze registrate.
    
    Returns:
        DataFrame con tutte le presenze
    """
    if 'presenze_studenti' not in st.session_state or not st.session_state.presenze_studenti:
        return pd.DataFrame()
    
    rows = []
    
    for event_id, presenze in st.session_state.presenze_studenti.items():
        data, laboratorio, aula, gruppo = event_id.split('_', 3)
        for student_id, presenza_info in presenze.items():
            # Verifica se la presenza è nel nuovo formato (dizionario con presente, nome, cognome)
            if isinstance(presenza_info, dict) and 'presente' in presenza_info:
                # Usa direttamente le informazioni salvate
                student_name = f"{presenza_info.get('cognome', '')} {presenza_info.get('nome', '')}"
                presente = presenza_info['presente']
            else:
                # Formato vecchio (booleano)
                presente = presenza_info
                student_name = ""
                
                # Cerca di recuperare il nome dello studente
                if 'studenti' in st.session_state:
                    # Cerca prima per ID esatto
                    for student in st.session_state.studenti:
                        if student.get('id', '') == student_id:
                            student_name = f"{student.get('cognome', '')} {student.get('nome', '')}"
                            break
                    
                    # Se non lo trova e non ha un nome, cerca per indice
                    if not student_name:
                        try:
                            index = int(student_id) if isinstance(student_id, str) and not student_id.startswith(("STD_", "dict_")) else -1
                            if 0 <= index < len(st.session_state.studenti):
                                student = st.session_state.studenti[index]
                                student_name = f"{student.get('cognome', '')} {student.get('nome', '')}"
                        except (ValueError, TypeError):
                            # Fallback: cerchiamo per corrispondenza di stringa
                            for i, student in enumerate(st.session_state.studenti):
                                if str(i) == str(student_id):
                                    student_name = f"{student.get('cognome', '')} {student.get('nome', '')}"
                                    break
            
            rows.append({
                'Data': data,
                'Laboratorio': laboratorio,
                'Aula': aula,
                'Gruppo': gruppo,
                'ID Studente': student_id,
                'Nome Studente': student_name,
                'Presente': presente
            })
    
    return pd.DataFrame(rows)

def generate_attendance_report():
    """
    Genera un report delle presenze in formato PDF.
    
    Returns:
        BytesIO contenente il file PDF
    """
    # Ottieni tutte le presenze
    df = get_all_attendance()
    
    buffer = BytesIO()
    
    # Crea un documento PDF
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1*cm, leftMargin=1*cm, topMargin=1*cm, bottomMargin=1*cm)
    elements = []
    
    # Stili per il documento
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Aggiungi titolo
    elements.append(Paragraph("Report Presenze Studenti ai Laboratori", title_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # Aggiungi data generazione
    data_generazione = datetime.now().strftime("%d/%m/%Y %H:%M")
    elements.append(Paragraph(f"Generato il: {data_generazione}", normal_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # Iniziamo con tutti i laboratori programmati
    elements.append(Paragraph("Elenco Completo Laboratori Programmati", subtitle_style))
    elements.append(Spacer(1, 0.3*cm))
    
    # Mappiamo le presenze in un dizionario per facile accesso
    presenza_dict = {}
    if not df.empty:
        df['Presente'] = df['Presente'].map({True: 'Sì', False: 'No'})
        for _, row in df.iterrows():
            key = (row['Laboratorio'], row['Data'], row['Aula'], row['Gruppo'], row['ID Studente'])
            presenza_dict[key] = (row['Nome Studente'], row['Presente'])
    
    # Recuperare tutti i laboratori programmati
    if 'programmazione' in st.session_state and st.session_state.programmazione:
        # Raggruppiamo i laboratori programmati per lab, data, aula, gruppo
        lab_programmati = {}
        for evento in st.session_state.programmazione:
            key = (evento['laboratorio'], evento['data'], evento['aula'], evento['gruppo'])
            if key not in lab_programmati:
                lab_programmati[key] = []
            
            # Ottieni gli studenti per questo gruppo
            studenti = []
            if evento['tipo_gruppo'] == 'standard' and 'gruppi_standard' in st.session_state:
                studenti = st.session_state.gruppi_standard.get(evento['gruppo'], [])
            elif evento['tipo_gruppo'] == 'ridotto' and 'gruppi_ridotti' in st.session_state:
                studenti = st.session_state.gruppi_ridotti.get(evento['gruppo'], [])
            
            # Estrai le informazioni dello studente
            for student_id in studenti:
                student_name = ""
                # Cerca il nome dello studente nel dizionario
                if 'studenti' in st.session_state:
                    for student in st.session_state.studenti:
                        if isinstance(student_id, dict):
                            # Se student_id è già un dizionario, usa quello
                            student_name = f"{student_id.get('cognome', '')} {student_id.get('nome', '')}"
                            break
                        elif isinstance(student_id, (int, str)):
                            # Cerca per indice
                            try:
                                idx = int(student_id) if isinstance(student_id, str) and not student_id.startswith(("STD_", "dict_")) else -1
                                if 0 <= idx < len(st.session_state.studenti):
                                    student_info = st.session_state.studenti[idx]
                                    student_name = f"{student_info.get('cognome', '')} {student_info.get('nome', '')}"
                                    break
                            except (ValueError, TypeError):
                                # Se non è un indice valido, cerchiamo per ID
                                if student.get('id', '') == student_id:
                                    student_name = f"{student.get('cognome', '')} {student.get('nome', '')}"
                                    break
                                
                # Cerca se questo studente ha una presenza registrata
                presente = "Non registrato"
                
                # Converte student_id in stringa per la ricerca nel dizionario
                student_id_str = str(student_id)
                if isinstance(student_id, dict):
                    # Se è un dizionario, cerca per cognome e nome
                    for key, value in presenza_dict.items():
                        # Verifica se il lab, data, aula e gruppo corrispondono
                        if key[0] == evento['laboratorio'] and key[1] == evento['data'] and key[2] == evento['aula'] and key[3] == evento['gruppo']:
                            # Cerca per nome e cognome, che dovrebbero essere in value[0]
                            cognome_nome_presenza = value[0]
                            cognome_nome_studente = f"{student_id.get('cognome', '')} {student_id.get('nome', '')}"
                            if cognome_nome_presenza == cognome_nome_studente:
                                student_name = cognome_nome_presenza or student_name
                                presente = value[1]
                                break
                else:
                    # Per ID normali (non dizionari)
                    lookup_key = (evento['laboratorio'], evento['data'], evento['aula'], evento['gruppo'], student_id_str)
                    if presenza_dict and lookup_key in presenza_dict:
                        student_name = presenza_dict[lookup_key][0] or student_name  # Usa il nome del registro presenze se disponibile
                        presente = presenza_dict[lookup_key][1]
                
                # Usa la chiave dell'evento corrente per aggiungere lo studente al gruppo corretto
                event_key = (evento['laboratorio'], evento['data'], evento['aula'], evento['gruppo'])
                if event_key in lab_programmati:
                    lab_programmati[event_key].append((student_id, student_name, presente))
        
        # Ora stampiamo tutti i laboratori programmati
        for (lab, data, aula, gruppo), studenti in sorted(lab_programmati.items(), key=lambda x: (x[0][1], x[0][0])):  # Ordina per data e poi per nome del laboratorio
            # Aggiungi intestazione per il laboratorio
            elements.append(Paragraph(f"Laboratorio: {lab}", subtitle_style))
            elements.append(Paragraph(f"Data: {data} - Aula: {aula} - Gruppo: {gruppo}", normal_style))
            elements.append(Spacer(1, 0.3*cm))
            
            # Crea tabella delle presenze
            table_data = [['ID Studente', 'Nome Studente', 'Presente']]
            for student_id, student_name, presente in studenti:
                # Converti student_id in stringa in modo sicuro
                if isinstance(student_id, dict):
                    student_id_str = f"STD_{student_id.get('cognome', '')[:3]}_{student_id.get('nome', '')[:3]}"
                else:
                    student_id_str = str(student_id)
                
                table_data.append([
                    student_id_str,
                    student_name,
                    presente
                ])
            
            # Stili per la tabella
            table = Table(table_data, colWidths=[3*cm, 10*cm, 2*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 0.5*cm))
    
    # Se ci sono presenze registrate, aggiungiamo il riepilogo per studente
    if not df.empty:
        elements.append(Paragraph("Riepilogo Presenze per Studente", subtitle_style))
        elements.append(Spacer(1, 0.3*cm))
        
        student_groups = df.groupby(['ID Studente', 'Nome Studente'])
        
        for (student_id, student_name), student_df in student_groups:
            # Calcola percentuale di presenze
            total_labs = len(student_df)
            present_labs = len(student_df[student_df['Presente'] == 'Sì'])
            attendance_percentage = (present_labs / total_labs * 100) if total_labs > 0 else 0
            
            elements.append(Paragraph(f"Studente: {student_name} (ID: {student_id})", normal_style))
            elements.append(Paragraph(f"Totale Presenze: {present_labs}/{total_labs} ({attendance_percentage:.1f}%)", normal_style))
            
            # Tabella delle presenze per questo studente
            table_data = [['Data', 'Laboratorio', 'Aula', 'Gruppo', 'Presente']]
            for _, row in student_df.iterrows():
                table_data.append([
                    row['Data'],
                    row['Laboratorio'],
                    row['Aula'],
                    row['Gruppo'],
                    row['Presente']
                ])
            
            table = Table(table_data, colWidths=[2.5*cm, 6*cm, 3*cm, 2.5*cm, 2*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 0.5*cm))
    
    # Costruisci il documento
    doc.build(elements)
    
    buffer.seek(0)
    return buffer

def attendance_interface():
    """
    Interfaccia utente per la gestione delle presenze.
    """
    # Inizializza il sistema di presenze
    initialize_attendance()
    
    st.header("Registro Presenze Studenti")
    
    # Verifica che ci sia una programmazione
    if not st.session_state.programmazione:
        st.warning("Non è stata ancora generata una programmazione. Vai alla sezione 'Programmazione' per generarla.")
        return
    
    # Crea tre tab per diverse visualizzazioni
    tab1, tab2, tab3 = st.tabs(["Segna Presenze", "Riepilogo Presenze", "Esporta Report"])
    
    # Tab 1: Segna Presenze
    with tab1:
        st.subheader("Registrazione Presenze")
        st.write("Seleziona un laboratorio programmato e segna le presenze/assenze degli studenti.")
        
        # Raggruppa gli eventi per data
        dates = sorted(list(set([evento["data"] for evento in st.session_state.programmazione])))
        
        selected_date = st.selectbox("Seleziona Data:", options=dates)
        
        if selected_date:
            # Filtra gli eventi per la data selezionata
            eventi_data = [ev for ev in st.session_state.programmazione if ev["data"] == selected_date]
            
            # Organizza gli eventi per laboratorio
            labs_data = {}
            for ev in eventi_data:
                key = f"{ev['laboratorio']} - {ev['ora_inizio']}-{ev['ora_fine']} - Aula: {ev['aula']} - Gruppo: {ev['gruppo']}"
                labs_data[key] = ev
            
            selected_lab = st.selectbox("Seleziona Laboratorio:", options=list(labs_data.keys()))
            
            if selected_lab:
                evento = labs_data[selected_lab]
                
                # Ottieni l'elenco degli studenti per questo gruppo
                studenti_gruppo = []
                
                if evento["tipo_gruppo"] == "standard":
                    studenti_gruppo = st.session_state.gruppi_standard.get(evento["gruppo"], [])
                else:
                    studenti_gruppo = st.session_state.gruppi_ridotti.get(evento["gruppo"], [])
                
                if studenti_gruppo:
                    st.write(f"### Studenti del Gruppo {evento['gruppo']}")
                    
                    # Ottieni le presenze già registrate per questo evento
                    presenze = get_lab_attendance(evento["data"], evento["laboratorio"], evento["aula"], evento["gruppo"])
                    
                    # Preparazione lista studenti con checkbox per presenze
                    student_list = []
                    for student_id in studenti_gruppo:
                        # Gli studenti in gruppi_standard e gruppi_ridotti sono direttamente i loro ID
                        # Cerchiamo lo studente a cui corrisponde questo ID
                        student_info = {}
                        # In questo caso, i student_id sono gli indici nella lista studenti
                        # Verifichiamo il tipo di student_id e cercheremo lo studente in modo appropriato
                        if isinstance(student_id, dict):
                            # Se student_id è già un dizionario, lo usiamo direttamente
                            student_info = student_id
                        elif isinstance(student_id, (int, str)):
                            # Se è un numero o una stringa, cerchiamo per indice
                            try:
                                index = int(student_id) if isinstance(student_id, str) else student_id
                                if 0 <= index < len(st.session_state.studenti):
                                    student_info = st.session_state.studenti[index]
                            except (ValueError, TypeError):
                                # Se non è un indice valido, cerchiamo per corrispondenza esatta con l'ID
                                for i, student in enumerate(st.session_state.studenti):
                                    if str(i) == str(student_id):
                                        student_info = student
                                        break
                        
                        if student_info:
                            # Creiamo un identificatore uniforme (stringa) per l'ID
                            id_str = str(student_id) if not isinstance(student_id, dict) else f"std_{len(student_list)}"
                            # Usiamo sempre una chiave stringa come ID
                            index_for_key = len(student_list)  # Indice corrente nell'array student_list
                            student_list.append({
                                'id': id_str,  # ID convertito a stringa
                                'original_id': student_id,  # Manteniamo l'ID originale per riferimento
                                'cognome': student_info.get('cognome', ''),
                                'nome': student_info.get('nome', ''),
                                'presente': presenze.get(str(index_for_key), False)  # Usiamo l'indice come chiave per evitare problemi
                            })
                    
                    # Crea una tabella di studenti con checkbox
                    for i, student in enumerate(student_list):
                        col1, col2, col3 = st.columns([1, 3, 1])
                        with col1:
                            # Per evitare problemi con ID complessi, convertire a stringa
                            id_str = str(student['id']) if not isinstance(student['id'], dict) else "ID"
                            st.write(f"#{id_str}")
                        with col2:
                            st.write(f"{student['cognome']} {student['nome']}")
                        with col3:
                            # Creiamo una chiave unica che non dipenda dall'ID
                            checkbox_key = f"presence_{evento['data']}_{evento['laboratorio']}_{i}"
                            presente = st.checkbox(
                                "Presente", 
                                value=student['presente'],
                                key=checkbox_key
                            )
                            # Crea un oggetto studente completo
                            student_oggetto = {
                                'id': student['id'],
                                'cognome': student['cognome'],
                                'nome': student['nome']
                            }
                            # Aggiorna in tempo reale con l'oggetto completo
                            mark_attendance(
                                evento["data"], 
                                evento["laboratorio"], 
                                evento["aula"], 
                                evento["gruppo"], 
                                student_oggetto, 
                                presente
                            )
                    
                    # Pulsanti per selezionare tutti o nessuno
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Seleziona Tutti"):
                            for student in student_list:
                                # Crea oggetto studente completo con nome e cognome
                                student_oggetto = {
                                    'id': student['id'],
                                    'cognome': student['cognome'],
                                    'nome': student['nome']
                                }
                                mark_attendance(
                                    evento["data"], 
                                    evento["laboratorio"], 
                                    evento["aula"], 
                                    evento["gruppo"], 
                                    student_oggetto, 
                                    True
                                )
                            st.rerun()
                    with col2:
                        if st.button("Deseleziona Tutti"):
                            for student in student_list:
                                # Crea oggetto studente completo con nome e cognome
                                student_oggetto = {
                                    'id': student['id'],
                                    'cognome': student['cognome'],
                                    'nome': student['nome']
                                }
                                mark_attendance(
                                    evento["data"], 
                                    evento["laboratorio"], 
                                    evento["aula"], 
                                    evento["gruppo"], 
                                    student_oggetto, 
                                    False
                                )
                            st.rerun()
                else:
                    st.warning(f"Non ci sono studenti assegnati al gruppo {evento['gruppo']}.")
    
    # Tab 2: Riepilogo Presenze
    with tab2:
        st.subheader("Riepilogo Presenze")
        
        # Ottieni tutte le presenze
        df_presenze = get_all_attendance()
        
        if not df_presenze.empty:
            # Converti i boolean in Sì/No per una migliore visualizzazione
            df_presenze['Presente'] = df_presenze['Presente'].map({True: 'Sì', False: 'No'})
            
            # Opzioni di filtro
            filter_option = st.radio("Filtra per:", ["Tutti", "Laboratorio", "Studente"])
            
            if filter_option == "Laboratorio":
                # Filtra per laboratorio
                labs = sorted(df_presenze['Laboratorio'].unique())
                selected_lab = st.selectbox("Seleziona Laboratorio:", options=labs)
                
                if selected_lab:
                    # Filtra per data del laboratorio selezionato
                    lab_dates = sorted(df_presenze[df_presenze['Laboratorio'] == selected_lab]['Data'].unique())
                    selected_date = st.selectbox("Seleziona Data:", options=lab_dates)
                    
                    if selected_date:
                        # Mostra presenze per il laboratorio selezionato nella data selezionata
                        filtered_df = df_presenze[
                            (df_presenze['Laboratorio'] == selected_lab) & 
                            (df_presenze['Data'] == selected_date)
                        ]
                        
                        st.write(f"### Presenze per {selected_lab} del {selected_date}")
                        
                        # Calcola statistiche
                        total = len(filtered_df)
                        presenti = len(filtered_df[filtered_df['Presente'] == 'Sì'])
                        percentuale = (presenti / total * 100) if total > 0 else 0
                        
                        st.write(f"**Totale presenze**: {presenti}/{total} ({percentuale:.1f}%)")
                        
                        # Mostra tabella
                        st.dataframe(filtered_df[['Gruppo', 'Nome Studente', 'Presente']], use_container_width=True)
            
            elif filter_option == "Studente":
                # Ottieni elenco studenti
                students = sorted(df_presenze['Nome Studente'].unique())
                selected_student = st.selectbox("Seleziona Studente:", options=students)
                
                if selected_student:
                    # Filtra per studente
                    student_df = df_presenze[df_presenze['Nome Studente'] == selected_student]
                    
                    st.write(f"### Presenze di {selected_student}")
                    
                    # Calcola statistiche
                    total = len(student_df)
                    presenti = len(student_df[student_df['Presente'] == 'Sì'])
                    percentuale = (presenti / total * 100) if total > 0 else 0
                    
                    st.write(f"**Totale presenze**: {presenti}/{total} ({percentuale:.1f}%)")
                    
                    # Mostra tabella
                    st.dataframe(student_df[['Data', 'Laboratorio', 'Aula', 'Gruppo', 'Presente']], use_container_width=True)
            
            else:  # Tutti
                # Mostra statistiche generali
                total_eventi = len(df_presenze['Laboratorio'].unique())
                st.write(f"Totale laboratori con presenze registrate: {total_eventi}")
                
                # Raggruppa per laboratorio
                labs_summary = df_presenze.groupby('Laboratorio').agg(
                    Totale=('Presente', 'count'),
                    Presenti=('Presente', lambda x: (x == 'Sì').sum()),
                ).reset_index()
                
                labs_summary['Percentuale'] = labs_summary['Presenti'] / labs_summary['Totale'] * 100
                
                st.write("### Riepilogo per Laboratorio")
                st.dataframe(labs_summary, use_container_width=True)
                
                # Mostra tabella completa
                st.write("### Tutte le Presenze")
                st.dataframe(df_presenze, use_container_width=True)
        else:
            st.info("Non sono ancora state registrate presenze.")
    
    # Tab 3: Esporta Report
    with tab3:
        st.subheader("Esportazione Report Presenze")
        
        # Ottieni tutte le presenze
        df_presenze = get_all_attendance()
        
        if not df_presenze.empty:
            # Opzioni di esportazione
            st.write("Seleziona il formato di esportazione:")
            
            export_option = st.radio("Formato:", ["PDF", "Excel"])
            
            if export_option == "PDF":
                if st.button("Genera Report PDF"):
                    with st.spinner("Generazione report in corso..."):
                        pdf_buffer = generate_attendance_report()
                        
                        if pdf_buffer:
                            st.success("Report PDF generato con successo!")
                            
                            st.download_button(
                                label="Scarica Report PDF",
                                data=pdf_buffer,
                                file_name="report_presenze.pdf",
                                mime="application/pdf"
                            )
                        else:
                            st.error("Errore nella generazione del report PDF.")
            
            elif export_option == "Excel":
                if st.button("Genera Report Excel"):
                    # Converti i boolean in Sì/No per una migliore visualizzazione
                    df_presenze['Presente'] = df_presenze['Presente'].map({True: 'Sì', False: 'No'})
                    
                    # Crea buffer per Excel
                    buffer = BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        # Foglio con tutte le presenze
                        df_presenze.to_excel(writer, sheet_name='Tutte le Presenze', index=False)
                        
                        # Foglio con riepilogo per laboratorio
                        labs_summary = df_presenze.groupby(['Laboratorio', 'Data', 'Aula', 'Gruppo']).agg(
                            Totale=('Presente', 'count'),
                            Presenti=('Presente', lambda x: (x == 'Sì').sum()),
                        ).reset_index()
                        labs_summary['Percentuale'] = labs_summary['Presenti'] / labs_summary['Totale'] * 100
                        labs_summary.to_excel(writer, sheet_name='Riepilogo Laboratori', index=False)
                        
                        # Foglio con riepilogo per studente
                        student_summary = df_presenze.groupby(['ID Studente', 'Nome Studente']).agg(
                            Totale=('Presente', 'count'),
                            Presenti=('Presente', lambda x: (x == 'Sì').sum()),
                        ).reset_index()
                        student_summary['Percentuale'] = student_summary['Presenti'] / student_summary['Totale'] * 100
                        student_summary.to_excel(writer, sheet_name='Riepilogo Studenti', index=False)
                    
                    buffer.seek(0)
                    
                    st.success("Report Excel generato con successo!")
                    
                    st.download_button(
                        label="Scarica Report Excel",
                        data=buffer,
                        file_name="report_presenze.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        else:
            st.info("Non sono ancora state registrate presenze. Segna almeno una presenza prima di esportare il report.")