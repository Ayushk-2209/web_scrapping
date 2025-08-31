from flask import Flask, jsonify, request, send_file, redirect, url_for
import io
import pandas as pd

app = Flask(__name__)


# --- API: GET with search, filter, sort, pagination ---
@app.route('/api/products', methods=['GET'])
def get_products():
    try:
        df = pd.read_csv('flipkart_product_data.csv')
        # Filtering
        brand = request.args.get('brand')
        title = request.args.get('title')
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        sort_by = request.args.get('sort_by')
        order = request.args.get('order', 'asc')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        if brand:
            df = df[df['brand'].str.contains(brand, case=False, na=False)]
        if title:
            df = df[df['title'].str.contains(title, case=False, na=False)]
        if min_price is not None:
            df = df[df['price'].astype(float) >= min_price]
        if max_price is not None:
            df = df[df['price'].astype(float) <= max_price]
        if sort_by and sort_by in df.columns:
            df = df.sort_values(by=sort_by, ascending=(order=='asc'))

        total = len(df)
        start = (page-1)*per_page
        end = start+per_page
        data = df.iloc[start:end].to_dict(orient='records')
        return jsonify({'products': data, 'total': total, 'page': page, 'per_page': per_page})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- API: POST to add product ---
@app.route('/api/products', methods=['POST'])
def add_product():
    try:
        new_product = request.json
        df = pd.read_csv('flipkart_product_data.csv')
        df = df.append(new_product, ignore_index=True)
        df.to_csv('flipkart_product_data.csv', index=False)
        return jsonify({'message': 'Product added successfully.'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- API: PUT to update product by index ---
@app.route('/api/products/<int:idx>', methods=['PUT'])
def update_product(idx):
    try:
        update_data = request.json
        df = pd.read_csv('flipkart_product_data.csv')
        if idx < 0 or idx >= len(df):
            return jsonify({'error': 'Invalid index'}), 404
        for k, v in update_data.items():
            if k in df.columns:
                df.at[idx, k] = v
        df.to_csv('flipkart_product_data.csv', index=False)
        return jsonify({'message': 'Product updated successfully.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- API: DELETE product by index ---
@app.route('/api/products/<int:idx>', methods=['DELETE'])
def delete_product(idx):
    try:
        df = pd.read_csv('flipkart_product_data.csv')
        if idx < 0 or idx >= len(df):
            return jsonify({'error': 'Invalid index'}), 404
        df = df.drop(df.index[idx])
        df.to_csv('flipkart_product_data.csv', index=False)
        return jsonify({'message': 'Product deleted successfully.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- API: Download CSV ---
@app.route('/api/products/download', methods=['GET'])
def download_csv():
    try:
        return send_file('flipkart_product_data.csv', as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# --- Web: Home page with search, filter, sort, pagination, download, loading/error ---
@app.route('/')
def show_products():
    try:
        df = pd.read_csv('flipkart_product_data.csv')
        # Get query params
        brand = request.args.get('brand', '')
        title = request.args.get('title', '')
        min_price = request.args.get('min_price', '')
        max_price = request.args.get('max_price', '')
        sort_by = request.args.get('sort_by', 'price')
        order = request.args.get('order', 'asc')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))

        # Filtering
        if brand:
            df = df[df['brand'].str.contains(brand, case=False, na=False)]
        if title:
            df = df[df['title'].str.contains(title, case=False, na=False)]
        if min_price:
            df = df[df['price'].astype(float) >= float(min_price)]
        if max_price:
            df = df[df['price'].astype(float) <= float(max_price)]
        if sort_by in df.columns:
            df = df.sort_values(by=sort_by, ascending=(order=='asc'))

        total = len(df)
        start = (page-1)*per_page
        end = start+per_page
        page_df = df.iloc[start:end]

        # Pagination controls
        total_pages = max(1, (total + per_page - 1) // per_page)
        prev_page = max(1, page-1)
        next_page = min(total_pages, page+1)

        # Table with clickable rows
        table_html = page_df.to_html(classes='table table-striped', index=False, border=0, escape=False)

        html = f'''
        <html>
        <head>
            <title>Flipkart Products</title>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css">
            <script>
            function goToDetail(idx) {{ window.location = '/product/' + idx; }}
            function showLoading() {{ document.getElementById('loading').style.display = 'block'; }}
            </script>
        </head>
        <body>
            <div class="container mt-4">
                <h2>Flipkart Products</h2>
                <form method="get" class="form-inline mb-3">
                    <input type="text" name="brand" value="{brand}" placeholder="Brand" class="form-control mr-2">
                    <input type="text" name="title" value="{title}" placeholder="Title" class="form-control mr-2">
                    <input type="number" name="min_price" value="{min_price}" placeholder="Min Price" class="form-control mr-2">
                    <input type="number" name="max_price" value="{max_price}" placeholder="Max Price" class="form-control mr-2">
                    <select name="sort_by" class="form-control mr-2">
                        {''.join([f'<option value="{col}"'+(' selected' if col==sort_by else '')+f'>{col}</option>' for col in df.columns])}
                    </select>
                    <select name="order" class="form-control mr-2">
                        <option value="asc"{' selected' if order=='asc' else ''}>Asc</option>
                        <option value="desc"{' selected' if order=='desc' else ''}>Desc</option>
                    </select>
                    <button type="submit" class="btn btn-primary mr-2" onclick="showLoading()">Search</button>
                    <a href="/api/products/download" class="btn btn-success">Download CSV</a>
                </form>
                <div id="loading" style="display:none;">Loading...</div>
                <div class="table-responsive">
                {table_html.replace('<tr>', '<tr onclick="goToDetail(this.rowIndex+'+str(start-1)+')">', 1)}
                </div>
                <nav aria-label="Page navigation">
                  <ul class="pagination">
                    <li class="page-item{' disabled' if page==1 else ''}"><a class="page-link" href="?page={prev_page}&per_page={per_page}&brand={brand}&title={title}&min_price={min_price}&max_price={max_price}&sort_by={sort_by}&order={order}">Previous</a></li>
                    <li class="page-item disabled"><a class="page-link">Page {page} of {total_pages}</a></li>
                    <li class="page-item{' disabled' if page==total_pages else ''}"><a class="page-link" href="?page={next_page}&per_page={per_page}&brand={brand}&title={title}&min_price={min_price}&max_price={max_price}&sort_by={sort_by}&order={order}">Next</a></li>
                  </ul>
                </nav>
            </div>
        </body>
        </html>
        '''
        return html
    except Exception as e:
        return f"<h3>Error: {e}</h3>"

# --- Web: Product details page ---
@app.route('/product/<int:idx>')
def product_detail(idx):
    try:
        df = pd.read_csv('flipkart_product_data.csv')
        if idx < 0 or idx >= len(df):
            return f"<h3>Product not found</h3>"
        row = df.iloc[idx]
        html = f'''
        <html>
        <head>
            <title>Product Detail</title>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css">
        </head>
        <body>
            <div class="container mt-4">
                <h2>Product Detail</h2>
                <table class="table table-bordered">
                    {''.join([f'<tr><th>{col}</th><td>{row[col]}</td></tr>' for col in df.columns])}
                </table>
                <a href="/" class="btn btn-secondary">Back</a>
            </div>
        </body>
        </html>
        '''
        return html
    except Exception as e:
        return f"<h3>Error: {e}</h3>"

if __name__ == '__main__':
    app.run(debug=True, port=5050)
