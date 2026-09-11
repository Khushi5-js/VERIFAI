// VERIFAI Scoreboard & Leaderboard Controller

let allCases = [];
let currentFilter = "ALL";
let searchQuery = "";

document.addEventListener("DOMContentLoaded", () => {
  fetchScoreboard();

  // Search input
  const searchInput = document.getElementById("search-input");
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      searchQuery = e.target.value.toLowerCase().trim();
      renderTable();
    });
  }

  // Filter tabs
  const filterBtns = document.querySelectorAll("[data-filter]");
  filterBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      filterBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentFilter = btn.getAttribute("data-filter");
      renderTable();
    });
  });

  // Modal close
  const modal = document.getElementById("quick-modal");
  const modalClose = document.getElementById("modal-close");
  if (modalClose && modal) {
    modalClose.addEventListener("click", () => modal.style.display = "none");
    modal.addEventListener("click", (e) => {
      if (e.target === modal) modal.style.display = "none";
    });
  }
});


async function fetchScoreboard() {
  try {
    const res = await fetch("/api/scoreboard");
    if (!res.ok) throw new Error("Failed to fetch scoreboard");
    const data = await res.json();

    allCases = data.leaderboard || [];

    // Render KPIs
    document.getElementById("kpi-total").textContent = data.total_cases;
    document.getElementById("kpi-authentic").textContent = data.tier_counts.AUTHENTIC || 0;
    const tamperedCount = (data.tier_counts.SUSPICIOUS || 0) + (data.tier_counts.HIGH_RISK || 0) + (data.tier_counts.FABRICATED || 0);
    document.getElementById("kpi-tampered").textContent = tamperedCount;
    document.getElementById("kpi-avg-score").textContent = data.average_risk_score;

    const pill = document.getElementById("scoreboard-total-pill");
    if (pill) pill.textContent = `${data.total_cases} CASES LOGGED`;

    renderTable();

  } catch (err) {
    console.error(err);
    document.getElementById("scoreboard-tbody").innerHTML = `
      <tr><td colspan="8" style="text-align: center; color: var(--accent-red); padding: 2rem;">
        Failed to load scoreboard data. Verify that backend engine is running.
      </td></tr>
    `;
  }
}


function renderTable() {
  const tbody = document.getElementById("scoreboard-tbody");
  if (!tbody) return;

  let filtered = allCases.filter(c => {
    const tier = (c.risk_assessment?.tier || "AUTHENTIC").toUpperCase();
    if (currentFilter !== "ALL" && tier !== currentFilter) return false;

    if (searchQuery) {
      const matchId = (c.case_id || "").toLowerCase().includes(searchQuery);
      const matchName = (c.filename || "").toLowerCase().includes(searchQuery);
      const matchHash = (c.local_forensics?.hashes?.sha256 || "").toLowerCase().includes(searchQuery);
      if (!matchId && !matchName && !matchHash) return false;
    }

    return true;
  });

  if (filtered.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="8" style="text-align: center; color: var(--text-muted); padding: 3rem;">
          No forensic cases match the specified filters.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = filtered.map((c, idx) => {
    const risk = c.risk_assessment || {};
    const score = risk.score || 0;
    const color = risk.color || "#06b6d4";
    const sha256 = c.local_forensics?.hashes?.sha256 || "N/A";
    const shortHash = sha256.length > 16 ? `${sha256.substring(0, 10)}...${sha256.substring(sha256.length - 6)}` : sha256;

    return `
      <tr>
        <td style="font-family: var(--font-mono); font-weight: 700; color: ${idx === 0 ? 'var(--accent-red)' : 'var(--text-muted)'};">
          #${idx + 1}
        </td>
        <td>
          <a href="/frontend/workshop.html?case_id=${c.case_id}" style="color: var(--accent-cyan); text-decoration: none; font-family: var(--font-mono); font-weight: 600;">
            ${c.case_id}
          </a>
        </td>
        <td>
          <div style="display: flex; align-items: center; gap: 0.5rem;">
            <span class="chip" style="font-size: 0.7rem;">${c.local_forensics?.file_type?.toUpperCase() || 'FILE'}</span>
            <span style="font-weight: 500; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${c.filename}">
              ${c.filename}
            </span>
          </div>
        </td>
        <td>
          <span style="font-family: var(--font-mono); font-size: 0.78rem; color: var(--text-muted);" title="${sha256}">
            ${shortHash}
          </span>
        </td>
        <td>
          <div style="display: flex; align-items: center; gap: 0.5rem;">
            <strong style="font-family: var(--font-mono); font-size: 1.05rem; color: ${color};">
              ${score}
            </strong>
            <span style="font-size: 0.72rem; color: var(--text-muted);">/100</span>
          </div>
        </td>
        <td>
          <span class="stage-status-pill" style="background: ${color}22; color: ${color}; border: 1px solid ${color}44;">
            ${risk.badge || risk.tier}
          </span>
        </td>
        <td style="color: var(--text-muted); font-size: 0.82rem; white-space: nowrap;">
          ${c.created_at ? c.created_at.split(' ')[0] : 'N/A'}
        </td>
        <td>
          <div style="display: flex; gap: 0.4rem;">
            <a href="/frontend/workshop.html?case_id=${c.case_id}" class="btn btn-primary btn-sm" title="Inspect full evidence trail">
              Inspect
            </a>
            <button class="btn btn-outline btn-sm" onclick="openQuickView('${c.case_id}')">
              Quick View
            </button>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}


window.openQuickView = function(caseId) {
  const caseItem = allCases.find(c => c.case_id === caseId);
  if (!caseItem) return;

  const modal = document.getElementById("quick-modal");
  const modalBody = document.getElementById("modal-body");
  const risk = caseItem.risk_assessment || {};
  const local = caseItem.local_forensics || {};
  const ela = local.ela || {};

  modalBody.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.5rem;">
      <div>
        <span class="chip">${caseItem.case_id}</span>
        <h2 style="font-size: 1.6rem; margin-top: 0.4rem;">${caseItem.filename}</h2>
        <span style="color: var(--text-muted); font-size: 0.85rem;">Logged: ${caseItem.created_at}</span>
      </div>
      <div style="text-align: right;">
        <div style="font-size: 2rem; font-weight: 800; font-family: var(--font-mono); color: ${risk.color}; line-height: 1;">
          ${risk.score}/100
        </div>
        <span class="stage-status-pill" style="background: ${risk.color}22; color: ${risk.color}; margin-top: 0.3rem; display: inline-block;">
          ${risk.badge}
        </span>
      </div>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 1.5rem;">
      <div>
        <h4 style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.5rem; text-transform: uppercase;">Original Subject</h4>
        <div style="background: #000; border-radius: var(--radius-sm); height: 220px; display: flex; align-items: center; justify-content: center; overflow: hidden;">
          <img src="${caseItem.file_url}" style="max-width: 100%; max-height: 100%; object-fit: contain;">
        </div>
      </div>
      <div>
        <h4 style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.5rem; text-transform: uppercase;">ELA Error Heatmap</h4>
        <div style="background: #000; border-radius: var(--radius-sm); height: 220px; display: flex; align-items: center; justify-content: center; overflow: hidden;">
          ${ela.ela_performed ? `<img src="${ela.ela_image_url}" style="max-width: 100%; max-height: 100%; object-fit: contain;">` : '<span style="color: var(--text-muted); font-size: 0.85rem;">ELA not applicable</span>'}
        </div>
      </div>
    </div>

    <div style="background: rgba(0,0,0,0.3); padding: 1.25rem; border-radius: var(--radius-md); border: 1px solid var(--border-subtle); margin-bottom: 1.5rem;">
      <h4 style="font-size: 0.85rem; color: var(--accent-cyan); text-transform: uppercase; margin-bottom: 0.5rem;">Investigator Recommendation</h4>
      <p style="font-size: 0.92rem; color: #e2e8f0;">${risk.recommendation}</p>
    </div>

    <div style="display: flex; justify-content: flex-end; gap: 0.75rem;">
      <a href="/api/cases/${caseItem.case_id}/report.pdf" class="btn btn-outline" target="_blank">Download PDF Report</a>
      <a href="/frontend/workshop.html?case_id=${caseItem.case_id}" class="btn btn-primary">Open Full Workshop Audit</a>
    </div>
  `;

  modal.style.display = "flex";
};
