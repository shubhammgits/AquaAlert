let _stream = null;
let _capturedDataUrl = "";

function _isLocalhostHost(hostname) {
  const h = String(hostname || "").toLowerCase();
  return h === "localhost" || h === "127.0.0.1";
}

function _cameraBlockedByInsecureOrigin() {
  // Most browsers require HTTPS for camera, except localhost/127.0.0.1.
  try {
    const { protocol, hostname } = window.location;
    if (protocol === "https:") return false;
    return !_isLocalhostHost(hostname);
  } catch {
    return !window.isSecureContext;
  }
}

async function initCamera() {
  const video = document.getElementById("video");
  const captureBtn = document.getElementById("captureBtn");
  const submitBtn = document.getElementById("submitBtn");
  const msg = document.getElementById("reportMsg");
  if (!video || !captureBtn || !submitBtn) return;

  msg.textContent = "";

  // iOS/Safari autoplay policies: muted video is more likely to start.
  try {
    video.muted = true;
    video.setAttribute("muted", "");
    video.setAttribute("playsinline", "");
  } catch {
    // ignore
  }

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    msg.textContent = "Camera API not available in this browser. Open in Chrome/Edge on https or localhost.";
    return;
  }

  async function startCamera() {
    msg.textContent = "";

    if (_cameraBlockedByInsecureOrigin()) {
      // Warn, but still attempt: some environments/devices may allow it.
      msg.textContent = `Camera may be blocked on insecure URL: ${window.location.origin}. Prefer https://, or open on this PC via http://localhost:8000 or http://127.0.0.1:8000 (not a LAN IP).`;
    }

    try {
      _stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: "environment" } },
        audio: false,
      });
      video.srcObject = _stream;

      // Some browsers require an explicit play().
      try {
        await video.play();
      } catch {
        // If play() is blocked by gesture policy, the stream may still be live.
      }

      // Don't hang startup waiting for metadata; race with a short timeout.
      await Promise.race([
        new Promise((resolve) => {
          if (video.videoWidth && video.videoHeight) return resolve(true);
          const done = () => {
            video.removeEventListener("loadedmetadata", done);
            resolve(true);
          };
          video.addEventListener("loadedmetadata", done);
        }),
        new Promise((resolve) => setTimeout(resolve, 1500)),
      ]);

      return true;
    } catch (err) {
      console.error("getUserMedia failed:", err);
      const name = (err && err.name) || "Error";
      const isVSCode = /vscode/i.test(navigator.userAgent || "");
      const hint =
        name === "NotAllowedError"
          ? " Allow camera permission in the browser/site settings."
          : name === "NotFoundError"
          ? " No camera device found."
          : "";
      const originHint = !window.isSecureContext ? " Use https:// or localhost." : "";
      const vscodeHint = isVSCode ? " VS Code Simple Browser often blocks camera; use Chrome/Edge." : "";
      msg.textContent = `Camera not available: ${name}.${hint}${originHint}${vscodeHint}`;
      return false;
    }
  }

  await startCamera();

  captureBtn.addEventListener("click", () => {
    // If camera didn't start due to gesture/permissions, let Capture also act as a retry.
    if (!_stream || !video.srcObject) {
      msg.textContent = "Starting camera...";
      startCamera().then((ok) => {
        if (ok) msg.textContent = "Camera ready. Tap Capture again.";
      });
      return;
    }
    const canvas = document.getElementById("canvas");
    const w = video.videoWidth || 720;
    const h = video.videoHeight || 960;
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, w, h);
    _capturedDataUrl = canvas.toDataURL("image/jpeg", 0.85);
    msg.textContent = "Captured. Tap Submit Report.";
  });

  submitBtn.addEventListener("click", submitReport);

  window.addEventListener("beforeunload", () => {
    try {
      if (_stream) {
        _stream.getTracks().forEach((t) => t.stop());
      }
    } catch {
      // ignore
    }
  });
}

function getCurrentPosition() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error("Geolocation not supported"));
      return;
    }
    navigator.geolocation.getCurrentPosition(resolve, reject, {
      enableHighAccuracy: true,
      timeout: 15000,
      maximumAge: 0,
    });
  });
}

async function submitReport() {
  const msg = document.getElementById("reportMsg");
  msg.textContent = "";
  if (!_capturedDataUrl) {
    msg.textContent = "Capture an image first.";
    return;
  }

  const district = (document.getElementById("district").value || "").trim();
  const state = ((document.getElementById("state") || {}).value || "").trim();
  const city = ((document.getElementById("city") || {}).value || "").trim();
  const contact_phone = (document.getElementById("contactPhone").value || "").trim();
  if (!district || district.length < 2) {
    msg.textContent = "Please enter your district/area.";
    return;
  }
  if (!contact_phone || contact_phone.length < 6) {
    msg.textContent = "Please enter a valid contact number.";
    return;
  }

  let pos;
  try {
    pos = await getCurrentPosition();
  } catch {
    msg.textContent = "Unable to get GPS location.";
    return;
  }

  const { latitude, longitude, accuracy } = pos.coords;
  if (accuracy > 100) {
    msg.textContent = "GPS accuracy is too low (>100m). Move to open area and try again.";
    return;
  }

  const description = (document.getElementById("desc").value || "").trim();
  const payload = {
    latitude,
    longitude,
    accuracy,
    timestamp: pos.timestamp,
    district,
    state,
    city,
    contact_phone,
    description,
    image_base64: _capturedDataUrl,
  };

  try {
    msg.textContent = "Submitting...";
    await API.request("/reports", { method: "POST", body: payload, auth: true });
    msg.textContent = "Report submitted.";
    _capturedDataUrl = "";
    document.getElementById("desc").value = "";
    // keep district/phone for convenience
    await refreshMyReports();
    await refreshClustersOnMap();
    await refreshValidationCandidates();
  } catch (err) {
    msg.textContent = err.message;
  }
}

async function refreshMyReports() {
  const holder = document.getElementById("myReports");
  if (!holder) return;
  holder.innerHTML = "";
  
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
    if (r.status === "submitted") return "Pending supervisor acceptance";
    if (r.status === "accepted") return "Accepted — pending worker assignment";
    if (r.status === "assigned") return "Worker assigned — work in progress";
    if (r.status === "completed") return "Completed by worker — awaiting supervisor verification";
    if (r.status === "closed") return "Resolved";
    return r.status || "";
  }

  try {
    const reports = await API.request("/reports/me");
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
            <span class="pill">${r.status}</span>
            <span class="muted">${new Date(r.created_at).toLocaleString()}</span>
          </div>
          <div class="muted">District: ${escapeHtml(r.district || "")}</div>
          <div class="muted">${escapeHtml(r.description || "")}</div>
          ${
            r.assigned_worker
              ? `<div class="muted">Assigned worker: ${escapeHtml(r.assigned_worker.name || "")} (ID: ${r.assigned_worker.id})</div>`
              : ""
          }
          ${
            r.expected_completion_at
              ? `<div class="muted">ETA: ${new Date(r.expected_completion_at).toLocaleString()}</div>`
              : ""
          }
          <div class="muted">${escapeHtml(statusHint(r))}</div>
          ${renderProgress(r.status)}
          ${r.resolution_message ? `<div class="muted">${escapeHtml(r.resolution_message)}</div>` : ""}
          <div class="actions">
            <a class="btn btn-secondary" href="${r.image_url}" target="_blank" rel="noreferrer">View Image</a>
            ${
              r.qr_url
                ? `<a class="btn btn-secondary" href="${r.qr_url}" target="_blank" rel="noreferrer">View QR</a>`
                : ""
            }
            ${
              r.completion_image_url
                ? `<a class="btn btn-secondary" href="${r.completion_image_url}" target="_blank" rel="noreferrer">View Completion Photo</a>`
                : ""
            }
          </div>
          <details>
            <summary class="muted">AI analysis</summary>
            <div class="muted">Problem: ${escapeHtml((r.ai.problem || []).join(", "))}</div>
            <div class="muted">Causes: ${escapeHtml((r.ai.causes || []).join(", "))}</div>
            <div class="muted">Precautions: ${escapeHtml((r.ai.precautions || []).join(", "))}</div>
            <div class="muted">Prevention: ${escapeHtml((r.ai.prevention || []).join(", "))}</div>
          </details>
        </div>
      `
      )
      .join("");
  } catch (err) {
    holder.innerHTML = `<div class="muted">${escapeHtml(err.message)}</div>`;
  }
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
