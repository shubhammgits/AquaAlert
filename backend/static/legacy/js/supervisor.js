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
