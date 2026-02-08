// Google Client ID
const GOOGLE_CLIENT_ID = '699830957144-oe51ctmnhtt2bfv866jd4pjjpul43kjh.apps.googleusercontent.com';

// Auth State Management
const AuthManager = {
  SESSION_KEY: 'psyche_session',
  USER_KEY: 'psyche_user',

  getSession() {
    const data = localStorage.getItem(this.SESSION_KEY);
    if (!data) return null;

    const session = JSON.parse(data);
    if (new Date(session.expires_at) < new Date()) {
      this.logout();
      return null;
    }
    return session;
  },

  getUser() {
    const data = localStorage.getItem(this.USER_KEY);
    return data ? JSON.parse(data) : null;
  },

  setAuth(user, session) {
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
    localStorage.setItem(this.SESSION_KEY, JSON.stringify(session));
    this.updateUI();
  },

  logout() {
    const session = this.getSession();
    if (session) {
      fetch('/api/auth/logout', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${session.token}` }
      }).catch(() => {});
    }
    localStorage.removeItem(this.USER_KEY);
    localStorage.removeItem(this.SESSION_KEY);
    this.updateUI();
    closeUserDropdown();
  },

  isLoggedIn() {
    return this.getSession() !== null;
  },

  getVIPLevel() {
    const user = this.getUser();
    return user ? user.vip_level : 'free';
  },

  getAuthHeaders() {
    const session = this.getSession();
    return session ? { 'Authorization': `Bearer ${session.token}` } : {};
  },

  updateUI() {
    const authBtn = document.getElementById('authBtn');
    const userEmail = document.getElementById('userEmail');
    const vipBadge = document.getElementById('vipBadge');
    const user = this.getUser();

    if (user) {
      authBtn.textContent = user.name ? user.name.split(' ')[0] : 'Account';
      userEmail.textContent = user.email;
      const vipLevel = user.vip_level || 'free';
      vipBadge.textContent = vipLevel.toUpperCase();
      vipBadge.className = `vip-badge vip-${vipLevel}`;
    } else {
      authBtn.textContent = 'Sign In';
      userEmail.textContent = '';
      vipBadge.textContent = 'FREE';
      vipBadge.className = 'vip-badge vip-free';
    }
  },

  async refreshUser() {
    const session = this.getSession();
    if (!session) return;

    try {
      const response = await fetch('/api/auth/me', {
        headers: this.getAuthHeaders()
      });

      if (response.ok) {
        const user = await response.json();
        localStorage.setItem(this.USER_KEY, JSON.stringify(user));
        this.updateUI();
      } else if (response.status === 401) {
        this.logout();
      }
    } catch (error) {
      console.error('Failed to refresh user:', error);
    }
  }
};

// Auth UI Functions
function handleAuthClick() {
  if (AuthManager.isLoggedIn()) {
    toggleUserDropdown();
  } else {
    openAuthModal();
  }
}

function openAuthModal() {
  document.getElementById('authModal').classList.add('active');
  initGoogleSignIn();
}

function closeAuthModal() {
  document.getElementById('authModal').classList.remove('active');
}

function toggleUserDropdown() {
  const dropdown = document.getElementById('userDropdown');
  dropdown.classList.toggle('active');
}

function closeUserDropdown() {
  const dropdown = document.getElementById('userDropdown');
  dropdown.classList.remove('active');
}

// Close dropdown when clicking outside
document.addEventListener('click', (e) => {
  const userMenu = document.querySelector('.user-menu');
  if (userMenu && !userMenu.contains(e.target)) {
    closeUserDropdown();
  }
});

// Google Sign-In
function initGoogleSignIn() {
  if (window.google) {
    google.accounts.id.initialize({
      client_id: GOOGLE_CLIENT_ID,
      callback: handleGoogleSignIn,
      auto_select: false,
      cancel_on_tap_outside: true
    });
    google.accounts.id.renderButton(
      document.getElementById('googleSignIn'),
      {
        theme: 'outline',
        size: 'large',
        text: 'signin_with',
        shape: 'pill',
        width: 300
      }
    );
  }
}

async function handleGoogleSignIn(response) {
  try {
    const idToken = response.credential;

    const apiResponse = await fetch('/api/auth/google', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ idToken })
    });

    if (!apiResponse.ok) {
      const error = await apiResponse.json();
      throw new Error(error.error || 'Authentication failed');
    }

    const data = await apiResponse.json();

    AuthManager.setAuth(data.user, data.session);
    closeAuthModal();

    // Reload metaphors with real user purchases
    if (typeof loadMetaphors === 'function') {
      loadMetaphors();
    }

    alert('Welcome to Psyche, ' + (data.user.name || 'friend') + '!');

  } catch (error) {
    console.error('Google Sign-In error:', error);
    alert('Sign-in failed: ' + error.message);
  }
}
