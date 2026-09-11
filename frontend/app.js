// VERIFAI Workshop Dashboard Script

document.addEventListener("DOMContentLoaded", () => {
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("file-input");
  const btnBrowse = document.getElementById("btn-browse");
  const uploadSection = document.getElementById("upload-section");
  const telemetryPipeline = document.getElementById("telemetry-pipeline");
  const pipelineStatusBadge = document.getElementById("pipeline-status-badge");
  const workspaceResults = document.getElementById("workspace-results");
  const btnNewAnalysis = document.getElementById("btn-new-analysis");

  // Health check
  checkHealth();

  // Check if case_id passed in URL query param
  const urlParams = new URLSearchParams(window.location.search);
  const caseIdParam = urlParams.get("case_id");
  if (caseIdParam) {
    loadExistingCase(caseIdParam);
  }

  // Browse button trigger
  if (btnBrowse && fileInput) {
    btnBrowse.addEventListener("click", (e) => {
      e.stopPropagation();
      fileInput.click();
    });
  }

  if (dropzone && fileInput) {
    dropzone.addEventListener("click", () => fileInput.click());

    // Drag & Drop events
    ["dragenter", "dragover"].forEach(evt => {
      dropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        dropzone.classList.add("dragover");
      });
    });

    ["dragleave", "drop"].forEach(evt => {
      dropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        dropzone.classList.remove("dragover");
      });
    });

    dropzone.addEventListener("drop", (e) => {
      const files = e.dataTransfer.files;
      if (files && files.length > 0) {
        handleFileUpload(files[0]);
      }
    });

    fileInput.addEventListener("change", () => {
      if (fileInput.files && fileInput.files.length > 0) {
        handleFileUpload(fileInput.files[0]);
      }
    });
  }

  if (btnNewAnalysis) {
    btnNewAnalysis.addEventListener("click", () => {
      workspaceResults.style.display = "none";
      telemetryPipeline.style.display = "none";
      uploadSection.style.display = "block";
      fileInput.value = "";
      window.history.replaceState({}, document.title, window.location.pathname);
    });
  }

  // Setup viewer tabs
  setupViewerTabs();

  // Setup split slider
  setupSplitSlider();

  // Setup copy writeup button
  const btnCopy = document.getElementById("btn-copy-writeup");
  if (btnCopy) {
    btnCopy.addEventListener("click", () => {
      const text = document.getElementById("writeup-content").textContent;
      navigator.clipboard.writeText(text).then(() => {
        const orig = btnCopy.textContent;
        btnCopy.textContent = "Copied!";
        setTimeout(() => { btnCopy.textContent = orig; }, 2000);
      });
    });
  }
});


async function checkHealth() {
  try {
    const res = await fetch("/api/health");
    if (res.ok) {
      const data = await res.json();
      const statusText = document.getElementById("system-status-text");
      if (statusText) {
        statusText.textContent = data.gemini_configured ? "ENGINE ONLINE (AI ACTIVE)" : "ENGINE ONLINE (HEURISTIC)";
      }
    }
  } catch (err) {
    console.warn("Health check error:", err);
  }
}


async function handleFileUpload(file) {
  const uploadSection = document.getElementById("upload-section");
  const telemetryPipeline = document.getElementById("telemetry-pipeline");
  const workspaceResults = document.getElementById("workspace-results");

  // Show telemetry and hide upload section
  uploadSection.style.display = "none";
  telemetryPipeline.style.display = "block";
  workspaceResults.style.display = "none";

  // Animate stages
  startPipelineAnimation();

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch("/api/verify", {
      method: "POST",
      body: formData
    });

    if (!response.ok) {
      throw new Error(`Analysis failed with status ${response.status}`);
    }

    const caseData = await response.json();

    // Finish pipeline animation
    completePipelineAnimation(caseData);

    // Render results after small delay for dramatic forensic presentation
    setTimeout(() => {
      renderCaseResults(caseData);
    }, 700);

  } catch (error) {
    alert("Verification Error: " + error.message);
    uploadSection.style.display = "block";
    telemetryPipeline.style.display = "none";
  }
}


window.loadDemoSample = async function(sampleId) {
  const uploadSection = document.getElementById("upload-section");
  const telemetryPipeline = document.getElementById("telemetry-pipeline");
  const workspaceResults = document.getElementById("workspace-results");

  uploadSection.style.display = "none";
  telemetryPipeline.style.display = "block";
  workspaceResults.style.display = "none";

  startPipelineAnimation();

  try {
    const response = await fetch(`/api/verify-demo/${sampleId}`, {
      method: "POST"
    });

    if (!response.ok) {
      throw new Error(`Demo verification failed (${response.status})`);
    }

    const caseData = await response.json();
    completePipelineAnimation(caseData);

    setTimeout(() => {
      renderCaseResults(caseData);
    }, 700);
  } catch (error) {
    alert("Demo Error: " + error.message);
    uploadSection.style.display = "block";
    telemetryPipeline.style.display = "none";
  }
};


async function loadExistingCase(caseId) {
  try {
    const res = await fetch(`/api/cases/${caseId}`);
    if (!res.ok) throw new Error("Case not found");
    const caseData = await res.json();
    document.getElementById("upload-section").style.display = "none";
    document.getElementById("telemetry-pipeline").style.display = "none";
    renderCaseResults(caseData);
  } catch (e) {
    console.error("Failed to load case:", e);
  }
}


let animInterval = null;
function startPipelineAnimation() {
  const nodes = document.querySelectorAll(".pipeline-node");
  nodes.forEach(n => {
    n.className = "pipeline-node";
    const sp = n.querySelector(".node-spinner");
    if (sp) sp.remove();
  });

  let current = 0;
  if (animInterval) clearInterval(animInterval);

  nodes[0].classList.add("active");
  const spin = document.createElement("div");
  spin.className = "node-spinner";
  nodes[0].appendChild(spin);

  animInterval = setInterval(() => {
    if (current < 7) {
      nodes[current].classList.remove("active");
      nodes[current].classList.add("passed");
      const sp = nodes[current].querySelector(".node-spinner");
      if (sp) sp.remove();

      current++;
      nodes[current].classList.add("active");
      const nextSpin = document.createElement("div");
      nextSpin.className = "node-spinner";
      nodes[current].appendChild(nextSpin);
    }
  }, 400);
}


function completePipelineAnimation(caseData) {
  if (animInterval) clearInterval(animInterval);
  const nodes = document.querySelectorAll(".pipeline-node");
  const trail = caseData.evidence_trail || [];

  nodes.forEach((node, idx) => {
    node.className = "pipeline-node";
    const sp = node.querySelector(".node-spinner");
    if (sp) sp.remove();

    const stageStatus = trail[idx] ? trail[idx].status.toLowerCase() : "passed";
    node.classList.add(stageStatus);
  });

  const badge = document.getElementById("pipeline-status-badge");
  if (badge) {
    badge.textContent = "VERIFICATION COMPLETE";
    badge.style.color = "#10b981";
    badge.style.borderColor = "rgba(16, 185, 129, 0.4)";
  }
}


function renderCaseResults(caseData) {
  const workspaceResults = document.getElementById("workspace-results");
  workspaceResults.style.display = "block";

  const risk = caseData.risk_assessment || {};
  const score = risk.score || 0;
  const factors = risk.factors || {};
  const local = caseData.local_forensics || {};
  const hashes = local.hashes || {};
  const ela = local.ela || {};

  // Case meta
  document.getElementById("display-case-id").textContent = `CASE: ${caseData.case_id}`;
  document.getElementById("display-timestamp").textContent = caseData.created_at;
  document.getElementById("display-verdict-title").textContent = risk.badge || "ANALYZED";
  document.getElementById("display-verdict-title").style.color = risk.color || "#06b6d4";
  document.getElementById("display-recommendation").textContent = risk.recommendation || "";

  // Verdict banner accent border
  const banner = document.getElementById("verdict-banner");
  if (banner) {
    banner.style.borderLeft = `6px solid ${risk.color || "#06b6d4"}`;
  }

  // Gauge animation (circumference is 2 * PI * 42 = 263.89)
  const circle = document.getElementById("gauge-circle");
  const scoreNum = document.getElementById("display-score-num");
  if (circle) {
    circle.style.stroke = risk.color || "#06b6d4";
    const offset = 264 - (264 * (score / 100));
    setTimeout(() => {
      circle.style.strokeDashoffset = offset;
    }, 100);
  }
  if (scoreNum) {
    scoreNum.textContent = score;
    scoreNum.style.color = risk.color || "#06b6d4";
  }

  // Factor breakdown
  setBar("meta", factors.metadata_risk || 0, 30);
  setBar("ela", factors.ela_compression_risk || 0, 25);
  setBar("struct", factors.container_structure_risk || 0, 20);
  setBar("neural", factors.neural_ai_risk || 0, 25);

  // Hashes
  document.getElementById("hash-sha256").textContent = hashes.sha256 || "N/A";
  document.getElementById("hash-md5").textContent = hashes.md5 || "N/A";

  // PDF Download Link
  const btnPdf = document.getElementById("btn-download-pdf");
  if (btnPdf) {
    btnPdf.href = `/api/cases/${caseData.case_id}/report.pdf`;
  }

  // Images setup
  const isImage = local.file_type === "image";
  const origUrl = caseData.file_url;
  const elaUrl = ela.ela_image_url || origUrl;

  const sliderBox = document.getElementById("slider-box");
  const singleImg = document.getElementById("single-view-img");
  const sliderOrig = document.getElementById("slider-orig-img");
  const sliderEla = document.getElementById("slider-ela-img");

  if (isImage && ela.ela_performed) {
    sliderBox.style.display = "block";
    singleImg.style.display = "none";
    sliderOrig.src = origUrl;
    sliderEla.src = elaUrl;
    document.getElementById("slider-range").value = 50;
    updateSlider(50);
  } else {
    // Non-image or PDF
    sliderBox.style.display = "none";
    singleImg.style.display = "block";
    singleImg.src = isImage ? origUrl : "/frontend/pdf-placeholder.svg";
  }

  // Evidence Trail Accordion
  renderTrailAccordion(caseData.evidence_trail || []);

  // Writeup
  const writeupBox = document.getElementById("writeup-content");
  if (writeupBox) {
    writeupBox.textContent = caseData.writeup || "No write-up generated.";
  }

  // Smooth scroll to results
  workspaceResults.scrollIntoView({ behavior: "smooth" });
}


function setBar(id, val, max) {
  const numEl = document.getElementById(`score-${id}`);
  const fillEl = document.getElementById(`bar-${id}`);
  if (numEl) numEl.textContent = `${val} / ${max}`;
  if (fillEl) {
    const pct = Math.min(100, Math.round((val / max) * 100));
    fillEl.style.width = `${pct}%`;
  }
}


function renderTrailAccordion(trail) {
  const container = document.getElementById("trail-accordion-list");
  if (!container) return;
  container.innerHTML = "";

  trail.forEach((item, idx) => {
    const statusLower = (item.status || "passed").toLowerCase();
    const itemEl = document.createElement("div");
    itemEl.className = "trail-item";

    const isFirst = idx === 0;

    itemEl.innerHTML = `
      <div class="trail-header" data-stage="${item.stage}">
        <div class="trail-title-group">
          <span class="stage-badge">STAGE 0${item.stage}</span>
          <strong style="font-size: 0.92rem;">${item.name}</strong>
        </div>
        <div style="display: flex; align-items: center; gap: 0.75rem;">
          <span class="stage-status-pill status-${statusLower}">${item.status}</span>
          <span style="color: var(--text-muted); font-size: 0.8rem;">▼</span>
        </div>
      </div>
      <div class="trail-body ${isFirst ? 'open' : ''}">
        <p style="font-size: 0.88rem; color: #e2e8f0; margin-bottom: 0.75rem; font-weight: 500;">
          ${item.summary}
        </p>
        <ul class="trail-details-list">
          ${(item.details || []).map(d => `<li><span>▸</span><span>${d}</span></li>`).join('')}
        </ul>
      </div>
    `;

    const header = itemEl.querySelector(".trail-header");
    const body = itemEl.querySelector(".trail-body");
    header.addEventListener("click", () => {
      body.classList.toggle("open");
    });

    container.appendChild(itemEl);
  });
}


function setupViewerTabs() {
  const tabSplit = document.getElementById("tab-split");
  const tabOrig = document.getElementById("tab-original");
  const tabEla = document.getElementById("tab-ela");

  const sliderBox = document.getElementById("slider-box");
  const singleImg = document.getElementById("single-view-img");
  const sliderOrig = document.getElementById("slider-orig-img");
  const sliderEla = document.getElementById("slider-ela-img");

  if (!tabSplit) return;

  const setActive = (activeTab) => {
    [tabSplit, tabOrig, tabEla].forEach(t => t.classList.remove("active"));
    activeTab.classList.add("active");
  };

  tabSplit.addEventListener("click", () => {
    setActive(tabSplit);
    sliderBox.style.display = "block";
    singleImg.style.display = "none";
    updateSlider(document.getElementById("slider-range").value);
  });

  tabOrig.addEventListener("click", () => {
    setActive(tabOrig);
    sliderBox.style.display = "none";
    singleImg.style.display = "block";
    singleImg.src = sliderOrig.src;
  });

  tabEla.addEventListener("click", () => {
    setActive(tabEla);
    sliderBox.style.display = "none";
    singleImg.style.display = "block";
    singleImg.src = sliderEla.src;
  });
}


function setupSplitSlider() {
  const range = document.getElementById("slider-range");
  if (range) {
    range.addEventListener("input", (e) => {
      updateSlider(e.target.value);
    });
  }
}


function updateSlider(val) {
  const overlay = document.getElementById("slider-overlay");
  const handle = document.getElementById("slider-handle");
  if (overlay && handle) {
    overlay.style.width = `${val}%`;
    handle.style.left = `${val}%`;
  }
}
