import ast
import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer
from scipy.stats import zscore

def preprocess_data(file_path, output_path):
    # Load data
    data = pd.read_csv(file_path)

    # Change column names to lowercase
    data.columns = [col.lower() for col in data.columns]

    # Noise cleansing: strip strings of extra whitespace
    for col in data.select_dtypes(include=['object']).columns:
        data[col] = data[col].str.strip()

    # Imputation for missing values
    numeric_cols = data.select_dtypes(include=[np.number]).columns
    categorical_cols = data.select_dtypes(include=['object']).columns

    # Drop numeric columns with all NaN values
    numeric_cols_with_data = [col for col in numeric_cols if data[col].notna().any()]

    # Fill numeric columns with median
    if numeric_cols_with_data:
        num_imputer = SimpleImputer(strategy='median')
        data[numeric_cols_with_data] = num_imputer.fit_transform(data[numeric_cols_with_data])

    # Fill categorical columns with mode
    if not data[categorical_cols].empty:
        cat_imputer = SimpleImputer(strategy='most_frequent')
        data[categorical_cols] = cat_imputer.fit_transform(data[categorical_cols])

    # Outlier handling using z-score (remove rows with z-score > 3)
    if numeric_cols_with_data:
        z_scores = np.abs(zscore(data[numeric_cols_with_data]))
        data = data[(z_scores < 3).all(axis=1)]

    # Normalize rating column to scale 0-10
    if 'rating' in data.columns:
        min_rating = data['rating'].min()
        max_rating = data['rating'].max()
        if max_rating > min_rating:  # Avoid division by zero
            data['rating'] = ((data['rating'] - min_rating) / (max_rating - min_rating)) * 10

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

    # Remove duplicates
    data = data.drop_duplicates()

    # Save preprocessed data
    data.to_csv(output_path, index=False)

input_file = 'destinasi-wisata-indonesia.csv'
output_file = 'destinasi-wisata-indonesia-processed.csv'
preprocess_data(input_file, output_file)