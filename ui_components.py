"""
Componenti UI per l'applicazione di programmazione laboratori.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import base64
from io import BytesIO

def create_navbar():
    """
    Crea una barra di navigazione fissa per l'applicazione.
    """
    # Aggiungi CSS per la barra di navigazione fissa
    st.markdown("""
    <style>
    .navbar {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background-color: #1e88e5;
        color: white;
        padding: 10px 20px;
        z-index: 1000;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    
    .navbar-brand {
        font-size: 1.5rem;
        font-weight: bold;
        color: white;
        text-decoration: none;
    }
    
    .navbar-menu {
        display: flex;
        gap: 20px;
    }
    
    .navbar-item {
        color: white;
        text-decoration: none;
        cursor: pointer;
        padding: 5px 10px;
        border-radius: 5px;
        transition: background-color 0.3s;
    }
    
    .navbar-item:hover {
        background-color: rgba(255,255,255,0.2);
    }
    
    /* Aggiungi padding al corpo per evitare che il contenuto venga nascosto sotto la navbar */
    .main-content {
        padding-top: 60px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Crea la barra di navigazione
    nav_html = """
    <div class="navbar">
        <div class="navbar-brand">SimPlanner</div>
        <div class="navbar-menu">
            <a class="navbar-item" href="javascript:void(0);" onclick="document.getElementById('section-config').scrollIntoView();">Configurazione</a>
            <a class="navbar-item" href="javascript:void(0);" onclick="document.getElementById('section-schedule').scrollIntoView();">Programmazione</a>
            <a class="navbar-item" href="javascript:void(0);" onclick="document.getElementById('section-visualization').scrollIntoView();">Visualizzazione</a>
            <a class="navbar-item" href="javascript:void(0);" onclick="document.getElementById('section-export').scrollIntoView();">Esportazione</a>
            <a class="navbar-item" href="javascript:void(0);" onclick="document.getElementById('section-inventory').scrollIntoView();">Inventario</a>
            <a class="navbar-item" href="javascript:void(0);" onclick="document.getElementById('section-attendance').scrollIntoView();">Presenze</a>
            <a class="navbar-item" href="javascript:void(0);" onclick="document.getElementById('section-valutazione').scrollIntoView();">Valutazione</a>
            <a class="navbar-item" href="javascript:void(0);" onclick="document.getElementById('section-backup').scrollIntoView();">Backup</a>
        </div>
    </div>
    
    <div class="main-content"></div>
    """
    
    st.markdown(nav_html, unsafe_allow_html=True)

def section_header(title, section_id):
    """
    Crea un'intestazione di sezione con ID per la navigazione.
    """
    st.markdown(f'<div id="{section_id}"></div>', unsafe_allow_html=True)
    st.header(title)
    st.markdown("---")

def create_preview_card(title, content, actions=None):
    """
    Crea una card di anteprima per vari elementi.
    
    Args:
        title: Titolo della card
        content: Contenuto HTML della card
        actions: Lista di tuple (etichetta, chiave) per i pulsanti di azione
    """
    # CSS per la card
    st.markdown("""
    <style>
    .preview-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 20px;
        background-color: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .preview-card-title {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 10px;
        color: #1e88e5;
    }
    
    .preview-card-content {
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Crea la card
    st.markdown(f"""
    <div class="preview-card">
        <div class="preview-card-title">{title}</div>
        <div class="preview-card-content">{content}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Aggiungi pulsanti di azione se presenti
    if actions:
        cols = st.columns(len(actions))
        for i, (label, key) in enumerate(actions):
            with cols[i]:
                return st.button(label, key=key)
    
    return None

def show_toast_notification(message, type="success"):
    """
    Mostra una notifica toast.
    
    Args:
        message: Messaggio da mostrare
        type: Tipo di notifica (success, info, warning, error)
    """
    if type == "success":
        st.success(message)
    elif type == "info":
        st.info(message)
    elif type == "warning":
        st.warning(message)
    elif type == "error":
        st.error(message)

def add_shortcut_buttons():
    """
    Aggiunge pulsanti di scorciatoia per operazioni comuni.
    """
    st.markdown("""
    <style>
    .shortcut-buttons {
        position: fixed;
        bottom: 20px;
        right: 20px;
        display: flex;
        flex-direction: column;
        gap: 10px;
        z-index: 1000;
    }
    
    .shortcut-button {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background-color: #1e88e5;
        color: white;
        display: flex;
        justify-content: center;
        align-items: center;
        cursor: pointer;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        transition: transform 0.3s, background-color 0.3s;
    }
    
    .shortcut-button:hover {
        transform: scale(1.1);
        background-color: #1976d2;
    }
    </style>
    
    <div class="shortcut-buttons">
        <div class="shortcut-button" onclick="document.documentElement.scrollTop = 0;" title="Torna all'inizio">
            ↑
        </div>
        <div class="shortcut-button" onclick="document.getElementById('section-export').scrollIntoView();" title="Vai all'esportazione">
            📥
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_compact_mode_toggle():
    """
    Crea un toggle per la modalità compatta.
    
    Returns:
        True se la modalità compatta è attiva, False altrimenti
    """
    if 'compact_mode' not in st.session_state:
        st.session_state.compact_mode = False
        
    compact_mode = st.toggle("Modalità compatta", value=st.session_state.compact_mode)
    
    if compact_mode != st.session_state.compact_mode:
        st.session_state.compact_mode = compact_mode
        st.rerun()
        
    # Applica CSS per la modalità compatta
    if compact_mode:
        st.markdown("""
        <style>
        div.block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        
        div.stExpander {
            margin-bottom: 0.5rem;
        }
        
        div.stButton > button {
            padding-top: 0.25rem;
            padding-bottom: 0.25rem;
        }
        
        div.row-widget.stRadio > div {
            flex-direction: row;
            align-items: center;
        }
        
        div.row-widget.stRadio > div > label {
            padding: 0.25rem 0.5rem;
            margin: 0 0.25rem;
        }
        </style>
        """, unsafe_allow_html=True)
    
    return compact_mode

def load_css_animation():
    """
    Carica animazioni CSS per l'interfaccia
    """
    st.markdown("""
    <style>
    /* Animazione di fade-in per le sezioni */
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(20px); }
      to { opacity: 1; transform: translateY(0); }
    }
    
    .stHeader {
      animation: fadeIn 0.5s ease-out;
    }
    
    /* Effetto hover sulle card */
    div.element-container div.stDataFrame,
    div.row-widget.stButton > button {
      transition: transform 0.3s, box-shadow 0.3s;
    }
    
    div.element-container div.stDataFrame:hover,
    div.row-widget.stButton > button:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

def get_download_link(data, filename, text):
    """
    Crea un link di download per i dati.
    
    Args:
        data: Dati da scaricare (BytesIO)
        filename: Nome del file
        text: Testo del link
    
    Returns:
        Codice HTML per il link di download
    """
    b64 = base64.b64encode(data.getvalue()).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">{text}</a>'
    return href

def display_event_log(logs):
    """
    Visualizza il log degli eventi con formattazione migliorata.
    
    Args:
        logs: Lista di tuple (timestamp, evento, dettagli)
    """
    if not logs:
        st.info("Nessun evento registrato.")
        return
    
    # Crea CSS per il log
    st.markdown("""
    <style>
    .event-log {
        max-height: 300px;
        overflow-y: auto;
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 10px;
    }
    
    .log-entry {
        padding: 8px;
        margin-bottom: 8px;
        border-radius: 5px;
        border-left: 3px solid #1e88e5;
        background-color: #f8f9fa;
    }
    
    .log-time {
        font-size: 0.8rem;
        color: #666;
    }
    
    .log-event {
        font-weight: bold;
        color: #1e88e5;
    }
    
    .log-details {
        margin-top: 5px;
        font-size: 0.9rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Crea HTML per il log
    log_html = '<div class="event-log">'
    
    for timestamp, evento, dettagli in logs:
        log_html += f'''
        <div class="log-entry">
            <div class="log-time">{timestamp.strftime('%d/%m/%Y %H:%M:%S')}</div>
            <div class="log-event">{evento}</div>
            <div class="log-details">{dettagli}</div>
        </div>
        '''
    
    log_html += '</div>'
    
    # Visualizza il log
    st.markdown(log_html, unsafe_allow_html=True)

def create_tutorial_steps():
    """
    Funzione semplificata che sostituisce il tutorial interattivo precedente,
    che era troppo pesante per l'applicazione.
    """
    pass

def initialize_log():
    """
    Inizializza il log degli eventi se non esiste.
    """
    if 'event_log' not in st.session_state:
        st.session_state.event_log = []

def log_event(evento, dettagli):
    """
    Aggiunge un evento al log.
    
    Args:
        evento: Nome dell'evento
        dettagli: Dettagli dell'evento
    """
    initialize_log()
    st.session_state.event_log.append((datetime.now(), evento, dettagli))

def get_event_log():
    """
    Ottiene il log degli eventi.
    
    Returns:
        Lista di tuple (timestamp, evento, dettagli)
    """
    initialize_log()
    return st.session_state.event_log