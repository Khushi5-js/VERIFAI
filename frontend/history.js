// VERIFAI Case History Archive Controller

// Universal Previous Page Navigation Helper
window.navigateBack = function(fallback = 'index.html#app') {
  const isInternalReferrer = document.referrer && (
    document.referrer.includes(window.location.host) ||
    document.referrer.startsWith('file:')
  );
  if (isInternalReferrer && window.history.length > 1) {
    window.history.back();
  } else if (window.history.length > 1 && !document.referrer) {
    window.history.back();
  } else {
    window.location.href = fallback;
  }
};

let historyCases = [];

document.addEventListener("DOMContentLoaded", () => {
  fetchHistory();

  const searchInput = document.getElementById("history-search");
  const filterTier = document.getElementById("filter-tier");
  const filterType = document.getElementById("filter-type");

  if (searchInput) searchInput.addEventListener("input", filterAndRender);
  if (filterTier) filterTier.addEventListener("change", filterAndRender);
  if (filterType) filterType.addEventListener("change", filterAndRender);
});


async function fetchHistory() {
  try {
    const res = await fetch("/api/cases");
    if (!res.ok) throw new Error("Failed to load cases");
    historyCases = await res.json();

    const pill = document.getElementById("history-total-pill");
    if (pill) pill.textContent = `${historyCases.length} CASES ARCHIVED`;

    filterAndRender();

  } catch (err) {
    console.error(err);
    document.getElementById("history-grid").innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; color: var(--accent-red); padding: 3rem;">
        Failed to load case archive. Ensure backend service is running.
      </div>
    `;
  }
}


function filterAndRender() {
  const grid = document.getElementById("history-grid");
  if (!grid) return;

  const searchVal = (document.getElementById("history-search")?.value || "").toLowerCase().trim();
  const tierVal = document.getElementById("filter-tier")?.value || "ALL";
  const typeVal = document.getElementById("filter-type")?.value || "ALL";

  const filtered = historyCases.filter(c => {
    const tier = (c.risk_assessment?.tier || "AUTHENTIC").toUpperCase();
    if (tierVal !== "ALL" && tier !== tierVal) return false;

    const ftype = c.local_forensics?.file_type || "other";
    if (typeVal !== "ALL" && ftype !== typeVal) return false;

    if (searchVal) {
      const idMatch = (c.case_id || "").toLowerCase().includes(searchVal);
      const nameMatch = (c.filename || "").toLowerCase().includes(searchVal);
      const hashMatch = (c.local_forensics?.hashes?.sha256 || "").toLowerCase().includes(searchVal);
      if (!idMatch && !nameMatch && !hashMatch) return false;
    }

    return true;
  });

  if (filtered.length === 0) {
    grid.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; color: var(--text-muted); padding: 4rem;">
        No cases found in archive matching your criteria.
      </div>
    `;
    return;
  }

  grid.innerHTML = filtered.map(c => {
    const risk = c.risk_assessment || {};
    const score = risk.score || 0;
    const color = risk.color || "#06b6d4";
    const local = c.local_forensics || {};
    const isImage = local.file_type === "image";
    const thumbUrl = isImage ? c.file_url : "";
    const sizeStr = local.hashes?.size_formatted || "Unknown size";
    const sha256 = local.hashes?.sha256 || "N/A";
    const shortSha = sha256.length > 16 ? `${sha256.substring(0, 10)}...` : sha256;

    const reasons = risk.flagged_reasons || [];
    const reasonSummary = reasons.length > 0 ? reasons[0] : "Clean container telemetry.";

    return `
      <div class="glass-panel case-card">
        <div>
          <!-- Thumbnail -->
          <div class="case-card-thumb">
            ${isImage 
              ? `<img src="${thumbUrl}" alt="Evidence Thumbnail" loading="lazy">`
              : `<div style="text-align: center; color: var(--accent-cyan); font-family: var(--font-mono);">
                  <svg width="48" height="48" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>
                  <div style="font-size: 0.8rem; margin-top: 0.35rem;">PDF EVIDENCE</div>
                 </div>`
            }
          </div>

          <!-- Header -->
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem;">
            <div>
              <span class="chip">${c.case_id}</span>
              <h3 style="font-size: 1.1rem; margin-top: 0.35rem; word-break: break-all;" title="${c.filename}">
                ${c.filename}
              </h3>
            </div>
            <div style="text-align: right;">
              <div style="font-size: 1.4rem; font-weight: 800; font-family: var(--font-mono); color: ${color}; line-height: 1;">
                ${score}
              </div>
              <span style="font-size: 0.65rem; color: var(--text-muted);">/100</span>
            </div>
          </div>

          <!-- Metadata info -->
          <div style="font-size: 0.8rem; color: var(--text-muted); display: flex; flex-direction: column; gap: 0.25rem; margin-bottom: 1rem; font-family: var(--font-mono);">
            <div>Logged: ${c.created_at || 'N/A'}</div>
            <div>Size: ${sizeStr} | SHA: ${shortSha}</div>
          </div>

          <!-- Findings pill -->
          <div style="margin-bottom: 1rem;">
            <span class="stage-status-pill" style="background: ${color}22; color: ${color}; border: 1px solid ${color}44; display: inline-block;">
              ${risk.badge || risk.tier}
            </span>
            <p style="font-size: 0.82rem; color: var(--text-secondary); margin-top: 0.5rem; line-height: 1.4;">
              ${reasonSummary}
            </p>
          </div>
        </div>

        <!-- Card Actions -->
        <div style="display: flex; gap: 0.5rem; border-top: 1px solid var(--border-subtle); padding-top: 1rem; margin-top: 0.5rem;">
          <a href="workshop.html?case_id=${c.case_id}" class="btn btn-primary btn-sm" style="flex: 1; justify-content: center;">
            Reopen Case
          </a>
          <a href="/api/cases/${c.case_id}/report.pdf" class="btn btn-outline btn-sm" target="_blank" title="Download PDF Report">
            PDF
          </a>
          <button class="btn btn-outline btn-sm" onclick="deleteCaseRecord('${c.case_id}')" style="color: var(--accent-red);" title="Delete Record">
            ✕
          </button>
        </div>

      </div>
    `;
  }).join('');
}


window.deleteCaseRecord = async function(caseId) {
  if (!confirm(`Are you sure you want to permanently delete case record ${caseId}?`)) {
    return;
  }
  try {
    const res = await fetch(`/api/cases/${caseId}`, { method: "DELETE" });
    if (!res.ok) throw new Error("Delete failed");
    historyCases = historyCases.filter(c => c.case_id !== caseId);
    filterAndRender();
    const pill = document.getElementById("history-total-pill");
    if (pill) pill.textContent = `${historyCases.length} CASES ARCHIVED`;
  } catch (err) {
    alert("Could not delete case: " + err.message);
  }
};
