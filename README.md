# Psyche - Divine Consciousness Platform

A unified platform for grounding & centering your energy, strengthening your sense of purpose, and living with clarity and intention in everyday life.

## Setup

### Prerequisites
- Python 3.8+
- Supabase account

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file in the project root:
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

3. Create Supabase table:
```sql
CREATE TABLE subscribers (
  id BIGSERIAL PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  subscribed_at TIMESTAMPTZ NOT NULL
);
```

### Running the Application

1. Start the backend:
```bash
python app.py
```

2. Open `index.html` in your browser

## API Endpoints

### POST /api/subscribe
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

### subscribers table
- `id` - Primary key
- `email` - Unique email address
- `subscribed_at` - Timestamp of subscription (UTC)
