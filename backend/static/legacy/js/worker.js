let _workerStream = null;
let _workerCaptured = "";
let _locTimer = null;

let _assignedCache = [];
let _historyCache = [];

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function initWorker() {
  await initWorkerCamera();
  startLocationPings();
  await refreshAssigned();
  await refreshHistory();
  renderRightHistory();
}

function fmtDateShort(iso) {
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return "";
    return d.toLocaleDateString(undefined, { day: "2-digit", month: "short", year: "numeric" });
  } catch {
    return "";
  }
}

function badgeForStatus(status) {
  const s = String(status || "").toLowerCase();
  if (s === "closed") return { cls: "badge--completed", label: "Completed" };
  if (s === "completed") return { cls: "badge--progress", label: "In Progress" };
  if (s === "assigned") return { cls: "badge--assigned", label: "Assigned" };
  if (s === "rejected") return { cls: "badge--critical", label: "Needs Action" };
  return { cls: "badge--pending", label: "Pending" };
}

function goToCompletion(reportId) {
  try {
    const sel = document.getElementById("reportSelect");
    if (sel && reportId) sel.value = String(reportId);
    window.location.hash = "#completion";
  } catch {
    // ignore
  }
}

function startLocationPings() {
  // Ping immediately, then periodically. Silent failures (GPS off, permissions, etc).
  if (_locTimer) clearInterval(_locTimer);
  pingWorkerLocation();
  _locTimer = setInterval(pingWorkerLocation, 30000);
  window.addEventListener("beforeunload", () => {
    if (_locTimer) clearInterval(_locTimer);
  });
}

async function pingWorkerLocation() {
  try {
    const pos = await getCurrentPositionWorker();
    const { latitude, longitude, accuracy } = pos.coords;
    if (accuracy > 100) return;
    await API.request("/workers/location", {
      method: "POST",
      body: { latitude, longitude, accuracy, timestamp: pos.timestamp },
      auth: true,
    });
  } catch {
    // ignore
  }
}

async function initWorkerCamera() {
  const video = document.getElementById("video");
  const captureBtn = document.getElementById("captureBtn");
  const submitBtn = document.getElementById("submitCompletionBtn");
  const msg = document.getElementById("workerMsg");

  msg.textContent = "";
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    msg.textContent = "Camera API not available in this browser. Open in Chrome/Edge on https or localhost.";
    return;
  }
  if (!window.isSecureContext) {
    msg.textContent =
      "Camera requires a secure context. Use https://, or open via http://localhost:8000 or http://127.0.0.1:8000 (not a LAN IP).";
  }
  try {
    _workerStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: { ideal: "environment" } },
      audio: false,
    });
    video.srcObject = _workerStream;
  } catch {
    msg.textContent =
      "Camera permission denied or unavailable. Tip: use https:// or http://localhost:8000 / 127.0.0.1; VS Code Simple Browser often blocks camera.";
    return;
  }

  captureBtn.addEventListener("click", () => {
    const canvas = document.getElementById("canvas");
    const w = video.videoWidth || 720;
    const h = video.videoHeight || 960;
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, w, h);
    _workerCaptured = canvas.toDataURL("image/jpeg", 0.85);
    msg.textContent = "Captured. Tap Send to Supervisor.";
  });

  submitBtn.addEventListener("click", submitCompletion);
}

async function refreshHistory() {
  const holder = document.getElementById("historyList");
  if (!holder) return;
  holder.innerHTML = "";

  let rows = [];
  try {
    rows = await API.request("/reports/history");
  } catch (err) {
    holder.innerHTML = `<div class="muted">${escapeHtml(err.message)}</div>`;
    return;
  }

  if (!rows.length) {
    holder.innerHTML = `<div class="empty-state">No verified completions yet.</div>`;
    _historyCache = [];
    renderRightHistory();
    return;
  }

  _historyCache = rows;
  renderRightHistory();

  holder.innerHTML = rows
    .map((r) => {
      const verifiedAt = r.completion_verified_at
        ? new Date(r.completion_verified_at).toLocaleString()
        : r.completed_at
        ? new Date(r.completed_at).toLocaleString()
        : "";

      const actions = [];
      if (r.completion_image_url) {
        actions.push(
          `<a class="btn btn-secondary" href="${r.completion_image_url}" target="_blank" rel="noreferrer">View Completion Photo</a>`
        );
      }
      actions.push(
          `<a class="btn btn-secondary" href="https://www.google.com/maps?q=${r.latitude},${r.longitude}" target="_blank" rel="noreferrer">Open in Maps</a>`
        );

        return `
          <div class="item">
            <div class="row">
              <span class="pill">${escapeHtml(r.severity)}</span>
              <span class="badge badge--completed">Completed</span>
              <span class="muted">Report #${r.id}</span>
            </div>
            ${verifiedAt ? `<div class="muted">Verified: ${escapeHtml(verifiedAt)}</div>` : ""}
            <div class="muted">District: ${escapeHtml(r.district || "")}</div>
            ${r.resolution_message ? `<div class="muted">${escapeHtml(r.resolution_message)}</div>` : ""}
            <div class="actions">${actions.join("")}</div>
          </div>
        `;
      })
      .join("");
  }

function getCurrentPositionWorker() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) reject(new Error("no geo"));
    navigator.geolocation.getCurrentPosition(resolve, reject, {
      enableHighAccuracy: true,
      timeout: 15000,
      maximumAge: 0,
    });
  });
}

async function refreshAssigned() {
  const list = document.getElementById("assignedList");
  const select = document.getElementById("reportSelect");
  list.innerHTML = "";
  select.innerHTML = "";

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
    if (r.status === "assigned") {
      if (r.resolution_message && String(r.resolution_message).trim()) {
        return "Rejected — resubmit completion photo";
      }
      return "Assigned to you — in progress";
    }
    if (r.status === "completed") return "Submitted completion — awaiting verification";
    if (r.status === "closed") return "Resolved";
    return r.status || "";
  }

  let reports = [];
  try {
    reports = await API.request("/reports/assigned");
  } catch (err) {
    list.innerHTML = `<div class="muted">${escapeHtml(err.message)}</div>`;
    return;
  }

  if (!reports.length) {
    list.innerHTML = `<div class="empty-state">No assigned tasks right now.</div>`;
    _assignedCache = [];
    renderRightHistory();
    return;
  }

  _assignedCache = reports;
  renderRightHistory();

  reports.forEach((r) => {
    const opt = document.createElement("option");
    opt.value = r.id;
    opt.textContent = `#${r.id} • ${r.district} • ${r.status}`;
    select.appendChild(opt);
  });

  list.innerHTML = reports
    .map(
      (r) => {
        const badge = badgeForStatus(r.status);
        return `
          <div class="item">
            <div class="row">
              <span class="pill">${escapeHtml(r.severity)}</span>
              <span class="badge ${badge.cls}">${badge.label}</span>
              <span class="muted">Report #${escapeHtml(r.id)}</span>
            </div>
            <div class="muted">${escapeHtml(statusHint(r))}</div>
            ${renderProgress(r.status)}
            <div class="muted">District: ${escapeHtml(r.district || "")}</div>
            <div class="muted">Contact: ${escapeHtml(r.contact_phone || "")}</div>
            ${r.resolution_message ? `<div class="muted">${escapeHtml(r.resolution_message)}</div>` : ""}
            <div class="actions">
              <a class="btn btn-secondary" href="https://www.google.com/maps?q=${r.latitude},${r.longitude}" target="_blank" rel="noreferrer">Open Map</a>
              <button class="btn" type="button" onclick="goToCompletion(${Number(r.id) || 0})">Submit Completion</button>
            </div>
          </div>
        `;
      }
    )
    .join("");
}

function renderRightHistory() {
  const root = document.getElementById("rightHistory");
  if (!root) return;

  const combined = [];
  _assignedCache.forEach((r) => combined.push({ kind: "assigned", r }));
  _historyCache.forEach((r) => combined.push({ kind: "history", r }));

  if (!combined.length) {
    root.innerHTML = `<div class="empty-state">No previous reports yet.</div>`;
    return;
  }

  root.innerHTML = combined
    .slice(0, 20)
    .map(({ kind, r }) => {
      const id = escapeHtml(r.id || "");
      const title = `R-${id}`;
      const date = fmtDateShort(r.created_at || r.completed_at || r.completion_verified_at);
      const loc = escapeHtml(r.district || "");
      const meta = [date, loc].filter(Boolean).join(" • ");

      const badge = badgeForStatus(kind === "history" ? "closed" : r.status);

      const actions = [];
      actions.push(
        `<a class="btn btn-secondary" href="https://www.google.com/maps?q=${r.latitude},${r.longitude}" target="_blank" rel="noreferrer">Open Map</a>`
      );
      if (r.completion_image_url) {
        actions.push(
          `<a class="btn btn-secondary" href="${r.completion_image_url}" target="_blank" rel="noreferrer">Completion Photo</a>`
        );
      }
      if (kind !== "history") {
        actions.push(`<button class="btn" type="button" onclick="goToCompletion(${Number(r.id) || 0})">Submit</button>`);
      }

      const bodyBits = [];
      bodyBits.push(`<div class="muted">Severity: ${escapeHtml(r.severity || "")}</div>`);
      if (r.resolution_message) bodyBits.push(`<div class="muted">${escapeHtml(r.resolution_message)}</div>`);

      return `
        <div class="hitem" data-hitem>
          <button class="hitem__head" type="button" data-hitem-toggle>
            <div>
              <div class="hitem__title">${title}</div>
              <div class="hitem__meta">${meta}</div>
            </div>
            <span class="badge ${badge.cls}">${badge.label}</span>
          </button>
          <div class="hitem__body" data-hitem-body>
            <div class="hitem__bodyInner">
              ${bodyBits.join("")}
              <div class="actions">${actions.join("")}</div>
            </div>
          </div>
        </div>
      `;
    })
    .join("");

  wireHistoryToggles(root);
}

function wireHistoryToggles(root) {
  if (!root) return;
  const items = root.querySelectorAll("[data-hitem]");
  items.forEach((item) => {
    const btn = item.querySelector("[data-hitem-toggle]");
    const body = item.querySelector("[data-hitem-body]");
    if (!btn || !body) return;
    btn.addEventListener("click", () => {
      const isOpen = item.classList.toggle("is-open");
      if (isOpen) {
        body.style.maxHeight = body.scrollHeight + "px";
      } else {
        body.style.maxHeight = "0px";
      }
    });
  });
}

async function submitCompletion() {
  const msg = document.getElementById("workerMsg");
  msg.textContent = "";
  const reportId = Number(document.getElementById("reportSelect").value || 0);
  if (!reportId) {
    msg.textContent = "Select a report first.";
    return;
  }
  if (!_workerCaptured) {
    msg.textContent = "Capture an image first.";
    return;
  }

  let pos;
  try {
    pos = await getCurrentPositionWorker();
  } catch {
    msg.textContent = "Unable to get GPS location.";
    return;
  }

  const { latitude, longitude, accuracy } = pos.coords;
  if (accuracy > 100) {
    msg.textContent = "GPS accuracy is too low (>100m).";
    return;
  }

  const payload = {
    latitude,
    longitude,
    accuracy,
    timestamp: pos.timestamp,
    image_base64: _workerCaptured,
  };

  try {
    msg.textContent = "Sending...";
    await API.request(`/reports/${reportId}/complete`, { method: "POST", body: payload, auth: true });
    msg.textContent = "Sent to supervisor for verification.";
    _workerCaptured = "";
    await refreshAssigned();
  } catch (err) {
    msg.textContent = err.message;
  }
}
