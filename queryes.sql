-- Active: 1791373155342@@127.0.0.1@3306@porto_db
-- SQLBook: Markup
How many taxi, trips and GPS are there in the dataset?
- 82781502 gps points
- 1655585 trips
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
What is the most used call type per taxi?  
Call type B globally with 796270 calls  
| taxi id | A call | B call | C call |
|---|---|---|---|
|20000380 | 774 | 1512 | 1221|
|20000589 | 738 | 2869 | 1053|
| 20000233 | 1192 | 3274 | 1794|
-- SQLBook: Code
SELECT `TAXI_ID`,
    COUNT(CASE WHEN call_type = 'A' THEN 1 END) AS A_count,
    COUNT(CASE WHEN call_type = 'B' THEN 1 END) AS B_count,
    COUNT(CASE WHEN call_type = 'C' THEN 1 END) AS C_count
FROM rides GROUP BY `TAXI_ID`;
-- SQLBook: Markup
For each call type, compute:
- the average trip duration and distance, 
- report the share of trips starting in four time bands: 00–06, 06–12, 12–18, and 18–24.

- Duration minutes:
A) 13 min B) 11 min C) 14 min
- Distance Km:
A) 6,38 km B) 5,99 km C) 7,78 km

- Share of trips:
1) 00-06: 305321 18,44%
2) 06-12: 476730 28,80%
3) 12-18: 509806 30,80%
4) 18-24: 363728 22%
-- SQLBook: Code
SELECT AVG(distance_km) AS avg_distance_km, AVG(duration_seconds) / 60 AS avg_duration_min, `CALL_TYPE`
FROM rides GROUP BY `CALL_TYPE`;
-- SQLBook: Code
SELECT
    SUM(CASE WHEN HOUR(call_date) BETWEEN 0 AND 5 THEN 1 ELSE 0 END) AS first_quarter_count,
    SUM(CASE WHEN HOUR(call_date) BETWEEN 6 AND 11 THEN 1 ELSE 0 END) AS second_quarter_count,
    SUM(CASE WHEN HOUR(call_date) BETWEEN 12 AND 17 THEN 1 ELSE 0 END) AS third_quarter_count,
    SUM(CASE WHEN HOUR(call_date) BETWEEN 18 AND 23 THEN 1 ELSE 0 END) AS fourth_quarter_count
FROM rides;

-- SQLBook: Markup
Find the taxis with the most total hours driven as well as total distance driven. List them in order of total hours.

-taxis with most distance driven:
1) 20000904
2) 20000351
3) 20000276
4) 20000436
5) 20000529
6) 20000403
7) 20000678
8) 20000364
9) 20000372
10) 20000435

-taxis with most total hours:
1) 20000904
2) 20000129
3) 20000307
4) 20000529
5) 20000276
6) 20000436
7) 20000483
8) 20000372
9) 20000616
10) 20000179
-- SQLBook: Code

SELECT SUM(distance_km) AS total_distance, taxi_id
FROM rides
GROUP BY taxi_id
ORDER BY total_distance DESC
LIMIT 10;

SELECT SUM(duration_seconds) AS total_duration, taxi_id
FROM rides
GROUP BY taxi_id
ORDER BY total_duration DESC
LIMIT 10;
-- SQLBook: Markup
Find the trips that started on one calendar day and ended on the next (midnight crossers).

found 8199 trips. first three:
| TRIP_ID | start date | end date|
|--- |--- |---|
| 1372722134620000435	|2013-07-01 23:42:14	|2013-07-02 00:02:59|
|1372722457620000569	|2013-07-01 23:47:37	|2013-07-02 00:28:37|
|1372722471620000540	|2013-07-01 23:47:51	|2013-07-02 00:02:36|
-- SQLBook: Code
WITH trips_with_end AS (
    SELECT
        trip_id,
        call_date,
        TIMESTAMPADD(SECOND, duration_seconds, call_date) AS end_date
    FROM rides
)
SELECT
    trip_id,
    call_date,
    end_date
FROM trips_with_end
WHERE DATE(call_date) <> DATE(end_date);
-- SQLBook: Markup
Find the trips whose start and end points are within 50 m of each other (circular trips).  
Found 21497 circular trips
1) 1372638303620000112 20mt
2) 1372638513620000473 50 mt
3) 1372639092620000233 9 mt
-- SQLBook: Code
CREATE DEFINER=`root`@`%` FUNCTION `trip_ends_distance`(p_trip_id BIGINT) RETURNS decimal(10,3)
    READS SQL DATA
    DETERMINISTIC
BEGIN
    DECLARE distance_km DECIMAL(10,3);

    SELECT ST_Distance_Sphere(
        POINT(
            CAST(JSON_UNQUOTE(JSON_EXTRACT(polyline, '$[0][0]')) AS DECIMAL(10,7)),
            CAST(JSON_UNQUOTE(JSON_EXTRACT(polyline, '$[0][1]')) AS DECIMAL(10,7))
        ),
        POINT(
            CAST(JSON_UNQUOTE(JSON_EXTRACT(polyline, CONCAT('$[', JSON_LENGTH(polyline) - 1, '][0]'))) AS DECIMAL(10,7)),
            CAST(JSON_UNQUOTE(JSON_EXTRACT(polyline, CONCAT('$[', JSON_LENGTH(polyline) - 1, '][1]'))) AS DECIMAL(10,7))
        )
    ) / 1000
    INTO distance_km
    FROM rides
    WHERE trip_id = p_trip_id
    LIMIT 1;

    RETURN distance_km;
END


-- SQLBook: Code
SELECT
    trip_id,
    trip_ends_distance(trip_id) AS calculated_distance_km
FROM rides
WHERE trip_ends_distance(trip_id) <= 0.05;

-- SQLBook: Markup
For each taxi, compute the average idle time between consecutive trips. List the top 20 taxis with the highest average idle time.  
The taxis with the highets idel time:
1) 20000941
2) 20000969
3) 20000510
4) 20000312
5) 20000609
6) 20000579
7) 20000079
8) 20000072
9) 20000185
10) 20000449
11) 20000170
12) 20000902
13) 20000535
14) 20000315
15) 20000225
16) 20000071
17) 20000545
18) 20000407
19) 20000205
20) 20000443
-- SQLBook: Code

ALTER TABLE rides ADD COLUMN end_date DATETIME GENERATED ALWAYS AS (TIMESTAMPADD(SECOND, duration_seconds, call_date)) STORED;
-- SQLBook: Code
WITH ordered_trips AS (
    SELECT
        taxi_id,
        end_date,
        `CALL_DATE`,
        LEAD(`CALL_DATE`) OVER (
            PARTITION BY taxi_id
            ORDER BY `CALL_DATE`
        ) AS next_start
    FROM rides
),
idle_times AS (
    SELECT
        taxi_id,
        TIMESTAMPDIFF(
            SECOND,
            end_date,
            next_start
        ) AS idle_seconds
    FROM ordered_trips
    WHERE next_start IS NOT NULL
)
SELECT
    taxi_id,
    AVG(idle_seconds) AS avg_idle_seconds
FROM idle_times
GROUP BY taxi_id
ORDER BY avg_idle_seconds DESC
LIMIT 20;