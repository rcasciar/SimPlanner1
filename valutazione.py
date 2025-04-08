"""
Modulo per la gestione delle valutazioni dei laboratori.
Permette di caricare immagini e documenti PDF con descrizioni associate
per le diverse tipologie di laboratori, gestire docenti/collaboratori/tutor
e inviare link dei laboratori.
"""

import streamlit as st
import os
import base64
from datetime import datetime
import json
from PIL import Image
import io
import pandas as pd
import uuid
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Configurazione
EVAL_DIR = "valutazioni"
MAX_IMAGES_PER_CATEGORY = 40
ALLOWED_EXTENSIONS = ["jpg", "jpeg", "png", "pdf"]
DOCENTI_FILE = os.path.join(EVAL_DIR, "docenti.json")

# Assicurati che le directory necessarie esistano
os.makedirs(EVAL_DIR, exist_ok=True)
for category in ["cognitivi", "gestuali", "relazionali", "multidimensionali"]:
    os.makedirs(os.path.join(EVAL_DIR, category), exist_ok=True)

def is_valid_file(filename):
    """
    Verifica se il file ha un'estensione consentita.
    
    Args:
        filename: Nome del file da verificare
    
    Returns:
        bool: True se l'estensione è consentita, False altrimenti
    """
    return filename.lower().split(".")[-1] in ALLOWED_EXTENSIONS

def save_uploaded_file(uploaded_file, category, description, link=""):
    """
    Salva un file caricato nella directory appropriata.
    
    Args:
        uploaded_file: File caricato tramite st.file_uploader
        category: Categoria del laboratorio (cognitivi, gestuali, ecc.)
        description: Descrizione testuale associata all'immagine
        link: URL associato al file caricato (opzionale)
    
    Returns:
        str: Percorso del file salvato o None in caso di errore
    """
    try:
        if not uploaded_file:
            return None
            
        # Crea un nome file univoco con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_ext = uploaded_file.name.split(".")[-1].lower()
        filename = f"{timestamp}_{uploaded_file.name}"
        
        # Percorso di salvataggio
        save_path = os.path.join(EVAL_DIR, category, filename)
        
        # Salva il file
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        # Salva anche la descrizione e il link in un file JSON associato
        desc_path = os.path.join(EVAL_DIR, category, f"{timestamp}_{uploaded_file.name}.json")
        with open(desc_path, "w", encoding="utf-8") as f:
            json.dump({
                "description": description, 
                "filename": uploaded_file.name, 
                "uploaded_at": timestamp,
                "link": link
            }, f, ensure_ascii=False)
            
        return save_path
    except Exception as e:
        st.error(f"Errore nel salvataggio del file: {e}")
        return None

def get_image_files(category):
    """
    Ottiene tutti i file immagine e le loro descrizioni per una categoria.
    
    Args:
        category: Categoria del laboratorio (cognitivi, gestuali, ecc.)
    
    Returns:
        list: Lista di tuple (percorso_file, descrizione, timestamp, nome_originale, link)
    """
    try:
        cat_dir = os.path.join(EVAL_DIR, category)
        if not os.path.exists(cat_dir):
            return []
            
        files = []
        for filename in os.listdir(cat_dir):
            if filename.endswith(".json"):
                continue
                
            # Cerca il file JSON associato
            json_filename = f"{filename}.json"
            json_path = os.path.join(cat_dir, json_filename)
            
            description = ""
            timestamp = ""
            original_name = filename
            link = ""
            
            # Se esiste il file JSON, carica la descrizione e il link
            if os.path.exists(json_path):
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        description = data.get("description", "")
                        timestamp = data.get("uploaded_at", "")
                        original_name = data.get("filename", filename)
                        link = data.get("link", "")
                except:
                    pass
                    
            files.append((os.path.join(cat_dir, filename), description, timestamp, original_name, link))
            
        # Ordina per timestamp (più recenti prima)
        files.sort(key=lambda x: x[2] if x[2] else "", reverse=True)
        return files
    except Exception as e:
        st.error(f"Errore nel caricamento dei file: {e}")
        return []

def delete_image(file_path, category):
    """
    Elimina un'immagine e il suo file JSON associato.
    
    Args:
        file_path: Percorso completo del file da eliminare
        category: Categoria del laboratorio (cognitivi, gestuali, ecc.)
    
    Returns:
        bool: True se l'eliminazione è riuscita, False altrimenti
    """
    try:
        # Elimina il file immagine
        if os.path.exists(file_path):
            os.remove(file_path)
            
        # Cerca ed elimina il file JSON associato
        json_path = f"{file_path}.json"
        if os.path.exists(json_path):
            os.remove(json_path)
            
        return True
    except Exception as e:
        st.error(f"Errore nell'eliminazione del file: {e}")
        return False

def render_file_preview(file_path, description, link=""):
    """
    Visualizza un'anteprima del file (immagine o PDF).
    
    Args:
        file_path: Percorso del file da visualizzare
        description: Descrizione del file
        link: Link associato al file (opzionale)
    """
    file_ext = file_path.lower().split(".")[-1]
    
    # Mostra descrizione
    st.write(f"**Descrizione:** {description}")
    
    # Mostra link se presente
    if link:
        st.write(f"**Link:** [{link}]({link})")
    
    if file_ext in ["jpg", "jpeg", "png"]:
        # Visualizza l'immagine
        try:
            image = Image.open(file_path)
            st.image(image, use_container_width=True)
        except Exception as e:
            st.error(f"Errore nella visualizzazione dell'immagine: {e}")
    elif file_ext == "pdf":
        # Per i PDF, crea un link per visualizzarli
        try:
            with open(file_path, "rb") as f:
                pdf_data = f.read()
                
            # Codifica il PDF in base64 per il link
            b64_pdf = base64.b64encode(pdf_data).decode("utf-8")
            pdf_display = f'<embed src="data:application/pdf;base64,{b64_pdf}" width="100%" height="500" type="application/pdf">'
            
            # Mostra PDF
            st.markdown(pdf_display, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Errore nella visualizzazione del PDF: {e}")

# Funzioni per la gestione dei docenti/collaboratori/tutor
def carica_docenti():
    """
    Carica i docenti/collaboratori/tutor dal file JSON.
    
    Returns:
        dict: Dizionario con i dati dei docenti
    """
    if os.path.exists(DOCENTI_FILE):
        try:
            with open(DOCENTI_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Errore nel caricamento dei docenti: {e}")
            return {"docenti": [], "assegnazioni": {}}
    else:
        return {"docenti": [], "assegnazioni": {}}

def salva_docenti(docenti_data):
    """
    Salva i docenti/collaboratori/tutor nel file JSON.
    
    Args:
        docenti_data: Dizionario con i dati dei docenti
    
    Returns:
        bool: True se il salvataggio è riuscito, False altrimenti
    """
    try:
        with open(DOCENTI_FILE, "w", encoding="utf-8") as f:
            json.dump(docenti_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"Errore nel salvataggio dei docenti: {e}")
        return False

def aggiungi_docente(nome, cognome, mail_unito, mail_aziendale):
    """
    Aggiunge un nuovo docente/collaboratore/tutor.
    
    Args:
        nome: Nome del docente
        cognome: Cognome del docente
        mail_unito: Email universitaria
        mail_aziendale: Email aziendale
    
    Returns:
        str: ID del nuovo docente o None in caso di errore
    """
    try:
        docenti_data = carica_docenti()
        docente_id = str(uuid.uuid4())
        
        docenti_data["docenti"].append({
            "id": docente_id,
            "nome": nome,
            "cognome": cognome,
            "mail_unito": mail_unito,
            "mail_aziendale": mail_aziendale,
            "creato_il": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        if not docenti_data["assegnazioni"].get(docente_id):
            docenti_data["assegnazioni"][docente_id] = {
                "cognitivi": [],
                "gestuali": [],
                "relazionali": [],
                "multidimensionali": []
            }
        
        salva_docenti(docenti_data)
        return docente_id
    except Exception as e:
        st.error(f"Errore nell'aggiunta del docente: {e}")
        return None

def elimina_docente(docente_id):
    """
    Elimina un docente/collaboratore/tutor.
    
    Args:
        docente_id: ID del docente da eliminare
    
    Returns:
        bool: True se l'eliminazione è riuscita, False altrimenti
    """
    try:
        docenti_data = carica_docenti()
        
        # Rimuovi il docente dalla lista
        docenti_data["docenti"] = [d for d in docenti_data["docenti"] if d.get("id") != docente_id]
        
        # Rimuovi le assegnazioni
        if docente_id in docenti_data["assegnazioni"]:
            del docenti_data["assegnazioni"][docente_id]
        
        salva_docenti(docenti_data)
        return True
    except Exception as e:
        st.error(f"Errore nell'eliminazione del docente: {e}")
        return False

def aggiorna_assegnazioni(docente_id, categoria, file_ids):
    """
    Aggiorna le assegnazioni di file per un docente.
    
    Args:
        docente_id: ID del docente
        categoria: Categoria dei laboratori
        file_ids: Lista di ID dei file assegnati
    
    Returns:
        bool: True se l'aggiornamento è riuscito, False altrimenti
    """
    try:
        docenti_data = carica_docenti()
        
        if docente_id not in docenti_data["assegnazioni"]:
            docenti_data["assegnazioni"][docente_id] = {
                "cognitivi": [],
                "gestuali": [],
                "relazionali": [],
                "multidimensionali": []
            }
        
        docenti_data["assegnazioni"][docente_id][categoria] = file_ids
        
        salva_docenti(docenti_data)
        return True
    except Exception as e:
        st.error(f"Errore nell'aggiornamento delle assegnazioni: {e}")
        return False

def importa_docenti_da_excel(file_content):
    """
    Importa docenti da un file Excel.
    
    Args:
        file_content: Contenuto del file Excel
    
    Returns:
        tuple: (num_importati, errori)
    """
    try:
        df = pd.read_excel(io.BytesIO(file_content))
        
        # Verificare e normalizzare le colonne
        required_columns = ["nome", "cognome", "mail_unito", "mail_aziendale"]
        
        # Mappa di possibili nomi di colonne
        column_mapping = {
            "nome": ["nome", "name", "first name", "nome docente"],
            "cognome": ["cognome", "surname", "last name", "family name", "cognome docente"],
            "mail_unito": ["mail unito", "email unito", "mail universitaria", "email universitaria", "mail università", "mail unica"],
            "mail_aziendale": ["mail aziendale", "email aziendale", "mail azienda", "email azienda"]
        }
        
        # Cerca colonne corrispondenti
        column_dict = {}
        for req_col, possible_names in column_mapping.items():
            found = False
            for col in df.columns:
                if col.lower() in possible_names:
                    column_dict[req_col] = col
                    found = True
                    break
            if not found:
                return (0, f"Colonna '{req_col}' non trovata nel file Excel")
        
        # Carica i docenti esistenti
        docenti_data = carica_docenti()
        
        num_importati = 0
        errori = []
        
        # Importa i docenti
        for _, row in df.iterrows():
            try:
                nome = str(row[column_dict["nome"]]).strip()
                cognome = str(row[column_dict["cognome"]]).strip()
                mail_unito = str(row[column_dict["mail_unito"]]).strip()
                mail_aziendale = str(row[column_dict["mail_aziendale"]]).strip()
                
                # Validazione base
                if not nome or not cognome:
                    errori.append(f"Riga con nome/cognome mancante: {row.to_dict()}")
                    continue
                
                # Validazione email
                email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                if mail_unito and not re.match(email_pattern, mail_unito):
                    errori.append(f"Email UniTo non valida per {nome} {cognome}: {mail_unito}")
                    continue
                
                if mail_aziendale and not re.match(email_pattern, mail_aziendale):
                    errori.append(f"Email aziendale non valida per {nome} {cognome}: {mail_aziendale}")
                    continue
                
                # Controlla se il docente esiste già (in base a email)
                exists = False
                for docente in docenti_data["docenti"]:
                    if (docente["mail_unito"].lower() == mail_unito.lower() and mail_unito) or \
                       (docente["mail_aziendale"].lower() == mail_aziendale.lower() and mail_aziendale):
                        exists = True
                        break
                
                if not exists:
                    aggiungi_docente(nome, cognome, mail_unito, mail_aziendale)
                    num_importati += 1
                
            except Exception as e:
                errori.append(f"Errore nell'importazione della riga {_+2}: {str(e)}")
        
        return (num_importati, "\n".join(errori) if errori else "")
    
    except Exception as e:
        return (0, f"Errore nell'importazione del file Excel: {str(e)}")

def valutazione_interface():
    """
    Interfaccia utente per la gestione delle valutazioni dei laboratori.
    """
    st.header("Valutazione dei Laboratori")
    
    # Seleziona categoria
    categories = {
        "Laboratori Cognitivi": "cognitivi",
        "Laboratori Gestuali": "gestuali",
        "Laboratori Relazionali": "relazionali",
        "Laboratori Multidimensionali": "multidimensionali"
    }
    
    # Usa tab per le categorie principali
    main_tabs = st.tabs(["Valutazioni", "Docenti/Collaboratori/Tutor"])
    
    with main_tabs[0]:
        # Usa tab per le diverse categorie
        tabs = st.tabs(list(categories.keys()))
        
        for i, (category_name, category_id) in enumerate(categories.items()):
            with tabs[i]:
                st.subheader(category_name)
                
                # Mostra il caricamento di nuovi file
                with st.expander("Carica nuova valutazione", expanded=False):
                    # Campo di descrizione
                    description = st.text_area(f"Descrizione per {category_name}", key=f"desc_{category_id}")
                    
                    # Campo per il link
                    link = st.text_input(f"Link per {category_name} (URL)", key=f"link_{category_id}")
                    
                    # Caricamento file
                    uploaded_file = st.file_uploader(
                        f"Carica un'immagine o PDF per {category_name} (JPG, JPEG, PNG, PDF)",
                        type=ALLOWED_EXTENSIONS,
                        key=f"upload_{category_id}"
                    )
                    
                    if st.button("Salva", key=f"save_{category_id}"):
                        if uploaded_file:
                            # Verifica il numero di file esistenti
                            existing_files = get_image_files(category_id)
                            if len(existing_files) >= MAX_IMAGES_PER_CATEGORY:
                                st.warning(f"Hai raggiunto il limite massimo di {MAX_IMAGES_PER_CATEGORY} file per questa categoria. Elimina alcuni file prima di caricarne altri.")
                            else:
                                # Salva il file
                                saved_path = save_uploaded_file(uploaded_file, category_id, description, link)
                                if saved_path:
                                    st.success(f"File '{uploaded_file.name}' caricato con successo!")
                                    # Memorizza lo stato di caricamento riuscito per utilizzarlo in un eventuale rerun
                                    st.session_state[f"upload_success_{category_id}"] = True
                                    st.rerun()
                        else:
                            st.warning("Seleziona un file da caricare.")
                
                # Mostra i file esistenti
                st.subheader(f"Valutazioni esistenti ({category_name})")
                
                files = get_image_files(category_id)
                if not files:
                    st.info(f"Nessuna valutazione caricata per {category_name}.")
                else:
                    # Mostra il numero di file
                    st.write(f"{len(files)}/{MAX_IMAGES_PER_CATEGORY} valutazioni caricate")
                    
                    # Crea una visualizzazione a griglia per le immagini
                    for i in range(0, len(files), 2):
                        cols = st.columns(2)
                        
                        # Prima colonna
                        with cols[0]:
                            if i < len(files):
                                file_path, description, timestamp, original_name, link = files[i]
                                st.write(f"**{original_name}**")
                                render_file_preview(file_path, description, link)
                                
                                # Pulsante di eliminazione
                                if st.button(f"Elimina", key=f"del_{category_id}_{i}"):
                                    if delete_image(file_path, category_id):
                                        st.success(f"File '{original_name}' eliminato con successo!")
                                        st.rerun()
                        
                        # Seconda colonna
                        with cols[1]:
                            if i+1 < len(files):
                                file_path, description, timestamp, original_name, link = files[i+1]
                                st.write(f"**{original_name}**")
                                render_file_preview(file_path, description, link)
                                
                                # Pulsante di eliminazione
                                if st.button(f"Elimina", key=f"del_{category_id}_{i+1}"):
                                    if delete_image(file_path, category_id):
                                        st.success(f"File '{original_name}' eliminato con successo!")
                                        st.rerun()
    
    # Funzione per inviare email
    def invia_link_email(docente, categoria, files_selezionati):
        """
        Invia i link dei file selezionati via email al docente.
        
        Args:
            docente: Dati del docente
            categoria: Categoria dei laboratori
            files_selezionati: Lista di file selezionati da inviare
            
        Returns:
            bool: True se l'invio è riuscito, False altrimenti
        """
        try:
            # Ottenere parametri email da session_state o configurazione
            smtp_server = st.session_state.get("smtp_server", "")
            smtp_port = st.session_state.get("smtp_port", 587)
            smtp_user = st.session_state.get("smtp_user", "")
            smtp_password = st.session_state.get("smtp_password", "")
            sender_email = st.session_state.get("sender_email", "")
            
            if not smtp_server or not smtp_user or not smtp_password or not sender_email:
                st.warning("Configura i parametri email nelle impostazioni o utilizza l'opzione 'Genera Testo con Link'.")
                return False
            
            # Comporre l'email
            msg = MIMEMultipart()
            msg["From"] = sender_email
            
            # Determinare l'email del destinatario, preferenza per UniTo
            recipient_email = docente["mail_unito"] if docente["mail_unito"] else docente["mail_aziendale"]
            if not recipient_email:
                st.warning(f"Nessuna email disponibile per {docente['nome']} {docente['cognome']}")
                return False
                
            msg["To"] = recipient_email
            msg["Subject"] = f"Link per valutazione laboratori: {categoria.capitalize()}"
            
            # Corpo del messaggio
            body = f"""
            SimPlanner - Sistema Avanzato di Programmazione Laboratori Professionalizzanti in Infermieristica
            
            Gentil* Conduttor*, di seguito i link di accesso ai moduli di valutazione per il laboratorio condotto
            
            {categoria.capitalize()} - {docente['nome']} {docente['cognome']}
            
            """
            
            # Aggiungi link per ogni file selezionato
            for file_id in files_selezionati:
                for file_path, description, _, original_name, link in get_image_files(categoria):
                    if os.path.basename(file_path) == os.path.basename(file_id):
                        body += f"\n- {original_name}: {link}\n"
                        body += f"  Descrizione: {description}\n"
            
            body += """
            
            Cordiali saluti,
            SimPlanner - Sistema di Programmazione Laboratori
            """
            
            msg.attach(MIMEText(body, "plain"))
            
            # Invia email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            st.error(f"Errore nell'invio dell'email: {e}")
            st.info("Puoi usare l'opzione 'Genera Testo con Link' per creare un file di testo o PDF con i link che puoi inviare manualmente.")
            return False
            
    def genera_pdf_links(docente, categoria, categoria_name, files_selezionati):
        """
        Genera un PDF con i link dei file selezionati.
        
        Args:
            docente: Dati del docente
            categoria: ID della categoria dei laboratori
            categoria_name: Nome della categoria visualizzato
            files_selezionati: Lista di file selezionati
            
        Returns:
            BytesIO: Buffer contenente il PDF generato o None in caso di errore
        """
        try:
            files = get_image_files(categoria)
            buffer = BytesIO()
            
            # Creazione del documento PDF
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            elements = []
            
            # Titolo
            title_style = ParagraphStyle(
                'Title',
                parent=styles['Title'],
                fontSize=16,
                spaceAfter=12
            )
            
            # Intestazione dell'applicazione
            app_header_style = ParagraphStyle(
                'AppHeader',
                parent=styles['Title'],
                fontSize=14,
                spaceAfter=6,
                alignment=1  # Centered
            )
            app_header = Paragraph("SimPlanner - Sistema Avanzato di Programmazione Laboratori Professionalizzanti in Infermieristica", app_header_style)
            elements.append(app_header)
            elements.append(Spacer(1, 12))
            
            # Intestazione personalizzata per il docente
            salutation_style = ParagraphStyle(
                'Salutation',
                parent=styles['Normal'],
                fontSize=12,
                leading=15,
                spaceAfter=8
            )
            salutation = Paragraph(f"Gentil* Conduttor*, di seguito i link di accesso ai moduli di valutazione per il laboratorio condotto", salutation_style)
            elements.append(salutation)
            
            # Titolo del documento
            title_style.alignment = 1  # Centered
            title = Paragraph(f"{categoria_name} - {docente['nome']} {docente['cognome']}", title_style)
            elements.append(title)
            elements.append(Spacer(1, 12))
            
            # Data documento
            date_style = ParagraphStyle(
                'Date',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.gray,
                alignment=1  # Centered
            )
            date_text = Paragraph(f"Generato il {datetime.now().strftime('%d/%m/%Y')}", date_style)
            elements.append(date_text)
            elements.append(Spacer(1, 20))
            
            # Contenuto
            text_style = ParagraphStyle(
                'Content',
                parent=styles['Normal'],
                fontSize=10,
                leading=14
            )
            
            link_style = ParagraphStyle(
                'Link',
                parent=text_style,
                textColor=colors.blue
            )
            
            for file_id in files_selezionati:
                for file_path, description, _, original_name, link in files:
                    if os.path.basename(file_path) == os.path.basename(file_id):
                        elements.append(Paragraph(f"<b>{original_name}</b>", text_style))
                        if link:
                            elements.append(Paragraph(f"Link: <a href='{link}'>{link}</a>", link_style))
                        elements.append(Paragraph(f"Descrizione: {description}", text_style))
                        elements.append(Spacer(1, 10))
            
            # Costruisci il PDF
            doc.build(elements)
            
            # Preparazione per il download
            buffer.seek(0)
            return buffer
            
        except Exception as e:
            st.error(f"Errore nella generazione del PDF: {e}")
            return None
    
    
    with main_tabs[1]:
        st.subheader("Gestione Docenti/Collaboratori/Tutor")
        
        # Crea 3 sezioni: Aggiungi, Gestisci, Assegna Link
        doc_tabs = st.tabs(["Aggiungi/Importa", "Gestisci", "Assegna Link e Invia Email", "Impostazioni Email"])
        
        # Tab 1: Aggiungi/Importa
        with doc_tabs[0]:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Inserimento Manuale")
                nome = st.text_input("Nome")
                cognome = st.text_input("Cognome")
                mail_unito = st.text_input("Mail UniTo")
                mail_aziendale = st.text_input("Mail Aziendale")
                
                if st.button("Aggiungi Docente/Collaboratore/Tutor"):
                    if nome and cognome:
                        if mail_unito or mail_aziendale:
                            # Validazione email
                            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                            error = False
                            
                            if mail_unito and not re.match(email_pattern, mail_unito):
                                st.error("Email UniTo non valida.")
                                error = True
                            
                            if mail_aziendale and not re.match(email_pattern, mail_aziendale):
                                st.error("Email aziendale non valida.")
                                error = True
                            
                            if not error:
                                docente_id = aggiungi_docente(nome, cognome, mail_unito, mail_aziendale)
                                if docente_id:
                                    st.success(f"Docente {nome} {cognome} aggiunto con successo!")
                                    # Reset campi
                                    st.session_state.mail_unito = ""
                                    st.session_state.mail_aziendale = ""
                                    st.session_state.nome = ""
                                    st.session_state.cognome = ""
                                    st.rerun()
                        else:
                            st.warning("Inserire almeno un indirizzo email (UniTo o aziendale).")
                    else:
                        st.warning("Nome e cognome sono campi obbligatori.")
            
            with col2:
                st.subheader("Importazione da Excel")
                st.markdown("""
                Formato Excel richiesto:
                - Colonne: Nome, Cognome, Mail UniTo, Mail Aziendale
                - Un docente/collaboratore/tutor per riga
                """)
                
                excel_file = st.file_uploader("Carica file Excel (.xlsx)", type=["xlsx"])
                
                if st.button("Importa da Excel") and excel_file:
                    num_importati, errori = importa_docenti_da_excel(excel_file.read())
                    if num_importati > 0:
                        st.success(f"Importati {num_importati} docenti/collaboratori/tutor.")
                        if errori:
                            with st.expander("Dettagli errori"):
                                st.error(errori)
                    else:
                        st.error(f"Nessun docente importato. {errori}")
        
        # Tab 2: Gestisci
        with doc_tabs[1]:
            st.subheader("Docenti/Collaboratori/Tutor")
            
            docenti_data = carica_docenti()
            if not docenti_data["docenti"]:
                st.info("Nessun docente/collaboratore/tutor presente. Aggiungi o importa dalla scheda precedente.")
            else:
                # Crea una tabella con i dati
                df = pd.DataFrame([
                    {
                        "ID": d["id"],
                        "Nome": d["nome"],
                        "Cognome": d["cognome"],
                        "Mail UniTo": d["mail_unito"],
                        "Mail Aziendale": d["mail_aziendale"],
                        "Data inserimento": d.get("creato_il", "")
                    }
                    for d in docenti_data["docenti"]
                ])
                
                # Filtri di ricerca
                search = st.text_input("Ricerca (nome, cognome, email)", "")
                if search:
                    df = df[
                        df["Nome"].str.contains(search, case=False) | 
                        df["Cognome"].str.contains(search, case=False) | 
                        df["Mail UniTo"].str.contains(search, case=False) | 
                        df["Mail Aziendale"].str.contains(search, case=False)
                    ]
                
                st.dataframe(df)
                
                # Selezione per eliminazione
                selected_id = st.selectbox("Seleziona docente/collaboratore/tutor da eliminare", 
                                           options=df["ID"].tolist(),
                                           format_func=lambda x: f"{df[df['ID'] == x]['Nome'].iloc[0]} {df[df['ID'] == x]['Cognome'].iloc[0]}")
                
                if st.button("Elimina Selezionato"):
                    if elimina_docente(selected_id):
                        st.success("Docente/collaboratore/tutor eliminato con successo!")
                        st.rerun()
        
        # Tab 3: Assegna Link e Invia Email
        with doc_tabs[2]:
            st.subheader("Assegna Link ai Docenti/Collaboratori/Tutor")
            
            docenti_data = carica_docenti()
            if not docenti_data["docenti"]:
                st.info("Nessun docente/collaboratore/tutor presente. Aggiungi o importa docenti prima.")
            else:
                # Selezione docente
                docenti_options = [f"{d['nome']} {d['cognome']}" for d in docenti_data["docenti"]]
                docenti_ids = [d["id"] for d in docenti_data["docenti"]]
                
                docente_idx = st.selectbox("Seleziona docente/collaboratore/tutor", 
                                          range(len(docenti_options)),
                                          format_func=lambda i: docenti_options[i])
                
                docente_id = docenti_ids[docente_idx]
                docente = next((d for d in docenti_data["docenti"] if d["id"] == docente_id), None)
                
                # Mostra info docente
                if docente:
                    st.write(f"**Mail UniTo:** {docente['mail_unito']}")
                    st.write(f"**Mail Aziendale:** {docente['mail_aziendale']}")
                    
                    # Tabs per categorie
                    assign_tabs = st.tabs(list(categories.keys()))
                    
                    for i, (category_name, category_id) in enumerate(categories.items()):
                        with assign_tabs[i]:
                            st.subheader(f"Assegna {category_name}")
                            
                            # Ottieni tutti i file della categoria
                            files = get_image_files(category_id)
                            
                            if not files:
                                st.info(f"Nessun file presente nella categoria {category_name}.")
                            else:
                                # Ottieni assegnazioni attuali
                                current_assignments = docenti_data["assegnazioni"].get(docente_id, {}).get(category_id, [])
                                
                                # Visualizza file come checkbox
                                st.write("Seleziona i file da assegnare:")
                                
                                file_options = {}
                                for file_path, description, _, original_name, link in files:
                                    file_id = os.path.basename(file_path)
                                    is_assigned = file_id in current_assignments
                                    file_options[file_id] = st.checkbox(
                                        f"{original_name} - {description[:50]}{'...' if len(description) > 50 else ''}",
                                        value=is_assigned,
                                        key=f"assign_{docente_id}_{category_id}_{file_id}"
                                    )
                                
                                # Pulsante per salvare le assegnazioni
                                if st.button("Salva Assegnazioni", key=f"save_assign_{category_id}"):
                                    selected_files = [file_id for file_id, selected in file_options.items() if selected]
                                    if aggiorna_assegnazioni(docente_id, category_id, selected_files):
                                        st.success("Assegnazioni salvate con successo!")
                                        st.rerun()
                                
                                # Pulsanti per inviare via email o generare testo con i link
                                cols = st.columns(2)
                                with cols[0]:
                                    if st.button("Invia Link via Email", key=f"send_email_{category_id}"):
                                        selected_files = [file_id for file_id, selected in file_options.items() if selected]
                                        
                                        if not selected_files:
                                            st.warning("Nessun file selezionato per l'invio.")
                                        else:
                                            if invia_link_email(docente, category_id, selected_files):
                                                st.success("Email inviata con successo!")
                                            else:
                                                st.error("Errore nell'invio dell'email. Controlla le impostazioni email.")
                                
                                with cols[1]:
                                    if st.button("Genera Testo con Link", key=f"gen_text_{category_id}"):
                                        selected_files = [file_id for file_id, selected in file_options.items() if selected]
                                        
                                        if not selected_files:
                                            st.warning("Nessun file selezionato.")
                                        else:
                                            # Genera testo con i link
                                            text = f"SimPlanner - Sistema Avanzato di Programmazione Laboratori Professionalizzanti in Infermieristica\n\n"
                                            text += f"Gentil* Conduttor*, di seguito i link di accesso ai moduli di valutazione per il laboratorio condotto\n\n"
                                            text += f"{category_name} - {docente['nome']} {docente['cognome']}\n\n"
                                            
                                            for file_id in selected_files:
                                                for file_path, description, _, original_name, link in files:
                                                    if os.path.basename(file_path) == os.path.basename(file_id):
                                                        text += f"• {original_name}:\n"
                                                        text += f"  Link: {link}\n"
                                                        text += f"  Descrizione: {description}\n\n"
                                            
                                            # Mostra il testo in un campo copiabile
                                            st.text_area("Copia e incolla il seguente testo in una email:", text, height=300)
                                            
                                            # Opzionalmente, crea un file scaricabile
                                            st.download_button(
                                                label="Scarica come file di testo",
                                                data=text,
                                                file_name=f"link_{category_id}_{docente['cognome']}_{datetime.now().strftime('%Y%m%d')}.txt",
                                                mime="text/plain"
                                            )
                                            
                                            # Aggiungi pulsante per generare PDF
                                            pdf_buffer = genera_pdf_links(docente, category_id, category_name, selected_files)
                                            if pdf_buffer:
                                                st.download_button(
                                                    label="Scarica come PDF",
                                                    data=pdf_buffer,
                                                    file_name=f"link_{category_id}_{docente['cognome']}_{datetime.now().strftime('%Y%m%d')}.pdf",
                                                    mime="application/pdf"
                                                )
        
        # Tab 4: Impostazioni Email
        with doc_tabs[3]:
            st.subheader("Impostazioni Email")
            
            # Salva impostazioni nella session state
            if "smtp_server" not in st.session_state:
                st.session_state.smtp_server = ""
            if "smtp_port" not in st.session_state:
                st.session_state.smtp_port = 587
            if "smtp_user" not in st.session_state:
                st.session_state.smtp_user = ""
            if "smtp_password" not in st.session_state:
                st.session_state.smtp_password = ""
            if "sender_email" not in st.session_state:
                st.session_state.sender_email = ""
            
            st.session_state.smtp_server = st.text_input("Server SMTP", st.session_state.smtp_server)
            st.session_state.smtp_port = st.number_input("Porta SMTP", value=st.session_state.smtp_port)
            st.session_state.smtp_user = st.text_input("Username SMTP", st.session_state.smtp_user)
            st.session_state.smtp_password = st.text_input("Password SMTP", st.session_state.smtp_password, type="password")
            st.session_state.sender_email = st.text_input("Email Mittente", st.session_state.sender_email)
            
            if st.button("Salva Impostazioni Email"):
                st.success("Impostazioni email salvate con successo!")
                
            with st.expander("Informazioni SMTP"):
                st.markdown("""
                ### Configurazione SMTP
                
                Per inviare email, è necessario configurare le impostazioni SMTP:
                
                - **Gmail**: 
                  - Server SMTP: smtp.gmail.com
                  - Porta: 587
                  - Richiede l'uso di password per app (impostazioni Google Account)
                
                - **Outlook/Office 365**:
                  - Server SMTP: smtp.office365.com
                  - Porta: 587
                  
                - **UniTo**:
                  - Server SMTP: smtp.unito.it
                  - Porta: 587 o 465 (SSL/TLS)
                  - Username: nome.cognome@unito.it
                  - Verifica con IT UniTo per impostazioni corrette se necessario
                
                ### Alternativa all'invio email
                Se non vuoi configurare le impostazioni SMTP, puoi sempre utilizzare l'opzione **"Genera Testo con Link"** 
                che ti permette di creare un file di testo o PDF con i link da inviare manualmente.
                """)
                
                st.warning("Attenzione: La password SMTP viene salvata in memoria e non viene crittografata. Non utilizzare la tua password principale, ma crea password specifiche per app quando possibile.")
                st.info("Per evitare configurazioni email, usa l'opzione 'Genera Testo con Link' nella scheda 'Assegna Link e Invia Email'.")
    
