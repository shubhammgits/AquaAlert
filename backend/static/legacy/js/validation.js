async function refreshValidationCandidates() {
  const box = document.getElementById("validationBox");
  if (!box) return;
  box.innerHTML = '<div class="muted">Checking nearby reports...</div>';

  let pos;
  try {
    pos = await new Promise((resolve, reject) => {
      if (!navigator.geolocation) reject(new Error("no geo"));
      navigator.geolocation.getCurrentPosition(resolve, reject, { enableHighAccuracy: true, timeout: 12000 });
    });
  } catch {
    box.innerHTML = '<div class="muted">Enable GPS to verify nearby reports.</div>';
    return;
  }

  try {
    const lat = pos.coords.latitude;
    const lon = pos.coords.longitude;
    const candidates = await API.request(`/validation/nearby?lat=${lat}&lon=${lon}&radius_m=1000`);
    if (!candidates.length) {
      box.innerHTML = '<div class="muted">No nearby verification requests right now.</div>';
      return;
    }

    box.innerHTML = candidates
      .map(
        (c) => `
      <div class="item" data-report-id="${c.report_id}">
        <div class="row">
          <span class="pill">${c.severity}</span>
          <span class="muted">${new Date(c.created_at).toLocaleString()}</span>
        </div>
        <div class="muted">District: ${escapeHtml(c.district || "")}</div>
        <div class="muted">${escapeHtml(c.description || "")}</div>
        <div class="actions">
          <button class="btn" type="button" onclick="voteNearby(${c.report_id}, true)">Yes, it's true</button>
          <button class="btn btn-secondary" type="button" onclick="voteNearby(${c.report_id}, false)">No / not sure</button>
        </div>
      </div>
    `
      )
      .join("");
  } catch (err) {
    box.innerHTML = `<div class="muted">${escapeHtml(err.message)}</div>`;
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

async function voteNearby(reportId, vote) {
  const item = document.querySelector(`[data-report-id="${reportId}"]`);
  if (item) item.querySelector(".actions").innerHTML = '<div class="muted">Submitting...</div>';
  try {
    await API.request(`/validation/${reportId}/vote`, { method: "POST", body: { vote }, auth: true });
    if (item) item.innerHTML = '<div class="muted">Thanks for confirming.</div>';
    await refreshClustersOnMap();
  } catch (err) {
    if (item) item.innerHTML = `<div class="muted">${escapeHtml(err.message)}</div>`;
  }
}
