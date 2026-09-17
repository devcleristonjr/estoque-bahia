(() => {
  const mapElement = document.getElementById('leaflet-map');
  if (!mapElement || typeof L === 'undefined') {
    return;
  }

  const map = L.map('leaflet-map', {
    maxBounds: [[-18.75, -46.5], [-8.0, -37.0]],
    maxBoundsViscosity: 1.0,
    minZoom: 6,
  }).setView([-12.8, -41.7], 7);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18,
    attribution: '&copy; OpenStreetMap contributors',
  }).addTo(map);

  const markerLayer = L.layerGroup().addTo(map);
  const totalPontosEl = document.getElementById('map-total-pontos');
  const totalBannersEl = document.getElementById('map-total-banners');

  const filters = {
    territorio_id: document.getElementById('filter-territorio'),
    municipio_id: document.getElementById('filter-municipio'),
    material_id: document.getElementById('filter-material'),
    status: document.getElementById('filter-status'),
  };

  function getQueryString() {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, element]) => {
      if (element && element.value) {
        params.set(key, element.value);
      }
    });
    return params.toString();
  }

  function escapeHtml(value) {
    return String(value || '')
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
  }

  async function refreshMap() {
    const response = await fetch(`/api/mapa?${getQueryString()}`, {
      headers: { Accept: 'application/json' },
    });
    const points = await response.json();

    markerLayer.clearLayers();
    let totalBanners = 0;
    const bounds = [];
    const duplicateCounts = new Map();

    points.forEach((point) => {
      totalBanners += Number(point.total_banners || 0);
      bounds.push([point.latitude, point.longitude]);

      const coordinateKey = `${point.latitude}:${point.longitude}`;
      const duplicateIndex = duplicateCounts.get(coordinateKey) || 0;
      duplicateCounts.set(coordinateKey, duplicateIndex + 1);

      const markerOffset = duplicateIndex * 0.00022;
      const lat = point.latitude + ((duplicateIndex % 2 === 0 ? 1 : -1) * markerOffset);
      const lng = point.longitude + ((duplicateIndex % 3 === 0 ? 1 : -1) * markerOffset * 1.2);

      const popupHtml = `
        <div class="p-1" style="min-width: 240px; max-width: 300px;">
          <div class="fw-bold mb-1">${escapeHtml(point.nome)}</div>
          <div class="small text-muted mb-2">${escapeHtml(point.municipio)} • ${escapeHtml(point.territorio)}</div>
          <div class="mb-2"><strong>Banners:</strong> ${Number(point.total_banners || 0)}</div>
          <div class="mb-2"><strong>Responsável:</strong> ${escapeHtml(point.responsavel_nome || '-')}</div>
          ${point.foto ? `<div class="mb-2"><img src="/${escapeHtml(point.foto)}" alt="Foto" style="width:100%;height:140px;object-fit:cover;border-radius:12px;"></div>` : ''}
          <div class="d-grid gap-2">
            ${point.whatsapp_url ? `<a class="btn btn-success btn-sm" target="_blank" rel="noopener noreferrer" href="${escapeHtml(point.whatsapp_url)}">💬 Falar no WhatsApp</a>` : ''}
            <a class="btn btn-outline-primary btn-sm" href="${escapeHtml(point.detail_url)}">Ver detalhes</a>
          </div>
        </div>
      `;
      L.marker([lat, lng]).addTo(markerLayer).bindPopup(popupHtml);
    });

    if (totalPontosEl) totalPontosEl.textContent = String(points.length);
    if (totalBannersEl) totalBannersEl.textContent = String(Math.round(totalBanners));

    if (bounds.length > 0) {
      map.fitBounds(bounds, { padding: [30, 30] });
    } else {
      map.setView([-12.8, -41.7], 7);
    }
  }

  Object.values(filters).forEach((element) => {
    if (element) {
      element.addEventListener('change', refreshMap);
    }
  });

  const button = document.getElementById('map-filter-button');
  if (button) {
    button.addEventListener('click', refreshMap);
  }

  refreshMap().catch((error) => {
    console.error(error);
  });
})();
