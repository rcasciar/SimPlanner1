"""
Modulo per la gestione dei backup dell'applicazione SimPlanner.
Fornisce funzionalità per il salvataggio automatico, backup periodici e ripristino.
"""
import os
import json
import shutil
import datetime
import time
import threading
import zipfile
import streamlit as st
from io import BytesIO
import pandas as pd
import pickle

# Configurazione
BACKUP_DIR = "backup"
TEMP_DIR = "temp_files"
BACKUP_INTERVAL_DAYS = 7  # Intervallo di backup in giorni

# Assicurati che le directory necessarie esistano
os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

def get_session_data():
    """
    Ottiene i dati attuali della sessione da salvare.
    
    Returns:
        dict: I dati della sessione.
    """
    session_data = {}
    
    # Elementi della sessione da salvare
    keys_to_save = [
        'studenti', 'laboratori', 'num_macrogruppi', 'anno_corso', 'anno_accademico', 'sede_cdl', 
        'gruppi_standard', 'gruppi_ridotti', 'aule', 'data_inizio', 'data_fine', 
        'programmazione', 'device_giacenze', 'device_requisiti_lab', 'presenze_studenti'
    ]
    
    for key in keys_to_save:
        if key in st.session_state:
            session_data[key] = st.session_state[key]
    
    return session_data

def save_session_data(trigger_event=None):
    """
    Salva i dati della sessione in un file temporaneo.
    Questo viene chiamato dopo ogni modifica ai dati.
    
    Args:
        trigger_event: Evento che ha innescato il salvataggio (per debug).
    """
    try:
        session_data = get_session_data()
        
        # Se non ci sono dati da salvare, esci
        if not session_data:
            return
        
        # Salva i dati in un file temporaneo
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_file = os.path.join(TEMP_DIR, f"session_data_{timestamp}.pkl")
        
        with open(temp_file, 'wb') as f:
            pickle.dump(session_data, f)
        
        # Mantieni solo gli ultimi 5 file temporanei per risparmiare spazio
        clean_temp_files()
        
        # Aggiorna il riferimento all'ultimo salvataggio
        st.session_state['last_save_time'] = datetime.datetime.now()
        st.session_state['last_save_file'] = temp_file
        
        print(f"Dati salvati in {temp_file}" + (f" trigger: {trigger_event}" if trigger_event else ""))
    except Exception as e:
        print(f"Errore durante il salvataggio dei dati: {e}")

def clean_temp_files(max_files=5):
    """
    Mantiene solo gli ultimi N file temporanei.
    
    Args:
        max_files: Numero massimo di file temporanei da mantenere.
    """
    try:
        files = [os.path.join(TEMP_DIR, f) for f in os.listdir(TEMP_DIR) 
                 if f.startswith("session_data_") and f.endswith(".pkl")]
        
        # Ordina i file per data di modifica (più recenti prima)
        files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        # Elimina i file in eccesso
        for file in files[max_files:]:
            os.remove(file)
    except Exception as e:
        print(f"Errore durante la pulizia dei file temporanei: {e}")

def create_backup():
    """
    Crea un backup completo dei dati dell'applicazione.
    Include sia i file di sessione temporanei che eventuali file esterni.
    
    Returns:
        str: Percorso del file di backup creato.
    """
    try:
        # Salva i dati correnti prima di creare il backup
        save_session_data("backup_creation")
        
        # Crea un nome file per il backup con la data
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(BACKUP_DIR, f"backup_{timestamp}.zip")
        
        # Crea un file ZIP contenente tutti i file necessari
        with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Aggiungi tutti i file temporanei
            for file in os.listdir(TEMP_DIR):
                if file.startswith("session_data_") and file.endswith(".pkl"):
                    zipf.write(os.path.join(TEMP_DIR, file), 
                              arcname=os.path.join("temp_files", file))
            
            # Aggiungi altri file rilevanti (se necessario)
            # Ad esempio file Excel, PDF generati, ecc.
            for directory in ['export']:
                if os.path.exists(directory):
                    for root, _, files in os.walk(directory):
                        for file in files:
                            full_path = os.path.join(root, file)
                            zipf.write(full_path, 
                                     arcname=os.path.join(root, file))
        
        # Aggiorna la data dell'ultimo backup
        st.session_state['last_backup_time'] = datetime.datetime.now()
        st.session_state['last_backup_file'] = backup_file
        
        # Mantieni solo gli ultimi 10 backup per risparmiare spazio
        clean_backup_files()
        
        print(f"Backup creato in {backup_file}")
        return backup_file
    except Exception as e:
        print(f"Errore durante la creazione del backup: {e}")
        return None

def clean_backup_files(max_files=10):
    """
    Mantiene solo gli ultimi N file di backup.
    
    Args:
        max_files: Numero massimo di file di backup da mantenere.
    """
    try:
        files = [os.path.join(BACKUP_DIR, f) for f in os.listdir(BACKUP_DIR) 
                 if f.startswith("backup_") and f.endswith(".zip")]
        
        # Ordina i file per data di modifica (più recenti prima)
        files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        # Elimina i file in eccesso
        for file in files[max_files:]:
            os.remove(file)
    except Exception as e:
        print(f"Errore durante la pulizia dei file di backup: {e}")

def check_backup_needed():
    """
    Controlla se è necessario creare un nuovo backup in base all'intervallo configurato.
    
    Returns:
        bool: True se è necessario un backup, False altrimenti.
    """
    # Se non è mai stato fatto un backup, creane uno
    if 'last_backup_time' not in st.session_state:
        return True
    
    # Calcola il tempo trascorso dall'ultimo backup
    last_backup = st.session_state['last_backup_time']
    now = datetime.datetime.now()
    days_since_backup = (now - last_backup).days
    
    # Crea un nuovo backup se sono passati almeno BACKUP_INTERVAL_DAYS giorni
    return days_since_backup >= BACKUP_INTERVAL_DAYS

def extract_from_backup(backup_file, extract_dir=None):
    """
    Estrae i file da un backup.
    
    Args:
        backup_file: Il file di backup da estrarre.
        extract_dir: Directory in cui estrarre i file.
                     Se None, viene creata una directory temporanea.
    
    Returns:
        str: La directory in cui sono stati estratti i file.
    """
    try:
        if extract_dir is None:
            # Crea una directory temporanea per l'estrazione
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            extract_dir = os.path.join(TEMP_DIR, f"extract_{timestamp}")
            os.makedirs(extract_dir, exist_ok=True)
        
        # Estrai tutti i file
        with zipfile.ZipFile(backup_file, 'r') as zipf:
            zipf.extractall(extract_dir)
        
        return extract_dir
    except Exception as e:
        print(f"Errore durante l'estrazione del backup: {e}")
        return None

def get_latest_save_from_backup(backup_file):
    """
    Recupera l'ultimo salvataggio da un file di backup.
    
    Args:
        backup_file: Il file di backup da cui estrarre il salvataggio.
    
    Returns:
        dict: I dati del salvataggio o None in caso di errore.
    """
    try:
        # Estrai il backup in una directory temporanea
        extract_dir = extract_from_backup(backup_file)
        if not extract_dir:
            return None
        
        # Trova il file di salvataggio più recente
        temp_dir = os.path.join(extract_dir, "temp_files")
        if os.path.exists(temp_dir):
            files = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir) 
                     if f.startswith("session_data_") and f.endswith(".pkl")]
            
            if not files:
                return None
            
            # Ordina i file per data di modifica (più recenti prima)
            files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            # Carica il file più recente
            with open(files[0], 'rb') as f:
                session_data = pickle.load(f)
            
            return session_data
        
        return None
    except Exception as e:
        print(f"Errore durante il recupero del salvataggio dal backup: {e}")
        return None

def restore_from_backup(backup_file):
    """
    Ripristina i dati dell'applicazione da un backup.
    
    Args:
        backup_file: Il file di backup da cui ripristinare i dati.
    
    Returns:
        bool: True se il ripristino è riuscito, False altrimenti.
    """
    try:
        # Recupera l'ultimo salvataggio dal backup
        session_data = get_latest_save_from_backup(backup_file)
        if not session_data:
            return False
        
        # Ripristina i dati nella sessione
        for key, value in session_data.items():
            st.session_state[key] = value
        
        print(f"Ripristino dal backup {backup_file} completato")
        return True
    except Exception as e:
        print(f"Errore durante il ripristino dal backup: {e}")
        return False

def get_available_backups():
    """
    Ottiene l'elenco dei backup disponibili.
    
    Returns:
        list: Lista di tuple (nome_file, data_creazione, dimensione).
    """
    backups = []
    
    try:
        for file in os.listdir(BACKUP_DIR):
            if file.startswith("backup_") and file.endswith(".zip"):
                full_path = os.path.join(BACKUP_DIR, file)
                # Ottieni la data di creazione e dimensione
                timestamp = os.path.getmtime(full_path)
                create_date = datetime.datetime.fromtimestamp(timestamp)
                size_bytes = os.path.getsize(full_path)
                size_mb = size_bytes / (1024 * 1024)  # Converti in MB
                
                backups.append((file, full_path, create_date, size_mb))
        
        # Ordina per data (più recenti prima)
        backups.sort(key=lambda x: x[2], reverse=True)
    except Exception as e:
        print(f"Errore durante il recupero dei backup disponibili: {e}")
    
    return backups

def download_backup(backup_file):
    """
    Prepara un backup per il download.
    
    Args:
        backup_file: Il file di backup da scaricare.
    
    Returns:
        BytesIO: Il contenuto del file di backup.
    """
    try:
        with open(backup_file, 'rb') as f:
            data = f.read()
        
        return BytesIO(data)
    except Exception as e:
        print(f"Errore durante la preparazione del backup per il download: {e}")
        return None

def initialize_backup_system():
    """
    Inizializza il sistema di backup.
    Questa funzione dovrebbe essere chiamata all'avvio dell'applicazione.
    """
    # Inizializza le variabili di sessione se non esistono
    if 'last_save_time' not in st.session_state:
        st.session_state['last_save_time'] = datetime.datetime.now()
    
    if 'last_backup_time' not in st.session_state:
        # Verifica se esistono backup precedenti
        backups = get_available_backups()
        if backups:
            st.session_state['last_backup_time'] = backups[0][2]
            st.session_state['last_backup_file'] = backups[0][1]
        else:
            # Se non ci sono backup, imposta una data vecchia per forzare un backup
            st.session_state['last_backup_time'] = datetime.datetime.now() - datetime.timedelta(days=BACKUP_INTERVAL_DAYS)
    
    # Controlla se è necessario un backup
    if check_backup_needed():
        create_backup()

def backup_interface():
    """
    Interfaccia utente per la gestione dei backup.
    """
    st.subheader("Gestione Backup")
    
    # Mostra informazioni sul sistema di backup
    st.write("Il sistema esegue automaticamente un backup completo ogni 7 giorni.")
    st.write("Tutti i dati vengono salvati automaticamente dopo ogni modifica.")
    
    # Informazioni sull'ultimo salvataggio e backup
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Ultimo salvataggio")
        if 'last_save_time' in st.session_state:
            st.write(f"Data: {st.session_state['last_save_time'].strftime('%d/%m/%Y %H:%M:%S')}")
        else:
            st.write("Nessun salvataggio effettuato")
    
    with col2:
        st.subheader("Ultimo backup")
        if 'last_backup_time' in st.session_state:
            st.write(f"Data: {st.session_state['last_backup_time'].strftime('%d/%m/%Y %H:%M:%S')}")
        else:
            st.write("Nessun backup effettuato")
    
    # Pulsanti per azioni manuali
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Salva ora"):
            save_session_data("manual_save")
            st.success("Dati salvati con successo!")
    
    with col2:
        if st.button("Crea backup ora"):
            backup_file = create_backup()
            if backup_file:
                st.success(f"Backup creato con successo!")
            else:
                st.error("Errore durante la creazione del backup")
    
    # Elenco dei backup disponibili
    st.subheader("Backup disponibili")
    backups = get_available_backups()
    
    if not backups:
        st.write("Nessun backup disponibile")
    else:
        # Crea una tabella con i backup disponibili
        backup_data = {
            "Nome": [b[0] for b in backups],
            "Data": [b[2].strftime("%d/%m/%Y %H:%M:%S") for b in backups],
            "Dimensione (MB)": [f"{b[3]:.2f}" for b in backups]
        }
        
        df = pd.DataFrame(backup_data)
        st.dataframe(df, use_container_width=True)
        
        # Selezione del backup per ripristino o download
        selected_backup_name = st.selectbox("Seleziona un backup", [b[0] for b in backups])
        
        selected_backup = next((b for b in backups if b[0] == selected_backup_name), None)
        
        if selected_backup:
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Ripristina questo backup"):
                    if st.session_state.get('confirm_restore', False):
                        success = restore_from_backup(selected_backup[1])
                        if success:
                            st.success("Backup ripristinato con successo! Ricarica la pagina per vedere le modifiche.")
                            st.session_state['confirm_restore'] = False
                        else:
                            st.error("Errore durante il ripristino del backup")
                    else:
                        st.warning("⚠️ Questa operazione sovrascriverà tutti i dati attuali. Confermi?")
                        st.session_state['confirm_restore'] = True
                        st.button("Annulla", on_click=lambda: st.session_state.update({'confirm_restore': False}))
            
            with col2:
                if st.download_button(
                    label="Scarica questo backup",
                    data=download_backup(selected_backup[1]),
                    file_name=selected_backup[0],
                    mime="application/zip"
                ):
                    st.success("Download avviato!")