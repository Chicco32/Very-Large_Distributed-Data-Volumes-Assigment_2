# How many taxi, trips and GPS are there in the dataset?
SELECT COUNT(distinct taxi_id) AS taxi_count FROM rides;
Select COUNT(distinct trip_id) AS trip_count FROM rides;
select SUM(num_gps_points) AS gps_count FROM rides;
# 82781502 gps points, 173653 trips, 442 taxis
