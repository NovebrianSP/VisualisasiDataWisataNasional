from flask import Flask, request, render_template
import pandas as pd
import folium
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import re
import json

app = Flask(__name__)

# Load preprocessed data
data = pd.read_csv('destinasi-wisata-indonesia-processed.csv')

# Extract unique cities for dropdown
cities = sorted(data['city'].unique())

def clean_text(text):
    """Clean text input similar to preprocessing."""
    text = re.sub(r"[^a-zA-Z0-9 ]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.lower()

@app.route('/rekomendasi')
def index():
    return render_template('index.html', cities=cities)

@app.route('/recommend', methods=['POST'])
def recommend():
    # Get user inputs
    description = request.form.get('description', '').strip()
    city = request.form.get('city', '').strip()
    max_price = request.form.get('price', '').strip()

    # Convert price input to integer
    max_price = int(max_price) if max_price.isdigit() else float('inf')

    # Filter data based on inputs
    filtered_data = data.copy()

    if description:
        clean_desc = clean_text(description)
        filtered_data = filtered_data[
            filtered_data['description'].str.contains(clean_desc, na=False, case=False)
        ]

    if city:
        filtered_data = filtered_data[filtered_data['city'].str.lower() == city.lower()]

    if max_price < float('inf'):
        filtered_data = filtered_data[filtered_data['price'] <= max_price]

    # Generate map with filtered locations
    if not filtered_data.empty:
        wisata_map = folium.Map(
            location=[filtered_data['lat'].mean(), filtered_data['long'].mean()],
            zoom_start=5
        )
        colors = {
            'Taman Hiburan': 'orange',
            'Cagar Alam': 'green',
            'Bahari': 'blue',
            'Budaya': 'purple',
            'Pusat Perbelanjaan': 'red',
            'Tempat Ibadah': 'darkblue'
        }

        for _, row in filtered_data.iterrows():
            category_color = colors.get(row['category'], 'gray')  # Default to gray if category is missing
            folium.Marker(
                location=[row['lat'], row['long']],
                popup=(f"<b>{row['place_name']}</b><br>"
                       f"Kategori: {row['category']}<br>"
                       f"Harga: Rp {row['price']}<br>"
                       f"Rating: {row['rating'] / 10}"),
                tooltip=row['place_name'],
                icon=folium.Icon(color=category_color)
            ).add_to(wisata_map)

        # Add legend for categories
        legend_html = """
             <div style="position: fixed; 
                         bottom: 50px; left: 50px; width: 200px; height: auto; 
                         background-color: white; border: 2px solid black; z-index:9999; 
                         font-size: 12px; padding: 10px;">
             <b>Legenda Kategori</b><br>
             <i style="background: orange; padding: 5px;"></i> Taman Hiburan<br>
             <i style="background: green; padding: 5px;"></i> Cagar Alam<br>
             <i style="background: blue; padding: 5px;"></i> Bahari<br>
             <i style="background: purple; padding: 5px;"></i> Budaya<br>
             <i style="background: red; padding: 5px;"></i> Pusat Perbelanjaan<br>
             <i style="background: darkblue; padding: 5px;"></i> Tempat Ibadah<br>
             <i style="background: gray; padding: 5px;"></i> Lainnya<br>
             </div>
        """
        wisata_map.get_root().html.add_child(folium.Element(legend_html))

        # Save map to HTML
        map_file = 'static/maps/wisata_map.html'
        wisata_map.save(map_file)

    # Prepare data for charts
    # Pie Chart for Category
    category_counts = filtered_data['category'].value_counts()
    category_labels = category_counts.index.tolist()
    category_values = category_counts.values.tolist()

    # Bar Chart for Price
    price_bins = pd.cut(filtered_data['price'], bins=5)
    price_counts = price_bins.value_counts()
    price_labels = [str(interval) for interval in price_counts.index]
    price_values = price_counts.values.tolist()

    # Bar Chart for Rating
    rating_bins = pd.cut(filtered_data['rating'], bins=5)
    rating_counts = rating_bins.value_counts()
    rating_labels = [str(interval) for interval in rating_counts.index]
    rating_values = rating_counts.values.tolist()

    return render_template(
        'result.html',
        data=filtered_data.to_dict(orient='records'),
        map_path='/static/maps/wisata_map.html',
        category_labels=json.dumps(category_labels),
        category_values=json.dumps(category_values),
        price_labels=json.dumps(price_labels),
        price_values=json.dumps(price_values),
        rating_labels=json.dumps(rating_labels),
        rating_values=json.dumps(rating_values),
    )

# Prepare data for charts
def prepare_chart_data():
    # Data untuk chart kategori
    category_counts = data['category'].value_counts()
    category_labels = category_counts.index.tolist()
    category_values = category_counts.values.tolist()

    # Data untuk chart kota
    city_counts = data['city'].value_counts()
    city_labels = city_counts.index.tolist()
    city_values = city_counts.values.tolist()

    # Data untuk chart harga
    price_counts = data['price'].value_counts().sort_index()
    price_labels = price_counts.index.tolist()
    price_values = price_counts.values.tolist()

    # Data untuk chart rating
    rating_bins = pd.cut(data['rating'], bins=5)
    rating_counts = rating_bins.value_counts()
    rating_labels = [str(interval) for interval in rating_counts.index]
    rating_values = rating_counts.values.tolist()

    # Data untuk kategori per kota
    city_category = data.groupby(['city', 'category']).size().unstack(fill_value=0)
    city_category_labels = city_category.index.tolist()
    category_per_city_labels = city_category.columns.tolist()
    category_per_city_values = city_category.values.tolist()

    # Data untuk destinasi berdasarkan kategori
    destinations_per_category = data.groupby('category')['place_name'].apply(list).to_dict()

    # Data untuk destinasi berdasarkan kota
    destinations_per_city = data.groupby('city')['place_name'].apply(list).to_dict()

    # Kategori dengan rating terbanyak
    top_rating_category = data.groupby('category')['rating'].mean().sort_values(ascending=False).to_dict()

    # Destinasi dengan rating tertinggi berdasarkan kota
    top_rated_destinations_per_city = data.loc[data.groupby('city')['rating'].idxmax()][['city', 'place_name', 'rating']]

    return {
        "category_labels": category_labels,
        "category_values": category_values,
        "city_labels": city_labels,
        "city_values": city_values,
        "price_labels": price_labels,
        "price_values": price_values,
        "rating_labels": rating_labels,
        "rating_values": rating_values,
        "city_category_labels": city_category_labels,
        "category_per_city_labels": category_per_city_labels,
        "category_per_city_values": category_per_city_values,
        "destinations_per_category": destinations_per_category,
        "destinations_per_city": destinations_per_city,
        "top_rating_category": top_rating_category,
        "top_rated_destinations_per_city": top_rated_destinations_per_city,
    }

@app.route('/')
def dashboard():
    # Prepare chart data
    chart_data = prepare_chart_data()

    # Generate map for all destinations
    wisata_map = folium.Map(
        location=[data['lat'].mean(), data['long'].mean()],
        zoom_start=5
    )
    colors = {
        'Taman Hiburan': 'orange',
        'Cagar Alam': 'green',
        'Bahari': 'blue',
        'Budaya': 'purple',
        'Pusat Perbelanjaan': 'red',
        'Tempat Ibadah': 'darkblue'
    }

    for _, row in data.iterrows():
        category_color = colors.get(row['category'], 'gray')  # Default to gray if category is missing
        folium.Marker(
            location=[row['lat'], row['long']],
            popup=(f"<b>{row['place_name']}</b><br>"
                   f"Kategori: {row['category']}<br>"
                   f"Harga: Rp {row['price']}<br>"
                   f"Rating: {row['rating'] / 10}"),
            tooltip=row['place_name'],
            icon=folium.Icon(color=category_color)
        ).add_to(wisata_map)

    # Save map to HTML
    map_file = 'static/maps/all_destinations_map.html'
    wisata_map.save(map_file)

    # Render template with chart data and map path
    return render_template(
        'dashboard.html',
        category_labels=json.dumps(chart_data['category_labels']),
        category_values=json.dumps(chart_data['category_values']),
        city_labels=json.dumps(chart_data['city_labels']),
        city_values=json.dumps(chart_data['city_values']),
        price_labels=json.dumps(chart_data['price_labels']),
        price_values=json.dumps(chart_data['price_values']),
        rating_labels=json.dumps(chart_data['rating_labels']),
        rating_values=json.dumps(chart_data['rating_values']),
        city_category_labels=json.dumps(chart_data['city_category_labels']),
        category_per_city_labels=json.dumps(chart_data['category_per_city_labels']),
        category_per_city_values=json.dumps(chart_data['category_per_city_values']),
        destinations_per_category=json.dumps(chart_data['destinations_per_category']),
        destinations_per_city=json.dumps(chart_data['destinations_per_city']),
        top_rating_category=json.dumps(chart_data['top_rating_category']),
        top_rated_destinations_per_city=json.dumps(chart_data['top_rated_destinations_per_city'].to_dict(orient='records')),
        map_path='/static/maps/all_destinations_map.html'
    )

if __name__ == '__main__':
    app.run(debug=True)