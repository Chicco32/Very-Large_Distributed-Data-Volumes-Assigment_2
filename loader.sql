-- Loader che crea la tabella "rides" e carica i dati dal CSV "porto.csv"
-- Assicurati di avere i permessi per creare tabelle e caricare dati nel database

CREATE DATABASE IF NOT EXISTS `porto_db`;

USE `porto_db`;

CREATE TABLE IF NOT EXISTS `porto_db`.`rides` (
    TRIP_ID BIGINT PRIMARY KEY,
    CALL_TYPE CHAR(1),
    ORIGIN_CALL FLOAT DEFAULT NULL,
    ORIGIN_STAND FLOAT DEFAULT NULL,
    TAXI_ID INT,
    CALL_DATE DATETIME,
    DAY_TYPE CHAR(1),
    missing_data BOOLEAN,
    POLYLINE JSON,
    NUM_GPS_POINTS INT
);

-- carica i dati dal CSV nella tabella "rides"
-- Richiede che local_infile sia abilitato nel client e nel server MySQL.
-- Il valore di CSV_PATH deve essere definito nel file .env e sostituito dal
-- tool che esegue questo script (MySQL non legge direttamente i file .env).
LOAD DATA LOCAL INFILE '${CSV_PATH}'
INTO TABLE porto_db.rides
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

--ALTER TABLE `porto_db`.`rides`
--DROP COLUMN IF EXISTS `missing_data`;