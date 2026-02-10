// Metaphor UI Functions

let metaphors = METAPHOR_CATALOG.slice();
let userPurchases = [];

async function loadMetaphors() {
  try {
    metaphors = METAPHOR_CATALOG
      .slice()
      .sort((a, b) => (a.order_index ?? 9999) - (b.order_index ?? 9999));

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
      <button class="btn btn-unlock" onclick="unlockMetaphor('${metaphor.id}')">Unlock $${metaphor.price}</button>
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
  const metaphor = metaphors.find(m => m.id === metaphorId);
  if (!metaphor) return;

  const keywords = metaphor.keywords ? metaphor.keywords.join(' · ') : '';
  const modalContent = `
    <div class="modal-symbol">${metaphor.symbol || '✦'}</div>
    <h2>${metaphor.title}</h2>
    <div class="modal-keywords">${keywords}</div>
    <div class="modal-preview">${metaphor.preview_content || 'Preview content coming soon...'}</div>
    <div class="modal-actions">
      <button class="btn btn-unlock" onclick="unlockMetaphor('${metaphor.id}')">Unlock for $${metaphor.price}</button>
      <button class="btn btn-preview" onclick="closeModal()">Back to Library</button>
    </div>
  `;

  document.getElementById('modalContent').innerHTML = modalContent;
  document.getElementById('previewModal').classList.add('active');
}

function closeModal() {
  document.getElementById('previewModal').classList.remove('active');
}

function readFull(metaphorId) {
  const metaphor = metaphors.find(m => m.id === metaphorId);
  if (!metaphor) return;

  const keywords = metaphor.keywords ? metaphor.keywords.join(' · ') : '';
  const modalContent = `
    <div class="modal-symbol">${metaphor.symbol || '✦'}</div>
    <h2>${metaphor.title}</h2>
    <div class="modal-keywords">${keywords}</div>
    <div class="modal-preview">${metaphor.full_content || 'Full content coming soon...'}</div>
    <div class="modal-actions">
      <button class="btn btn-preview" onclick="closeModal()">Back to Library</button>
    </div>
  `;

  document.getElementById('modalContent').innerHTML = modalContent;
  document.getElementById('previewModal').classList.add('active');
}

function unlockMetaphor(metaphorId) {
  alert(`Stripe checkout for ${metaphorId} coming soon!`);
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
      return sum + (m ? m.price : 0);
    }, 0);

    // Extract emoji and clean name
    const nameMatch = bundle.name.match(/^([📚🎵])\.s*(.+)/);
    const emoji = nameMatch ? nameMatch[1] : '✦';
    const cleanName = nameMatch ? nameMatch[2] : bundle.name;

    return `
      <div class="metaphor-card bundle-card">
        <div class="bundle-icon">${emoji}</div>
        <h3 class="bundle-title">${cleanName}</h3>
        <div class="bundle-description">${bundle.description}</div>
        <div class="bundle-pricing">
          ${!isSubscription && originalPrice > bundle.price ? 
            `<span class="original-price">$${originalPrice.toFixed(2)}</span>` : ''}
          <span class="bundle-price">$${bundle.price.toFixed(2)}${isSubscription ? '/mo' : ''}</span>
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

function unlockBundle(bundleId) {
  alert(`Stripe checkout for bundle ${bundleId} coming soon!`);
}
