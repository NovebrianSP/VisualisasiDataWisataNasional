import pandas as pd
import numpy as np

data = pd.read_csv('destinasi-wisata-indonesia-processed.csv')

print(data[['lat', 'long']].head())

invalid_coords = data[(data['lat'] < -90) | (data['lat'] > 90) | (data['long'] < -180) | (data['long'] > 180)]
if not invalid_coords.empty:
    print("Koordinat yang tidak valid ditemukan:")
    print(invalid_coords)
    
    print(data['lat'].dtype, data['long'].dtype)