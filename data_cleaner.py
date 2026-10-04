# Data Cleaner for Taxi Data
# 1. se ci sono trip con polilinee con 2 o meno punti GPS, significa che la corsa non è valida. In questo caso, MISSING_DATA dovrebbe essere TRUE.
# 2. Se ci ono entrare che violano i vincoli di coerenza di call_type, allora si scartano.
# 3. le coppie (TIMESTAMP, TAXI_ID) devono essere univoque. Se ci sono duplicati, significa che lo stesso taxi ha inviato più volte la stessa corsa nello stesso istante.
#    essendo gia stati scartati i dati non conformi, non ci sono elementi per distinguere le due corse e arbitrariamente si può tiene solo una delle due. 
#    Se invece uno dei due vincoli non è rispettato, allora si mantiene quello che rispetta i vincoli e si scarta l'altro.
#   Per statistiche contiamo quanti dati arbitrariamente scartiamo per questo motivo, in particolare contiamo solo se scaritamo due polinee differenti.
# 4. se restano ancora duplicati di TRIP_ID, significia che sono corse effettivamente distinte ma con lo stesso TRIP_ID. 
#    In questo caso TRIP_id verra riassegnato in modo univoco.

import pandas as pd
import json

from test import conta_punti
def load_csv(file_path):
    """
    Carica un file CSV in un DataFrame di pandas.
    
    Args:
        file_path (str): Il percorso del file CSV da caricare.
        
    Returns:
        pd.DataFrame: Il DataFrame contenente i dati del CSV.
    """
    try:
        df = pd.read_csv(file_path)
        print(f"Caricato il file {file_path} con {len(df)} righe.")
        return df
    except Exception as e:
        print(f"Errore durante il caricamento del file {file_path}: {e}")
        return None
    
def delete_invalid_polilines(df):
    """
    Rimuove le corse con polilinee non valide (meno di 3 punti GPS) e MISSING_DATA=False.
    
    Args:
        df (pd.DataFrame): Il DataFrame contenente i dati delle corse.
        
    Returns:
        pd.DataFrame: Il DataFrame filtrato senza le corse non valide.
    """
    # Calcola il numero di punti GPS per ogni corsa
    df['NUM_GPS_POINTS'] = df['POLYLINE'].apply(conta_punti)
    
    # Filtra le corse valide
    valid_df = df[(df['NUM_GPS_POINTS'] >= 3) | (df['MISSING_DATA'] == True)]
    
    print(f"Rimosse {len(df) - len(valid_df)} corse con polilinee non valide.")
    
    return valid_df

def delete_inconsistent_call_types(df):
    """
    Rimuove le corse che violano i vincoli di coerenza di CALL_TYPE.
    
    Args:
        df (pd.DataFrame): Il DataFrame contenente i dati delle corse.
        
    Returns:
        pd.DataFrame: Il DataFrame filtrato senza le corse non coerenti.
    """
    # Tipo A: ORIGIN_CALL deve essere presente
    anomalie_A = df[(df['CALL_TYPE'] == 'A') & (df['ORIGIN_CALL'].isna())]

    # Tipo B: ORIGIN_STAND deve essere presente
    anomalie_B = df[(df['CALL_TYPE'] == 'B') & (df['ORIGIN_STAND'].isna())]

    # Tipo C: Nessun ID deve essere presente (chiamata per strada)
    anomalie_C = df[(df['CALL_TYPE'] == 'C') & 
                    (~df['ORIGIN_CALL'].isna() | ~df['ORIGIN_STAND'].isna())]

    # Rimuove le corse non coerenti
    valid_df = df.drop(anomalie_A.index).drop(anomalie_B.index).drop(anomalie_C.index)
    
    print(f"Rimosse {len(df) - len(valid_df)} corse non coerenti con CALL_TYPE.")
    
    return valid_df

def delete_duplicate_timestamp_taxi(df):
    """
    Rimuove le corse duplicate basate sulla coppia (TIMESTAMP, TAXI_ID).
    
    Args:
        df (pd.DataFrame): Il DataFrame contenente i dati delle corse.
        
    Returns:
        pd.DataFrame: Il DataFrame filtrato senza le corse duplicate.
    """
    diff_poli = 0
    
    # Trova duplicati basati su (TIMESTAMP, TAXI_ID)
    duplicati_timestamp_taxi = df.duplicated(subset=['TIMESTAMP', 'TAXI_ID'], keep=False)
    
    # Conta quanti duplicati hanno polilinee differenti
    for _, group in df[duplicati_timestamp_taxi].groupby(['TIMESTAMP', 'TAXI_ID']):
        if group['POLYLINE'].nunique() > 1:
            diff_poli += 1
            
    # Mantieni solo la prima occorrenza di ciascun duplicato
    valid_df = df[~duplicati_timestamp_taxi | ~df.duplicated(subset=['TIMESTAMP', 'TAXI_ID'], keep='first')]
            
    
    print(f"Rimosse {len(df) - len(valid_df)} corse duplicate basate su (TIMESTAMP, TAXI_ID).")
    print(f"Di queste, {diff_poli} avevano polilinee differenti.")
    
    return valid_df

def reassign_trip_ids(df):
    """
    Riassegna TRIP_ID univoci per le corse duplicate.
    
    Args:
        df (pd.DataFrame): Il DataFrame contenente i dati delle corse.
        
    Returns:
        pd.DataFrame: Il DataFrame con TRIP_ID riassegnati.
    """
    # Trova duplicati basati su TRIP_ID
    duplicati_trip_id = df.duplicated(subset=['TRIP_ID'], keep=False)
    
    # Riassegna TRIP_ID univoci per i duplicati
    df.loc[duplicati_trip_id, 'TRIP_ID'] = df.loc[duplicati_trip_id].groupby('TRIP_ID').cumcount() + 1
    
    print(f"Riassegnati TRIP_ID univoci per {duplicati_trip_id.sum()} corse duplicate.")
    
    return df

def convert_timestamp_to_datetime(df):
    """
    Converte la colonna TIMESTAMP in formato datetime.
    
    Args:
        df (pd.DataFrame): Il DataFrame contenente i dati delle corse.
        
    Returns:
        pd.DataFrame: Il DataFrame con TIMESTAMP convertito in datetime.
    """
    df['TIMESTAMP'] = pd.to_datetime(df['TIMESTAMP'], unit='s')
    print("Colonna TIMESTAMP convertita in formato datetime.")
    return df


def save_cleaned_data(df, output_path):
    """
    Salva il DataFrame pulito in un file CSV.
    
    Args:
        df (pd.DataFrame): Il DataFrame contenente i dati puliti.
        output_path (str): Il percorso del file CSV di output.
    """
    try:
        df.to_csv(output_path, index=False)
        print(f"Dati puliti salvati in {output_path}.")
    except Exception as e:
        print(f"Errore durante il salvataggio dei dati puliti: {e}")


def clean_data(df, output_path):
    """
    Esegue tutte le operazioni di pulizia dei dati.
    
    Args:
        df (pd.DataFrame): Il DataFrame contenente i dati delle corse.
        output_path (str): Il percorso del file CSV di output.
    Returns:
        pd.DataFrame: Il DataFrame pulito.
    """
    df = delete_invalid_polilines(df)
    df = delete_inconsistent_call_types(df)
    df = delete_duplicate_timestamp_taxi(df)
    df = reassign_trip_ids(df)
    df = convert_timestamp_to_datetime(df)
    save_cleaned_data(df, output_path)
    
    return df

INPUT_PATH = 'porto/porto.csv'
OUTPUT_PATH = 'porto/porto_cleaned.csv'
cleaned_df = clean_data(load_csv(INPUT_PATH), OUTPUT_PATH)