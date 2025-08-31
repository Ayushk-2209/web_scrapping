
from flask import Flask, jsonify, render_template, request
import pandas as pd
import numpy as np

app = Flask(__name__, template_folder='templates')
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/products', methods=['GET'])
def get_products():
    try:
        page = int(request.args.get('page', 1))
        brand = request.args.get('brand', '').strip().lower()
        title = request.args.get('title', '').strip().lower()
        min_price = request.args.get('min_price', '').strip()
        max_price = request.args.get('max_price', '').strip()
        print(f"Reading CSV...", flush=True)
        df = pd.read_csv('flipkart_product_data.csv')
        print(f"Loaded {len(df)} rows from CSV", flush=True)
        # Filtering
        if brand:
            df['brand'] = df['brand'].astype(str).str.strip().str.lower()
            print('BRAND COLUMN UNIQUE VALUES:', df['brand'].unique(), flush=True)
            df = df[df['brand'].str.contains(brand)]
            print(f"Filtered by brand '{brand}', {len(df)} rows left", flush=True)
            print(df[['brand','title','price']].head(10), flush=True)
        if title:
            df['title'] = df['title'].astype(str).str.strip().str.lower()
            print('TITLE COLUMN UNIQUE VALUES:', df['title'].unique(), flush=True)
            df = df[df['title'].str.contains(title)]
            print(f"Filtered by title '{title}', {len(df)} rows left", flush=True)
            print(df[['brand','title','price']].head(10), flush=True)
        if min_price:
            df = df[pd.to_numeric(df['price'], errors='coerce') >= float(min_price)]
            print(f"Filtered by min_price '{min_price}', {len(df)} rows left", flush=True)
        if max_price:
            df = df[pd.to_numeric(df['price'], errors='coerce') <= float(max_price)]
            print(f"Filtered by max_price '{max_price}', {len(df)} rows left", flush=True)
        total = len(df)
        per_page = len(df)
        start = (page - 1) * per_page
        end = start + per_page
        # Replace all NaN in the DataFrame with None so JSON is valid
        df = df.replace({np.nan: None})
        data = df.iloc[start:end].to_dict(orient='records')
        print(f"Returning {len(data)} products (page {page})", flush=True)
        return jsonify({
            'products': data,
            'total': total,
            'per_page': per_page,
            'page': page
        })
    except Exception as e:
        import traceback
        print('API ERROR:', str(e), flush=True)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True,port=5050)


