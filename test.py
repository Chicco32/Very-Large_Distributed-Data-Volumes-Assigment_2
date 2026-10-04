import pandas as pd
import json

# 1. Caricamento del dataset
# Usa nrows=100000 se vuoi limitare la lettura esattamente alle prime 100.000 righe
df = pd.read_csv('porto/porto.csv')

print(f"Totale righe analizzate: {len(df)}")
print("-" * 40)

# ==========================================
# CONTROLLO 1: DUPLICATI
# ==========================================
# TRIP_ID è l'identificatore univoco per ogni corsa
duplicati = df.duplicated(subset=['TRIP_ID']).sum()
print(f"1. Trovati {duplicati} TRIP_ID duplicati.")

if duplicati > 0:
    print(df[df.duplicated(subset=['TRIP_ID'], keep=False)].head())

print("-" * 40)

# ==========================================
# CONTROLLO 2: COERENZA CALL_TYPE
# ==========================================
# Tipo A: ORIGIN_CALL deve essere presente
anomalie_A = df[(df['CALL_TYPE'] == 'A') & (df['ORIGIN_CALL'].isna())]

# Tipo B: ORIGIN_STAND deve essere presente
anomalie_B = df[(df['CALL_TYPE'] == 'B') & (df['ORIGIN_STAND'].isna())]

# Tipo C: Nessun ID deve essere presente (chiamata per strada)
anomalie_C = df[(df['CALL_TYPE'] == 'C') & 
                (~df['ORIGIN_CALL'].isna() | ~df['ORIGIN_STAND'].isna())]

print("2. Risultati validazione CALL_TYPE:")
print(f"   - Corse tipo 'A' senza ORIGIN_CALL: {len(anomalie_A)}")
print(f"   - Corse tipo 'B' senza ORIGIN_STAND: {len(anomalie_B)}")
print(f"   - Corse tipo 'C' con ID non nulli: {len(anomalie_C)}")

print("-" * 40)

# ==========================================
# CONTROLLO 3: MISSING_DATA vs PUNTI GPS
# ==========================================
# MISSING_DATA = FALSE significa che i dati sono COMPLETI.
# Controlliamo i casi in cui POLYLINE è una lista vuota "[]" per vedere se combaciano.

corse_vuote = df[df['POLYLINE'] == '[]']
print(f"3. Trovate {len(corse_vuote)} corse con POLYLINE vuota (0 punti GPS).")

# Incoerenza: La stringa è vuota ma MISSING_DATA dice che i dati sono completi (False)
incoerenze_missing = corse_vuote[corse_vuote['MISSING_DATA'] == True]
print(f"   - Di queste, {len(incoerenze_missing)} corse affermano che MISSING_DATA è TRUE.")

# Opzionale: Calcolare quanti punti GPS ci sono in ogni corsa valida
# NOTA: json.loads è significativamente più veloce di ast.literal_eval per grandi dataset
def conta_punti(polyline_str):
    if polyline_str == '[]':
        return 0
    try:
        return len(json.loads(polyline_str))
    except:
        return 0

# Applica il conteggio solo per avere una statistica (può impiegare qualche secondo su 100k righe)
print("   - Calcolo della lunghezza delle traiettorie in corso...")
#df['NUM_GPS_POINTS'] = df['POLYLINE'].apply(conta_punti)

#corse_con_pochi_punti = df[(df['NUM_GPS_POINTS'] < 3) & (df['MISSING_DATA'] == False)]
#print(f"   - Corse con meno di 3 punti (non valide) ma con MISSING_DATA=False: {len(corse_con_pochi_punti)}")

# controlla tutte le coppie Timestamp-taxi_id per vedere se ci sono duplicati
#duplicati_timestamp_taxi = df.duplicated(subset=['TIMESTAMP', 'TAXI_ID'], keep=False)
#print(f"   - Corse con duplicati di Timestamp e TAXI_ID: {duplicati_timestamp_taxi.sum()}")
#stampa le prime 10 coppie duplicate
#print(df[duplicati_timestamp_taxi].head(10))

#media di punti GPS per corsa
df['NUM_GPS_POINTS'] = df['POLYLINE'].apply(conta_punti)
media_punti_gps = df['NUM_GPS_POINTS'].mean()
print(f"   - Media di punti GPS per corsa: {media_punti_gps:.2f}")