# Metaphor Library - Backend & Database Documentation

## Overview
The Metaphor Library is a premium content system where users can purchase individual metaphors (philosophical explanations) as one-time purchases.

**Architecture:**
- **Frontend** owns all content (title, symbol, keywords, doctrine, preview, full text) in `METAPHOR_CATALOG`
- **Backend** owns purchases tracking and payment processing
- Content updates = simple frontend edits, no database changes needed

---

## Database Schema

**Note:** The `metaphors` table is optional. Current implementation uses frontend catalog only.

### Tables

#### 1. `metaphors` (OPTIONAL - not currently used)
Originally designed to store metaphor content. Now content lives in frontend `METAPHOR_CATALOG`.
Keep this table if you want database-driven content in the future.

| Column | Type | Description |
|--------|------|-------------|
| id | TEXT (PK) | Unique identifier (e.g., 'poker', 'chess') |
| title | TEXT | Display title (e.g., 'Poker') |
| symbol | TEXT | Unicode symbol or emoji (e.g., '♠') |
| keywords | TEXT[] | Array of 3 keywords (e.g., ['Uncertainty', 'State', 'Mastery']) |
| doctrine | TEXT | One-line core teaching |
| preview_content | TEXT | Free preview content (2-3 sections) |
| full_content | TEXT | Complete metaphor explanation (locked) |
| price | DECIMAL(10,2) | Price in USD (default: 5.00) |
| status | TEXT | 'available' or 'coming_soon' |
| order_index | INT | Display order on page |
| created_at | TIMESTAMPTZ | Creation timestamp |
| updated_at | TIMESTAMPTZ | Last update timestamp |

#### 2. `user_purchases`
Tracks which metaphors each user has purchased.

| Column | Type | Description |
|--------|------|-------------|
| id | BIGSERIAL (PK) | Auto-increment ID |
| user_id | TEXT | User identifier (from auth system) |
| metaphor_id | TEXT (FK) | References metaphors(id) |
| purchased_at | TIMESTAMPTZ | Purchase timestamp |
| price_paid | DECIMAL(10,2) | Amount paid |
| payment_id | TEXT | Stripe payment ID |
| UNIQUE(user_id, metaphor_id) | | Prevents duplicate purchases |

#### 3. `metaphor_suggestions`
Community-submitted metaphor ideas.

| Column | Type | Description |
|--------|------|-------------|
| id | BIGSERIAL (PK) | Auto-increment ID |
| name | TEXT | Submitter name (optional) |
| email | TEXT | Submitter email (optional) |
| suggestion | TEXT | Metaphor suggestion |
| reason | TEXT | Why it fits Psyche |
| submitted_at | TIMESTAMPTZ | Submission timestamp |
| status | TEXT | 'pending', 'approved', 'rejected' |

### Indexes
- `idx_user_purchases_user_id` - Fast lookup of user's purchases
- `idx_user_purchases_metaphor_id` - Fast lookup of metaphor purchases
- `idx_metaphors_status` - Filter by availability status
- `idx_metaphors_order` - Ordered display

---

## Backend API Endpoints

### Page Routes

#### `GET /metaphors`
Serves the metaphor library page (game.html).

#### `GET /metaphors/<metaphor_id>`
Serves individual metaphor page (game.html with dynamic content).

**Example:** `/metaphors/poker`

---

### API Endpoints

**Note:** `/api/metaphors` endpoints are not used in current implementation. Content comes from frontend catalog.

#### `GET /api/metaphors` (NOT USED)
~~Fetch all metaphors (ordered by order_index).~~

**Current approach:** Content is in frontend `METAPHOR_CATALOG` in `game.html`.

---

#### `GET /api/metaphors/<metaphor_id>` (NOT USED)
~~Fetch single metaphor by ID.~~

**Current approach:** Content is in frontend `METAPHOR_CATALOG` in `game.html`.

---

#### `GET /api/user/purchases`
Get list of metaphor IDs the current user has purchased.

**Headers:**
- `X-User-Id: <user_id>` (temporary - will be replaced with JWT)

**Response:**
```json
["poker", "chess", "choir"]
```

---

#### `GET /api/check-purchase/<metaphor_id>`
Check if current user has purchased a specific metaphor.

**Example:** `/api/check-purchase/poker`

**Headers:**
- `X-User-Id: <user_id>` (temporary)

**Response:**
```json
{
  "purchased": true
}
```

---

#### `POST /api/metaphor-suggestions`
Submit a community metaphor suggestion.

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "suggestion": "Basketball as a metaphor",
  "reason": "It shows teamwork and flow state"
}
```

**Response:**
```json
{
  "message": "Thank you for your suggestion!"
}
```

---

## User Flow

### 1. Browse Metaphors
- User visits `/metaphors`
- Frontend loads `METAPHOR_CATALOG` (no API call needed)
- Frontend fetches `/api/user/purchases` to check ownership
- Cards display:
  - **Purchased**: "Read Full →" button
  - **Not purchased**: "Preview" + "Unlock $5" buttons

### 2. Preview Content
- User clicks "Preview"
- Modal shows `preview_content` from frontend catalog
- Shows "Unlock" button if not purchased

### 3. Purchase Flow (To Be Implemented)
- User clicks "Unlock $5"
- Redirect to Stripe checkout
- After payment: Stripe webhook inserts into `user_purchases`
- User redirected back to `/metaphors/<metaphor_id>` (now unlocked)

### 4. View Full Content
- User clicks "Read Full →" (only visible if purchased)
- Modal shows `full_content` from frontend catalog
- No additional API calls needed

---

## Authentication (TODO)

**Current State:**
- Using temporary `X-User-Id` header
- Default: `'demo_user'`

**Future Implementation:**
- JWT-based authentication
- Session management
- Integrate with Supabase Auth or custom auth system

---

## Payment Integration (TODO)

### Stripe Setup Required:
1. Create Stripe account
2. Add Stripe API keys to `.env`:
   ```
   STRIPE_SECRET_KEY=sk_test_...
   STRIPE_PUBLISHABLE_KEY=pk_test_...
   STRIPE_WEBHOOK_SECRET=whsec_...
   ```
3. Create products in Stripe Dashboard
4. Implement checkout endpoint
5. Set up webhook endpoint for payment confirmation

---

## Content Management

### Adding/Editing Metaphors

**Location:** `/Users/eva/PythonProject/views/game.html`

**Edit the `METAPHOR_CATALOG` array:**

```javascript
const METAPHOR_CATALOG = [
  {
    id: "poker",              // Unique ID (used for purchases)
    title: "Poker",           // Display title
    symbol: "♠",              // Unicode symbol
    keywords: ["Uncertainty", "State", "Mastery"],  // 3 keywords
    doctrine: "Trust without proof.",  // One-line teaching
    preview_content: "...",   // Free preview (2-3 paragraphs)
    full_content: "...",      // Full metaphor (all sections)
    price: 5.00,              // Price in USD
    status: "available",      // 'available' or 'coming_soon'
    order_index: 1            // Display order
  },
  // Add more metaphors here...
];
```

**Benefits:**
- ✅ No database updates needed
- ✅ Easy to edit content
- ✅ Version control friendly
- ✅ Fast page loads (no API calls)
- ✅ Backend only tracks purchases

---

## Testing

### Test API Endpoints:
```bash
# Content is now in frontend, so /api/metaphors is not used

# Check purchase (demo user)
curl -H "X-User-Id: demo_user" http://localhost:8080/api/check-purchase/poker

# Get user purchases
curl -H "X-User-Id: demo_user" http://localhost:8080/api/user/purchases

# Submit suggestion
curl -X POST http://localhost:8080/api/metaphor-suggestions \
  -H "Content-Type: application/json" \
  -d '{"suggestion": "Test metaphor", "reason": "Testing"}'
```

### Test Purchase Flow (Manual):
```sql
-- Insert test purchase in Supabase SQL Editor
INSERT INTO user_purchases (user_id, metaphor_id, price_paid)
VALUES ('demo_user', 'poker', 5.00);
```

---

## Sample Metaphors

Current metaphors in frontend catalog:
1. **Poker** (♠) - Uncertainty · State · Mastery - Available
2. **Chess** (♟) - Clarity · Intention · Strategy - Available
3. **Choir** (♫) - Resonance · Unity · Harmony - Available
4. **Orchestra** (🎻) - Structure · Timing · Flow - Coming Soon
5. **Zodiac** (✶) - Cycles · Archetypes · Timing - Coming Soon

**To add more:** Edit `METAPHOR_CATALOG` in `game.html`

---

## File Structure

```
/Users/eva/PythonProject/
├── app.py                      # Flask backend with API endpoints
├── database_schema.sql         # Database schema (run in Supabase)
├── views/
│   ├── index.html             # Main landing page
│   └── game.html              # Metaphor library page (to be created)
├── .env                       # Environment variables (Supabase keys)
└── METAPHOR_README.md         # This file
```

---

## Next Steps

1. ✅ Database schema created (purchases only)
2. ✅ Backend API endpoints implemented (purchases + suggestions)
3. ✅ Frontend catalog created in `game.html`
4. ✅ Full content display working
5. ⏳ Add full metaphor content to frontend catalog
6. ⏳ Implement Stripe payment integration
7. ⏳ Add proper authentication (JWT/session)
8. ⏳ Test end-to-end purchase flow

---

## Notes

- All prices are in USD
- One-time purchases (not subscriptions)
- Users can buy individual metaphors or bundles (future)
- **Content is stored in frontend catalog** (`game.html`)
- **Backend only tracks purchases** (`user_purchases` table)
- Preview content is always free
- Full content requires purchase
- Easy to update content without database changes
