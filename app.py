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
import uuid
import json
import stripe

load_dotenv()

app = Flask(__name__)
CORS(app)

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
SESSION_DURATION_DAYS = 30

# Stripe configuration
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

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

def create_session(user_uuid, google_id=None):
    """Create a new session token for user"""
    token = secrets.token_urlsafe(64)
    expires_at = datetime.utcnow() + timedelta(days=SESSION_DURATION_DAYS)

    session_data = {
        'user_uuid': str(user_uuid),
        'token': token,
        'expires_at': expires_at.isoformat()
    }
    if google_id:
        session_data['google_id'] = google_id

    supabase.table('sessions').insert(session_data).execute()

    return token, expires_at

def verify_session(token):
    """Verify session token and return user_id if valid"""
    try:
        result = supabase.table('sessions')\
            .select('user_uuid, expires_at')\
            .eq('token', token)\
            .execute()

        if result.data and len(result.data) > 0:
            session = result.data[0]
            expires_at = datetime.fromisoformat(session['expires_at'].replace('Z', '+00:00'))
            if expires_at > datetime.now(expires_at.tzinfo):
                return session['user_uuid']
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

# TEMPORARY: Original homepage (uncomment after Apple approval)
# @app.route('/')
# def index():
#     return send_from_directory('views', 'index.html')

# TEMPORARY: Professional page for Apple review
@app.route('/')
def index():
    return send_from_directory('views', 'apple-home.html')

# Original creative homepage (accessible during Apple review period)
@app.route('/product')
def product_page():
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

@app.route('/manifestation-tool')
def manifestation_tool():
    return send_from_directory('views', 'manifestation-tool.html')

@app.route('/interview-round-1')
def interview_round_1():
    # Public access (no token) - redirect or show error
    return send_from_directory('views', 'questionnaire.html')

@app.route('/interview/<token>')
def interview_with_token(token):
    """Serve interview page for valid token"""
    try:
        # Validate token
        result = supabase.table('interview_invites')\
            .select('*')\
            .eq('token', token)\
            .single()\
            .execute()

        if not result.data:
            return "Invalid or expired interview link.", 404

        invite = result.data

        # Check if already completed
        if invite['status'] == 'completed':
            return "This interview has already been submitted.", 400

        # Check if expired
        if invite['expires_at']:
            from datetime import datetime
            expires = datetime.fromisoformat(invite['expires_at'].replace('Z', '+00:00'))
            if datetime.now(expires.tzinfo) > expires:
                return "This interview link has expired.", 400

        # Mark as started if first time
        if invite['status'] == 'pending':
            supabase.table('interview_invites')\
                .update({'status': 'started', 'started_at': datetime.utcnow().isoformat()})\
                .eq('token', token)\
                .execute()

        return send_from_directory('views', 'questionnaire.html')

    except Exception as e:
        print(f"Interview token error: {e}")
        return "Invalid interview link.", 404

@app.route('/api/interview/validate/<token>', methods=['GET'])
def validate_interview_token(token):
    """Validate token and return candidate info"""
    try:
        result = supabase.table('interview_invites')\
            .select('*')\
            .eq('token', token)\
            .single()\
            .execute()

        if not result.data:
            return jsonify({'valid': False, 'error': 'Invalid token'}), 404

        invite = result.data

        if invite['status'] == 'completed':
            return jsonify({'valid': False, 'error': 'Already submitted'}), 400

        return jsonify({
            'valid': True,
            'candidate_email': invite['candidate_email'],
            'candidate_name': invite['candidate_name'],
            'position': invite['position']
        }), 200

    except Exception as e:
        return jsonify({'valid': False, 'error': str(e)}), 500

@app.route('/api/interview/submit', methods=['POST'])
def submit_interview():
    """Submit interview responses"""
    data = request.get_json()
    token = data.get('token')
    responses = data.get('responses')

    if not token or not responses:
        return jsonify({'error': 'Token and responses required'}), 400

    try:
        # Validate token
        invite_result = supabase.table('interview_invites')\
            .select('*')\
            .eq('token', token)\
            .single()\
            .execute()

        if not invite_result.data:
            return jsonify({'error': 'Invalid token'}), 404

        invite = invite_result.data

        if invite['status'] == 'completed':
            return jsonify({'error': 'Already submitted'}), 400

        # Save responses
        supabase.table('interview_responses').insert({
            'invite_id': invite['id'],
            'token': token,
            'candidate_email': invite['candidate_email'],
            'candidate_name': invite['candidate_name'],
            'responses': responses
        }).execute()

        # Mark invite as completed
        supabase.table('interview_invites')\
            .update({'status': 'completed', 'completed_at': datetime.utcnow().isoformat()})\
            .eq('token', token)\
            .execute()

        return jsonify({'success': True, 'message': 'Interview submitted successfully'}), 200

    except Exception as e:
        print(f"Interview submit error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/interview/create', methods=['POST'])
def create_interview_invite():
    """Create a new interview invite (admin use)"""
    data = request.get_json()
    candidate_email = data.get('email')
    candidate_name = data.get('name')
    position = data.get('position', 'Design Intern')

    if not candidate_email:
        return jsonify({'error': 'Email required'}), 400

    try:
        # Generate unique token
        token = secrets.token_urlsafe(32)

        # Set expiration (end of day, 14 days from now)
        expires_at = (datetime.utcnow() + timedelta(days=14)).replace(hour=23, minute=59, second=59).isoformat()

        # Create invite
        result = supabase.table('interview_invites').insert({
            'token': token,
            'candidate_email': candidate_email,
            'candidate_name': candidate_name,
            'position': position,
            'expires_at': expires_at
        }).execute()

        interview_url = f"https://psyche-ai.xyz/interview/{token}"

        return jsonify({
            'success': True,
            'token': token,
            'url': interview_url,
            'expires_at': expires_at
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/home')
def home():
    return send_from_directory('views', 'apple-home.html')

@app.route('/privacy')
def privacy():
    return send_from_directory('views', 'privacy.html')

@app.route('/app-privacy')
def app_privacy():
    return send_from_directory('views', 'app-privacy.html')

@app.route('/terms')
def terms():
    return send_from_directory('views', 'terms.html')

@app.route('/metaphors/<metaphor_id>')
def metaphor_detail(metaphor_id):
    return send_from_directory('views', 'metaphor-detail.html')

@app.route('/views/<path:filename>')
def views_static(filename):
    return send_from_directory('views', filename)

@app.route('/logos/<path:filename>')
def logos_static(filename):
    return send_from_directory('logos', filename)

@app.route('/images/<path:filename>')
def images_static(filename):
    return send_from_directory('images', filename)

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

# --- Auth Endpoints ---

@app.route('/api/auth/google', methods=['POST'])
def auth_google():
    """Handle Google Sign-In - uses users table for user storage"""
    data = request.get_json()
    id_token_str = data.get('idToken')

    if not id_token_str:
        return jsonify({'error': 'ID token required'}), 400

    google_user = verify_google_token(id_token_str)
    if not google_user:
        return jsonify({'error': 'Invalid Google token'}), 401

    try:
        # Check if user exists by google_id in users table
        existing = supabase.table('users')\
            .select('*')\
            .eq('google_id', google_user['google_id'])\
            .limit(1)\
            .execute()

        if existing.data and len(existing.data) > 0:
            user = existing.data[0]
            user_id = user['id']
            # Update existing user info
            supabase.table('users').update({
                'name': google_user['name']
            }).eq('google_id', google_user['google_id']).execute()
        else:
            # Create new user entry
            result = supabase.table('users').insert({
                'email': google_user['email'],
                'name': google_user['name'],
                'provider': 'google',
                'google_id': google_user['google_id']
            }).execute()
            user = result.data[0]
            user_id = user['id']

        # Create session using user uuid as identifier
        session_token, expires_at = create_session(user['uuid'], google_user['google_id'])

        return jsonify({
            'user': {
                'id': user['uuid'],
                'email': google_user['email'],
                'name': google_user['name'],
                'avatar_url': google_user['avatar_url'],
                'vip_level': 'free'
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
    """Get current authenticated user from users table"""
    try:
        result = supabase.table('users')\
            .select('uuid, email, name')\
            .eq('uuid', request.user_id)\
            .limit(1)\
            .execute()

        if not result.data or len(result.data) == 0:
            return jsonify({'error': 'User not found'}), 404

        user = result.data[0]
        return jsonify({
            'id': user['uuid'],
            'email': user['email'],
            'name': user['name'],
            'vip_level': 'free'
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
    """Get all metaphors from database"""
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
    """Get single metaphor by ID from database"""
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
            .eq('user_uuid', request.user_id)\
            .execute()

        purchased_ids = [p['metaphor_id'] for p in result.data]
        return jsonify(purchased_ids), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/metaphors/<metaphor_id>/content', methods=['GET'])
@require_auth
def get_metaphor_content(metaphor_id):
    """Get metaphor content from database - full if purchased, preview if not"""
    try:
        # Check if user has purchased this metaphor
        purchase_check = supabase.table('user_purchases')\
            .select('*')\
            .eq('user_uuid', request.user_id)\
            .eq('metaphor_id', metaphor_id)\
            .execute()

        has_purchased = len(purchase_check.data) > 0

        # Get metaphor data from database
        metaphor = supabase.table('metaphors')\
            .select('*')\
            .eq('id', metaphor_id)\
            .single()\
            .execute()

        if not metaphor.data:
            return jsonify({'error': 'Metaphor not found'}), 404
        
        return jsonify({
            'id': metaphor_id,
            'title': metaphor.data['title'],
            'content': metaphor.data['full_content'] if has_purchased else metaphor.data['preview_content'],
            'has_access': has_purchased,
            'is_preview': not has_purchased
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/purchase/<metaphor_id>', methods=['POST'])
@require_auth
def purchase_metaphor(metaphor_id):
    """Purchase a metaphor for the current user"""
    try:
        # Check if already purchased
        existing = supabase.table('user_purchases')\
            .select('*')\
            .eq('user_uuid', request.user_id)\
            .eq('metaphor_id', metaphor_id)\
            .execute()

        if existing.data and len(existing.data) > 0:
            return jsonify({'error': 'Already purchased'}), 400

        # Get user info for the purchase record
        user = supabase.table('users')\
            .select('email, name')\
            .eq('uuid', request.user_id)\
            .single()\
            .execute()

        # Insert purchase record
        supabase.table('user_purchases').insert({
            'user_uuid': request.user_id,
            'email': user.data['email'],
            'name': user.data['name'],
            'metaphor_id': metaphor_id,
            'price_paid': '5.00'
        }).execute()

        return jsonify({'message': 'Purchase successful'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/check-purchase/<metaphor_id>', methods=['GET'])
@require_auth
def check_purchase(metaphor_id):
    """Check if user has purchased specific metaphor"""
    try:
        result = supabase.table('user_purchases')\
            .select('*')\
            .eq('user_uuid', request.user_id)\
            .eq('metaphor_id', metaphor_id)\
            .execute()

        return jsonify({'purchased': len(result.data) > 0}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/purchase/bundle/<bundle_id>', methods=['POST'])
@require_auth
def purchase_bundle(bundle_id):
    """Purchase a bundle - grants access to all metaphors in bundle"""
    try:
        # Get bundle info
        bundle = supabase.table('bundles')\
            .select('*')\
            .eq('id', bundle_id)\
            .single()\
            .execute()

        if not bundle.data:
            return jsonify({'error': 'Bundle not found'}), 404

        # Get user info
        user = supabase.table('users')\
            .select('email, name')\
            .eq('uuid', request.user_id)\
            .single()\
            .execute()

        # Check what user already owns
        existing = supabase.table('user_purchases')\
            .select('metaphor_id')\
            .eq('user_uuid', request.user_id)\
            .in_('metaphor_id', bundle.data['metaphor_ids'])\
            .execute()

        already_owned = [p['metaphor_id'] for p in existing.data]
        new_metaphors = [m for m in bundle.data['metaphor_ids'] if m not in already_owned]

        # Insert new purchases
        if new_metaphors:
            purchases = []
            for metaphor_id in new_metaphors:
                purchases.append({
                    'user_uuid': request.user_id,
                    'email': user.data['email'],
                    'name': user.data['name'],
                    'metaphor_id': metaphor_id,
                    'price_paid': '5.00'
                })

            supabase.table('user_purchases').insert(purchases).execute()

        return jsonify({
            'bundle_id': bundle_id,
            'bundle_name': bundle.data['name'],
            'granted_metaphors': new_metaphors,
            'already_owned': already_owned,
            'total_metaphors': len(bundle.data['metaphor_ids']),
            'new_access_count': len(new_metaphors)
        }), 200

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

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """Submit user feedback"""
    data = request.get_json()
    email = data.get('email')
    title = data.get('title')
    feedback = data.get('feedback')
    source = data.get('source', 'unknown')

    if not email or not feedback:
        return jsonify({'error': 'Email and feedback are required'}), 400

    # Check if user is authenticated
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = verify_session(token) if token else None

    try:
        supabase.table('feedback').insert({
            'email': email,
            'title': title,
            'feedback': feedback,
            'source': source,
            'user_id': user_id
        }).execute()

        return jsonify({'message': 'Thank you for your feedback!'}), 200
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

# --- Stripe Webhook ---

@app.route('/api/stripe/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')

    # Skip signature verification in debug mode (local testing only)
    if app.debug:
        try:
            event = json.loads(payload)
            print("DEBUG MODE: Skipping Stripe signature verification")
        except json.JSONDecodeError:
            return jsonify({'error': 'Invalid JSON payload'}), 400
    else:
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            return jsonify({'error': 'Invalid payload'}), 400
        except stripe.error.SignatureVerificationError:
            return jsonify({'error': 'Invalid signature'}), 400

    # Handle checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        # Get user ID and metaphor ID from client_reference_id (format: "userId_metaphorId")
        client_reference_id = session.get('client_reference_id')
        customer_email = session.get('customer_details', {}).get('email')

        print(f"Payment completed - client_reference_id: {client_reference_id}, email: {customer_email}")

        if client_reference_id and '_' in client_reference_id:
            try:
                user_uuid, metaphor_id = client_reference_id.split('_', 1)

                # Look up user by uuid
                user_result = supabase.table('users')\
                    .select('uuid, email, name')\
                    .eq('uuid', user_uuid)\
                    .single()\
                    .execute()

                if user_result.data:
                    user = user_result.data

                    # Check if already purchased
                    existing = supabase.table('user_purchases')\
                        .select('id')\
                        .eq('user_uuid', user['uuid'])\
                        .eq('metaphor_id', metaphor_id)\
                        .execute()

                    if not existing.data:
                        # Insert purchase record
                        supabase.table('user_purchases').insert({
                            'user_uuid': user['uuid'],
                            'metaphor_id': metaphor_id,
                            'email': user['email'],
                            'name': user['name'],
                            'price_paid': '5.00'
                        }).execute()
                        print(f"Purchase recorded: user={user['email']}, metaphor={metaphor_id}")
                    else:
                        print(f"Already purchased: user={user['email']}, metaphor={metaphor_id}")
                else:
                    print(f"User not found: {user_uuid}")
            except Exception as e:
                print(f"Error processing payment: {e}")

    return jsonify({'received': True}), 200

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8080)

# Vercel serverless function handler
app = app
