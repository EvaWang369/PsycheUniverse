// Mode Switch - Toggle between Metaphor Library and Frequency Vault

function setMode(mode) {
  const metaphorMode = document.getElementById('metaphorMode');
  const videoMode = document.getElementById('videoMode');
  const tabMetaphor = document.getElementById('tabMetaphor');
  const tabVideo = document.getElementById('tabVideo');
  const metaphorVisual = document.getElementById('metaphorVisual');
  const frequencyVisual = document.getElementById('frequencyVisual');
  const heroTitle = document.getElementById('heroTitle');
  const heroSubtitle = document.getElementById('heroSubtitle');
  const heroDesc = document.getElementById('heroDesc');

  const isVideo = mode === 'video';

  // Toggle content visibility
  metaphorMode.style.display = isVideo ? 'none' : 'block';
  videoMode.style.display = isVideo ? 'block' : 'none';

  // Toggle tab active states
  tabMetaphor.classList.toggle('active', !isVideo);
  tabVideo.classList.toggle('active', isVideo);
  tabMetaphor.setAttribute('aria-selected', String(!isVideo));
  tabVideo.setAttribute('aria-selected', String(isVideo));

  // Toggle hero visuals
  metaphorVisual.classList.toggle('hidden', isVideo);
  frequencyVisual.classList.toggle('hidden', !isVideo);

  // Update hero text
  if (isVideo) {
    heroTitle.textContent = 'FREQUENCY VAULT';
    heroSubtitle.textContent = 'High-Frequency Visual Sessions';
    heroDesc.innerHTML = 'Immersive sound experiences.<br>Tune into clarity, calm, and connection.';
  } else {
    heroTitle.textContent = 'METAPHOR LIBRARY';
    heroSubtitle.textContent = 'Reality, Seen Through Lenses';
    heroDesc.innerHTML = 'One Law. Many Reflections.<br>They help you understand the law, faster.';
  }

  // Update URL hash
  history.replaceState(null, '', isVideo ? '#vault' : '#metaphors');

  // Load frequency videos if switching to video mode
  if (isVideo && typeof renderFrequencyVideos === 'function') {
    renderFrequencyVideos();
  }
}

function initModeFromHash() {
  const hash = location.hash;
  if (hash === '#vault') {
    setMode('video');
  } else {
    setMode('metaphor');
  }
}
