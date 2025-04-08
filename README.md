# Programmazione Laboratori

Un'applicazione Streamlit per la programmazione dei laboratori per studenti.

## Installazione

Per eseguire questa applicazione localmente, segui questi passaggi:

1. Assicurati di avere Python 3.9 o superiore installato
2. Scarica tutti i file di questo progetto in una cartella locale
3. Installa le dipendenze necessarie eseguendo:
   ```
   pip install streamlit pandas numpy plotly openpyxl
   ```
4. Avvia l'applicazione:
   ```
   streamlit run app.py
   ```
5. L'app si aprirà automaticamente nel tuo browser predefinito

## Utilizzo

1. Nella scheda "Programmazione":
   - Inserisci il numero di studenti
   - Inserisci i nomi degli studenti manualmente o carica un file Excel
   - Fai clic su "Genera Programmazione" per creare l'orario dei laboratori
   - Visualizza la programmazione in diverse modalità (per stanza, per laboratorio, per giorno)

2. Nella scheda "Laboratori e Dispositivi":
   - Gestisci i dispositivi richiesti per ciascun laboratorio
   - Aggiungi nuovi dispositivi al sistema

3. Nella scheda "Inventario":
   - Visualizza e aggiorna l'inventario dei dispositivi
   - Ricevi avvisi quando le scorte sono basse

4. Nella scheda "Gestione Completamento":
   - Segna i laboratori come completati
   - Monitora l'utilizzo dei dispositivi

## Note

- L'algoritmo di programmazione si adatta automaticamente al numero di studenti
- Per gruppi piccoli (5 o meno studenti), viene utilizzato un algoritmo speciale che assegna tutti gli studenti a ogni laboratorio