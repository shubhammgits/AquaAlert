async function refreshVerifyQueue() {
  const holder = document.getElementById("verifyQueue");
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

  let reports = [];
  try {
    reports = await API.request("/reports");
  } catch (err) {
    holder.innerHTML = `<div class="muted">${escapeHtml(err.message)}</div>`;
    return;
  }

  const completed = reports.filter((r) => r.status === "completed");
  if (!completed.length) {
    holder.innerHTML = `<div class="muted">No completion submissions waiting.</div>`;
    return;
  }

  holder.innerHTML = completed
    .map(
      (r) => `
    <div class="item">
      <div class="row">
        <span class="pill">${r.severity}</span>
        <span class="pill">${r.status}</span>
        <span class="muted">Report #${r.id}</span>
      </div>
      <div class="muted">Completed — awaiting your verification</div>
      ${renderProgress(r.status)}
      <div class="muted">Reported: ${new Date(r.created_at).toLocaleString()}</div>
      <div class="muted">District: ${escapeHtml(r.district || "")}</div>
      <div class="actions">
        <a class="btn btn-secondary" href="${r.image_url}" target="_blank" rel="noreferrer">View User Photo</a>
        ${
          r.completion_image_url
            ? `<a class="btn btn-secondary" href="${r.completion_image_url}" target="_blank" rel="noreferrer">View Worker Photo</a>`
            : `<span class="muted">No worker photo</span>`
        }
        <button class="btn" type="button" onclick="verifyReport(${r.id}, true, '${String(r.created_at || "").replaceAll("'", "\\'")}')">Yes, solved</button>
        <button class="btn btn-secondary" type="button" onclick="verifyReport(${r.id}, false, '${String(r.created_at || "").replaceAll("'", "\\'")}')">No, not completed</button>
      </div>
    </div>
  `
    )
    .join("");
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function _fmtDateShort(iso) {
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return "";
    return d.toLocaleDateString(undefined, { day: "2-digit", month: "short", year: "numeric" });
  } catch {
    return "";
  }
}

function _badgeForStatus(status) {
  const s = String(status || "").toLowerCase();
  if (s === "closed") return { cls: "badge--completed", label: "Completed" };
  if (s === "completed") return { cls: "badge--progress", label: "In Progress" };
  if (s === "assigned") return { cls: "badge--assigned", label: "Assigned" };
  if (s === "accepted") return { cls: "badge--progress", label: "In Progress" };
  if (s === "rejected") return { cls: "badge--critical", label: "Needs Action" };
  return { cls: "badge--pending", label: "Pending" };
}

window.renderSupervisorStats = function (reports) {
  try {
    const totalEl = document.getElementById("statTotal");
    const highEl = document.getElementById("statHigh");
    const pendingEl = document.getElementById("statPending");
    const resolvedEl = document.getElementById("statResolved");
    if (!totalEl || !highEl || !pendingEl || !resolvedEl) return;

    const rows = Array.isArray(reports) ? reports : [];
    const total = rows.length;
    const high = rows.filter((r) => r && r.severity === "High").length;
    const pending = rows.filter((r) => r && (r.status === "submitted" || r.status === "accepted")).length;
    const resolved = rows.filter((r) => r && r.status === "closed").length;

    totalEl.textContent = String(total);
    highEl.textContent = String(high);
    pendingEl.textContent = String(pending);
    resolvedEl.textContent = String(resolved);
  } catch {
    // ignore
  }
};

window.renderSupervisorRightHistory = function (reports) {
  const root = document.getElementById("rightHistory");
  if (!root) return;
  const rows = Array.isArray(reports) ? reports : [];
  if (!rows.length) {
    root.innerHTML = `<div class="empty-state">No activity yet.</div>`;
    return;
  }

  const top = rows
    .slice()
    .sort((a, b) => {
      const ta = new Date(a.created_at || 0).getTime();
      const tb = new Date(b.created_at || 0).getTime();
      return tb - ta;
    })
    .slice(0, 18);

  root.innerHTML = top
    .map((r) => {
      const id = escapeHtml(r.id || "");
      const title = `R-${id}`;
      const date = _fmtDateShort(r.created_at);
      const loc = escapeHtml(r.district || "");
      const meta = [date, loc].filter(Boolean).join(" • ");
      const badge = _badgeForStatus(r.status);
      const bodyBits = [];
      bodyBits.push(`<div class="muted">Severity: ${escapeHtml(r.severity || "")}</div>`);
      bodyBits.push(`<div class="muted">Status: ${escapeHtml(r.status || "")}</div>`);
      if (r.assigned_worker && r.assigned_worker.name) bodyBits.push(`<div class="muted">Worker: ${escapeHtml(r.assigned_worker.name)}</div>`);
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
              <div class="actions">
                <a class="btn btn-secondary" href="${r.image_url}" target="_blank" rel="noreferrer">User Photo</a>
                <a class="btn btn-secondary" href="https://www.google.com/maps?q=${r.latitude},${r.longitude}" target="_blank" rel="noreferrer">Map</a>
              </div>
            </div>
          </div>
        </div>
      `;
    })
    .join("");

  wireHistoryToggles(root);
};

function wireHistoryToggles(root) {
  if (!root) return;
  const items = root.querySelectorAll("[data-hitem]");
  items.forEach((item) => {
    const btn = item.querySelector("[data-hitem-toggle]");
    const body = item.querySelector("[data-hitem-body]");
    if (!btn || !body) return;
    btn.addEventListener("click", () => {
      const isOpen = item.classList.toggle("is-open");
      if (isOpen) body.style.maxHeight = body.scrollHeight + "px";
      else body.style.maxHeight = "0px";
    });
  });
}

async function refreshWorkersList() {
  const root = document.getElementById("workerList");
  if (!root) return;
  root.innerHTML = "";

  let rows = [];
  try {
    rows = await API.request("/workers?max_age_sec=900", { auth: true });
  } catch (err) {
    root.innerHTML = `<div class="muted">${escapeHtml(err.message)}</div>`;
    return;
  }

  if (!rows.length) {
    root.innerHTML = `<div class="empty-state">No workers found.</div>`;
    return;
  }

  const now = Date.now();
  function computeStatus(w) {
    const avail = !!w.is_available;
    const updated = w.location_updated_at ? new Date(w.location_updated_at).getTime() : 0;
    const isFresh = updated && now - updated < 15 * 60 * 1000;
    if (!updated || !isFresh) return { label: "Offline", badge: { cls: "badge--pending", label: "Offline" } };
    if (avail) return { label: "Available", badge: { cls: "badge--completed", label: "Available" } };
    return { label: "Busy", badge: { cls: "badge--progress", label: "Busy" } };
  }

  root.innerHTML = rows
    .slice(0, 40)
    .map((w) => {
      const st = computeStatus(w);
      const name = escapeHtml(w.name || "Worker");
      const phone = escapeHtml(w.phone || "");
      const district = escapeHtml(w.district || "");
      const updatedAt = w.location_updated_at ? _fmtDateShort(w.location_updated_at) : "";
      const subBits = [phone, district, updatedAt ? `Updated: ${updatedAt}` : ""].filter(Boolean).join(" • ");
      return `
        <div class="witem">
          <div class="witem__meta">
            <div class="witem__name">${name}</div>
            <div class="witem__sub">${subBits || "—"}</div>
          </div>
          <span class="badge ${st.badge.cls}">${st.badge.label}</span>
        </div>
      `;
    })
    .join("");
}

// Hook up refresh button if present.
(function () {
  const btn = document.getElementById("refreshWorkersBtn");
  if (btn) btn.addEventListener("click", refreshWorkersList);
})();

// Expose so inline scripts can call after initial loads.
window.refreshWorkersList = refreshWorkersList;

async function verifyReport(reportId, approved, createdAt) {
  const reported = createdAt ? new Date(createdAt).toLocaleString() : "";
  const message = approved
    ? `Your reported issue (${reported}) has been resolved and verified.`
    : "Work not completed. Do it again and resubmit a new live photo for verification.";
  try {
    await API.request(`/reports/${reportId}/verify`, { method: "PATCH", body: { approved, message }, auth: true });
    await refreshSupervisorViews();
    await refreshVerifyQueue();
    await refreshClustersOnMap(true);
  } catch (err) {
    alert(err.message);
  }
}
