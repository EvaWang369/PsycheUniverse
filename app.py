from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from supabase import create_client
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
CORS(app)

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

@app.route('/')
def index():
    return send_from_directory('views', 'index.html')

@app.route('/subliminalgen')
def subliminalgen():
    return send_from_directory('views', 'subliminalgen.html')

@app.route('/pitch')
def pitch():
    return send_from_directory('views', 'pitch.html')

@app.route('/views/<path:filename>')
def views_static(filename):
    return send_from_directory('views', filename)

@app.route('/logos/<path:filename>')
def logos_static(filename):
    return send_from_directory('logos', filename)

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/api/subscribe', methods=['POST'])
def subscribe():
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    try:
        result = supabase.table('universal_subscription').insert({
            'email': email
        }).execute()
        
        return jsonify({'message': 'Successfully subscribed!'}), 200
    except Exception as e:
        if 'duplicate' in str(e).lower():
            return jsonify({'error': 'Email already subscribed'}), 400
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8080)
