# Istruzioni per il Deploy di SimPlanner su Streamlit Community Cloud

## 1. Prepara il tuo Repository GitHub

1. Crea un account GitHub se non ne hai già uno: https://github.com/signup
2. Crea un nuovo repository pubblico su GitHub (ad esempio "simplanner")
3. Scarica tutti i file dal tuo progetto Replit
4. Aggiungi un file `requirements.txt` alla radice del progetto con il seguente contenuto:

```
streamlit
pandas
numpy
plotly
python-docx
reportlab
weasyprint
pdfkit
openpyxl
```

5. Aggiungi anche un file `.streamlit/config.toml` con il seguente contenuto:

```toml
[server]
headless = true
```

6. Carica tutti i file nel tuo repository GitHub (puoi usare l'interfaccia web di GitHub o Git)

## 2. Configura Streamlit Community Cloud

1. Vai su https://streamlit.io/cloud
2. Registrati usando il tuo account GitHub
3. Dopo aver effettuato l'accesso, fai clic su "New app"
4. Seleziona il tuo repository, il ramo (di solito "main") e il percorso al file principale ("app.py")
5. Fai clic su "Deploy"
6. Attendi che l'app venga distribuita (potrebbe richiedere alcuni minuti)

## 3. Configurazioni Aggiuntive (opzionali)

Se la tua app richiede impostazioni specifiche:

1. Puoi configurare variabili d'ambiente nelle impostazioni dell'app su Streamlit Cloud
2. Puoi configurare un dominio personalizzato (se disponibile nel tuo piano)
3. Puoi impostare l'app come privata richiedendo l'accesso tramite OAuth

## 4. Vantaggi di Streamlit Community Cloud

- Hosting gratuito e stabile
- App sempre attiva (no sleep mode)
- Distribuzione automatica quando fai commit al tuo repository
- Opzioni di autenticazione (se necessario)
- Dashboard per monitorare l'utilizzo

## 5. Esportazione dei File da Replit

Per scaricare i file da Replit:

1. Nel tuo progetto Replit, seleziona tutti i file che vuoi includere
2. Fai clic con il tasto destro e seleziona "Download"
3. In alternativa, puoi utilizzare l'opzione di esportazione di Replit per scaricare un archivio del progetto

**Importante**: Assicurati di includere tutti i file necessari, inclusi quelli nella directory `attached_assets` se utilizzati dall'applicazione.