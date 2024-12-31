import pandas as pd
import ast
import re

def preprocess_data(input_file, output_file):
    # Load data
    data = pd.read_csv(input_file)

    # Standardize column names
    data.columns = [col.strip().replace(" ", "_").lower() for col in data.columns]

    # Extract coordinates if they are in string format (e.g., "{lat: ..., lng: ...}")
    def extract_coordinates(coord_str):
        try:
            coord_dict = ast.literal_eval(coord_str)
            return coord_dict['lat'], coord_dict['lng']
        except (ValueError, KeyError, TypeError):
            return None, None

    data['lat'], data['long'] = zip(*data['coordinate'].apply(extract_coordinates))

    # Drop rows with missing coordinates or invalid values
    data = data.dropna(subset=['lat', 'long'])

    # Ensure lat and long are numeric
    data['lat'] = pd.to_numeric(data['lat'], errors='coerce')
    data['long'] = pd.to_numeric(data['long'], errors='coerce')

    # Preprocess text in the description column
    def clean_text(text):
        if pd.isna(text):
            return ""
        # Remove special characters and extra whitespace
        text = re.sub(r"[^a-zA-Z0-9 ]", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text.lower()

    if 'description' in data.columns:
        data['description'] = data['description'].apply(clean_text)

    # Drop unnecessary columns
    columns_to_drop = ['coordinate', 'column1', '_1']
    data = data.drop(columns=[col for col in columns_to_drop if col in data.columns])

    # Save preprocessed data to a new CSV file
    data.to_csv(output_file, index=False)

# Example usage
input_file = 'destinasi-wisata-indonesia.csv'  # Replace with the actual file path
output_file = 'preprocessed-destinasi-wisata-indonesia.csv'  # Replace with the desired output file path
preprocess_data(input_file, output_file)