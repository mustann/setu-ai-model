// SIH 2026 Model 1: Report Structuring & Classification AI - Interactive Client

let activeFile = null;
let currentReportJson = null;

// DOM Elements
const reportForm = document.getElementById("reportForm");
const reportText = document.getElementById("reportText");
const reportLocation = document.getElementById("reportLocation");
const reportTimestamp = document.getElementById("reportTimestamp");
const wordCounter = document.getElementById("wordCounter");
const demoAssetName = document.getElementById("demoAssetName");
const mediaDropzone = document.getElementById("mediaDropzone");
const mediaFileInput = document.getElementById("mediaFileInput");
const mediaPreviewContainer = document.getElementById("mediaPreviewContainer");
const mediaPreviewImg = document.getElementById("mediaPreviewImg");
const mediaFileName = document.getElementById("mediaFileName");
const btnRemoveMedia = document.getElementById("btnRemoveMedia");
const btnSubmit = document.getElementById("btnSubmit");
const btnSpinner = document.getElementById("btnSpinner");
const btnText = document.getElementById("btnText");
const btnDetectGps = document.getElementById("btnDetectGps");
const btnNowTime = document.getElementById("btnNowTime");
const btnCopyJson = document.getElementById("btnCopyJson");
const scenarioCardsContainer = document.getElementById("scenarioCardsContainer");

// Result DOM Elements
const reviewBanner = document.getElementById("reviewBanner");
const reviewTitle = document.getElementById("reviewTitle");
const reviewSubtitle = document.getElementById("reviewSubtitle");
const reviewChip = document.getElementById("reviewChip");
const latencyBadge = document.getElementById("latencyBadge");

const kpiConfidence = document.getElementById("kpiConfidence");
const kpiCompleteness = document.getElementById("kpiCompleteness");
const kpiMissingCount = document.getElementById("kpiMissingCount");
const kpiMedia = document.getElementById("kpiMedia");
const kpiFramesChecked = document.getElementById("kpiFramesChecked");

// Pillar 1: Report Understanding Elements
const primaryDomainLabel = document.getElementById("primaryDomainLabel");
const problemTypeLabel = document.getElementById("problemTypeLabel");
const domainConfidenceBadge = document.getElementById("domainConfidenceBadge");
const domainConfidenceBar = document.getElementById("domainConfidenceBar");
const severityConfidenceBadge = document.getElementById("severityConfidenceBadge");
const severityLevelBadge = document.getElementById("severityLevelBadge");
const textReasonText = document.getElementById("textReasonText");
const severitySignalsList = document.getElementById("severitySignalsList");

// Pillar 2: Media Understanding Elements
const mediaVisualConfidenceBadge = document.getElementById("mediaVisualConfidenceBadge");
const visualDescriptionText = document.getElementById("visualDescriptionText");
const unrelatedBadge = document.getElementById("unrelatedBadge");
const visualConceptsList = document.getElementById("visualConceptsList");

// Pillar 3: Text <-> Media Check Elements
const claimMatchBadge = document.getElementById("claimMatchBadge");
const claimReportedProblem = document.getElementById("claimReportedProblem");
const claimObservedProblem = document.getElementById("claimObservedProblem");
const mediaVerdictText = document.getElementById("mediaVerdictText");
const claimReasonText = document.getElementById("claimReasonText");

// Completeness Elements
const completenessScoreBadge = document.getElementById("completenessScoreBadge");
const missingFieldsContainer = document.getElementById("missingFieldsContainer");
const citizenSuggestionsList = document.getElementById("citizenSuggestionsList");

// Outputs
const model2JsonOutput = document.getElementById("model2JsonOutput");
const jsonOutput = document.getElementById("jsonOutput");

// Initialize on Load
document.addEventListener("DOMContentLoaded", () => {
  loadScenarios();
  setupWordCounter();
  setupDropzone();
  setupHelpers();
  setupInputListeners();
});

// Load Pre-built Scenarios from API (Strictly 5 scenarios)
async function loadScenarios() {
  try {
    const res = await fetch("/demo-scenarios");
    const scenarios = await res.json();

    scenarioCardsContainer.innerHTML = "";
    scenarios.forEach((sc, idx) => {
      const card = document.createElement("div");
      card.className = `scenario-card ${idx === 0 ? "scenario-flagship active" : ""}`;
      card.id = `card_${sc.id}`;

      let tagBadge = sc.badge || sc.category_expected;

      card.innerHTML = `
        <span class="scenario-tag">${tagBadge}</span>
        <h4>${sc.title}</h4>
        <p title="${sc.description}">${sc.description}</p>
      `;

      card.addEventListener("click", () => selectScenario(sc, card));
      scenarioCardsContainer.appendChild(card);
    });

    // Auto-select Flagship scenario on first load
    if (scenarios.length > 0) {
      selectScenario(scenarios[0], scenarioCardsContainer.children[0]);
    }
  } catch (err) {
    console.error("Failed to load scenarios:", err);
  }
}

// Select Scenario and Populate Form - executes real pipeline
function selectScenario(sc, cardElement) {
  document.querySelectorAll(".scenario-card").forEach(c => c.classList.remove("active"));
  if (cardElement) cardElement.classList.add("active");

  reportText.value = sc.text;
  reportLocation.value = sc.location || "";
  reportTimestamp.value = sc.timestamp || "";
  updateWordCount();

  if (sc.media_file) {
    demoAssetName.value = sc.media_file;
    activeFile = null;
    mediaFileInput.value = "";
    mediaFileName.textContent = sc.media_file;
    mediaPreviewImg.src = `/assets/${sc.media_file}`;
    mediaDropzone.style.display = "none";
    mediaPreviewContainer.style.display = "block";
  } else {
    clearMediaAttachment(false);
  }

  // Live execution through the actual Model 1 pipeline
  executeClassification();
}

// Media Removal (Section 17)
function clearMediaAttachment(triggerStale = true) {
  activeFile = null;
  demoAssetName.value = "";
  mediaFileInput.value = "";
  mediaFileName.textContent = "None";
  mediaPreviewImg.src = "";
  mediaPreviewContainer.style.display = "none";
  mediaDropzone.style.display = "block";

  if (triggerStale) {
    markInputsStale();
  }
}

function setupWordCounter() {
  reportText.addEventListener("input", updateWordCount);
}

function updateWordCount() {
  const words = reportText.value.trim().split(/\s+/).filter(Boolean).length;
  wordCounter.textContent = `${words} words`;
  wordCounter.style.color = words < 4 ? "var(--accent-rose)" : "var(--accent-emerald)";
}

// Stale State Handling (Section 16)
function markInputsStale() {
  currentReportJson = null;
  reviewBanner.className = "review-banner review-manual";
  reviewChip.textContent = "INPUT CHANGED";
  reviewChip.style.background = "rgba(245, 158, 11, 0.2)";
  reviewChip.style.color = "var(--accent-amber)";
  reviewTitle.textContent = "Input Changed — Execute Analysis Again";
  reviewSubtitle.textContent = "Inputs have been updated. Press 'Execute Structuring & Classification AI' to run fresh analysis.";

  latencyBadge.textContent = "Awaiting execution...";
  kpiConfidence.textContent = "Awaiting analysis";
  kpiCompleteness.textContent = "--";
  kpiMissingCount.textContent = "Pending execution";
  kpiMedia.textContent = activeFile || demoAssetName.value ? "PENDING" : "NO_MEDIA";
  kpiFramesChecked.textContent = "Pending execution";

  primaryDomainLabel.textContent = "--";
  problemTypeLabel.textContent = "--";
  domainConfidenceBadge.textContent = "--";
  domainConfidenceBar.style.width = "0%";
  severityLevelBadge.textContent = "PENDING";
  severityLevelBadge.className = "severity-badge sev-Low";
  textReasonText.textContent = "Awaiting execution...";
  severitySignalsList.innerHTML = `<span style="font-size: 0.75rem; color: var(--text-dim);">Awaiting analysis</span>`;

  const hasMedia = !!(activeFile || demoAssetName.value);
  visualDescriptionText.textContent = hasMedia ? '"Media attached — awaiting execution."' : '"No media provided."';
  visualDescriptionText.style.color = "var(--text-dim)";
  mediaVisualConfidenceBadge.textContent = "--";
  unrelatedBadge.textContent = "--";
  visualConceptsList.innerHTML = `<span style="font-size: 0.75rem; color: var(--text-dim);">${hasMedia ? "Awaiting visual inspection" : "No media provided."}</span>`;

  claimReportedProblem.textContent = "--";
  claimObservedProblem.textContent = "--";
  claimMatchBadge.textContent = "--";
  claimReasonText.textContent = '"Media comparison pending execution..."';
  mediaVerdictText.className = "media-verdict";
  mediaVerdictText.style.background = "rgba(255, 255, 255, 0.05)";
  mediaVerdictText.innerHTML = `<span>Status: Awaiting analysis</span>`;

  completenessScoreBadge.textContent = "--";
  missingFieldsContainer.innerHTML = `<span style="font-size: 0.75rem; color: var(--text-dim);">Awaiting analysis</span>`;
  citizenSuggestionsList.innerHTML = `<span style="font-size: 0.75rem; color: var(--text-dim);">Awaiting analysis</span>`;

  model2JsonOutput.innerHTML = `<code>{\n  "status": "Awaiting execution"\n}</code>`;
  jsonOutput.innerHTML = `<code>{\n  "status": "Awaiting execution"\n}</code>`;
}

function setupInputListeners() {
  reportText.addEventListener("input", markInputsStale);
  reportLocation.addEventListener("input", markInputsStale);
  reportTimestamp.addEventListener("input", markInputsStale);
}

function setupDropzone() {
  mediaDropzone.addEventListener("click", () => mediaFileInput.click());

  mediaFileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      handleFileSelected(e.target.files[0]);
    }
  });

  ["dragenter", "dragover"].forEach(evtName => {
    mediaDropzone.addEventListener(evtName, (e) => {
      e.preventDefault();
      mediaDropzone.classList.add("dragover");
    });
  });

  ["dragleave", "drop"].forEach(evtName => {
    mediaDropzone.addEventListener(evtName, (e) => {
      e.preventDefault();
      mediaDropzone.classList.remove("dragover");
    });
  });

  mediaDropzone.addEventListener("drop", (e) => {
    if (e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  btnRemoveMedia.addEventListener("click", () => clearMediaAttachment(true));
}

function handleFileSelected(file) {
  activeFile = file;
  demoAssetName.value = "";
  mediaFileName.textContent = `${file.name} (${Math.round(file.size / 1024)} KB)`;

  console.log(`[DEVELOPMENT LOG] File selected in browser: ${file.name} | MIME: ${file.type || "unknown"} | Size: ${file.size} bytes`);

  if (file.type.startsWith("image/")) {
    const reader = new FileReader();
    reader.onload = (e) => {
      mediaPreviewImg.src = e.target.result;
      mediaDropzone.style.display = "none";
      mediaPreviewContainer.style.display = "block";
    };
    reader.readAsDataURL(file);
  } else if (file.type.startsWith("video/")) {
    mediaPreviewImg.src = "";
    mediaDropzone.style.display = "none";
    mediaPreviewContainer.style.display = "block";
  }

  markInputsStale();
}

function setupHelpers() {
  if (btnDetectGps) {
    btnDetectGps.addEventListener("click", () => {
      reportLocation.value = "Opposite St. Xavier School Gate, Doranda, Ranchi (23.3440, 85.3090)";
      markInputsStale();
    });
  }

  if (btnNowTime) {
    btnNowTime.addEventListener("click", () => {
      reportTimestamp.value = new Date().toISOString();
      markInputsStale();
    });
  }

  const btnLoadMismatch = document.getElementById("btnLoadMismatch");
  if (btnLoadMismatch) {
    btnLoadMismatch.addEventListener("click", () => {
      demoAssetName.value = "unrelated_mismatch.jpg";
      activeFile = null;
      mediaFileName.textContent = "unrelated_mismatch.jpg";
      mediaPreviewImg.src = "/assets/unrelated_mismatch.jpg";
      mediaDropzone.style.display = "none";
      mediaPreviewContainer.style.display = "block";
      console.log("[DEVELOPMENT LOG] Loaded generic mismatch test asset: unrelated_mismatch.jpg");
      markInputsStale();
    });
  }

  const btnLoadPothole = document.getElementById("btnLoadPothole");
  if (btnLoadPothole) {
    btnLoadPothole.addEventListener("click", () => {
      demoAssetName.value = "pothole_road.jpg";
      activeFile = null;
      mediaFileName.textContent = "pothole_road.jpg";
      mediaPreviewImg.src = "/assets/pothole_road.jpg";
      mediaDropzone.style.display = "none";
      mediaPreviewContainer.style.display = "block";
      console.log("[DEVELOPMENT LOG] Loaded pothole asset: pothole_road.jpg");
      markInputsStale();
    });
  }

  btnCopyJson.addEventListener("click", () => {
    if (!currentReportJson) return;
    navigator.clipboard.writeText(JSON.stringify(currentReportJson, null, 2)).then(() => {
      btnCopyJson.textContent = "✓ Copied!";
      setTimeout(() => { btnCopyJson.textContent = "📋 Copy Full JSON"; }, 2000);
    });
  });

  reportForm.addEventListener("submit", (e) => {
    e.preventDefault();
    executeClassification();
  });
}

// Execute Structuring and Classification
async function executeClassification() {
  const text = reportText.value.trim();
  if (!text) {
    alert("Please enter a complaint description.");
    return;
  }

  setLoading(true);

  try {
    let result;
    const t0 = performance.now();

    if (activeFile) {
      // Multipart/form-data upload for custom uploaded files
      console.log(`[DEVELOPMENT LOG] File received for dispatch: ${activeFile.name} | MIME: ${activeFile.type} | size: ${activeFile.size} bytes`);
      console.log(`[DEVELOPMENT LOG] Vision processing started...`);

      const formData = new FormData();
      formData.append("text", text);
      formData.append("location", reportLocation.value.trim());
      formData.append("timestamp", reportTimestamp.value.trim());
      formData.append("media", activeFile);

      const res = await fetch("/classify-report", {
        method: "POST",
        body: formData
      });
      if (!res.ok) {
        throw new Error(`Server returned HTTP ${res.status}: ${res.statusText}`);
      }
      result = await res.json();
    } else {
      // JSON endpoint for text or demo asset testing
      const assetName = demoAssetName.value.trim() || null;
      if (assetName) {
        console.log(`[DEVELOPMENT LOG] Demo asset attached for dispatch: ${assetName}`);
        console.log(`[DEVELOPMENT LOG] Vision processing started...`);
      }
      const payload = {
        text: text,
        location: reportLocation.value.trim() || null,
        timestamp: reportTimestamp.value.trim() || null,
        demo_asset_name: assetName
      };

      const res = await fetch("/classify-report-json", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (!res.ok) {
        throw new Error(`Server returned HTTP ${res.status}: ${res.statusText}`);
      }
      result = await res.json();
    }

    const tEnd = performance.now();
    console.log(`[DEVELOPMENT LOG] Vision processing completed in ${Math.round(tEnd - t0)}ms`);
    if (result.media_relevance?.visual_analysis?.visual_concepts) {
      const conceptsStr = result.media_relevance.visual_analysis.visual_concepts
        .map(c => `${c.label} (${c.confidence.toFixed(2)})`)
        .join(", ");
      console.log(`[DEVELOPMENT LOG] Visual concepts returned: ${conceptsStr}`);
    }
    const comp = result.media_relevance?.claim_comparison;
    if (comp) {
      console.log(`[DEVELOPMENT LOG] Comparison completed: reported='${comp.reported_problem}', observed='${comp.observed_problem}', status=${comp.match_status}, confidence=${comp.confidence.toFixed(2)}`);
    }

    currentReportJson = result;
    renderResults(result);

  } catch (err) {
    console.error("Classification error:", err);
    showErrorState(err.message);
  } finally {
    setLoading(false);
  }
}

function setLoading(isLoading) {
  btnSubmit.disabled = isLoading;
  btnSpinner.style.display = isLoading ? "inline-block" : "none";
  btnText.textContent = isLoading ? "Running AI Models..." : "🚀 Execute Structuring & Classification AI";
}

function showErrorState(msg) {
  reviewBanner.className = "review-banner review-manual";
  reviewChip.textContent = "EXECUTION ERROR";
  reviewChip.style.background = "rgba(244, 63, 94, 0.2)";
  reviewChip.style.color = "var(--accent-rose)";
  reviewTitle.textContent = "Pipeline Execution Failed";
  reviewSubtitle.textContent = `Error: ${msg}. Please ensure backend server is operational.`;
}

// Render Results adhering to Model 1 Specification
function renderResults(data) {
  console.log("[RENDER START] Received Model 1 combined payload:", data);

  // Latency Badge
  if (latencyBadge && data.processing_metadata) {
    latencyBadge.textContent = `${data.processing_metadata.processing_time_ms} ms (Local Edge)`;
  }

  // Dynamic Top Banner (Sections 11 & 12)
  try {
    const matchStatus = data.media_relevance?.claim_comparison?.match_status || "NO_MEDIA";
    const isLowCompleteness = (data.completeness?.score || 0) < 0.50;

    if (reviewBanner && reviewChip && reviewTitle && reviewSubtitle) {
      if (matchStatus === "MISMATCH") {
        reviewBanner.className = "review-banner review-manual";
        reviewChip.textContent = "MEDIA MISMATCH DETECTED — HUMAN REVIEW";
        reviewChip.style.background = "rgba(244, 63, 94, 0.2)";
        reviewChip.style.color = "var(--accent-rose)";
        reviewTitle.textContent = "Media Mismatch Detected";
        reviewSubtitle.textContent = "The uploaded media may not support the reported problem. Human review recommended.";
      } else if (matchStatus === "UNCERTAIN") {
        reviewBanner.className = "review-banner review-manual";
        reviewChip.textContent = "ANALYSIS UNCERTAIN — HUMAN REVIEW";
        reviewChip.style.background = "rgba(245, 158, 11, 0.2)";
        reviewChip.style.color = "var(--accent-amber)";
        reviewTitle.textContent = "Analysis Uncertain";
        reviewSubtitle.textContent = data.media_relevance?.claim_comparison?.reason || "Human review recommended.";
      } else if (isLowCompleteness) {
        reviewBanner.className = "review-banner review-manual";
        reviewChip.textContent = "ADDITIONAL INFORMATION RECOMMENDED";
        reviewChip.style.background = "rgba(245, 158, 11, 0.2)";
        reviewChip.style.color = "var(--accent-amber)";
        reviewTitle.textContent = "Incomplete Complaint";
        reviewSubtitle.textContent = "Additional citizen information recommended.";
      } else if (data.severity?.level === "Critical") {
        reviewBanner.className = "review-banner review-manual";
        reviewChip.textContent = "CRITICAL HAZARD — HUMAN DISPATCH";
        reviewChip.style.background = "rgba(244, 63, 94, 0.2)";
        reviewChip.style.color = "var(--accent-rose)";
        reviewTitle.textContent = "Critical Hazard Alert";
        reviewSubtitle.textContent = data.severity?.signals?.[0] || "Emergency situation flagged.";
      } else {
        // Normal structured result - Never says "AUTOMATED ROUTING APPROVED" (Section 11)
        reviewBanner.className = "review-banner review-auto";
        reviewChip.textContent = "STRUCTURED REPORT READY FOR REVIEW";
        reviewChip.style.background = "rgba(16, 185, 129, 0.2)";
        reviewChip.style.color = "var(--accent-emerald)";
        reviewTitle.textContent = "Structured Civic Complaint";
        reviewSubtitle.textContent = "AI analysis complete — ready for human validation.";
      }
    }
  } catch (err) {
    console.error("Error rendering review banner:", err);
  }

  // Dynamic Top KPIs (Section 10)
  try {
    const matchStatus = data.media_relevance?.claim_comparison?.match_status || "NO_MEDIA";
    if (kpiConfidence) kpiConfidence.textContent = `${Math.round((data.overall_confidence || 0) * 100)}%`;
    if (kpiCompleteness) kpiCompleteness.textContent = `${Math.round((data.completeness?.score || 0) * 100)}%`;
    if (kpiMissingCount) kpiMissingCount.textContent = `${data.completeness?.missing_fields?.length || 0} missing fields`;

    if (kpiMedia) {
      kpiMedia.textContent = matchStatus;
      if (matchStatus === "MATCH") {
        kpiMedia.style.color = "var(--accent-emerald)";
      } else if (matchStatus === "MISMATCH") {
        kpiMedia.style.color = "var(--accent-rose)";
      } else if (matchStatus === "UNCERTAIN") {
        kpiMedia.style.color = "var(--accent-amber)";
      } else {
        kpiMedia.style.color = "var(--text-muted)";
      }
    }
    if (kpiFramesChecked) {
      kpiFramesChecked.textContent = `${data.media_relevance?.frames_checked || 0} frame(s) checked`;
    }
  } catch (err) {
    console.error("Error rendering KPIs:", err);
  }

  // CARD 1: REPORT UNDERSTANDING (Section 18)
  try {
    if (primaryDomainLabel) primaryDomainLabel.textContent = data.domain_classification?.category || "--";
    if (problemTypeLabel) problemTypeLabel.textContent = data.domain_classification?.problem_type || "--";
    const domConfPct = Math.round((data.domain_classification?.confidence || 0) * 100);
    if (domainConfidenceBadge) domainConfidenceBadge.textContent = `${domConfPct}% Conf.`;
    if (domainConfidenceBar) domainConfidenceBar.style.width = `${domConfPct}%`;
    if (textReasonText) textReasonText.textContent = data.domain_classification?.reason || "--";

    if (severityLevelBadge && data.severity) {
      severityLevelBadge.textContent = (data.severity.level || "Low").toUpperCase();
      severityLevelBadge.className = `severity-badge sev-${data.severity.level}`;
    }
    if (severityConfidenceBadge && data.severity) {
      severityConfidenceBadge.textContent = `${Math.round((data.severity.confidence || 0) * 100)}% Conf.`;
    }

    if (severitySignalsList) {
      severitySignalsList.innerHTML = "";
      if (data.severity?.signals && data.severity.signals.length > 0) {
        data.severity.signals.forEach(sig => {
          const chip = document.createElement("span");
          chip.className = "tag-chip";
          chip.textContent = sig;
          severitySignalsList.appendChild(chip);
        });
      } else {
        severitySignalsList.innerHTML = `<span style="font-size: 0.75rem; color: var(--text-dim);">No hazard signals</span>`;
      }
    }
    console.log("[RENDER PILLAR 1 SUCCESS] Report Understanding updated.");
  } catch (err) {
    console.error("Error rendering Pillar 1 (Report Understanding):", err);
  }

  // CARD 2: MEDIA UNDERSTANDING (Section 5 & 18)
  try {
    if (data.media_relevance?.provided && data.media_relevance?.visual_analysis) {
      const vis = data.media_relevance.visual_analysis;
      if (visualDescriptionText) {
        visualDescriptionText.textContent = `"${vis.visual_description || 'Visual observation recorded.'}"`;
        visualDescriptionText.style.color = "#f1f5f9";
      }

      const topConceptConf = vis.visual_concepts && vis.visual_concepts.length > 0
        ? Math.round(vis.visual_concepts[0].confidence * 100)
        : 80;
      if (mediaVisualConfidenceBadge) {
        mediaVisualConfidenceBadge.textContent = `${topConceptConf}% Visual Conf.`;
      }

      if (unrelatedBadge) {
        if (vis.unrelated_content) {
          unrelatedBadge.textContent = "YES (Unrelated Content)";
          unrelatedBadge.style.background = "rgba(244, 63, 94, 0.2)";
          unrelatedBadge.style.color = "var(--accent-rose)";
        } else {
          unrelatedBadge.textContent = "NO (Civic Domain)";
          unrelatedBadge.style.background = "rgba(16, 185, 129, 0.2)";
          unrelatedBadge.style.color = "var(--accent-emerald)";
        }
      }

      if (visualConceptsList) {
        visualConceptsList.innerHTML = "";
        if (vis.visual_concepts && vis.visual_concepts.length > 0) {
          vis.visual_concepts.forEach(vc => {
            const chip = document.createElement("span");
            chip.className = "tag-chip";
            chip.textContent = `${vc.label} (${Math.round(vc.confidence * 100)}%)`;
            visualConceptsList.appendChild(chip);
          });
        } else {
          visualConceptsList.innerHTML = `<span style="font-size: 0.75rem; color: var(--text-dim);">No concepts detected</span>`;
        }
      }
    } else {
      if (visualDescriptionText) {
        visualDescriptionText.textContent = '"No media provided."';
        visualDescriptionText.style.color = "var(--text-dim)";
      }
      if (mediaVisualConfidenceBadge) mediaVisualConfidenceBadge.textContent = "N/A";
      if (unrelatedBadge) unrelatedBadge.textContent = "N/A";
      if (visualConceptsList) {
        visualConceptsList.innerHTML = `<span style="font-size: 0.75rem; color: var(--text-dim);">No media provided.</span>`;
      }
    }
    console.log("[RENDER PILLAR 2 SUCCESS] Media Understanding updated.");
  } catch (err) {
    console.error("Error rendering Pillar 2 (Media Understanding):", err);
  }

  // CARD 3: TEXT <-> MEDIA CHECK (Section 6, 7 & 18)
  try {
    const claim = data.media_relevance?.claim_comparison;
    if (claim) {
      if (claimReportedProblem) claimReportedProblem.textContent = claim.reported_problem || "--";
      if (claimObservedProblem) claimObservedProblem.textContent = claim.observed_problem || "--";
      if (claimMatchBadge) claimMatchBadge.textContent = `${Math.round((claim.confidence || 0) * 100)}% Conf.`;
      if (claimReasonText) claimReasonText.textContent = `"${claim.reason || ''}"`;

      if (mediaVerdictText) {
        if (claim.match_status === "MATCH") {
          mediaVerdictText.className = "media-verdict verdict-match";
          mediaVerdictText.innerHTML = `<span>✓ MATCH — Evidence Visibly Supports Complaint</span>`;
        } else if (claim.match_status === "MISMATCH") {
          mediaVerdictText.className = "media-verdict verdict-mismatch";
          mediaVerdictText.innerHTML = `<span>⚠ MISMATCH — Media Does NOT Depict Reported Issue</span>`;
        } else if (claim.match_status === "UNCERTAIN") {
          mediaVerdictText.className = "media-verdict";
          mediaVerdictText.style.background = "rgba(245, 158, 11, 0.15)";
          mediaVerdictText.style.borderColor = "var(--accent-amber)";
          mediaVerdictText.innerHTML = `<span style="color: var(--accent-amber);">? UNCERTAIN — Blurry / Low Quality Photo</span>`;
        } else {
          mediaVerdictText.className = "media-verdict";
          mediaVerdictText.style.background = "rgba(255, 255, 255, 0.05)";
          mediaVerdictText.style.borderColor = "rgba(255, 255, 255, 0.1)";
          mediaVerdictText.innerHTML = `<span style="color: var(--text-muted);">○ NO_MEDIA — Text-Only Grievance</span>`;
        }
      }
    }
    console.log("[RENDER PILLAR 3 SUCCESS] Text <-> Media Check updated.");
  } catch (err) {
    console.error("Error rendering Pillar 3 (Text <-> Media Check):", err);
  }

  // CARD 4: COMPLETENESS & RECOMMENDATIONS (Section 8 & 18)
  try {
    if (completenessScoreBadge) {
      completenessScoreBadge.textContent = `${Math.round((data.completeness?.score || 0) * 100)}%`;
    }

    if (missingFieldsContainer) {
      missingFieldsContainer.innerHTML = "";
      if (data.completeness?.missing_fields && data.completeness.missing_fields.length > 0) {
        data.completeness.missing_fields.forEach(f => {
          const chip = document.createElement("span");
          chip.className = "missing-chip";
          chip.textContent = `Missing: ${f.replace('_', ' ')}`;
          missingFieldsContainer.appendChild(chip);
        });
      } else {
        missingFieldsContainer.innerHTML = `<span style="font-size: 0.75rem; color: var(--accent-emerald);">✓ All required fields provided</span>`;
      }
    }

    if (citizenSuggestionsList) {
      citizenSuggestionsList.innerHTML = "";
      if (data.completeness?.suggestions_for_citizen && data.completeness.suggestions_for_citizen.length > 0) {
        data.completeness.suggestions_for_citizen.forEach(sug => {
          const li = document.createElement("div");
          li.style.cssText = "font-size: 0.75rem; color: var(--text-muted); margin-bottom: 4px;";
          li.textContent = `💡 ${sug}`;
          citizenSuggestionsList.appendChild(li);
        });
      } else {
        citizenSuggestionsList.innerHTML = `<span style="font-size: 0.75rem; color: var(--text-dim);">No action needed from citizen</span>`;
      }
    }
    console.log("[RENDER PILLAR 4 SUCCESS] Completeness & Guidance updated.");
  } catch (err) {
    console.error("Error rendering Pillar 4 (Completeness & Guidance):", err);
  }

  // DOWNSTREAM MODEL 2 HANDOFF (Section 19 & 20)
  try {
    const model2Contract = {
      reported_domain: data.domain_classification?.category,
      reported_problem: data.domain_classification?.problem_type,
      media_visual_description: data.media_relevance?.visual_analysis ? data.media_relevance.visual_analysis.visual_description : null,
      media_visual_concepts: data.media_relevance?.visual_analysis ? data.media_relevance.visual_analysis.visual_concepts : [],
      media_match_status: data.media_relevance?.claim_comparison?.match_status,
      media_match_confidence: data.media_relevance?.claim_comparison?.confidence
    };
    if (model2JsonOutput) {
      model2JsonOutput.innerHTML = `<code>${escapeHtml(JSON.stringify(model2Contract, null, 2))}</code>`;
    }
  } catch (err) {
    console.error("Error rendering Model 2 Handoff:", err);
  }

  // Strict Section 17 JSON Viewer
  try {
    if (jsonOutput) {
      jsonOutput.innerHTML = `<code>${escapeHtml(JSON.stringify(data, null, 2))}</code>`;
    }
  } catch (err) {
    console.error("Error rendering Raw JSON:", err);
  }

  console.log("[RENDER COMPLETE] All 4 UI cards and diagnostic sections updated successfully!");
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}
