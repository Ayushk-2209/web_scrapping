from flask import Flask, jsonify, request, send_file, redirect, url_for, render_template, session
import pandas as pd
import os
import io
import jwt
import datetime
from functools import wraps
from werkzeug.utils import secure_filename
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

app = Flask(__name__)
app.secret_key = 'your_secret_key'
JWT_SECRET = 'jwt_secret_key'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# --- Helper functions ---
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-token')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(*args, **kwargs)
    return decorated

# --- User authentication (simple demo) ---
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    if data['username'] == 'admin' and data['password'] == 'admin':
        token = jwt.encode({'user': 'admin', 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)}, JWT_SECRET)
        return jsonify({'token': token})
    return jsonify({'message': 'Invalid credentials'}), 401

# --- API: GET all products (simple, no JWT) ---
@app.route('/api/products', methods=['GET'])
def get_products():
    try:
        df = pd.read_csv('flipkart_product_data.csv')
        data = df.to_dict(orient='records')
        return jsonify({'products': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- API: POST to add product (with image upload) ---
@app.route('/api/products', methods=['POST'])
@token_required
def add_product():
    try:
        new_product = request.form.to_dict()
        if 'image' in request.files and allowed_file(request.files['image'].filename):
            image = request.files['image']
            filename = secure_filename(image.filename)
            image.save(os.path.join(UPLOAD_FOLDER, filename))
            new_product['image'] = filename
        df = pd.read_csv('flipkart_product_data.csv')
        df = df.append(new_product, ignore_index=True)
        df.to_csv('flipkart_product_data.csv', index=False)
        return jsonify({'message': 'Product added successfully.'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- API: Bulk upload ---
@app.route('/api/products/bulk_upload', methods=['POST'])
@token_required
def bulk_upload():
    try:
        file = request.files['file']
        df_new = pd.read_csv(file)
        df = pd.read_csv('flipkart_product_data.csv')
        df = pd.concat([df, df_new], ignore_index=True)
        df.to_csv('flipkart_product_data.csv', index=False)
        return jsonify({'message': 'Bulk upload successful.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- API: Export to Excel ---
@app.route('/api/products/export_excel', methods=['GET'])
@token_required
def export_excel():
    try:
        df = pd.read_csv('flipkart_product_data.csv')
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        output.seek(0)
        return send_file(output, as_attachment=True, download_name='products.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- API: Export to PDF (simple chart) ---
@app.route('/api/products/export_pdf', methods=['GET'])
@token_required
def export_pdf():
    try:
        df = pd.read_csv('flipkart_product_data.csv')
        plt.figure(figsize=(8,4))
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df['price'].plot.hist(bins=20)
        plt.title('Price Distribution')
        plt.xlabel('Price')
        plt.ylabel('Count')
        pdf_path = 'price_chart.pdf'
        plt.savefig(pdf_path)
        plt.close()
        return send_file(pdf_path, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- API: Swagger/OpenAPI docs ---
@app.route('/api/docs')
def api_docs():
    return redirect('https://petstore.swagger.io/')

# --- Web: Home page (AJAX, responsive, analytics, error handling) ---
@app.route('/')
def home():
    return render_template('index.html')

# --- Error logging and user-friendly error pages ---
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, port=5050)
