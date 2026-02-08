# Bundle Purchase Implementation - TODO

## ❌ Not Yet Implemented:

### 1. Bundle Loading & Rendering
Add to game.html after line with `let userPurchases = [];`:

```javascript
let bundles = [];

// In loadMetaphors() function, add:
const bundlesResponse = await fetch('/api/bundles');
bundles = await bundlesResponse.json();
renderBundles();

// Add new function:
function renderBundles() {
  const bundlesGrid = document.getElementById('bundlesGrid');
  bundlesGrid.innerHTML = '';
  
  bundles.forEach(bundle => {
    bundlesGrid.innerHTML += createBundleCard(bundle);
  });
}

function createBundleCard(bundle) {
  const discount = bundle.discount_percent || 0;
  const metaphorCount = bundle.metaphor_ids.length;
  
  return `
    <div class="metaphor-card" style="border: 2px solid rgba(218, 165, 32, 0.4);">
      <div class="metaphor-symbol">🎁</div>
      <h3>${bundle.name}</h3>
      <div class="metaphor-keywords">${metaphorCount} Metaphors · Save ${discount}%</div>
      <div class="metaphor-doctrine">${bundle.description}</div>
      <div class="metaphor-actions">
        <button class="btn btn-unlock" onclick="purchaseBundle('${bundle.id}')">
          Unlock Bundle $${bundle.price}
        </button>
      </div>
    </div>
  `;
}
```

### 2. Purchase Functions
Replace `unlockMetaphor()` and add `purchaseBundle()`:

```javascript
function unlockMetaphor(metaphorId) {
  if (!AuthManager.isLoggedIn()) {
    alert('Please sign in to purchase');
    openAuthModal();
    return;
  }
  
  // TODO: Implement Stripe checkout
  const metaphor = metaphors.find(m => m.id === metaphorId);
  alert(`Stripe checkout for ${metaphor.title} ($${metaphor.price}) coming soon!`);
}

function purchaseBundle(bundleId) {
  if (!AuthManager.isLoggedIn()) {
    alert('Please sign in to purchase');
    openAuthModal();
    return;
  }
  
  // TODO: Implement Stripe checkout
  const bundle = bundles.find(b => b.id === bundleId);
  alert(`Stripe checkout for ${bundle.name} ($${bundle.price}) coming soon!`);
}
```

### 3. Backend Stripe Endpoints (app.py)
Add these endpoints:

```python
import stripe
import os

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

@app.route('/api/create-checkout', methods=['POST'])
def create_checkout():
    data = request.json
    session = AuthManager.get_session_from_request(request)
    
    if not session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    item_type = data.get('type')  # 'metaphor' or 'bundle'
    item_id = data.get('id')
    
    # Create Stripe checkout session
    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {'name': f'{item_id} - Psyche Metaphor'},
                'unit_amount': int(data['price'] * 100)
            },
            'quantity': 1
        }],
        mode='payment',
        success_url=f'{request.host_url}metaphors?success=true',
        cancel_url=f'{request.host_url}metaphors',
        metadata={
            'user_id': session['user_id'],
            'type': item_type,
            'item_id': item_id
        }
    )
    
    return jsonify({'checkout_url': checkout_session.url})

@app.route('/api/stripe-webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv('STRIPE_WEBHOOK_SECRET')
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        metadata = session['metadata']
        
        if metadata['type'] == 'bundle':
            # Insert multiple purchases for bundle
            bundle = supabase.table('bundles').select('*').eq('id', metadata['item_id']).single().execute()
            for metaphor_id in bundle.data['metaphor_ids']:
                supabase.table('user_purchases').insert({
                    'user_id': metadata['user_id'],
                    'metaphor_id': metaphor_id,
                    'price_paid': bundle.data['price'] / len(bundle.data['metaphor_ids']),
                    'payment_id': session['payment_intent'],
                    'bundle_id': metadata['item_id']
                }).execute()
        else:
            # Single metaphor purchase
            supabase.table('user_purchases').insert({
                'user_id': metadata['user_id'],
                'metaphor_id': metadata['item_id'],
                'price_paid': session['amount_total'] / 100,
                'payment_id': session['payment_intent']
            }).execute()
    
    return jsonify({'status': 'success'})
```

### 4. Environment Variables
Add to `.env`:
```
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

## Summary:
- ✅ Bundle section HTML added
- ❌ Bundle loading/rendering - Need to add
- ❌ Purchase logic - Need to implement
- ❌ Stripe integration - Need to set up
- ❌ Backend endpoints - Need to add

Ready to implement these step by step?
