"""
Funzioni di importazione avanzate per SimPlanner
"""
import pandas as pd
import streamlit as st
import io

def importa_giacenze_da_excel(excel_paste, uploaded_file=None):
    """
    Importa dati di giacenze da testo incollato da Excel o da file Excel caricato
    con supporto avanzato per diversi formati e nomi di colonne.
    
    Args:
        excel_paste: Testo incollato da Excel (può essere None se uploaded_file è fornito)
        uploaded_file: File Excel caricato (st.UploadedFile) o None
        
    Returns:
        tuple: (nuovi_prodotti, prodotti_aggiornati, errore)
    """
    # Se è stato fornito un file Excel caricato
    if uploaded_file is not None:
        try:
            # Leggi il file Excel caricato
            df = pd.read_excel(uploaded_file)
            
            # Normalizza i nomi delle colonne
            df.columns = [str(col).lower().strip() for col in df.columns]
            
            # Qui reimplementiamo la parte che avevamo dopo per processare il DataFrame
            # Cerca le colonne necessarie (con varie possibili denominazioni)
            col_codice = None
            for col in ['codice', 'code', 'cod', 'codice prodotto', 'id']:
                if col in df.columns:
                    col_codice = col
                    break
                    
            col_nome = None
            for col in ['nome', 'name', 'denominazione', 'prodotto', 'descrizione', 'description']:
                if col in df.columns:
                    col_nome = col
                    break
                    
            col_quantita = None
            for col in ['quantità', 'quantita', 'qty', 'quantity', 'giacenza', 'disponibilità', 'disponibilita']:
                if col in df.columns:
                    col_quantita = col
                    break
            
            # Verifica che le colonne richieste siano state trovate
            if not col_codice or not col_nome or not col_quantita:
                missing = []
                if not col_codice: missing.append("codice")
                if not col_nome: missing.append("nome")
                if not col_quantita: missing.append("quantità")
                
                error_msg = f"Intestazioni mancanti: {', '.join(missing)}. Colonne trovate: {', '.join(df.columns)}"
                return 0, 0, error_msg
            
            # Processa ogni riga
            nuovi_prodotti = 0
            prodotti_aggiornati = 0
            
            for _, row in df.iterrows():
                try:
                    # Estrai e pulisci i dati
                    codice_excel = str(row[col_codice]).strip()
                    nome_excel = str(row[col_nome]).strip()
                    
                    # Salta righe con codice vuoto
                    if not codice_excel or pd.isna(codice_excel):
                        continue
                        
                    # Assicurati che il nome non sia vuoto
                    if not nome_excel or pd.isna(nome_excel):
                        nome_excel = f"Prodotto {codice_excel}"
                    
                    # Gestisci vari formati per la quantità
                    try:
                        quantita_val = row[col_quantita]
                        if isinstance(quantita_val, (int, float)):
                            quantita_excel = int(quantita_val)
                        else:
                            # Converte stringhe come "1.200" o "1,200" in 1200
                            quantita_str = str(quantita_val).strip().replace('.', '').replace(',', '.')
                            quantita_excel = int(float(quantita_str))
                    except (ValueError, TypeError):
                        quantita_excel = 0
                    
                    # Verifica se il codice esiste già
                    codici_esistenti = [item["codice"] for item in st.session_state.device_giacenze]
                    if codice_excel in codici_esistenti:
                        # Aggiorna la quantità se il prodotto esiste già
                        for j, item in enumerate(st.session_state.device_giacenze):
                            if item["codice"] == codice_excel:
                                st.session_state.device_giacenze[j]["quantita"] = quantita_excel
                                # Aggiorna anche il nome se è cambiato
                                if nome_excel != item["nome"]:
                                    st.session_state.device_giacenze[j]["nome"] = nome_excel
                                prodotti_aggiornati += 1
                                break
                    else:
                        # Aggiungi nuovo prodotto se non esiste
                        st.session_state.device_giacenze.append({
                            "codice": codice_excel,
                            "nome": nome_excel,
                            "quantita": quantita_excel
                        })
                        nuovi_prodotti += 1
                except Exception as e:
                    st.warning(f"Errore nell'elaborazione di una riga: {str(e)}")
            
            return nuovi_prodotti, prodotti_aggiornati, None
            
        except Exception as e:
            return 0, 0, f"Errore nella lettura del file Excel: {str(e)}"
    
    # Altrimenti se è stato fornito testo incollato
    if not excel_paste:
        return 0, 0, "Nessun dato da importare"
    
    try:
        # Prima prova con pandas (gestisce meglio vari formati)
        try:
            from io import StringIO
            # Prova prima con tab come separatore
            df = pd.read_csv(StringIO(excel_paste), sep='\t')
            
            # Se non ci sono almeno 2 colonne, prova con altri separatori
            if len(df.columns) < 2:
                # Prova con virgola
                df = pd.read_csv(StringIO(excel_paste), sep=',')
                
                # Se ancora non funziona, prova con punto e virgola
                if len(df.columns) < 2:
                    df = pd.read_csv(StringIO(excel_paste), sep=';')
        except Exception:
            # Fallback al metodo manuale
            raise ValueError("Impossibile leggere i dati con pandas")
        
        # Normalizza i nomi delle colonne
        df.columns = [str(col).lower().strip() for col in df.columns]
        
        # Cerca le colonne necessarie (con varie possibili denominazioni)
        col_codice = None
        for col in ['codice', 'code', 'cod', 'codice prodotto', 'id']:
            if col in df.columns:
                col_codice = col
                break
                
        col_nome = None
        for col in ['nome', 'name', 'denominazione', 'prodotto', 'descrizione', 'description']:
            if col in df.columns:
                col_nome = col
                break
                
        col_quantita = None
        for col in ['quantità', 'quantita', 'qty', 'quantity', 'giacenza', 'disponibilità', 'disponibilita']:
            if col in df.columns:
                col_quantita = col
                break
        
        # Verifica che le colonne richieste siano state trovate
        if not col_codice or not col_nome or not col_quantita:
            missing = []
            if not col_codice: missing.append("codice")
            if not col_nome: missing.append("nome")
            if not col_quantita: missing.append("quantità")
            
            error_msg = f"Intestazioni mancanti: {', '.join(missing)}. Colonne trovate: {', '.join(df.columns)}"
            raise ValueError(error_msg)
        
        # Processa ogni riga
        nuovi_prodotti = 0
        prodotti_aggiornati = 0
        
        for _, row in df.iterrows():
            try:
                # Estrai e pulisci i dati
                codice_excel = str(row[col_codice]).strip()
                nome_excel = str(row[col_nome]).strip()
                
                # Salta righe con codice vuoto
                if not codice_excel or pd.isna(codice_excel):
                    continue
                    
                # Assicurati che il nome non sia vuoto
                if not nome_excel or pd.isna(nome_excel):
                    nome_excel = f"Prodotto {codice_excel}"
                
                # Gestisci vari formati per la quantità
                try:
                    quantita_val = row[col_quantita]
                    if isinstance(quantita_val, (int, float)):
                        quantita_excel = int(quantita_val)
                    else:
                        # Converte stringhe come "1.200" o "1,200" in 1200
                        quantita_str = str(quantita_val).strip().replace('.', '').replace(',', '.')
                        quantita_excel = int(float(quantita_str))
                except (ValueError, TypeError):
                    quantita_excel = 0
                
                # Verifica se il codice esiste già
                codici_esistenti = [item["codice"] for item in st.session_state.device_giacenze]
                if codice_excel in codici_esistenti:
                    # Aggiorna la quantità se il prodotto esiste già
                    for j, item in enumerate(st.session_state.device_giacenze):
                        if item["codice"] == codice_excel:
                            st.session_state.device_giacenze[j]["quantita"] = quantita_excel
                            # Aggiorna anche il nome se è cambiato
                            if nome_excel != item["nome"]:
                                st.session_state.device_giacenze[j]["nome"] = nome_excel
                            prodotti_aggiornati += 1
                            break
                else:
                    # Aggiungi nuovo prodotto se non esiste
                    st.session_state.device_giacenze.append({
                        "codice": codice_excel,
                        "nome": nome_excel,
                        "quantita": quantita_excel
                    })
                    nuovi_prodotti += 1
            except Exception as e:
                st.warning(f"Errore nell'elaborazione di una riga: {str(e)}")
    except Exception as e:
        # Se il metodo pandas fallisce, ricadi sul metodo manuale originale
        st.warning(f"Metodo avanzato fallito: {str(e)}. Provo con il metodo manuale.")
        
        # Metodo manuale di fallback
        righe = excel_paste.strip().split('\n')
        
        if len(righe) < 2:
            return 0, 0, "Formato non valido. È necessario includere almeno la riga di intestazione e una riga di dati."
        
        # Analizza la prima riga come intestazioni di colonna
        intestazioni = []
        if '\t' in righe[0]:
            intestazioni = [h.strip().lower() for h in righe[0].split('\t')]
        else:
            import re
            intestazioni = [h.strip().lower() for h in re.split(r'\s{2,}', righe[0])]
        
        # Cerca le colonne necessarie con vari nomi possibili
        idx_codice = -1
        for col in ['codice', 'code', 'cod', 'codice prodotto', 'id']:
            if col in intestazioni:
                idx_codice = intestazioni.index(col)
                break
                
        idx_nome = -1
        for col in ['nome', 'name', 'denominazione', 'prodotto', 'descrizione', 'description']:
            if col in intestazioni:
                idx_nome = intestazioni.index(col)
                break
                
        idx_quantita = -1
        for col in ['quantità', 'quantita', 'qty', 'quantity', 'giacenza', 'disponibilità', 'disponibilita']:
            if col in intestazioni:
                idx_quantita = intestazioni.index(col)
                break
        
        # Verifica che le colonne richieste siano state trovate
        if idx_codice == -1 or idx_nome == -1 or idx_quantita == -1:
            missing = []
            if idx_codice == -1: missing.append("codice")
            if idx_nome == -1: missing.append("nome")
            if idx_quantita == -1: missing.append("quantità")
            
            return 0, 0, f"Intestazioni mancanti: {', '.join(missing)}. Intestazioni trovate: {', '.join(intestazioni)}"
        
        # Processa le righe di dati (dalla seconda riga in poi)
        nuovi_prodotti = 0
        prodotti_aggiornati = 0
        
        for i in range(1, len(righe)):
            riga = righe[i]
            
            # Salta righe vuote
            if not riga.strip():
                continue
            
            # Gestisce i tab o più spazi come separatori
            if '\t' in riga:
                campi = riga.split('\t')
            else:
                # Se non ci sono tab, separa basandosi su spazi multipli
                import re
                campi = re.split(r'\s{2,}', riga)
            
            # Verifica che ci siano abbastanza campi
            if len(campi) <= max(idx_codice, idx_nome, idx_quantita):
                st.warning(f"Riga {i+1} ignorata (campi insufficienti): {riga}")
                continue
                
            try:
                # Estrai i dati dai campi corretti in base agli indici delle intestazioni
                codice_excel = str(campi[idx_codice].strip())
                nome_excel = str(campi[idx_nome].strip())
                
                # Salta righe con codice vuoto
                if not codice_excel:
                    continue
                    
                # Assicurati che il nome non sia vuoto
                if not nome_excel:
                    nome_excel = f"Prodotto {codice_excel}"
                
                # Gestisci vari formati dei numeri nella colonna quantità
                quantita_str = campi[idx_quantita].strip().replace('.', '').replace(',', '.')
                quantita_excel = int(float(quantita_str)) if quantita_str else 0
                
                # Verifica se il codice esiste già
                codici_esistenti = [item["codice"] for item in st.session_state.device_giacenze]
                if codice_excel in codici_esistenti:
                    # Aggiorna la quantità se il prodotto esiste già
                    for j, item in enumerate(st.session_state.device_giacenze):
                        if item["codice"] == codice_excel:
                            st.session_state.device_giacenze[j]["quantita"] = quantita_excel
                            # Aggiorna anche il nome se è cambiato
                            if nome_excel != item["nome"]:
                                st.session_state.device_giacenze[j]["nome"] = nome_excel
                            prodotti_aggiornati += 1
                            break
                else:
                    # Aggiungi nuovo prodotto se non esiste
                    st.session_state.device_giacenze.append({
                        "codice": codice_excel,
                        "nome": nome_excel,
                        "quantita": quantita_excel
                    })
                    nuovi_prodotti += 1
            except ValueError:
                st.warning(f"Riga {i+1} ignorata (errore formato): {riga}")
    
    return nuovi_prodotti, prodotti_aggiornati, None