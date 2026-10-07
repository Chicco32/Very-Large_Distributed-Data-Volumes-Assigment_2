import pandas as pd
import numpy as np
from DbConnector import DbConnector

class PolylineInfoHelper:
    def __init__(self):
        self.connection = DbConnector()
        self.db_connection = self.connection.db_connection
        self.cursor = self.connection.cursor
        
    def extract_polilyne_data(self):
        """
        Extracts polyline data from the database and returns it as a pandas DataFrame.
        
        returns:
            pd.DataFrame: A DataFrame containing trip_id, polyline, and num_gps_points columns.
        """
        query = "SELECT trip_id, polyline, num_gps_points FROM rides"
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        
        # Convert the fetched data into a pandas DataFrame
        df = pd.DataFrame(rows, columns=['trip_id', 'polyline', 'num_gps_points'])
        
        return df

    def calculate_distance_from_polyline(self, polyline, id=None):
        """
        Calculates the distance of a trip based on its polyline data.
        
        Args:
            polyline (json): The polyline string representing the trip's GPS points.
            Example: polyline = '[[-8.610291, 41.140746], [-8.6103, 41.140755], [-8.610309, 41.14089], [-8.613657, 41.141358]]'
            id (int): The ID of the trip (optional).

        Returns:
            float: The calculated distance of the trip.
        """
        # Convert the polyline string to a list of coordinates
        coordinates = np.array(eval(polyline))
        
        # Calculate the distance between consecutive points using the Haversine formula
        distances = []
        for i in range(len(coordinates) - 1):
            lat1, lon1 = coordinates[i]
            lat2, lon2 = coordinates[i + 1]
            
            # Convert latitude and longitude from degrees to radians
            lat1_rad, lon1_rad = np.radians(lat1), np.radians(lon1)
            lat2_rad, lon2_rad = np.radians(lat2), np.radians(lon2)
            
            # Haversine formula
            dlat = lat2_rad - lat1_rad
            dlon = lon2_rad - lon1_rad
            a = np.sin(dlat / 2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2)**2
            c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
            
            # Radius of Earth in kilometers (mean radius)
            R = 6371.0
            distance = R * c
            distances.append(distance)
        
        # Sum up all distances to get the total distance of the trip
        total_distance = sum(distances)
        print(f"Calculated distance for polyline {polyline}: {total_distance} km")
        
        return total_distance

    def update_DB_schema(self):
        """
        Updates the database schema by adding new columns for distance and duration.
        
        Args:
            cursor: The database cursor to execute SQL commands.
        """
        try:
            self.add_column_if_not_exists(
                "rides", "distance_km", "FLOAT"
            )

            self.add_column_if_not_exists(
                "rides", "duration_seconds", "INT"
            )
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
            self.cursor.execute(
                f"ALTER TABLE {table} ADD COLUMN {column} {column_type}"
            )
        
    def update_distance_and_duration(self, df):
        """
        Updates the distance and duration columns in the database for each trip based on the provided DataFrame
        containing trip_id, distance_km, and duration_seconds.
        
        Args:
            df (pd.DataFrame): A DataFrame containing trip_id, distance_km, and duration_seconds columns.
        """
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
                print (f"Updated {len(batch)} records in the database.")
        except Exception as e:
            print("ERROR: Failed to update distance and duration in the database:", e)
            self.db_connection.rollback()
        
def main():
    try:
        helper = PolylineInfoHelper()
        print("Database connection established.")
        print("Extracting polyline data from the database...")
        df = helper.extract_polilyne_data()
        print("Polyline data extracted successfully.")
        
        # Calculate distances and durations
        INTERVAL_SECONDS = 15 
        df['distance_km'] = df['polyline'].apply(helper.calculate_distance_from_polyline, args=(df['trip_id'],))
        df['duration_seconds'] = df['num_gps_points'] * INTERVAL_SECONDS
        print("Distance and duration calculated successfully. Sample data:")
        print(df.head())
        
        # Update the database schema and data
        helper.update_DB_schema()
        print("Database schema updated successfully.")
        helper.update_distance_and_duration(df)
        print("Distance and duration updated successfully.")
    except Exception as e:
        print("ERROR: Failed to process polyline data:", e)
    finally:
        if helper:
            helper.connection.close_connection()
    
main()