-- SQLBook: Markup
How many taxi, trips and GPS are there in the dataset?
- 82781502 gps points
- 173653 trips
- 442 taxis
-- SQLBook: Code

SELECT COUNT(distinct taxi_id) AS taxi_count FROM rides;
Select COUNT(distinct trip_id) AS trip_count FROM rides;
select SUM(num_gps_points) AS gps_count FROM rides;

-- SQLBook: Markup
What is the average trips per taxi?
- 3745.67
-- SQLBook: Code
SELECT AVG(trip_count) AS avg_trips_per_taxi
FROM (
    SELECT COUNT(*) AS trip_count
    FROM rides
    GROUP BY taxi_id
) AS trips_per_taxi;
-- SQLBook: Markup
List the 20 taxi with most trips.
1) 20000483 
2) 20000403
3) 20000307
4) 20000364
5) 20000621
6) 20000492
7) 20000129
8) 20000424
9) 20000089
10) 20000529
11) 20000616
12) 20000042
13) 20000678
14) 20000235
15) 20000304
16) 20000179
17) 20000325
18) 20000263
19) 20000233
20) 20000140
-- SQLBook: Code
SELECT taxi_id, COUNT(*) AS trip_count 
FROM rides
GROUP BY taxi_id
ORDER BY trip_count DESC
LIMIT 20;
-- SQLBook: Markup
1) What is the most used call type per taxi?  
Call type B with 796270 calls
-- SQLBook: Code
SELECT
    COUNT(CASE WHEN call_type = 'A' THEN 1 END) AS A_count,
    COUNT(CASE WHEN call_type = 'B' THEN 1 END) AS B_count,
    COUNT(CASE WHEN call_type = 'C' THEN 1 END) AS C_count
FROM rides;
-- SQLBook: Markup
2) For each call type, compute:
- the average trip duration and distance, 
- report the share of trips starting in four time bands: 00–06, 06–12, 12–18, and 18–24.
-- SQLBook: Code
CREATE FUNCTION estimate_distance(lat1 FLOAT, lon1 FLOAT, lat2 FLOAT, lon2 FLOAT)
RETURNS FLOAT
BEGIN
    DECLARE R FLOAT DEFAULT 6371; -- Radius of the Earth in kilometers
    DECLARE dLat FLOAT;
    DECLARE dLon FLOAT;
    DECLARE a FLOAT;
    DECLARE c FLOAT;
    DECLARE distance FLOAT;

    SET dLat = RADIANS(lat2 - lat1);
    SET dLon = RADIANS(lon2 - lon1);

    SET a = SIN(dLat / 2) * SIN(dLat / 2) +
            COS(RADIANS(lat1)) * COS(RADIANS(lat2)) *
            SIN(dLon / 2) * SIN(dLon / 2);
    
    SET c = 2 * ATAN2(SQRT(a), SQRT(1 - a));
    
    SET distance = R * c; -- Distance in kilometers

    RETURN distance;
END;

CREATE FUNCTION calculate_trip_distance(trip_id INT)
RETURNS FLOAT
BEGIN
    DECLARE total_distance FLOAT DEFAULT 0;
    DECLARE prev_lat FLOAT;
    DECLARE prev_lon FLOAT;
    DECLARE curr_lat FLOAT;
    DECLARE curr_lon FLOAT;

    DECLARE done INT DEFAULT FALSE;
    DECLARE gps_cursor CURSOR FOR 
        SELECT latitude, longitude 
        FROM gps_points 
        WHERE trip_id = trip_id 
        ORDER BY timestamp;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    OPEN gps_cursor;

    FETCH gps_cursor INTO prev_lat, prev_lon;

    WHILE NOT done DO
        FETCH gps_cursor INTO curr_lat, curr_lon;
        IF NOT done THEN
            SET total_distance = total_distance + estimate_distance(prev_lat, prev_lon, curr_lat, curr_lon);
            SET prev_lat = curr_lat;
            SET prev_lon = curr_lon;
        END IF;
    END WHILE;

    CLOSE gps_cursor;

    RETURN total_distance; -- Distance in kilometers
END;    