const topViews = document.querySelector('#topViews');
const topViewsUpdated = document.querySelector('#topViewsUpdated');

const escapeHTML = (value) => String(value).replace(/[&<>'"]/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' })[character]);
const formatViews = (views) => new Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 1 }).format(Number(views || 0));
const safeUrl = (value, prefix) => String(value || '').startsWith(prefix) ? value : '';

const showUnavailable = () => {
  if (!topViews) return;
  topViews.innerHTML = '<p class="top-views-loading">TOP VIEWS ARE REFRESHING. PLEASE CHECK BACK SOON.</p>';
};

const renderTopViews = (payload) => {
  if (!topViews || !Array.isArray(payload.videos) || payload.videos.length === 0) {
    showUnavailable();
    return;
  }

  topViews.innerHTML = payload.videos.slice(0, 3).map((video, index) => {
    const url = safeUrl(video.url, 'https://www.youtube.com/watch') || 'https://www.youtube.com/@tinuttslOfficial';
    const thumbnail = safeUrl(video.thumbnail, 'https://') || '';
    const image = thumbnail ? `<img src="${escapeHTML(thumbnail)}" alt="" />` : '';
    return `<a class="top-view-card" href="${escapeHTML(url)}" target="_blank" rel="noreferrer"><span class="top-view-rank">${index + 1}</span>${image}<h3>${escapeHTML(video.title)}</h3><p>${formatViews(video.views)} VIEWS ↗</p></a>`;
  }).join('');

  if (topViewsUpdated && payload.generated_at) {
    const updated = new Date(payload.generated_at);
    if (!Number.isNaN(updated.valueOf())) topViewsUpdated.textContent = `UPDATED ${updated.toLocaleString()}`;
  }
};

if (topViews) {
  fetch(`top-views.json?refresh=${Date.now()}`, { cache: 'no-store' })
    .then((response) => response.ok ? response.json() : Promise.reject(new Error('Top views unavailable')))
    .then(renderTopViews)
    .catch(showUnavailable);
}
