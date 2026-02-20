let _leafletMap = null;
let _markersLayer = null;

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function severityColor(sev) {
  if (sev === "High") return "#ff3b30";
  if (sev === "Medium") return "#ff9500";
  return "#34c759";
}

async function initClusterMap(elementId, { withPriorityList = false } = {}) {
  const el = document.getElementById(elementId);
  if (!el) return;

  _leafletMap = L.map(el);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap",
  }).addTo(_leafletMap);

  _markersLayer = L.layerGroup().addTo(_leafletMap);

  let center = [20.5937, 78.9629];
  let zoom = 5;
  try {
    const pos = await new Promise((resolve, reject) => {
      if (!navigator.geolocation) reject(new Error("no geo"));
      navigator.geolocation.getCurrentPosition(resolve, reject, { enableHighAccuracy: true, timeout: 6000 });
    });
    center = [pos.coords.latitude, pos.coords.longitude];
    zoom = 13;
  } catch {}

  _leafletMap.setView(center, zoom);
  await refreshClustersOnMap(withPriorityList);
}

async function refreshClustersOnMap(withPriorityList = false) {
  if (!_leafletMap || !_markersLayer) return;
  _markersLayer.clearLayers();

  const clusters = await API.request("/clusters");
  clusters.forEach((c) => {
    const color = severityColor(c.severity);
    const marker = L.circleMarker([c.latitude, c.longitude], {
      radius: 10,
      color,
      fillColor: color,
      fillOpacity: 0.65,
      weight: 2,
    }).bindPopup(
      `<b>Cluster</b>: ${c.cluster_id}<br/>` +
        `<b>Reports</b>: ${c.report_count}<br/>` +
        `<b>Severity</b>: ${c.severity}<br/>` +
        `<b>Priority</b>: ${c.priority}`
    );
    marker.addTo(_markersLayer);
  });

  if (withPriorityList) {
    const list = document.getElementById("clusterList");
    if (list) {
      list.innerHTML = clusters
        .map(
          (c) => `
          <div class="item">
            <div class="row">
              <span class="pill">${c.severity}</span>
              <span class="pill">Priority: ${c.priority}</span>
              <span class="pill">Reports: ${c.report_count}</span>
            </div>
            <div class="muted">${c.cluster_id}</div>
            <div class="actions">
              <a class="btn btn-secondary" href="https://www.google.com/maps?q=${c.latitude},${c.longitude}" target="_blank" rel="noreferrer">Open in Maps</a>
            </div>
          </div>
        `
        )
        .join("");
    }
  }
}

async function refreshSupervisorViews() {
  const holder = document.getElementById("allReports");
  if (!holder) return;
  holder.innerHTML = "";
  try {
    const reports = await API.request("/reports");
    if (!reports.length) {
      holder.innerHTML = `<div class="muted">No reports yet.</div>`;
      return;
    }
    holder.innerHTML = reports
      .map(
        (r) => `
        <div class="item">
          <div class="row">
            <span class="pill">${r.severity}</span>
            <span class="muted">${new Date(r.created_at).toLocaleString()}</span>
          </div>
          <div class="muted">Cluster: ${r.cluster_id}</div>
          <div class="muted">${escapeHtml((r.description || "").slice(0, 180))}</div>
          <div class="actions">
            <a class="btn btn-secondary" href="${r.qr_url}" target="_blank" rel="noreferrer">QR Code</a>
            <a class="btn btn-secondary" href="https://www.google.com/maps?q=${r.latitude},${r.longitude}" target="_blank" rel="noreferrer">Open in Maps</a>
          </div>
        </div>
      `
      )
      .join("");
  } catch (err) {
    holder.innerHTML = `<div class="muted">${escapeHtml(err.message)}</div>`;
  }
}
