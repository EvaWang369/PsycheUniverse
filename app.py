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

@app.route('/metaphors')
def metaphors():
    return send_from_directory('views', 'game.html')

@app.route('/metaphors/<metaphor_id>')
def metaphor_detail(metaphor_id):
    return send_from_directory('views', 'game.html')

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

# Metaphor API Endpoints

@app.route('/api/metaphors', methods=['GET'])
def get_metaphors():
    """Get all metaphors"""
    try:
        result = supabase.table('metaphors')\
            .select('*')\
            .order('order_index')\
            .execute()
        return jsonify(result.data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/metaphors/<metaphor_id>', methods=['GET'])
def get_metaphor(metaphor_id):
    """Get single metaphor by ID"""
    try:
        result = supabase.table('metaphors')\
            .select('*')\
            .eq('id', metaphor_id)\
            .single()\
            .execute()
        return jsonify(result.data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/api/user/purchases', methods=['GET'])
def get_user_purchases():
    """Get all metaphors purchased by current user"""
    # TODO: Get user_id from session/JWT after implementing auth
    user_id = request.headers.get('X-User-Id', 'demo_user')  # Temporary
    
    try:
        result = supabase.table('user_purchases')\
            .select('metaphor_id')\
            .eq('user_id', user_id)\
            .execute()
        
        purchased_ids = [p['metaphor_id'] for p in result.data]
        return jsonify(purchased_ids), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/check-purchase/<metaphor_id>', methods=['GET'])
def check_purchase(metaphor_id):
    """Check if user has purchased specific metaphor"""
    # TODO: Get user_id from session/JWT after implementing auth
    user_id = request.headers.get('X-User-Id', 'demo_user')  # Temporary
    
    try:
        result = supabase.table('user_purchases')\
            .select('*')\
            .eq('user_id', user_id)\
            .eq('metaphor_id', metaphor_id)\
            .execute()
        
        return jsonify({'purchased': len(result.data) > 0}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/metaphor-suggestions', methods=['POST'])
def submit_suggestion():
    """Submit a metaphor suggestion"""
    data = request.get_json()
    
    if not data.get('suggestion'):
        return jsonify({'error': 'Suggestion is required'}), 400
    
    try:
        result = supabase.table('metaphor_suggestions').insert({
            'name': data.get('name'),
            'email': data.get('email'),
            'suggestion': data.get('suggestion'),
            'reason': data.get('reason')
        }).execute()
        
        return jsonify({'message': 'Thank you for your suggestion!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8080)
