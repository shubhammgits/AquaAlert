let _stream = null;
let _capturedDataUrl = "";

async function initCamera() {
  const video = document.getElementById("video");
  const captureBtn = document.getElementById("captureBtn");
  const submitBtn = document.getElementById("submitBtn");
  const msg = document.getElementById("reportMsg");
  if (!video || !captureBtn || !submitBtn) return;

  msg.textContent = "";

  try {
    _stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: { ideal: "environment" } },
      audio: false,
    });
    video.srcObject = _stream;
  } catch (err) {
    msg.textContent = "Camera permission denied or unavailable.";
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
    _capturedDataUrl = canvas.toDataURL("image/jpeg", 0.85);
    msg.textContent = "Captured. Tap Submit Report.";
  });

  submitBtn.addEventListener("click", submitReport);
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
    description,
    image_base64: _capturedDataUrl,
  };

  try {
    msg.textContent = "Submitting...";
    await API.request("/reports", { method: "POST", body: payload, auth: true });
    msg.textContent = "Report submitted.";
    _capturedDataUrl = "";
    document.getElementById("desc").value = "";
    await refreshMyReports();
    await refreshClustersOnMap();
  } catch (err) {
    msg.textContent = err.message;
  }
}

async function refreshMyReports() {
  const holder = document.getElementById("myReports");
  if (!holder) return;
  holder.innerHTML = "";

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
            <span class="muted">${new Date(r.created_at).toLocaleString()}</span>
          </div>
          <div class="muted">${escapeHtml(r.description || "")}</div>
          <div class="actions">
            <a class="btn btn-secondary" href="${r.image_url}" target="_blank" rel="noreferrer">View Image</a>
            <a class="btn btn-secondary" href="${r.qr_url}" target="_blank" rel="noreferrer">View QR</a>
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
