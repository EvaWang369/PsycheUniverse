from flask import Flask, request, jsonify
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

@app.route('/api/subscribe', methods=['POST'])
def subscribe():
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    try:
        result = supabase.table('subscribers').insert({
            'email': email,
            'subscribed_at': datetime.utcnow().isoformat()
        }).execute()
        
        return jsonify({'message': 'Successfully subscribed!'}), 200
    except Exception as e:
        if 'duplicate' in str(e).lower():
            return jsonify({'error': 'Email already subscribed'}), 400
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
