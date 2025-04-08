"""
Implementazione del drag-and-drop per la gestione visuale della programmazione.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import json

def generate_calendar_html(programmazione, date_disponibili, aule):
    """
    Genera il codice HTML per il calendario drag-and-drop.
    
    Args:
        programmazione: Lista degli eventi programmati
        date_disponibili: Lista delle date disponibili
        aule: Lista delle aule disponibili
    
    Returns:
        HTML e JavaScript per il calendario interattivo
    """
    # Converti la programmazione in formato JSON per JavaScript
    eventi_json = json.dumps(programmazione)
    date_json = json.dumps([d.strftime("%d/%m/%Y") if isinstance(d, datetime) else d for d in date_disponibili])
    aule_json = json.dumps([a['nome'] if isinstance(a, dict) else a for a in aule])
    
    # Genera un ID unico per questa istanza
    calendar_id = "calendar-" + datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Stile e CSS
    style = """
    <style>
    .calendar-container {
        width: 100%;
        overflow-x: auto;
        padding-bottom: 20px;
    }
    
    .calendar {
        display: grid;
        grid-template-columns: 120px repeat(var(--num-days), minmax(180px, 1fr));
        gap: 4px;
        font-family: sans-serif;
    }
    
    .header-cell {
        background-color: #e3f2fd;
        padding: 8px;
        font-weight: bold;
        text-align: center;
        border-radius: 4px;
        border: 1px solid #ccc;
    }
    
    .time-cell {
        background-color: #e3f2fd;
        padding: 8px;
        font-weight: bold;
        text-align: right;
        border-radius: 4px;
        border: 1px solid #ccc;
    }
    
    .calendar-cell {
        min-height: 80px;
        background-color: #f8f9fa;
        border-radius: 4px;
        border: 1px dashed #ccc;
        padding: 2px;
    }
    
    .calendar-cell.droppable-hover {
        background-color: #bbdefb;
        border: 2px solid #1976d2;
    }
    
    .event {
        background-color: #1e88e5;
        color: white;
        padding: 6px;
        border-radius: 4px;
        margin-bottom: 4px;
        cursor: move;
        font-size: 0.8rem;
    }
    
    .event-dragging {
        opacity: 0.5;
    }
    
    .event-item-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .event-remove {
        cursor: pointer;
        color: #ffcdd2;
        padding: 2px 4px;
        border-radius: 50%;
    }
    
    .event-remove:hover {
        background-color: rgba(255, 255, 255, 0.2);
        color: #ef9a9a;
    }
    
    .unscheduled-container {
        margin-top: 20px;
        padding: 10px;
        background-color: #f5f5f5;
        border-radius: 4px;
        border: 1px solid #ddd;
    }
    
    .unscheduled-title {
        font-weight: bold;
        margin-bottom: 10px;
    }
    
    .unscheduled-events {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }
    </style>
    """
    
    # HTML per il calendario
    html = f"""
    {style}
    <div class="calendar-container">
        <div id="{calendar_id}" class="calendar"></div>
        
        <div class="unscheduled-container">
            <div class="unscheduled-title">Eventi non programmati</div>
            <div id="unscheduled-events-{calendar_id}" class="unscheduled-events"></div>
        </div>
    </div>
    """
    
    # JavaScript per gestire il drag-and-drop
    js = f"""
    <script>
    // Dati dal Python
    const events = {eventi_json};
    const availableDates = {date_json};
    const availableRooms = {aule_json};
    
    // Inizializzazione
    document.addEventListener('DOMContentLoaded', function() {{
        initCalendar('{calendar_id}', events, availableDates, availableRooms);
    }});
    
    function initCalendar(calendarId, events, dates, rooms) {{
        const calendar = document.getElementById(calendarId);
        const unscheduledContainer = document.getElementById(`unscheduled-events-${{calendarId}}`);
        
        // Imposta variabili CSS
        calendar.style.setProperty('--num-days', dates.length);
        
        // Crea l'intestazione con le date
        const headerRow = document.createElement('div');
        headerRow.style.display = 'contents';
        
        // Cella vuota per l'angolo superiore sinistro
        const cornerCell = document.createElement('div');
        cornerCell.className = 'header-cell';
        cornerCell.textContent = 'Orario / Data';
        headerRow.appendChild(cornerCell);
        
        // Celle per le date
        dates.forEach(date => {{
            const dateCell = document.createElement('div');
            dateCell.className = 'header-cell';
            dateCell.textContent = date;
            headerRow.appendChild(dateCell);
        }});
        
        calendar.appendChild(headerRow);
        
        // Crea le righe orarie
        const timeSlots = ['08:30-11:00', '11:10-13:30', '14:30-17:00'];
        timeSlots.forEach(timeSlot => {{
            const timeRow = document.createElement('div');
            timeRow.style.display = 'contents';
            
            // Cella per l'orario
            const timeCell = document.createElement('div');
            timeCell.className = 'time-cell';
            timeCell.textContent = timeSlot;
            timeRow.appendChild(timeCell);
            
            // Celle per ogni data
            dates.forEach(date => {{
                const cell = document.createElement('div');
                cell.className = 'calendar-cell';
                cell.dataset.date = date;
                cell.dataset.timeSlot = timeSlot;
                
                // Rendi la cella droppable
                cell.addEventListener('dragover', handleDragOver);
                cell.addEventListener('dragleave', handleDragLeave);
                cell.addEventListener('drop', handleDrop);
                
                timeRow.appendChild(cell);
            }});
            
            calendar.appendChild(timeRow);
        }});
        
        // Aggiungi gli eventi al calendario
        events.forEach(event => {{
            addEventToCalendar(event, calendarId);
        }});
        
        // Comunica a Streamlit quando gli eventi cambiano
        function notifyStreamlit() {{
            const allEvents = getAllEvents(calendarId);
            window.parent.postMessage({{
                type: 'calendar-events-update',
                events: allEvents
            }}, '*');
        }}
        
        // Funzione per aggiungere un evento al calendario
        function addEventToCalendar(event, calendarId) {{
            const eventElement = createEventElement(event);
            
            if (event.data && event.aula && event.ora_inizio) {{
                // Trova la cella corretta
                const cell = findCell(event.data, getTimeSlotFromEvent(event));
                if (cell) {{
                    cell.appendChild(eventElement);
                }} else {{
                    // Se non trova la cella, metti nell'area non programmati
                    unscheduledContainer.appendChild(eventElement);
                }}
            }} else {{
                // Eventi non programmati
                unscheduledContainer.appendChild(eventElement);
            }}
        }}
        
        function getTimeSlotFromEvent(event) {{
            if (event.ora_inizio === '08:30' && event.ora_fine === '11:00') return '08:30-11:00';
            if (event.ora_inizio === '11:10' && event.ora_fine === '13:30') return '11:10-13:30';
            if (event.ora_inizio === '14:30' && event.ora_fine === '17:00') return '14:30-17:00';
            return null;
        }}
        
        function findCell(date, timeSlot) {{
            const cells = document.querySelectorAll(`#${{calendarId}} .calendar-cell`);
            for (const cell of cells) {{
                if (cell.dataset.date === date && cell.dataset.timeSlot === timeSlot) {{
                    return cell;
                }}
            }}
            return null;
        }}
        
        function createEventElement(event) {{
            const eventElement = document.createElement('div');
            eventElement.className = 'event';
            eventElement.draggable = true;
            eventElement.dataset.id = event.id || Math.random().toString(36).substring(2);
            
            // Memorizza i dati dell'evento
            eventElement.dataset.event = JSON.stringify(event);
            
            // Prima riga: lab e gruppo
            const titleRow = document.createElement('div');
            titleRow.className = 'event-item-row';
            
            const labText = document.createElement('span');
            labText.textContent = event.laboratorio;
            titleRow.appendChild(labText);
            
            const groupText = document.createElement('span');
            groupText.textContent = `Gruppo: ${{event.gruppo}}`;
            titleRow.appendChild(groupText);
            
            eventElement.appendChild(titleRow);
            
            // Seconda riga: aula e controlli
            const detailsRow = document.createElement('div');
            detailsRow.className = 'event-item-row';
            
            const roomText = document.createElement('span');
            roomText.textContent = `Aula: ${{event.aula || 'Non assegnata'}}`;
            detailsRow.appendChild(roomText);
            
            const removeBtn = document.createElement('span');
            removeBtn.className = 'event-remove';
            removeBtn.textContent = '✕';
            removeBtn.addEventListener('click', function(e) {{
                e.stopPropagation();
                eventElement.remove();
                notifyStreamlit();
            }});
            detailsRow.appendChild(removeBtn);
            
            eventElement.appendChild(detailsRow);
            
            // Eventi per drag-and-drop
            eventElement.addEventListener('dragstart', handleDragStart);
            eventElement.addEventListener('dragend', handleDragEnd);
            
            return eventElement;
        }}
        
        // Handler per drag-and-drop
        function handleDragStart(e) {{
            e.dataTransfer.setData('text/plain', e.target.dataset.id);
            e.target.classList.add('event-dragging');
        }}
        
        function handleDragEnd(e) {{
            e.target.classList.remove('event-dragging');
            notifyStreamlit();
        }}
        
        function handleDragOver(e) {{
            e.preventDefault();
            e.currentTarget.classList.add('droppable-hover');
        }}
        
        function handleDragLeave(e) {{
            e.currentTarget.classList.remove('droppable-hover');
        }}
        
        function handleDrop(e) {{
            e.preventDefault();
            e.currentTarget.classList.remove('droppable-hover');
            
            const eventId = e.dataTransfer.getData('text/plain');
            const draggedEvent = document.querySelector(`.event[data-id="${{eventId}}"]`);
            
            if (draggedEvent) {{
                // Aggiorna i dati dell'evento
                const eventData = JSON.parse(draggedEvent.dataset.event);
                eventData.data = e.currentTarget.dataset.date;
                
                // Estrai ora inizio e fine dalla fascia oraria
                const [oraInizio, oraFine] = e.currentTarget.dataset.timeSlot.split('-');
                eventData.ora_inizio = oraInizio;
                eventData.ora_fine = oraFine;
                
                // Aggiorna il dataset dell'elemento
                draggedEvent.dataset.event = JSON.stringify(eventData);
                
                // Sposta l'elemento nella cella
                e.currentTarget.appendChild(draggedEvent);
                
                notifyStreamlit();
            }}
        }}
        
        // Ottieni tutti gli eventi dal calendario
        function getAllEvents(calendarId) {{
            const eventElements = document.querySelectorAll(`#${{calendarId}} .event, #unscheduled-events-${{calendarId}} .event`);
            return Array.from(eventElements).map(el => JSON.parse(el.dataset.event));
        }}
    }}
    </script>
    """
    
    return html + js

def create_drag_drop_calendar():
    """
    Crea un calendario drag-and-drop per la gestione della programmazione.
    """
    # Ottieni le date disponibili
    data_inizio = converti_data_italiana(st.session_state.data_inizio)
    data_fine = converti_data_italiana(st.session_state.data_fine)
    date_disponibili = []
    
    if data_inizio and data_fine:
        from datetime import timedelta
        
        current_date = data_inizio
        while current_date <= data_fine:
            if current_date.weekday() < 5:  # Solo giorni feriali (0-4: lunedì-venerdì)
                date_disponibili.append(current_date.strftime("%d/%m/%Y"))
            current_date += timedelta(days=1)
    
    # Se non ci sono date, mostra un messaggio
    if not date_disponibili:
        st.warning("Nessuna data disponibile. Configura prima le date.")
        return
    
    # Ottieni le aule
    aule = st.session_state.aule
    
    # Se non ci sono aule, mostra un messaggio
    if not aule:
        st.warning("Nessuna aula disponibile. Configura prima le aule.")
        return
    
    # Ottieni la programmazione
    programmazione = st.session_state.programmazione
    
    # Genera il codice HTML
    calendar_html = generate_calendar_html(programmazione, date_disponibili, aule)
    
    # Visualizza il calendario
    st.components.v1.html(calendar_html, height=600, scrolling=True)
    
    # Aggiungi JavaScript per ricevere gli eventi aggiornati
    st.markdown("""
    <script>
    // Ascolta i messaggi dal calendario
    window.addEventListener('message', function(e) {
        if (e.data.type === 'calendar-events-update') {
            // Invia i dati a Streamlit
            window.parent.postMessage({
                type: 'streamlit:setComponentValue',
                value: e.data.events
            }, '*');
        }
    });
    </script>
    """, unsafe_allow_html=True)
    
def converti_data_italiana(data_str):
    """
    Converte una data dal formato italiano (gg/mm/aaaa) a oggetto datetime
    """
    from datetime import datetime
    try:
        if data_str and isinstance(data_str, str):
            return datetime.strptime(data_str, "%d/%m/%Y")
        return None
    except Exception:
        return None