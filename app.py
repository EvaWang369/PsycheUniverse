from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from supabase import create_client
from datetime import datetime, timedelta
from dotenv import load_dotenv
from functools import wraps
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import os
import secrets

load_dotenv()

app = Flask(__name__)
CORS(app)

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
SESSION_DURATION_DAYS = 30

# --- Authentication Helpers ---

def verify_google_token(token):
    """Verify Google ID token and return user info"""
    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            GOOGLE_CLIENT_ID
        )

        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            return None

        return {
            'google_id': idinfo['sub'],
            'email': idinfo['email'],
            'name': idinfo.get('name'),
            'avatar_url': idinfo.get('picture')
        }
    except Exception as e:
        print(f"Google token verification failed: {e}")
        return None

def create_session(user_id):
    """Create a new session token for user"""
    token = secrets.token_urlsafe(64)
    expires_at = datetime.utcnow() + timedelta(days=SESSION_DURATION_DAYS)

    supabase.table('sessions').insert({
        'user_id': str(user_id),
        'token': token,
        'expires_at': expires_at.isoformat()
    }).execute()

    return token, expires_at

def verify_session(token):
    """Verify session token and return user_id if valid"""
    try:
        result = supabase.table('sessions')\
            .select('user_id, expires_at')\
            .eq('token', token)\
            .execute()

        if result.data and len(result.data) > 0:
            session = result.data[0]
            expires_at = datetime.fromisoformat(session['expires_at'].replace('Z', '+00:00'))
            if expires_at > datetime.now(expires_at.tzinfo):
                return session['user_id']
    except Exception as e:
        print(f"Session verification failed: {e}")
    return None

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'No authorization token provided'}), 401

        user_id = verify_session(token)
        if not user_id:
            return jsonify({'error': 'Invalid or expired session'}), 401

        request.user_id = user_id
        return f(*args, **kwargs)
    return decorated_function

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

# --- Auth Endpoints ---

@app.route('/api/auth/google', methods=['POST'])
def auth_google():
    """Handle Google Sign-In - uses user_purchases table for user storage"""
    data = request.get_json()
    id_token_str = data.get('idToken')

    if not id_token_str:
        return jsonify({'error': 'ID token required'}), 400

    google_user = verify_google_token(id_token_str)
    if not google_user:
        return jsonify({'error': 'Invalid Google token'}), 401

    try:
        # Check if user exists by google_id in user_purchases
        existing = supabase.table('user_purchases')\
            .select('*')\
            .eq('google_id', google_user['google_id'])\
            .limit(1)\
            .execute()

        if existing.data and len(existing.data) > 0:
            user = existing.data[0]
            # Update existing user info
            supabase.table('user_purchases').update({
                'name': google_user['name'],
                'avatar_url': google_user['avatar_url']
            }).eq('google_id', google_user['google_id']).execute()
        else:
            # Create new user entry (no purchase yet, just user record)
            result = supabase.table('user_purchases').insert({
                'user_id': google_user['google_id'],
                'email': google_user['email'],
                'name': google_user['name'],
                'google_id': google_user['google_id'],
                'avatar_url': google_user['avatar_url'],
                'vip_level': 'free',
                'metaphor_id': '_user_record'
            }).execute()
            user = result.data[0]

        # Create session using google_id as user identifier
        session_token, expires_at = create_session(google_user['google_id'])

        return jsonify({
            'user': {
                'id': google_user['google_id'],
                'email': google_user['email'],
                'name': google_user['name'],
                'avatar_url': google_user['avatar_url'],
                'vip_level': user.get('vip_level', 'free')
            },
            'session': {
                'token': session_token,
                'expires_at': expires_at.isoformat()
            }
        }), 200

    except Exception as e:
        print(f"Auth error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/me', methods=['GET'])
@require_auth
def get_current_user():
    """Get current authenticated user from user_purchases"""
    try:
        result = supabase.table('user_purchases')\
            .select('email, name, avatar_url, vip_level, google_id')\
            .eq('google_id', request.user_id)\
            .limit(1)\
            .execute()

        if not result.data or len(result.data) == 0:
            return jsonify({'error': 'User not found'}), 404

        user = result.data[0]
        return jsonify({
            'id': user['google_id'],
            'email': user['email'],
            'name': user['name'],
            'avatar_url': user.get('avatar_url'),
            'vip_level': user.get('vip_level', 'free')
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/logout', methods=['POST'])
@require_auth
def logout():
    """Invalidate current session"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    try:
        supabase.table('sessions').delete().eq('token', token).execute()
        return jsonify({'message': 'Logged out successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
@require_auth
def get_user_purchases():
    """Get all metaphors purchased by current user"""
    try:
        result = supabase.table('user_purchases')\
            .select('metaphor_id')\
            .eq('google_id', request.user_id)\
            .neq('metaphor_id', '_user_record')\
            .execute()

        purchased_ids = [p['metaphor_id'] for p in result.data]
        return jsonify(purchased_ids), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/check-purchase/<metaphor_id>', methods=['GET'])
@require_auth
def check_purchase(metaphor_id):
    """Check if user has purchased specific metaphor"""
    try:
        result = supabase.table('user_purchases')\
            .select('*')\
            .eq('google_id', request.user_id)\
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

# Bundle Endpoints

@app.route('/api/bundles', methods=['GET'])
def get_bundles():
    """Get all available bundles"""
    try:
        result = supabase.table('bundles')\
            .select('*')\
            .eq('status', 'active')\
            .execute()
        return jsonify(result.data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/bundles/<bundle_id>', methods=['GET'])
def get_bundle(bundle_id):
    """Get single bundle by ID"""
    try:
        result = supabase.table('bundles')\
            .select('*')\
            .eq('id', bundle_id)\
            .single()\
            .execute()
        return jsonify(result.data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 404

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8080)
