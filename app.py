from flask import Flask, request, render_template, send_from_directory
import pandas as pd
import folium
import re

app = Flask(__name__)

# Load preprocessed data
data = pd.read_csv('preprocessed-destinasi-wisata-indonesia.csv')

# Get unique cities for dropdown
cities = sorted(data['city'].dropna().unique())

def clean_text(text):
    """Clean text input similar to preprocessing."""
    text = re.sub(r"[^a-zA-Z0-9 ]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.lower()

@app.route('/')
def index():
    return render_template('index.html', cities=cities)

@app.route('/recommend', methods=['POST'])
def recommend():
    # Get user input
    description = request.form.get('description', '').strip()
    city = request.form.get('city', '').strip().lower()
    price_input = request.form.get('price', '')

    # Convert price to integer if it's not empty
    try:
        max_price = int(price_input) if price_input else None
    except ValueError:
        max_price = None

    # Filter data based on input
    filtered_data = data.copy()

    if description:
        clean_desc = clean_text(description)
        filtered_data = filtered_data[filtered_data['description'].str.contains(clean_desc, na=False)]

    if city:
        filtered_data = filtered_data[filtered_data['city'].str.lower() == city]

    if max_price is not None:
        filtered_data = filtered_data[filtered_data['price'] <= max_price]

    # Generate map with filtered locations
    if not filtered_data.empty:
        wisata_map = folium.Map(location=[filtered_data['lat'].mean(), filtered_data['long'].mean()], zoom_start=5)
        for _, row in filtered_data.iterrows():
            folium.Marker(
                location=[row['lat'], row['long']],
                popup=f"<b>{row['place_name']}</b><br>Kategori: {row['category']}<br>Harga: {row['price']}<br>Rating: {row['rating'] / 10}",
                tooltip=row['place_name']
            ).add_to(wisata_map)

        # Save map to HTML
        map_file = 'templates/map.html'
        wisata_map.save(map_file)

    # Pass filtered data to results page
    return render_template('result.html', data=filtered_data.to_dict(orient='records'))

@app.route('/map.html')
def show_map():
    return send_from_directory('templates', 'map.html')

if __name__ == '__main__':
    app.run(debug=True)