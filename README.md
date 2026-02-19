# Psyche - Divine Consciousness Platform

A unified platform for grounding & centering your energy, strengthening your sense of purpose, and living with clarity and intention in everyday life.

## Setup

### Prerequisites
- Python 3.8+
- Supabase account
- Google OAuth Client ID

### Deployment
Vercel
https://vercel.com/evawang369s-projects

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file in the project root:
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
GOOGLE_CLIENT_ID=your_google_client_id
```

3. Create Supabase tables:
```sql
-- Users table
CREATE TABLE users (
  id BIGSERIAL PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  name TEXT,
  provider TEXT DEFAULT 'google',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  google_id TEXT UNIQUE
);

-- Sessions table
CREATE TABLE sessions (
  id BIGSERIAL PRIMARY KEY,
  user_id TEXT NOT NULL,
  token TEXT UNIQUE NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- User purchases table
CREATE TABLE user_purchases (
  id BIGSERIAL PRIMARY KEY,
  user_id TEXT NOT NULL,
  email TEXT,
  name TEXT,
  metaphor_id TEXT NOT NULL,
  google_id TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Email subscriptions table
CREATE TABLE universal_subscription (
  id BIGSERIAL PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  subscribed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Disable RLS for backend access
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE sessions DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_purchases DISABLE ROW LEVEL SECURITY;
ALTER TABLE universal_subscription DISABLE ROW LEVEL SECURITY;
```

### Running the Application

1. Start the backend:
```bash
python app.py
```

2. Open `http://localhost:8080` in your browser

## Authentication Flow

### User Login Process
1. User clicks "Sign In" button
2. Google OAuth modal opens
3. User authenticates with Google
4. Frontend sends Google ID token to `/api/auth/google`
5. Backend verifies token and creates/updates user in `users` table
6. Backend creates session token and stores in `sessions` table
7. Frontend stores user data and session token in localStorage
8. User is now authenticated across all pages

### Session Management
- Sessions expire after 30 days
- Session tokens stored in localStorage with key `psyche_session`
- User data stored in localStorage with key `psyche_user`
- AuthManager handles authentication state across pages

## API Endpoints

### Authentication

#### POST /api/auth/google
Authenticate user with Google OAuth.

**Request:**
```json
{
  "idToken": "google_id_token_here"
}
```

**Response:**
```json
{
  "user": {
    "id": 123,
    "email": "user@example.com",
    "name": "User Name",
    "avatar_url": "https://...",
    "vip_level": "free"
  },
  "session": {
    "token": "session_token_here",
    "expires_at": "2024-03-15T10:30:00Z"
  }
}
```

#### GET /api/auth/me
Get current authenticated user info.

**Headers:**
```
Authorization: Bearer <session_token>
```

**Response:**
```json
{
  "id": 123,
  "email": "user@example.com",
  "name": "User Name",
  "vip_level": "free"
}
```

#### POST /api/auth/logout
Invalidate current session.

**Headers:**
```
Authorization: Bearer <session_token>
```

### Purchases

#### POST /api/purchase/<metaphor_id>
Purchase a metaphor for the current user.

**Headers:**
```
Authorization: Bearer <session_token>
```

**Response:**
```json
{
  "message": "Purchase successful"
}
```

#### GET /api/check-purchase/<metaphor_id>
Check if user has purchased a specific metaphor.

**Headers:**
```
Authorization: Bearer <session_token>
```

**Response:**
```json
{
  "purchased": true
}
```

#### GET /api/user/purchases
Get all metaphors purchased by current user.

**Headers:**
```
Authorization: Bearer <session_token>
```

**Response:**
```json
["poker", "chess", "choir"]
```

### Email Subscription

#### POST /api/subscribe
Subscribe a user with their email.

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "message": "Successfully subscribed!"
}
```

## Database Schema

### users table
- `id` - Auto-incrementing primary key
- `email` - Unique email address
- `name` - User's full name
- `provider` - OAuth provider (default: 'google')
- `created_at` - Account creation timestamp
- `google_id` - Google OAuth user ID

### sessions table
- `id` - Auto-incrementing primary key
- `user_id` - Reference to user's Google ID
- `token` - Unique session token
- `expires_at` - Session expiration timestamp
- `created_at` - Session creation timestamp

### user_purchases table
- `id` - Auto-incrementing primary key
- `user_id` - Reference to user's Google ID
- `email` - User's email (denormalized)
- `name` - User's name (denormalized)
- `metaphor_id` - ID of purchased metaphor
- `google_id` - Google OAuth user ID
- `created_at` - Purchase timestamp

### universal_subscription table
- `id` - Auto-incrementing primary key
- `email` - Subscriber's email address
- `subscribed_at` - Subscription timestamp
