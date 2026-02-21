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

    try {
      if (typeof window.renderSupervisorStats === "function") window.renderSupervisorStats(reports);
      if (typeof window.renderSupervisorRightHistory === "function") window.renderSupervisorRightHistory(reports);
    } catch {
      // ignore UI hooks
    }

    if (!reports.length) {
      holder.innerHTML = `<div class="muted">No reports yet.</div>`;
      return;
    }

    function formatDistance(m) {
      if (m === null || m === undefined) return "";
      const n = Number(m);
      if (!Number.isFinite(n)) return "";
      if (n < 1000) return `${Math.round(n)}m`;
      return `${(n / 1000).toFixed(1)}km`;
    }

    function renderProgress(status) {
      const steps = [
        { key: "submitted", label: "Submitted" },
        { key: "accepted", label: "Accepted" },
        { key: "assigned", label: "Assigned" },
        { key: "completed", label: "Completed" },
        { key: "closed", label: "Closed" },
      ];
      const idx = steps.findIndex((s) => s.key === status);
      const activeIdx = idx >= 0 ? idx : 0;
      return `
        <div class="progress" aria-label="Progress">
          ${steps
            .map((s, i) => `<span class="pill ${i <= activeIdx ? "active" : ""}">${s.label}</span>`)
            .join("")}
        </div>
      `;
    }

    function statusHint(r) {
      const hasWorker = !!(r.assigned_worker && r.assigned_worker.id);
      if (r.status === "submitted") return "Pending acceptance";
      if (r.status === "accepted") return hasWorker ? "Accepted" : "Accepted — pending assignment";
      if (r.status === "assigned") return hasWorker ? "Assigned — in progress" : "Assigned";
      if (r.status === "completed") return "Completed — awaiting verification";
      if (r.status === "closed") return "Resolved";
      return r.status || "";
    }

    async function getWorkersFor(district, lat, lon) {
      const qs = new URLSearchParams();
      if (district) qs.set("district", district);
      qs.set("only_available", "true");
      if (lat !== null && lat !== undefined && lon !== null && lon !== undefined) {
        qs.set("lat", String(lat));
        qs.set("lon", String(lon));
        qs.set("max_age_sec", "900");
      }
      return API.request(`/workers?${qs.toString()}`);
    }

    holder.innerHTML = reports
      .map(
        (r) => `
        <div class="item">
          <div class="row">
            <span class="pill">${r.severity}</span>
            <span class="pill">${r.status}</span>
            <span class="muted">${new Date(r.created_at).toLocaleString()}</span>
          </div>
          <div class="muted">${escapeHtml(statusHint(r))}</div>
          ${renderProgress(r.status)}
          <div class="muted">Cluster: ${r.cluster_id}</div>
          <div class="muted">District: ${escapeHtml(r.district || "")}</div>
          <div class="muted">Contact: ${escapeHtml(r.contact_phone || "")}</div>
          <div class="muted">${escapeHtml((r.description || "").slice(0, 180))}</div>
          ${
            r.assigned_worker
              ? `<div class="muted">Worker: ${escapeHtml(r.assigned_worker.name || "")} (ID: ${r.assigned_worker.id})</div>`
              : `<div class="muted">Worker: Not assigned</div>`
          }
          ${r.resolution_message ? `<div class="muted">${escapeHtml(r.resolution_message)}</div>` : ""}
          <div class="actions">
            <a class="btn btn-secondary" href="${r.image_url}" target="_blank" rel="noreferrer">View Image</a>
            ${
              r.completion_image_url
                ? `<a class="btn btn-secondary" href="${r.completion_image_url}" target="_blank" rel="noreferrer">View Worker Photo</a>`
                : ""
            }
            <a class="btn btn-secondary" href="${r.qr_url}" target="_blank" rel="noreferrer">QR Code</a>
            <a class="btn btn-secondary" href="https://www.google.com/maps?q=${r.latitude},${r.longitude}" target="_blank" rel="noreferrer">Open in Maps</a>
          </div>

          ${
            r.status === "submitted"
              ? `<div class="actions"><button class="btn" type="button" onclick="acceptReport(${r.id})">Accept report</button></div>`
              : ""
          }

          ${
            r.status === "accepted"
              ? `
                <div class="actions">
                  <button class="btn" type="button" onclick="openAssign(${r.id}, '${String(r.district || "").replaceAll("'", "\\'")}', ${r.latitude}, ${r.longitude})">Assign worker</button>
                </div>
              `
              : ""
          }

          <div id="assignBox_${r.id}" class="hidden"></div>
        </div>
      `
      )
      .join("");

    window.acceptReport = async (id) => {
      try {
        await API.request(`/reports/${id}/accept`, { method: "PATCH", body: {}, auth: true });
        await refreshSupervisorViews();
        await refreshClustersOnMap(true);
      } catch (err) {
        alert(err.message);
      }
    };

    window.openAssign = async (id, district, lat, lon) => {
      const box = document.getElementById(`assignBox_${id}`);
      box.classList.remove("hidden");
      box.innerHTML = `<div class="muted">Loading workers...</div>`;
      try {
        const workers = await getWorkersFor(district, lat, lon);
        if (!workers.length) {
          box.innerHTML = `<div class="muted">No available workers in this district.</div>`;
          return;
        }
        const options = workers
          .map((w) => {
            const dist = w.distance_m ? ` • ${formatDistance(w.distance_m)} away` : "";
            return `<option value="${w.id}">${escapeHtml(w.name)} (${escapeHtml(w.phone || "")})${dist}</option>`;
          })
          .join("");
        box.innerHTML = `
          <div class="actions">
            <select class="input" id="workerSel_${id}">${options}</select>
            <input class="input" id="eta_${id}" type="number" min="1" max="168" placeholder="ETA hours" />
            <button class="btn" type="button" onclick="assignReport(${id})">Assign</button>
          </div>
        `;
      } catch (err) {
        box.innerHTML = `<div class="muted">${escapeHtml(err.message)}</div>`;
      }
    };

    window.assignReport = async (id) => {
      const worker_id = Number(document.getElementById(`workerSel_${id}`).value);
      const eta_hours = Number(document.getElementById(`eta_${id}`).value || 0);
      try {
        await API.request(`/reports/${id}/assign`, {
          method: "PATCH",
          body: { worker_id, eta_hours: eta_hours || null, expected_completion_at: null },
          auth: true,
        });
        await refreshSupervisorViews();
      } catch (err) {
        alert(err.message);
      }
    };
  } catch (err) {
    holder.innerHTML = `<div class="muted">${escapeHtml(err.message)}</div>`;
  }
}
