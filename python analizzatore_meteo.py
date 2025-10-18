pip install pandas matplotlib
import pandas as pd
import matplotlib.pyplot as plt
import os

# ==============================================================================
# 1. MAPPATURA DELLE COLONNE E CONFIGURAZIONE
# ==============================================================================

# Definisce le posizioni (indice 0-based) delle colonne RILEVANTI nel file .dat
# Esempio: Colonna 3 -> Indice 2
COLUMNS_MAP = {
    'Ora': 2,
    'Giorno': 3,
    'Mese': 4,
    'Anno': 5,
    'Temperatura (°C)': 16,     # Posizione 17
    'Umidità (%)': 19,          # Posizione 20
    'Precipitazioni (mm)': 22,  # Posizione 23
    'Irraggiamento (W/m²)': 25, # Posizione 26
    'Pressione (hPa)': 28,      # Posizione 29
    'Velocità Vento (m/s)': 31, # Posizione 32
    'Direzione Vento (Gradi)': 34 # Posizione 35
}

# Definisce le funzioni di aggregazione per il Resampling (Da 15 minuti a Giornaliero/Mensile)
# La funzione di aggregazione è diversa a seconda del parametro:
# - Media (mean) per i parametri medi (T, U, Pressione, Vento)
# - Somma (sum) per i totali (Precipitazioni, Irraggiamento)
AGG_FUNCTIONS = {
    'Temperatura (°C)': 'mean',
    'Umidità (%)': 'mean',
    'Precipitazioni (mm)': 'sum',
    'Irraggiamento (W/m²)': 'sum',
    'Pressione (hPa)': 'mean',
    'Velocità Vento (m/s)': 'mean',
    'Direzione Vento (Gradi)': 'mean'
}

# ==============================================================================
# 2. FUNZIONE DI IMPORTAZIONE, PULIZIA E PREPARAZIONE DATI
# ==============================================================================

def load_and_prepare_data(file_path):
    """Carica il file .dat, seleziona le colonne e crea l'indice temporale."""
    
    # 1. Seleziona solo gli indici delle colonne necessarie, ordinati per l'importazione
    all_indices = sorted(COLUMNS_MAP.values())
    
    try:
        # Legge il file CSV (delimitato da virgola), specificando le colonne da usare
        df = pd.read_csv(
            file_path, 
            sep=',', 
            header=None, 
            usecols=all_indices, 
            na_values=['M', 'B', '217', 'ST019', '#36', 'M09'] # Pulisce i codici noti non numerici
        )
    except FileNotFoundError:
        print(f"ERRORE: File non trovato all'indirizzo {file_path}")
        return None
    except Exception as e:
        print(f"ERRORE durante la lettura del file: {e}")
        return None

    # 2. Rinomina le colonne in base alla mappatura
    # È necessario mappare le posizioni originali (indici) ai nomi
    rename_map = {index: name for name, index in COLUMNS_MAP.items()}
    df.rename(columns=rename_map, inplace=True)
    
    # 3. Creazione dell'indice Datetime (Data e Ora)
    # Combina Giorno, Mese, Anno e Ora (che è nel formato hh.mm.ss)
    df['Datetime'] = (
        df['Giorno'].astype(str).str.zfill(2) + '/' + 
        df['Mese'].astype(str).str.zfill(2) + '/' + 
        df['Anno'].astype(str).astype(str) + ' ' + 
        df['Ora']
    )
    
    # Converti la colonna 'Datetime' in un vero formato datetime
    df['Datetime'] = pd.to_datetime(df['Datetime'], format='%d/%m/%Y %H.%M.%S', errors='coerce')
    
    # Imposta la colonna Datetime come indice del DataFrame (Serie Temporale)
    df.set_index('Datetime', inplace=True)
    
    # 4. Pulizia Finale
    # Rimuove le righe dove non è stato possibile creare l'indice temporale
    df.dropna(subset=['Temperatura (°C)'], inplace=True) # Esempio: rimuovi se manca la T
    df = df.select_dtypes(include=['number']) # Assicura che i dati meteo siano numerici
    
    # Rimuove le colonne intermedie usate per creare l'indice
    df.drop(columns=['Giorno', 'Mese', 'Anno', 'Ora'], errors='ignore', inplace=True)
    
    return df

# ==============================================================================
# 3. FUNZIONE DI AGGREGAZIONE E GRAFICA
# ==============================================================================

def plot_data(df, freq, title_prefix, output_folder="Grafici_Meteo"):
    """Aggrega i dati e crea i grafici."""
    
    # Aggregazione (Resampling)
    # 'D' = Giornaliero (Daily), 'M' = Mensile (Monthly)
    df_resampled = df.resample(freq).agg(AGG_FUNCTIONS)
    
    if df_resampled.empty:
        print(f"Nessun dato valido da aggregare per la frequenza {freq}.")
        return

    # Creazione Cartella Output
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Generazione dei grafici per ogni parametro
    for column in df_resampled.columns:
        plt.figure(figsize=(12, 6))
        df_resampled[column].plot(kind='line', marker='o', linestyle='-')
        
        plt.title(f'{title_prefix} - {column}', fontsize=16)
        plt.xlabel('Data', fontsize=12)
        plt.ylabel(column, fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        
        # Salvataggio del grafico
        filename = f"{title_prefix.replace(' ', '_')}_{column.replace(' ', '_').replace('(', '').replace(')', '').replace('/', '-')}.png"
        plt.savefig(os.path.join(output_folder, filename))
        plt.close() # Chiude la figura per liberare memoria
    
    print(f"Generati con successo {len(df_resampled.columns)} grafici per l'analisi {title_prefix}.")

# ==============================================================================
# 4. ESECUZIONE PRINCIPALE
# ==============================================================================

if __name__ == '__main__':
    # >>> MODIFICARE QUESTO PERCORSO CON IL PATH CORRETTO DEL TUO FILE DAT <<<
    file_dat_path = 'path/del/tuo/file.dat' 
    
    # 1. Carica e prepara i dati
    data_15min = load_and_prepare_data(file_dat_path)
    
    if data_15min is not None:
        
        print(f"Dati a 15 minuti caricati: {len(data_15min)} record.")
        
        # 2. ANALISI GIORNALIERA (Frequenza 'D')
        plot_data(data_15min, 'D', 'Andamento Giornaliero')
        
        # 3. ANALISI MENSILE (Frequenza 'M')
        # L'aggregazione mensile prende i dati giornalieri aggregati come input
        # Se si esegue direttamente sui dati a 15 minuti, l'aggregazione è corretta

        plot_data(data_15min, 'M', 'Andamento Mensile')
