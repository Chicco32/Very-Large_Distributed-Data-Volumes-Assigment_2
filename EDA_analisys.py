FILE_PATH = "porto/porto.csv"
import pandas as pd

def load_csv(file_path):
    """
    Load a CSV file into a pandas DataFrame.

    Parameters:
    file_path (str): The path to the CSV file.

    Returns:
    pd.DataFrame: The loaded DataFrame.
    """
    try:
        df = pd.read_csv(file_path, chunksize=10000)  # Load in chunks to handle large files
        return df
    except Exception as e:
        print(f"Error loading CSV file: {e}")
        return None
    
def count_unique_values(df, column_name):
    """
    Count the number of unique values in a specified column of a DataFrame.

    Parameters:
    df (pd.DataFrame): The DataFrame to analyze.
    column_name (str): The name of the column to count unique values.

    Returns:
    int: The number of unique values in the specified column.
    """
    if column_name in df.columns:
        return df[column_name].nunique()
    else:
        print(f"Column '{column_name}' does not exist in the DataFrame.")
        return None
    
def analyze_data_count(df):
    """
    Analyze the DataFrame to count entries and unique values in each column.

    Parameters:
    df (pd.DataFrame): The DataFrame to analyze.

    Returns:
    dict: A dictionary containing the total number of entries and unique values for each column.
    """
    analysis_results = {
        'total_entries': len(df),
        'unique_values': {}
    }
    
    for column in df.columns:
        unique_count = count_unique_values(df, column)
        analysis_results['unique_values'][column] = unique_count
    
    return analysis_results

print("EDA Analysis Module Loaded. Use the functions to analyze your DataFrame.")
loaded_df = load_csv(FILE_PATH)
data_analysis_results = analyze_data_count(loaded_df)
print("Data Analysis Results:")
for column, unique_count in data_analysis_results['unique_values'].items():
    print(f"Column '{column}': {unique_count} unique values")