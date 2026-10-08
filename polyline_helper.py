import pandas as pd
import json
import mysql.connector
from haversine import haversine, Unit

class PolylineInfoHelper:
    def __init__(self):
        self.db_connection = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="secret",
            database="porto_db",
            allow_local_infile=True 
        )
        self.cursor = self.db_connection.cursor()
        
    def extract_polilyne_data(self):
        query = "SELECT trip_id, polyline, num_gps_points FROM rides"
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        
        df = pd.DataFrame(rows, columns=['trip_id', 'polyline', 'num_gps_points'])
        return df

    def calculate_distance_from_polyline(self, polyline):
        if not polyline or polyline == '[]':
            return 0.0

        try:
            coordinates = json.loads(polyline)
        except Exception:
            return 0.0
        
        total_distance = 0.0
        
        for i in range(len(coordinates) - 1):
            point1 = (coordinates[i][1], coordinates[i][0])
            point2 = (coordinates[i+1][1], coordinates[i+1][0])
            total_distance += haversine(point1, point2, unit=Unit.KILOMETERS)
            
        return total_distance

    def check_near_target(self, polyline, target_coords, radius_meters=100):
        """
        Checks if any point in the polyline is within the specified radius of target_coords.
        target_coords must be a tuple: (latitude, longitude)
        """
        if not polyline or polyline == '[]':
            return False
            
        try:
            coordinates = json.loads(polyline)
        except Exception:
            return False
            
        for point in coordinates:
            current_point = (point[1], point[0])
            
            distance = haversine(target_coords, current_point, unit=Unit.METERS)
            if distance <= radius_meters:
                return True
                
        return False

    def update_DB_schema(self):
        try:
            self.add_column_if_not_exists("rides", "distance_km", "FLOAT")
            self.add_column_if_not_exists("rides", "duration_seconds", "INT")
        except Exception as e:
            print("ERROR: Failed to update the database schema:", e)
            self.db_connection.rollback()
    
    def add_column_if_not_exists(self, table, column, column_type):
        self.cursor.execute("""
            SELECT COUNT(*)
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = %s
            AND COLUMN_NAME = %s
        """, (table, column))

        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
            
    def update_distance_and_duration(self, df):
        try:
            update_query = """
                UPDATE rides
                SET distance_km = %s,
                    duration_seconds = %s
                WHERE trip_id = %s
            """

            batch_size = 10_000

            values = [
                (row.distance_km, row.duration_seconds, row.trip_id)
                for row in df.itertuples(index=False)
            ]

            for i in range(0, len(values), batch_size):
                batch = values[i:i + batch_size]
                self.cursor.executemany(update_query, batch)
                self.db_connection.commit()
                print(f"Updated {len(batch)} records in the database.")
        except Exception as e:
            print("ERROR: Failed to update distance and duration in the database:", e)
            self.db_connection.rollback()

    def close_connection(self):
        if self.cursor:
            self.cursor.close()
        if self.db_connection:
            self.db_connection.close()
            
def main():
    helper = None 
    try:
        helper = PolylineInfoHelper()
        print("Database connection established.")
        print("Extracting polyline data from the database...")
        df = helper.extract_polilyne_data()
        print("Polyline data extracted successfully.")
        
        # 1. Calculate distances and durations
        INTERVAL_SECONDS = 15 
        print("Calculating route distances...")
        df['distance_km'] = df['polyline'].apply(helper.calculate_distance_from_polyline)
        df['duration_seconds'] = df['num_gps_points'] * INTERVAL_SECONDS
        
        # 2. Check proximity to a specific target
        # Pick any coordinate here (Latitude, Longitude)
        target_location = (41.15794, -8.62911)  # Currently set to Porto City Hall
        target_radius = 100                     # Radius in meters
        
        print(f"Checking proximity to coordinates {target_location} within {target_radius}m...")
        df['near_target'] = df['polyline'].apply(
            lambda x: helper.check_near_target(x, target_coords=target_location, radius_meters=target_radius)
        )
        
        # Output Results
        target_trips = df[df['near_target']]
        print("\n" + "="*40)
        print("SPATIAL QUERY RESULTS:")
        print(f"Total trips passing within {target_radius}m of {target_location}: {len(target_trips)}")
        if len(target_trips) > 0:
            print(f"Sample Trip IDs: {target_trips['trip_id'].head(5).tolist()}")
        print("="*40 + "\n")
        
        # Update the database
        helper.update_DB_schema()
        print("Database schema updated successfully.")
        helper.update_distance_and_duration(df)
        print("Distance and duration updated successfully.")
    except Exception as e:
        print("ERROR: Failed to process polyline data:", e)
    finally:
        if helper:
            helper.close_connection()
            
if __name__ == "__main__":
    main()
