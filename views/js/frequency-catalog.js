// Frequency Vault - Video catalog and rendering

const FREQUENCY_CATALOG = [
  {
    id: "528hz-clarity",
    title: "528Hz · Clarity Session",
    subtitle: "DNA repair frequency · Inner peace",
    duration: "15:00",
    videoUrl: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    status: "available"
  },
  {
    id: "432hz-calm",
    title: "432Hz · Deep Calm",
    subtitle: "Natural harmony · Grounding",
    duration: "20:00",
    videoUrl: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    status: "available"
  },
  {
    id: "639hz-connection",
    title: "639Hz · Heart Opening",
    subtitle: "Connection frequency · Love",
    duration: "18:00",
    videoUrl: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    status: "available"
  },
  {
    id: "741hz-awakening",
    title: "741Hz · Awakening",
    subtitle: "Intuition expansion · Clarity",
    duration: "12:00",
    videoUrl: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    status: "coming_soon"
  },
  {
    id: "852hz-spiritual",
    title: "852Hz · Third Eye",
    subtitle: "Spiritual activation · Vision",
    duration: "25:00",
    videoUrl: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    status: "coming_soon"
  },
  {
    id: "963hz-divine",
    title: "963Hz · Divine Connection",
    subtitle: "Crown chakra · Oneness",
    duration: "30:00",
    videoUrl: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    status: "coming_soon"
  }
];

function renderFrequencyVideos() {
  const grid = document.getElementById('frequencyGrid');
  if (!grid) return;

  grid.innerHTML = '';

  FREQUENCY_CATALOG.forEach(video => {
    const isComingSoon = video.status === 'coming_soon';

    const card = document.createElement('div');
    card.className = 'video-card';

    card.innerHTML = `
      <div class="video-card-poster">
        <span class="play-badge">${isComingSoon ? '◇' : '▶'}</span>
      </div>
      <div class="video-card-info">
        <h3>${video.title}</h3>
        <p>${video.subtitle}</p>
        ${isComingSoon
          ? '<span class="status-badge status-coming-soon">Coming Soon</span>'
          : `<span class="video-card-duration">${video.duration}</span>
             <div class="video-card-actions">
               <button class="btn btn-preview" onclick="openVideoPreview('${video.title}', '${video.videoUrl}')">Preview</button>
               <a href="#bundles-section" class="btn btn-unlock">Unlock</a>
             </div>`
        }
      </div>
    `;

    grid.appendChild(card);
  });
}

function openVideoPreview(title, embedUrl) {
  const modalContent = document.getElementById('modalContent');

  modalContent.innerHTML = `
    <h2>${title}</h2>
    <p class="modal-keywords">High-frequency visual session</p>
    <div class="modal-video-container">
      <iframe
        src="${embedUrl}?autoplay=0"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowfullscreen>
      </iframe>
    </div>
    <div class="modal-actions">
      <a href="#bundles-section" class="btn btn-unlock" onclick="closeModal()">Unlock All Videos</a>
      <button class="btn btn-preview" onclick="closeModal()">Close</button>
    </div>
  `;

  document.getElementById('previewModal').classList.add('active');
}
