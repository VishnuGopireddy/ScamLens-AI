(() => {
  "use strict";

  const GMAIL_POLL_INTERVAL_SEC = 60;

  const state = {
    activeTab: "investigator",
    activeEmailSource: "local",
    uploadedImages: [], // [{ filename, data_base64, previewUrl }]
    emails: [],
    selectedEmail: null,
    samples: [],
    architecture: null,
    selectedComponentId: "orchestrator",
    selectedToolName: null,
    currentFindings: [],
    evidenceFilter: "ALL",
    timerInterval: null,
    startTimeMs: 0,
    gmailReady: false,
    isScanning: false,
    polledGmailIds: new Set(),
    gmailPollTickId: null,
    gmailPollNextInSec: GMAIL_POLL_INTERVAL_SEC,
    gmailLastPollNote: "",
    gmailNewAlertCount: 0,
  };

  // ---------------------------------------------------------------------------
  // Utilities & SSE Streaming
  // ---------------------------------------------------------------------------
  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function getStrategy() {
    return document.getElementById("strategySelect").value || "linear";
  }

  function mountResultsTemplate(slotId) {
    const slot = document.getElementById(slotId);
    const tpl = document.getElementById("resultsWorkspaceTemplate");
    // Move existing results-stack if already initialized, or clone template once
    let existing = document.querySelector(".results-stack");
    if (!existing) {
      slot.appendChild(tpl.content.cloneNode(true));
    } else if (existing.parentElement !== slot) {
      slot.appendChild(existing);
    }
  }

  function startLiveTimer() {
    stopLiveTimer();
    state.startTimeMs = performance.now();
    const timerPill = document.getElementById("liveTimerPill");
    const dot = document.getElementById("livePulseDot");
    if (dot) {
      dot.className = "pulse-dot active";
    }
    state.timerInterval = setInterval(() => {
      if (!timerPill) return;
      const secs = ((performance.now() - state.startTimeMs) / 1000).toFixed(1);
      timerPill.textContent = `${secs}s`;
    }, 100);
  }

  function stopLiveTimer(finalState = "done") {
    if (state.timerInterval) {
      clearInterval(state.timerInterval);
      state.timerInterval = null;
    }
    const timerPill = document.getElementById("liveTimerPill");
    if (timerPill && state.startTimeMs) {
      const secs = ((performance.now() - state.startTimeMs) / 1000).toFixed(2);
      timerPill.textContent = `${secs}s`;
    }
    const dot = document.getElementById("livePulseDot");
    if (dot) {
      dot.className = `pulse-dot ${finalState}`;
    }
  }

  function resetLiveFeed(subtitleText) {
    const feed = document.getElementById("liveStatusFeed");
    const snapshot = document.getElementById("liveEmailSnapshot");
    const report = document.getElementById("reportContainer");
    const subtitle = document.getElementById("liveStageSubtitle");
    if (feed) feed.innerHTML = "";
    if (snapshot) {
      snapshot.innerHTML = "";
      snapshot.classList.add("hidden");
    }
    if (report) report.classList.add("hidden");
    if (subtitle) subtitle.textContent = subtitleText || "Running investigation...";
  }

  function appendStatusEvent(ev, isError = false) {
    const feed = document.getElementById("liveStatusFeed");
    const subtitle = document.getElementById("liveStageSubtitle");
    if (!feed) return;

    feed.querySelectorAll(".feed-item.latest").forEach((el) => el.classList.remove("latest"));
    const li = document.createElement("li");
    li.className = `feed-item latest${isError ? " error" : ""}`;
    li.innerHTML = `
      <span class="feed-time">${escapeHtml(ev.timestamp || "")}</span>
      <span class="feed-stage">${escapeHtml(ev.stage || "status")}</span>
      <div class="feed-body">
        <div class="feed-msg">${escapeHtml(ev.message || "")}</div>
        ${ev.detail ? `<div class="feed-detail">${escapeHtml(ev.detail)}</div>` : ""}
      </div>
    `;
    feed.appendChild(li);
    feed.scrollTop = feed.scrollHeight;
    if (subtitle && ev.message) {
      subtitle.textContent = ev.message;
    }

    // When an email is parsed during live streaming, show a clear inline snapshot!
    if (ev.stage === "email_parsed" && ev.data && ev.data.email) {
      const em = ev.data.email;
      const snapshot = document.getElementById("liveEmailSnapshot");
      if (snapshot) {
        snapshot.classList.remove("hidden");
        snapshot.innerHTML = `
          <div><strong>Email Being Analyzed:</strong> ${escapeHtml(em.subject)}</div>
          <div class="hint" style="margin-top:3px;">
            <strong>From:</strong> ${escapeHtml(em.sender || em.sender_email)} &nbsp;|&nbsp;
            <strong>Auth:</strong> SPF=${escapeHtml(em.spf_status)} / DKIM=${escapeHtml(em.dkim_status)} / DMARC=${escapeHtml(em.dmarc_status)} &nbsp;|&nbsp;
            <strong>URLs:</strong> ${(em.extracted_urls || []).length} &nbsp;|&nbsp;
            <strong>Attachments:</strong> ${(em.attachments || []).length}
          </div>
        `;
      }
      renderParsedEmail(em);
    }
  }

  async function streamSSE(url, body, handlers) {
    const resp = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!resp.ok) {
      const txt = await resp.text();
      throw new Error(`HTTP ${resp.status}: ${txt}`);
    }

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const frames = buffer.split("\n\n");
      buffer = frames.pop() || "";

      for (const frame of frames) {
        if (!frame.trim() || frame.startsWith(":")) continue;
        let eventName = "message";
        const dataLines = [];
        for (const line of frame.split("\n")) {
          if (line.startsWith("event:")) {
            eventName = line.slice(6).trim();
          } else if (line.startsWith("data:")) {
            dataLines.push(line.slice(5).trim());
          }
        }
        if (!dataLines.length) continue;
        let parsedData = {};
        try {
          parsedData = JSON.parse(dataLines.join("\n"));
        } catch {
          parsedData = { message: dataLines.join("\n") };
        }
        if (handlers[eventName]) {
          handlers[eventName](parsedData);
        }
      }
    }
  }

  // ---------------------------------------------------------------------------
  // Result Renderer
  // ---------------------------------------------------------------------------
  function verdictClass(verdict) {
    const v = (verdict || "").toLowerCase();
    if (v.includes("likely scam")) return "verdict-scam";
    if (v.includes("suspicious")) return "verdict-suspicious";
    if (v.includes("insufficient")) return "verdict-insufficient";
    return "verdict-clear";
  }

  function renderEvidenceCards() {
    const list = document.getElementById("evidenceList");
    if (!list) return;
    const filtered = state.evidenceFilter === "ALL"
      ? state.currentFindings
      : state.currentFindings.filter((f) => f.category === state.evidenceFilter || f.severity === state.evidenceFilter);

    if (!filtered.length) {
      list.innerHTML = `<p class="empty-state">No evidence indicators matched this filter.</p>`;
      return;
    }

    list.innerHTML = filtered.map((item) => {
      const sev = item.severity || "INFO";
      const sevBadge = `badge-${sev.toLowerCase()}`;
      const verifiedBadge = item.is_verified
        ? `<span class="badge badge-verified">Verified</span>`
        : `<span class="badge badge-heuristic">Heuristic</span>`;
      const metaKeys = item.metadata && Object.keys(item.metadata).length > 0;
      return `
        <div class="evidence-card sev-${escapeHtml(sev)}">
          <div class="evidence-top">
            <span class="badge ${sevBadge}">${escapeHtml(sev)}</span>
            <span class="badge badge-info">${escapeHtml(item.category)}</span>
            ${verifiedBadge}
            <span class="badge badge-heuristic">${escapeHtml(item.source)}</span>
          </div>
          <div class="evidence-summary">${escapeHtml(item.summary)}</div>
          ${item.details ? `<p class="evidence-details">${escapeHtml(item.details)}</p>` : ""}
          ${metaKeys ? `
            <details class="evidence-meta">
              <summary>Metadata</summary>
              <pre>${escapeHtml(JSON.stringify(item.metadata, null, 2))}</pre>
            </details>
          ` : ""}
        </div>
      `;
    }).join("");
  }

  function renderInvestigationResult(result, incidentStage = "PRE_ACTION") {
    const report = document.getElementById("reportContainer");
    if (!report || !result) return;
    report.classList.remove("hidden");

    const postAlert = document.getElementById("postActionAlert");
    const hasPostFinding = (result.evidence_findings || []).some((f) => f.source === "incident_stage_tracker");
    if (incidentStage === "POST_ACTION" || hasPostFinding) {
      postAlert.classList.remove("hidden");
    } else {
      postAlert.classList.add("hidden");
    }

    const vBadge = document.getElementById("verdictBadge");
    vBadge.textContent = result.verdict;
    vBadge.className = `verdict-badge ${verdictClass(result.verdict)}`;

    document.getElementById("reportSummary").textContent = result.summary || "";

    const score = Number(result.risk_score || 0);
    document.getElementById("riskScoreValue").textContent = String(score);
    const bar = document.getElementById("riskScoreBar");
    bar.style.width = `${Math.max(4, Math.min(100, score))}%`;
    bar.style.background = score >= 70 ? "var(--danger)" : score >= 35 ? "var(--warn)" : "var(--ok)";

    const confPct = Math.round(Number(result.confidence || 0) * 100);
    document.getElementById("confidenceValue").textContent = String(confPct);
    document.getElementById("confidenceBar").style.width = `${confPct}%`;

    const recsEl = document.getElementById("recommendationsList");
    recsEl.innerHTML = (result.recommended_actions || [])
      .map((act) => `<li>${escapeHtml(act)}</li>`)
      .join("");

    state.currentFindings = result.evidence_findings || [];
    state.evidenceFilter = "ALL";
    document.getElementById("evidenceCount").textContent = String(state.currentFindings.length);

    const categories = Array.from(new Set(state.currentFindings.map((f) => f.category)));
    const filtersEl = document.getElementById("evidenceFilters");
    filtersEl.innerHTML = ["ALL", ...categories]
      .map((cat) => `<button type="button" class="filter-pill ${cat === "ALL" ? "active" : ""}" data-filter="${escapeHtml(cat)}">${escapeHtml(cat)}</button>`)
      .join("");
    filtersEl.querySelectorAll(".filter-pill").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.evidenceFilter = btn.dataset.filter;
        filtersEl.querySelectorAll(".filter-pill").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        renderEvidenceCards();
      });
    });
    renderEvidenceCards();

    const uncList = document.getElementById("uncertaintiesList");
    const uncSection = document.getElementById("uncertaintiesSection");
    if ((result.uncertainties || []).length) {
      uncSection.classList.remove("hidden");
      uncList.innerHTML = result.uncertainties.map((u) => `<li>${escapeHtml(u)}</li>`).join("");
    } else {
      uncSection.classList.add("hidden");
    }

    const provList = document.getElementById("provenanceList");
    const provSection = document.getElementById("provenanceSection");
    if ((result.provenance || []).length) {
      provSection.classList.remove("hidden");
      provList.innerHTML = result.provenance
        .map((p) => `<div class="prov-row">${escapeHtml(JSON.stringify(p))}</div>`)
        .join("");
    } else {
      provSection.classList.add("hidden");
    }

    document.getElementById("disclaimerText").textContent = result.disclaimer || "";
  }

  // ---------------------------------------------------------------------------
  // System Health, Registry & Samples
  // ---------------------------------------------------------------------------
  async function loadSystemStatus() {
    try {
      const [health, gmail] = await Promise.all([
        fetch("/api/v1/health").then((r) => r.json()),
        fetch("/api/v1/emails/gmail/status").then((r) => r.json()),
      ]);

      const pillProv = document.getElementById("pillProvider");
      pillProv.textContent = `AI: ${health.ai_provider} (${health.ai_model})`;
      pillProv.className = "pill pill-info";

      const pillIntel = document.getElementById("pillIntel");
      pillIntel.textContent = health.mock_intelligence ? "Intel: Simulated Mock" : "Intel: Live RDAP / VT";
      pillIntel.className = `pill ${health.mock_intelligence ? "pill-warn" : "pill-ok"}`;

      const pillPriv = document.getElementById("pillPrivacy");
      pillPriv.textContent = health.enable_pii_redaction ? "Privacy Guard: ON" : "Privacy Guard: OFF";
      pillPriv.className = `pill ${health.enable_pii_redaction ? "pill-ok" : "pill-warn"}`;

      const pillGmail = document.getElementById("pillGmail");
      state.gmailReady = Boolean(gmail.ready);
      pillGmail.style.cursor = "pointer";
      pillGmail.title = "Open Live Gmail Forensics";

      const banner = document.getElementById("gmailAuthBanner");
      if (banner) {
        banner.textContent = `Gmail OAuth Status: ${gmail.status_note} (credentials.json: ${gmail.credentials_exists ? "found" : "missing"}, token.json: ${gmail.token_exists ? "found" : "missing"})`;
        banner.className = `info-banner ${gmail.ready ? "ok" : "warn"}`;
      }
      syncGmailAutoPollState();
    } catch (err) {
      console.error("Failed to fetch health:", err);
    }
  }

  async function loadSamplesAndRegistry() {
    try {
      const [samplesResp, regResp] = await Promise.all([
        fetch("/api/v1/samples").then((r) => r.json()),
        fetch("/api/v1/registry").then((r) => r.json()),
      ]);

      state.samples = samplesResp.samples || [];
      const select = document.getElementById("samplePresetSelect");
      state.samples.forEach((s) => {
        const opt = document.createElement("option");
        opt.value = s.id;
        opt.textContent = `${s.id}: ${s.name}`;
        select.appendChild(opt);
      });

      const casesDiv = document.getElementById("benchmarkCasesContainer");
      casesDiv.innerHTML = state.samples.map((s) => `
        <div class="sample-case-card">
          <div>
            <strong>${escapeHtml(s.id)} — ${escapeHtml(s.name)}</strong>
            <div class="hint">${escapeHtml((s.submission.text || "").slice(0, 110))}...</div>
          </div>
          <button type="button" class="btn btn-secondary btn-sm" data-sample-id="${escapeHtml(s.id)}">Load &amp; Run</button>
        </div>
      `).join("");
      casesDiv.querySelectorAll("[data-sample-id]").forEach((btn) => {
        btn.addEventListener("click", () => {
          applySampleCase(btn.dataset.sampleId);
          switchTab("investigator");
          runMultimodalInvestigation();
        });
      });

      const banks = regResp.banks || {};
      document.getElementById("registryBanksContainer").innerHTML = Object.entries(banks).map(([key, b]) => `
        <div class="registry-item">
          <strong>${escapeHtml(b.official_name)} (${escapeHtml(key.toUpperCase())})</strong>
          <div class="hint">Domains: ${(b.official_domains || []).map(escapeHtml).join(", ")}</div>
          <div class="hint">SMS Headers: ${(b.sms_headers || []).map(escapeHtml).join(", ")} | Helpline: ${escapeHtml(b.helpline)}</div>
        </div>
      `).join("");

      const gov = regResp.government_services || {};
      document.getElementById("registryGovContainer").innerHTML = Object.entries(gov).map(([key, g]) => `
        <div class="registry-item">
          <strong>${escapeHtml(g.name || key)}</strong>
          <div class="hint">${g.official_domains ? `Domains: ${g.official_domains.map(escapeHtml).join(", ")} | ` : ""}${g.portal ? `Portal: ${escapeHtml(g.portal)} | ` : ""}Helpline: ${escapeHtml(g.national_helpline || g.helpline || "N/A")}</div>
        </div>
      `).join("");

      document.getElementById("registryUpiRules").innerHTML = (regResp.upi_legitimacy_guidelines || [])
        .map((rule) => `<li>${escapeHtml(rule)}</li>`)
        .join("");
    } catch (err) {
      console.error("Failed loading samples/registry:", err);
    }
  }

  function applySampleCase(sampleId) {
    const sample = state.samples.find((s) => s.id === sampleId);
    if (!sample) return;
    const sub = sample.submission || {};
    document.getElementById("inputText").value = sub.text || "";
    document.getElementById("charCount").textContent = String((sub.text || "").length);
    document.getElementById("inputUrls").value = (sub.urls || []).join("\n");
    document.getElementById("inputQr").value = (sub.qr_payloads || [])[0] || "";
    updateQrLivePreview();
    document.getElementById("inputContext").value = sub.context_description || "";
    const stageVal = sub.incident_stage || "PRE_ACTION";
    const radio = document.querySelector(`input[name="incidentStage"][value="${stageVal}"]`);
    if (radio) radio.checked = true;
  }

  // ---------------------------------------------------------------------------
  // Tab 1: Multimodal Investigator
  // ---------------------------------------------------------------------------
  function updateQrLivePreview() {
    const val = document.getElementById("inputQr").value.trim();
    const box = document.getElementById("qrLivePreview");
    if (!val) {
      box.classList.add("hidden");
      return;
    }
    if (val.toLowerCase().startsWith("upi://pay")) {
      try {
        const qs = new URLSearchParams(val.split("?")[1] || "");
        box.innerHTML = `<strong>UPI Preview:</strong> Payee VPA=<code>${escapeHtml(qs.get("pa") || "unknown")}</code> | Name=${escapeHtml(qs.get("pn") || "unknown")}${qs.get("am") ? ` | Amount=INR ${escapeHtml(qs.get("am"))}` : ""}`;
        box.classList.remove("hidden");
        return;
      } catch {}
    }
    box.innerHTML = `<strong>QR Payload:</strong> ${escapeHtml(val.slice(0, 120))}`;
    box.classList.remove("hidden");
  }

  function handleImageFiles(files) {
    Array.from(files).forEach((file) => {
      if (!file.type.startsWith("image/")) return;
      const reader = new FileReader();
      reader.onload = (e) => {
        state.uploadedImages.push({
          filename: file.name,
          data_base64: e.target.result,
          previewUrl: e.target.result,
        });
        renderImagePreviews();
      };
      reader.readAsDataURL(file);
    });
  }

  function renderImagePreviews() {
    const list = document.getElementById("imagePreviewList");
    list.innerHTML = state.uploadedImages.map((img, idx) => `
      <div class="img-thumb">
        <img src="${img.previewUrl}" alt="${escapeHtml(img.filename)}" />
        <button type="button" data-remove-img="${idx}" title="Remove">&times;</button>
        <span>${escapeHtml(img.filename)}</span>
      </div>
    `).join("");
    list.querySelectorAll("[data-remove-img]").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.uploadedImages.splice(Number(btn.dataset.removeImg), 1);
        renderImagePreviews();
      });
    });
  }

  async function runMultimodalInvestigation() {
    mountResultsTemplate("multimodalResultsSlot");
    const runBtn = document.getElementById("runInvestigateBtn");
    runBtn.disabled = true;
    state.isScanning = true;

    const text = document.getElementById("inputText").value;
    const urlsRaw = document.getElementById("inputUrls").value;
    const urls = urlsRaw.split(/[\n,]+/).map((u) => u.trim()).filter(Boolean);
    const qr = document.getElementById("inputQr").value.trim();
    const context = document.getElementById("inputContext").value.trim();
    const stageEl = document.querySelector('input[name="incidentStage"]:checked');
    const incidentStage = stageEl ? stageEl.value : "PRE_ACTION";

    resetLiveFeed("Streaming live multimodal checks...");
    startLiveTimer();

    try {
      await streamSSE("/api/v1/investigate/stream", {
        text: text || null,
        urls,
        qr_payloads: qr ? [qr] : [],
        uploaded_images: state.uploadedImages.map((i) => ({ filename: i.filename, data_base64: i.data_base64 })),
        context_description: context || null,
        incident_stage: incidentStage,
        strategy: getStrategy(),
      }, {
        status: (ev) => appendStatusEvent(ev),
        result: (data) => {
          stopLiveTimer("done");
          renderInvestigationResult(data.investigation, incidentStage);
        },
        error: (err) => {
          stopLiveTimer("error");
          appendStatusEvent({ stage: "error", message: err.message, timestamp: err.timestamp }, true);
        },
      });
    } catch (err) {
      stopLiveTimer("error");
      appendStatusEvent({ stage: "error", message: err.message }, true);
    } finally {
      state.isScanning = false;
      runBtn.disabled = false;
    }
  }

  // ---------------------------------------------------------------------------
  // Tab 2: Email & Gmail Forensics
  // ---------------------------------------------------------------------------
  function authPill(label, val) {
    const v = (val || "unknown").toLowerCase();
    const cls = v === "pass" ? "badge-verified" : v.includes("fail") ? "badge-critical" : "badge-info";
    return `<span class="badge ${cls}">${escapeHtml(label)}: ${escapeHtml(v)}</span>`;
  }

  function renderEmailList(emails, sourceLabel, sourceKind = "local") {
    state.emails = (emails || []).map((em) => ({ ...em, _source: em._source || sourceKind }));
    const listEl = document.getElementById("emailList");
    document.getElementById("emailListTitle").textContent = sourceLabel || "Inbox Messages";
    document.getElementById("emailListCount").textContent = `${state.emails.length} message(s)`;

    if (!state.emails.length) {
      listEl.innerHTML = `<p class="empty-state">No emails found.</p>`;
      return;
    }

    listEl.innerHTML = state.emails.map((em) => {
      const selected = state.selectedEmail && state.selectedEmail.id === em.id ? " selected" : "";
      const verdictTag = em._verdict
        ? `<span class="badge ${em._risk_score >= 70 ? "badge-critical" : em._risk_score >= 35 ? "badge-medium" : "badge-verified"}">${escapeHtml(em._risk_score)}/100</span>`
        : `<span class="badge badge-info">${(em.extracted_urls || []).length} URL</span>`;
      return `
        <div class="email-row${selected}" data-email-id="${escapeHtml(em.id)}">
          <div class="email-row-main">
            <div class="email-row-subject">${escapeHtml(em.subject || "(No Subject)")}</div>
            <div class="email-row-meta">${escapeHtml(em.sender || em.sender_email)} &bull; ${escapeHtml(em.date || "")}</div>
          </div>
          <div class="email-row-badges">${verdictTag}</div>
        </div>
      `;
    }).join("");

    listEl.querySelectorAll(".email-row").forEach((row) => {
      row.addEventListener("click", () => {
        const found = state.emails.find((e) => e.id === row.dataset.emailId);
        if (found) {
          renderParsedEmail(found);
          listEl.querySelectorAll(".email-row").forEach((r) => r.classList.remove("selected"));
          row.classList.add("selected");
          if (found._investigation) {
            mountResultsTemplate("emailResultsSlot");
            renderInvestigationResult(found._investigation);
          }
        }
      });
    });
  }

  function renderParsedEmail(em) {
    state.selectedEmail = em;
    const box = document.getElementById("parsedEmailInspector");
    box.classList.remove("hidden");

    document.getElementById("parsedSubject").textContent = em.subject || "(No Subject)";
    document.getElementById("parsedHeadersGrid").innerHTML = `
      <div><strong>ID:</strong> <code>${escapeHtml(em.id)}</code></div>
      <div><strong>From:</strong> ${escapeHtml(em.sender || em.sender_email)}</div>
      <div><strong>Reply-To:</strong> ${escapeHtml(em.reply_to || "None")}</div>
      <div><strong>Date:</strong> ${escapeHtml(em.date || "Unknown")}</div>
    `;
    document.getElementById("parsedAuthBadges").innerHTML =
      authPill("SPF", em.spf_status) +
      authPill("DKIM", em.dkim_status) +
      authPill("DMARC", em.dmarc_status);

    const attBox = document.getElementById("parsedAttachmentsBox");
    if ((em.attachments || []).length) {
      attBox.classList.remove("hidden");
      attBox.innerHTML = `<strong>Attachments:</strong> ${em.attachments.map((a) => `<code>${escapeHtml(a.filename)}</code> (${a.size_bytes} B)`).join(", ")}`;
    } else {
      attBox.classList.add("hidden");
    }

    const urlBox = document.getElementById("parsedUrlsBox");
    if ((em.extracted_urls || []).length) {
      urlBox.classList.remove("hidden");
      urlBox.innerHTML = `<strong>Extracted URLs (${em.extracted_urls.length}):</strong><ul class="parsed-url-list">${em.extracted_urls.map((u) => `<li><code>${escapeHtml(u)}</code></li>`).join("")}</ul>`;
    } else {
      urlBox.classList.add("hidden");
    }

    document.getElementById("parsedBodyPreview").textContent = em.email_content || "(Empty body)";
  }

  async function loadLocalEmailsList() {
    mountResultsTemplate("emailResultsSlot");
    resetLiveFeed("Loading local email dataset...");
    try {
      const data = await fetch("/api/v1/emails/local").then((r) => r.json());
      if (data.detail) throw new Error(data.detail);
      document.getElementById("localDatasetInfo").textContent = `${data.source} (${data.count} emails)`;
      renderEmailList(data.emails || [], `Local Dataset (${data.source})`, "local");
      appendStatusEvent({ stage: "inbox_loaded", message: `Loaded ${data.count} emails from ${data.source}`, timestamp: new Date().toTimeString().slice(0, 8) });
      if (state.emails.length) {
        renderParsedEmail(state.emails[0]);
      }
    } catch (err) {
      appendStatusEvent({ stage: "error", message: err.message }, true);
    }
  }

  function getGmailQuery() {
    const el = document.getElementById("gmailQueryInput");
    return el ? el.value.trim() : "-in:trash -in:drafts";
  }

  async function fetchGmailEmailsList() {
    mountResultsTemplate("emailResultsSlot");
    resetLiveFeed("Fetching Gmail messages...");
    startLiveTimer();
    const query = getGmailQuery();
    const maxResults = Number(document.getElementById("gmailMaxInput").value || 5);
    appendStatusEvent({ stage: "reading_gmail", message: `Querying Gmail API (q="${query || "ALL MAIL"}", max=${maxResults})...`, timestamp: new Date().toTimeString().slice(0, 8) });

    try {
      const resp = await fetch(`/api/v1/emails/gmail?query=${encodeURIComponent(query)}&max_results=${maxResults}&include_spam_trash=true`);
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || "Failed to fetch Gmail");
      stopLiveTimer("done");
      renderEmailList(data.emails || [], `Gmail ("${query || "All Mail"}")`, "gmail");
      appendStatusEvent({ stage: "gmail_loaded", message: `Fetched and parsed ${data.count} Gmail message(s).`, timestamp: new Date().toTimeString().slice(0, 8) });
      if (state.emails.length) {
        renderParsedEmail(state.emails[0]);
      }
    } catch (err) {
      stopLiveTimer("error");
      appendStatusEvent({ stage: "gmail_error", message: err.message }, true);
    }
  }

  async function investigateEmailLive(payload) {
    mountResultsTemplate("emailResultsSlot");
    resetLiveFeed("Starting live email forensic investigation...");
    startLiveTimer();
    state.isScanning = true;

    try {
      await streamSSE("/api/v1/investigate/email/stream", payload, {
        status: (ev) => appendStatusEvent(ev),
        result: (data) => {
          stopLiveTimer("done");
          if (data.email) renderParsedEmail(data.email);
          if (data.investigation) {
            renderInvestigationResult(data.investigation, payload.incident_stage);
            if (state.selectedEmail) {
              state.selectedEmail._verdict = data.investigation.verdict;
              state.selectedEmail._risk_score = data.investigation.risk_score;
              state.selectedEmail._investigation = data.investigation;
              if (state.selectedEmail._source === "gmail" && state.selectedEmail.id) {
                state.polledGmailIds.add(state.selectedEmail.id);
              }
              renderEmailList(state.emails, document.getElementById("emailListTitle").textContent);
            }
          }
        },
        error: (err) => {
          stopLiveTimer("error");
          appendStatusEvent({ stage: "error", message: err.message, timestamp: err.timestamp }, true);
        },
      });
    } catch (err) {
      stopLiveTimer("error");
      appendStatusEvent({ stage: "error", message: err.message }, true);
    } finally {
      state.isScanning = false;
    }
  }

  async function scanInboxLive(source) {
    mountResultsTemplate("emailResultsSlot");
    resetLiveFeed(`Starting live ${source} inbox scan...`);
    startLiveTimer();
    state.isScanning = true;

    const query = getGmailQuery();
    const maxResults = source === "gmail" ? Number(document.getElementById("gmailMaxInput").value || 5) : 5;
    const scannedEmails = [];

    try {
      await streamSSE("/api/v1/emails/scan/stream", {
        source,
        query,
        max_results: maxResults,
        include_spam_trash: true,
        strategy: getStrategy(),
        incident_stage: document.getElementById("emailPostActionCheck").checked ? "POST_ACTION" : "PRE_ACTION",
      }, {
        status: (ev) => appendStatusEvent(ev),
        email_result: (data) => {
          const em = data.email;
          em._verdict = data.investigation.verdict;
          em._risk_score = data.investigation.risk_score;
          em._investigation = data.investigation;
          em._source = source;
          if (source === "gmail" && em.id) {
            state.polledGmailIds.add(em.id);
          }
          scannedEmails.push(em);
          renderEmailList(scannedEmails, `${source === "gmail" ? "Gmail" : "Local"} Live Scan (${scannedEmails.length})`, source);
          renderParsedEmail(em);
          renderInvestigationResult(data.investigation);
        },
        scan_complete: (ev) => {
          stopLiveTimer("done");
          appendStatusEvent({ stage: "scan_complete", message: ev.message, timestamp: ev.timestamp });
          if (source === "gmail") {
            state.gmailPollNextInSec = GMAIL_POLL_INTERVAL_SEC;
            state.gmailLastPollNote = `Last scan ${ev.timestamp || new Date().toTimeString().slice(0, 8)} • ${scannedEmails.length} scanned`;
            updateGmailPollIndicators();
          }
        },
        error: (err) => {
          stopLiveTimer("error");
          appendStatusEvent({ stage: "error", message: err.message, timestamp: err.timestamp }, true);
        },
      });
    } catch (err) {
      stopLiveTimer("error");
      appendStatusEvent({ stage: "error", message: err.message }, true);
    } finally {
      state.isScanning = false;
    }
  }

  function isGmailAutoPollEnabled() {
    const cb = document.getElementById("gmailAutoPollCheck");
    return Boolean(cb && cb.checked);
  }

  function updateGmailPollIndicators() {
    const pillGmail = document.getElementById("pillGmail");
    const pollStatus = document.getElementById("gmailPollStatus");
    const enabled = isGmailAutoPollEnabled();

    if (!state.gmailReady) {
      if (pillGmail) {
        pillGmail.textContent = "Gmail: OAuth Needed";
        pillGmail.className = "pill pill-warn";
      }
      if (pollStatus) {
        pollStatus.textContent = "Paused (Gmail OAuth needed)";
      }
      return;
    }

    if (!enabled) {
      if (pillGmail) {
        pillGmail.textContent = "Gmail: Ready (Poll Off)";
        pillGmail.className = "pill pill-ok";
      }
      if (pollStatus) {
        pollStatus.textContent = state.gmailLastPollNote
          ? `Off • ${state.gmailLastPollNote}`
          : "Auto-poll paused";
      }
      return;
    }

    if (state.isScanning) {
      if (pillGmail) {
        pillGmail.textContent = "Gmail: Checking...";
        pillGmail.className = "pill pill-info";
      }
      if (pollStatus) {
        pollStatus.textContent = "Polling Gmail for new emails...";
      }
      return;
    }

    if (pillGmail) {
      if (state.gmailNewAlertCount > 0) {
        pillGmail.textContent = `Gmail: ${state.gmailNewAlertCount} new (${state.gmailPollNextInSec}s)`;
        pillGmail.className = "pill pill-warn";
      } else {
        pillGmail.textContent = `Gmail: Auto-Poll (${state.gmailPollNextInSec}s)`;
        pillGmail.className = "pill pill-ok";
      }
    }
    if (pollStatus) {
      const prefix = state.gmailLastPollNote ? `${state.gmailLastPollNote} • ` : "";
      pollStatus.textContent = `${prefix}Next check in ${state.gmailPollNextInSec}s`;
    }
  }

  function syncGmailAutoPollState() {
    if (state.gmailPollTickId) {
      clearInterval(state.gmailPollTickId);
      state.gmailPollTickId = null;
    }

    if (state.gmailReady && isGmailAutoPollEnabled()) {
      state.gmailPollNextInSec = GMAIL_POLL_INTERVAL_SEC;
      state.gmailPollTickId = setInterval(() => {
        if (!state.gmailReady || !isGmailAutoPollEnabled()) return;
        if (state.isScanning) {
          updateGmailPollIndicators();
          return;
        }
        state.gmailPollNextInSec -= 1;
        if (state.gmailPollNextInSec <= 0) {
          state.gmailPollNextInSec = GMAIL_POLL_INTERVAL_SEC;
          pollGmailForNewEmails();
        } else {
          updateGmailPollIndicators();
        }
      }, 1000);
    }

    updateGmailPollIndicators();
  }

  async function pollGmailForNewEmails() {
    if (!state.gmailReady || state.isScanning || !isGmailAutoPollEnabled()) return;
    state.isScanning = true;
    updateGmailPollIndicators();

    const query = getGmailQuery();
    const maxResults = Number(document.getElementById("gmailMaxInput")?.value || 5);
    const onEmailTab = state.activeTab === "email";
    const newlyScanned = [];
    let fedStarted = false;

    try {
      await streamSSE("/api/v1/emails/scan/stream", {
        source: "gmail",
        query,
        max_results: maxResults,
        include_spam_trash: true,
        known_ids: Array.from(state.polledGmailIds),
        strategy: getStrategy(),
        incident_stage: document.getElementById("emailPostActionCheck")?.checked ? "POST_ACTION" : "PRE_ACTION",
      }, {
        status: (ev) => {
          // Only stream into the live feed when on the Email tab and new emails are being processed
          if (onEmailTab && ev.stage !== "reading_inbox" && ev.stage !== "inbox_listed") {
            if (!fedStarted) {
              mountResultsTemplate("emailResultsSlot");
              resetLiveFeed("New Gmail message(s) detected — scanning...");
              startLiveTimer();
              fedStarted = true;
            }
            appendStatusEvent(ev);
          }
        },
        email_result: (data) => {
          const em = data.email;
          em._verdict = data.investigation.verdict;
          em._risk_score = data.investigation.risk_score;
          em._investigation = data.investigation;
          em._source = "gmail";
          if (em.id) state.polledGmailIds.add(em.id);
          newlyScanned.push(em);

          // Prepend or update inside state.emails without losing previously listed messages
          const existingIdx = state.emails.findIndex((x) => x.id === em.id);
          if (existingIdx >= 0) {
            state.emails[existingIdx] = em;
          } else {
            state.emails.unshift(em);
          }
          renderEmailList(state.emails, `Gmail ("${query || "All Mail"}")`, "gmail");

          if (onEmailTab) {
            if (!fedStarted) {
              mountResultsTemplate("emailResultsSlot");
              fedStarted = true;
            }
            renderParsedEmail(em);
            renderInvestigationResult(data.investigation);
          }
        },
        scan_complete: (ev) => {
          if (fedStarted) {
            stopLiveTimer("done");
            appendStatusEvent({ stage: "scan_complete", message: ev.message, timestamp: ev.timestamp });
          }
          const ts = ev.timestamp || new Date().toTimeString().slice(0, 8);
          if (newlyScanned.length > 0) {
            state.gmailNewAlertCount += newlyScanned.length;
            state.gmailLastPollNote = `Last check ${ts} • ${newlyScanned.length} new scanned`;
          } else {
            state.gmailLastPollNote = `Last check ${ts} • 0 new`;
          }
        },
        error: (err) => {
          if (fedStarted) {
            stopLiveTimer("error");
            appendStatusEvent({ stage: "error", message: err.message, timestamp: err.timestamp }, true);
          }
          state.gmailLastPollNote = `Poll error: ${err.message}`;
        },
      });
    } catch (err) {
      if (fedStarted) {
        stopLiveTimer("error");
        appendStatusEvent({ stage: "error", message: err.message }, true);
      }
      state.gmailLastPollNote = `Poll error: ${err.message}`;
    } finally {
      state.isScanning = false;
      state.gmailPollNextInSec = GMAIL_POLL_INTERVAL_SEC;
      updateGmailPollIndicators();
    }
  }

  // ---------------------------------------------------------------------------
  // Tab 4: Technical Architecture, Orchestrator & 9-Tool Explorer
  // ---------------------------------------------------------------------------
  async function loadArchitectureDetails() {
    try {
      const data = await fetch("/api/v1/architecture").then((r) => r.json());
      state.architecture = data;
      if (!state.selectedToolName && data.tools && data.tools.length) {
        state.selectedToolName = data.tools[0].name;
      }
      renderArchitectureOverview();
      renderSelectedComponent();
      renderToolSelector();
      renderSelectedTool();
    } catch (err) {
      console.error("Failed to load architecture metadata:", err);
    }
  }

  function renderArchitectureOverview() {
    const arch = state.architecture;
    if (!arch) return;
    const rt = arch.runtime || {};
    const orch = arch.orchestrator || {};

    const badgesEl = document.getElementById("techRuntimeBadges");
    if (badgesEl) {
      badgesEl.innerHTML = `
        <span class="pill pill-info">Max Turns: ${escapeHtml(orch.max_turns)}</span>
        <span class="pill pill-info">Parallel Workers: ${escapeHtml(orch.max_workers)}</span>
        <span class="pill pill-ok">Tools: ${(arch.tools || []).length}</span>
        <span class="pill ${rt.mock_intelligence ? "pill-warn" : "pill-ok"}">${rt.mock_intelligence ? "Mock Intel" : "Live RDAP/VT"}</span>
      `;
    }

    const flowEl = document.getElementById("archComponentFlow");
    if (!flowEl) return;
    const ordered = [...(arch.components || [])].sort((a, b) => String(a.step).localeCompare(String(b.step)));
    flowEl.innerHTML = ordered.map((comp) => `
      <button type="button" class="arch-node ${comp.id === state.selectedComponentId ? "selected" : ""}" data-comp-id="${escapeHtml(comp.id)}">
        <div class="arch-node-top">
          <span class="arch-step">STEP ${escapeHtml(comp.step)}</span>
          <span class="badge badge-info">${escapeHtml(comp.badge)}</span>
        </div>
        <div class="arch-node-title">${escapeHtml(comp.title)}</div>
        <div class="arch-node-sub">${escapeHtml(comp.subtitle)}</div>
      </button>
    `).join("");

    flowEl.querySelectorAll("[data-comp-id]").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.selectedComponentId = btn.dataset.compId;
        renderArchitectureOverview();
        renderSelectedComponent();
      });
    });

    document.querySelectorAll("[data-diag-comp]").forEach((node) => {
      node.classList.toggle("selected-diag", node.dataset.diagComp === state.selectedComponentId);
      node.onclick = () => {
        state.selectedComponentId = node.dataset.diagComp;
        renderArchitectureOverview();
        renderSelectedComponent();
      };
    });

    document.querySelectorAll("[data-diag-tool]").forEach((chip) => {
      chip.onclick = (e) => {
        e.stopPropagation();
        state.selectedComponentId = "tools";
        state.selectedToolName = chip.dataset.diagTool;
        renderArchitectureOverview();
        renderSelectedComponent();
        renderToolSelector();
        renderSelectedTool();
      };
    });
  }

  function renderSelectedComponent() {
    const arch = state.architecture;
    const container = document.getElementById("archComponentDetail");
    if (!arch || !container) return;

    const comp = (arch.components || []).find((c) => c.id === state.selectedComponentId) || (arch.components || [])[0];
    if (!comp) return;

    const orch = arch.orchestrator || {};
    let extraHtml = "";

    if (comp.id === "orchestrator") {
      extraHtml = `
        <div class="tech-subpanel">
          <h4>Phase 1 Execution Cycle (2-Turn Fan-Out / Fan-In)</h4>
          <div class="orch-turn-grid">
            <div class="orch-turn-step">
              <strong>1. Incident Briefing</strong>
              PII redacted via <code>redact_pii()</code>; distinct-host URLs prioritized (up to 12) in <code>_build_orchestrator_prompt()</code>.
            </div>
            <div class="orch-turn-step">
              <strong>2. Turn 1: Parallel Fan-Out</strong>
              LLM selects forensic tools from <code>SCAMLENS_TOOLS</code>; <code>ThreadPoolExecutor</code> runs calls concurrently.
            </div>
            <div class="orch-turn-step">
              <strong>3. Turn 2: Forced Synthesis</strong>
              <code>tools=None</code> enforces final narrative synthesis; <code>scorer.py</code> computes deterministic 0-100 risk score.
            </div>
          </div>
          <details>
            <summary style="cursor:pointer;font-weight:600;color:#bae6fd;">Inspect Live Orchestrator System Prompt (<code>tool_prompts.json</code>)</summary>
            <pre class="tech-pre">${escapeHtml(orch.system_prompt || "")}</pre>
          </details>
          <details style="margin-top:8px;">
            <summary style="cursor:pointer;font-weight:600;color:#bae6fd;">Fallback &amp; Phase 2 LangGraph Roadmap</summary>
            <pre class="tech-pre">${escapeHtml(JSON.stringify(comp.details || {}, null, 2))}</pre>
          </details>
        </div>
      `;
    } else if (comp.id === "tools") {
      extraHtml = `
        <div class="tech-subpanel">
          <h4>Tool Dispatcher Contract</h4>
          <p class="hint" style="margin-bottom:8px;">Click any of the 9 tools on the right panel to inspect its full JSON schema, checks, and few-shot calibration. Quick jump:</p>
          <div class="tool-selector-grid">
            ${(arch.tools || []).map((t) => `<button type="button" class="tool-pill-btn ${t.name === state.selectedToolName ? "active" : ""}" data-jump-tool="${escapeHtml(t.name)}">${escapeHtml(t.name)}</button>`).join("")}
          </div>
        </div>
      `;
    } else if (comp.details && Object.keys(comp.details).length) {
      extraHtml = `
        <div class="tech-subpanel">
          <h4>Technical Configuration &amp; Contracts</h4>
          <pre class="tech-pre">${escapeHtml(JSON.stringify(comp.details, null, 2))}</pre>
        </div>
      `;
    }

    container.innerHTML = `
      <div class="card-header" style="margin-bottom:6px;">
        <div>
          <span class="badge badge-info">STEP ${escapeHtml(comp.step)} &bull; ${escapeHtml(comp.badge)}</span>
          <h2 style="margin-top:6px;">${escapeHtml(comp.title)}</h2>
          <p class="hint">${escapeHtml(comp.subtitle)}</p>
        </div>
      </div>
      <div class="tech-module-path">${escapeHtml(comp.module)}</div>
      <p style="margin:0 0 10px;font-size:0.86rem;">${escapeHtml(comp.summary)}</p>
      <strong style="font-size:0.82rem;color:#cbd5e1;">How It Works</strong>
      <ul class="tech-detail-list">
        ${(comp.highlights || []).map((h) => `<li>${escapeHtml(h)}</li>`).join("")}
      </ul>
      ${extraHtml}
    `;

    container.querySelectorAll("[data-jump-tool]").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.selectedToolName = btn.dataset.jumpTool;
        renderSelectedComponent();
        renderToolSelector();
        renderSelectedTool();
      });
    });
  }

  function renderToolSelector() {
    const arch = state.architecture;
    const el = document.getElementById("archToolPills");
    if (!arch || !el) return;

    el.innerHTML = (arch.tools || []).map((t) => `
      <button type="button" class="tool-pill-btn ${t.name === state.selectedToolName ? "active" : ""}" data-tool-name="${escapeHtml(t.name)}">
        ${escapeHtml(t.name)}
      </button>
    `).join("");

    el.querySelectorAll("[data-tool-name]").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.selectedToolName = btn.dataset.toolName;
        renderToolSelector();
        renderSelectedTool();
        if (state.selectedComponentId === "tools") {
          renderSelectedComponent();
        }
      });
    });
  }

  function renderSelectedTool() {
    const arch = state.architecture;
    const box = document.getElementById("archToolDetail");
    if (!arch || !box) return;

    const tool = (arch.tools || []).find((t) => t.name === state.selectedToolName) || (arch.tools || [])[0];
    if (!tool) return;

    const ex = (tool.few_shot_examples || [])[0];
    box.innerHTML = `
      <div style="display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:8px;margin-bottom:6px;">
        <strong style="font-size:0.95rem;font-family:var(--mono);color:#7dd3fc;">${escapeHtml(tool.name)}</strong>
        <span class="badge badge-verified">${escapeHtml(tool.execution)}</span>
      </div>
      <p style="margin:0 0 8px;">${escapeHtml(tool.description)}</p>
      <div class="tech-module-path" style="margin-top:0;">${escapeHtml(tool.module)}</div>
      <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px;">
        ${(tool.categories || []).map((c) => `<span class="badge badge-info">${escapeHtml(c)}</span>`).join("")}
      </div>

      ${(tool.checks || []).length ? `
        <strong style="font-size:0.8rem;color:#cbd5e1;">Forensic Checks &amp; Severities</strong>
        <ul class="tech-detail-list">
          ${tool.checks.map((c) => `<li>${escapeHtml(c)}</li>`).join("")}
        </ul>
      ` : ""}

      ${(tool.guidelines || []).length ? `
        <strong style="font-size:0.8rem;color:#cbd5e1;">Agent Prompt Guidelines</strong>
        <ul class="tech-detail-list">
          ${tool.guidelines.map((g) => `<li>${escapeHtml(g)}</li>`).join("")}
        </ul>
      ` : ""}

      <details open>
        <summary style="cursor:pointer;font-weight:600;color:#bae6fd;font-size:0.8rem;">OpenAI Parameter Schema</summary>
        <pre class="tech-pre">${escapeHtml(JSON.stringify(tool.parameters || {}, null, 2))}</pre>
      </details>

      ${ex ? `
        <details style="margin-top:8px;">
          <summary style="cursor:pointer;font-weight:600;color:#bae6fd;font-size:0.8rem;">Few-Shot Calibration Example</summary>
          <pre class="tech-pre">${escapeHtml(JSON.stringify(ex, null, 2))}</pre>
        </details>
      ` : ""}
    `;
  }

  // ---------------------------------------------------------------------------
  // Navigation & Event Binding
  // ---------------------------------------------------------------------------
  function switchTab(tabName) {
    state.activeTab = tabName;
    document.querySelectorAll(".tab-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.tab === tabName);
    });
    document.querySelectorAll(".tab-panel").forEach((panel) => {
      panel.classList.toggle("active", panel.id === `tab-${tabName}`);
    });
    if (tabName === "investigator") {
      mountResultsTemplate("multimodalResultsSlot");
    } else if (tabName === "email") {
      mountResultsTemplate("emailResultsSlot");
    }
  }

  function init() {
    mountResultsTemplate("multimodalResultsSlot");
    loadSystemStatus();
    loadSamplesAndRegistry();
    loadArchitectureDetails();

    document.querySelectorAll(".tab-btn").forEach((btn) => {
      btn.addEventListener("click", () => switchTab(btn.dataset.tab));
    });

    document.querySelectorAll(".subtab-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const src = btn.dataset.emailSource;
        state.activeEmailSource = src;
        document.querySelectorAll(".subtab-btn").forEach((b) => b.classList.toggle("active", b === btn));
        document.getElementById("emailSourceLocal").classList.toggle("active", src === "local");
        document.getElementById("emailSourceGmail").classList.toggle("active", src === "gmail");
        document.getElementById("emailSourceRaw").classList.toggle("active", src === "raw");
      });
    });

    document.getElementById("inputText").addEventListener("input", (e) => {
      document.getElementById("charCount").textContent = String(e.target.value.length);
    });
    document.getElementById("inputQr").addEventListener("input", updateQrLivePreview);

    document.getElementById("samplePresetSelect").addEventListener("change", (e) => {
      if (e.target.value) applySampleCase(e.target.value);
    });

    const dropzone = document.getElementById("imageDropzone");
    const fileInput = document.getElementById("inputImages");
    document.getElementById("browseImagesBtn").addEventListener("click", () => fileInput.click());
    fileInput.addEventListener("change", (e) => handleImageFiles(e.target.files));
    dropzone.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    });
    dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
    dropzone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
      handleImageFiles(e.dataTransfer.files);
    });

    document.getElementById("investigateForm").addEventListener("submit", (e) => {
      e.preventDefault();
      runMultimodalInvestigation();
    });

    document.getElementById("clearInvestigateBtn").addEventListener("click", () => {
      document.getElementById("investigateForm").reset();
      document.getElementById("charCount").textContent = "0";
      state.uploadedImages = [];
      renderImagePreviews();
      updateQrLivePreview();
    });

    document.getElementById("loadLocalEmailsBtn").addEventListener("click", loadLocalEmailsList);
    document.getElementById("scanLocalInboxBtn").addEventListener("click", () => scanInboxLive("local"));
    document.getElementById("fetchGmailBtn").addEventListener("click", fetchGmailEmailsList);
    document.getElementById("scanGmailInboxBtn").addEventListener("click", () => scanInboxLive("gmail"));
    document.getElementById("gmailAutoPollCheck").addEventListener("change", syncGmailAutoPollState);
    document.getElementById("pillGmail").addEventListener("click", () => {
      state.gmailNewAlertCount = 0;
      switchTab("email");
      document.querySelector('.subtab-btn[data-email-source="gmail"]')?.click();
      updateGmailPollIndicators();
    });

    document.getElementById("rawEmlFileInput").addEventListener("change", (e) => {
      const file = e.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (ev) => {
        document.getElementById("rawEmlInput").value = ev.target.result;
      };
      reader.readAsText(file);
    });

    document.getElementById("investigateRawEmlBtn").addEventListener("click", () => {
      const rawEml = document.getElementById("rawEmlInput").value;
      if (!rawEml.trim()) return;
      investigateEmailLive({
        source: "raw",
        raw_eml: rawEml,
        strategy: getStrategy(),
        incident_stage: document.getElementById("emailPostActionCheck").checked ? "POST_ACTION" : "PRE_ACTION",
      });
    });

    document.getElementById("investigateSelectedEmailBtn").addEventListener("click", () => {
      if (!state.selectedEmail) return;
      if (state.selectedEmail._source === "raw") {
        const rawEml = document.getElementById("rawEmlInput").value;
        investigateEmailLive({
          source: "raw",
          raw_eml: rawEml,
          strategy: getStrategy(),
          incident_stage: document.getElementById("emailPostActionCheck").checked ? "POST_ACTION" : "PRE_ACTION",
        });
        return;
      }
      const source = state.selectedEmail._source === "gmail" ? "gmail" : "local";
      investigateEmailLive({
        source,
        email_id: state.selectedEmail.id,
        strategy: getStrategy(),
        incident_stage: document.getElementById("emailPostActionCheck").checked ? "POST_ACTION" : "PRE_ACTION",
      });
    });
  }

  document.addEventListener("DOMContentLoaded", init);
})();
