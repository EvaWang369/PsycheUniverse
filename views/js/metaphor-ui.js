// Metaphor UI Functions

let metaphors = METAPHOR_CATALOG.slice();
let userPurchases = [];
const STRIPE_LINK_BASE = "https://buy.stripe.com/5kQdR125Y1uJfRk30e5gc00";

function getStripeLink(metaphorId) {
  // Append user ID and metaphor ID, so webhook knows who paid and for what
  if (typeof AuthManager !== 'undefined' && AuthManager.isLoggedIn()) {
    const user = AuthManager.getUser();
    if (user && user.id && metaphorId) {
      return `${STRIPE_LINK_BASE}?client_reference_id=${user.id}_${metaphorId}`;
    }
  }
  return STRIPE_LINK_BASE;
}

async function loadMetaphors() {
  try {
    // Load metaphors from database instead of static catalog
    const metaphorsResponse = await fetch('/api/metaphors');
    if (metaphorsResponse.ok) {
      metaphors = await metaphorsResponse.json();
    } else {
      // Fallback to static catalog
      metaphors = METAPHOR_CATALOG.slice();
    }
    
    metaphors.sort((a, b) => (a.order_index ?? 9999) - (b.order_index ?? 9999));

    if (AuthManager.isLoggedIn()) {
      const purchasesResponse = await fetch('/api/user/purchases', {
        headers: AuthManager.getAuthHeaders()
      });
      if (purchasesResponse.ok) {
        userPurchases = await purchasesResponse.json();
      } else {
        userPurchases = [];
      }
    } else {
      userPurchases = [];
    }

    renderMetaphors();
    await loadBundles();
  } catch (error) {
    console.error('Error loading metaphors:', error);
    // Fallback to static catalog
    metaphors = METAPHOR_CATALOG
      .slice()
      .sort((a, b) => (a.order_index ?? 9999) - (b.order_index ?? 9999));
    userPurchases = [];
    renderMetaphors();
  }
}

function renderMetaphors() {
  const coreGrid = document.getElementById('coreGrid');
  const moreGrid = document.getElementById('moreGrid');
  const expandingGrid = document.getElementById('expandingGrid');

  coreGrid.innerHTML = '';
  moreGrid.innerHTML = '';
  expandingGrid.innerHTML = '';

  const available = metaphors.filter(m => m.status === 'available');
  const comingSoon = metaphors.filter(m => m.status === 'coming_soon');

  available.slice(0, 3).forEach(m => {
    coreGrid.innerHTML += createMetaphorCard(m);
  });

  available.slice(3).forEach(m => {
    moreGrid.innerHTML += createMetaphorCard(m);
  });

  comingSoon.forEach(m => {
    expandingGrid.innerHTML += createMetaphorCard(m);
  });
}

function createMetaphorCard(metaphor) {
  const isPurchased = userPurchases.includes(metaphor.id);
  const isComingSoon = metaphor.status === 'coming_soon';
  const keywords = metaphor.keywords ? metaphor.keywords.join(' · ') : '';

  let actions = '';
  if (isComingSoon) {
    actions = '<span class="status-badge status-coming-soon">Coming Soon</span>';
  } else if (isPurchased) {
    actions = `<button class="btn btn-read" onclick="readFull('${metaphor.id}')">Read Full →</button>`;
  } else {
    actions = `
      <button class="btn btn-preview" onclick="showPreview('${metaphor.id}')">Preview →</button>
      <a href="${getStripeLink(metaphor.id)}" target="_blank" rel="noopener noreferrer" class="btn btn-unlock">Unlock $5</a>
    `;
  }

  return `
    <div class="metaphor-card">
      <div class="metaphor-symbol">${metaphor.symbol || '✦'}</div>
      <h3>${metaphor.title}</h3>
      <div class="metaphor-keywords">${keywords}</div>
      <div class="metaphor-doctrine">${metaphor.doctrine || ''}</div>
      <div class="metaphor-actions">${actions}</div>
    </div>
  `;
}

function toggleMoreLenses() {
  const section = document.getElementById('more-lenses');
  const btn = document.getElementById('expandBtn');
  
  if (section.style.display === 'none') {
    section.style.display = 'block';
    btn.classList.add('expanded');
  } else {
    section.style.display = 'none';
    btn.classList.remove('expanded');
  }
}

function showPreview(metaphorId) {
  fetchMetaphorContent(metaphorId, false);
}

function readFull(metaphorId) {
  window.location.href = `/metaphors/${metaphorId}`;
}

async function fetchMetaphorContent(metaphorId, isFullAccess) {
  try {
    const response = await fetch(`/api/metaphors/${metaphorId}/content`, {
      headers: AuthManager.getAuthHeaders()
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch content');
    }
    
    const data = await response.json();
    displayMetaphorContent(data);
  } catch (error) {
    console.error('Error fetching metaphor content:', error);
    // Fallback to static content
    const metaphor = metaphors.find(m => m.id === metaphorId);
    if (metaphor) {
      const fallbackData = {
        id: metaphor.id,
        title: metaphor.title,
        content: isFullAccess ? metaphor.full_content : metaphor.preview_content,
        has_access: isFullAccess,
        is_preview: !isFullAccess
      };
      displayMetaphorContent(fallbackData);
    }
  }
}

function displayMetaphorContent(data) {
  const metaphor = metaphors.find(m => m.id === data.id);
  const keywords = metaphor?.keywords ? metaphor.keywords.join(' · ') : '';
  
  let actions = '';
  if (data.has_access) {
    actions = '<button class="btn btn-preview" onclick="closeModal()">Back to Library</button>';
  } else {
    actions = `
      <button class="btn btn-unlock" onclick="unlockMetaphor('${data.id}')">Unlock for $${metaphor?.price || 5}</button>
      <button class="btn btn-preview" onclick="closeModal()">Back to Library</button>
    `;
  }

  const modalContent = `
    <div class="modal-symbol">${metaphor?.symbol || '✦'}</div>
    <h2>${data.title}</h2>
    <div class="modal-keywords">${keywords}</div>
    <div class="modal-preview">${data.content || 'Content coming soon...'}</div>
    <div class="modal-actions">${actions}</div>
  `;

  document.getElementById('modalContent').innerHTML = modalContent;
  document.getElementById('previewModal').classList.add('active');
}

function closeModal() {
  document.getElementById('previewModal').classList.remove('active');
}

async function unlockMetaphor(metaphorId) {
  if (!AuthManager.isLoggedIn()) {
    alert('Please sign in to purchase metaphors.');
    return;
  }

  try {
    const response = await fetch(`/api/purchase/${metaphorId}`, {
      method: 'POST',
      headers: AuthManager.getAuthHeaders()
    });

    const data = await response.json();

    if (response.ok) {
      alert('Purchase successful! You now have access to the full content.');
      closeModal();
      // Reload metaphors to update UI
      await loadMetaphors();
    } else {
      alert(data.error || 'Purchase failed. Please try again.');
    }
  } catch (error) {
    console.error('Purchase error:', error);
    alert('Network error. Please try again later.');
  }
}


async function loadBundles() {
  try {
    const response = await fetch('/api/bundles');
    if (response.ok) {
      const bundles = await response.json();
      renderBundles(bundles);
    }
  } catch (error) {
    console.error('Error loading bundles:', error);
  }
}

function renderBundles(bundles) {
  const bundlesGrid = document.getElementById('bundlesGrid');
  if (!bundles || bundles.length === 0) {
    bundlesGrid.innerHTML = '';
    return;
  }

  bundlesGrid.innerHTML = bundles.map(bundle => {
    const isSubscription = bundle.metaphor_ids.length === 0;
    const originalPrice = isSubscription ? 0 : bundle.metaphor_ids.reduce((sum, id) => {
      const m = metaphors.find(meta => meta.id === id);
      return sum + (m ? parseFloat(m.price) : 0);
    }, 0);

    // Extract emoji and clean name
    const nameMatch = bundle.name.match(/^([📚🎵])\.\s*(.+)/);
    const emoji = nameMatch ? nameMatch[1] : '✦';
    const cleanName = nameMatch ? nameMatch[2] : bundle.name;

    return `
      <div class="metaphor-card bundle-card">
        <div class="bundle-icon">${emoji}</div>
        <h3 class="bundle-title">${cleanName}</h3>
        <div class="bundle-description">${bundle.description}</div>
        <div class="bundle-pricing">
          ${!isSubscription && originalPrice > parseFloat(bundle.price) ? 
            `<span class="original-price">$${originalPrice.toFixed(2)}</span>` : ''}
          <span class="bundle-price">$${parseFloat(bundle.price).toFixed(2)}${isSubscription ? '/mo' : ''}</span>
        </div>
        ${bundle.discount_percent > 0 ? 
          `<div class="bundle-savings">Save ${bundle.discount_percent}%</div>` : ''}
        <button class="btn btn-unlock bundle-btn" onclick="unlockBundle('${bundle.id}')">
          ${isSubscription ? 'Subscribe' : 'Purchase'}
        </button>
      </div>
    `;
  }).join('');
}

async function unlockBundle(bundleId) {
  if (!AuthManager.isLoggedIn()) {
    alert('Please sign in to purchase bundles.');
    return;
  }

  try {
    const response = await fetch(`/api/purchase/bundle/${bundleId}`, {
      method: 'POST',
      headers: AuthManager.getAuthHeaders()
    });

    const data = await response.json();

    if (response.ok) {
      const message = `Bundle purchased successfully!\n\nGranted access to ${data.new_access_count} new metaphors:\n${data.granted_metaphors.join(', ')}\n\n${data.already_owned.length > 0 ? `Already owned: ${data.already_owned.join(', ')}` : ''}`;
      alert(message);
      // Reload metaphors to update UI
      await loadMetaphors();
    } else {
      alert(data.error || 'Bundle purchase failed. Please try again.');
    }
  } catch (error) {
    console.error('Bundle purchase error:', error);
    alert('Network error. Please try again later.');
  }
}
