(function () {
  const root = document.querySelector(".page");
  function readLocale() {
    const i18n = window.__V185_I18N__ || {};
    if (typeof i18n.readLocale === "function") return i18n.readLocale();
    const qs = new URLSearchParams(window.location.search || "");
    return (qs.get("ui_locale") || "zh").toLowerCase();
  }
  function applyLocale(locale, rootEl) {
    const i18n = window.__V185_I18N__ || {};
    if (typeof i18n.applyLocale === "function") i18n.applyLocale(locale, rootEl || document);
  }
  function refreshLocale(rootEl) {
    const i18n = window.__V185_I18N__ || {};
    if (typeof i18n.applyLocaleFor === "function") i18n.applyLocaleFor(rootEl || document);
    else applyLocale(readLocale(), rootEl || document);
  }
  function t(key, fallback) {
    const i18n = window.__V185_I18N__ || {};
    if (typeof i18n.t === "function") {
      const text = i18n.t(key);
      if (typeof text === "string" && text.trim() !== "" && text.indexOf("MISSING:") === -1) return text;
    }
    return fallback;
  }

  function pickFinalVideoUrl(task) {
    if (typeof window.__HF_PICK_FINAL_URL__ === "function") return window.__HF_PICK_FINAL_URL__(task);
    const media = (task && task.media) || {};
    let url = media.final_video_url || media.final_url || (task && task.final_video_url) || (task && task.final_url) || null;
    if (!url) {
      const id = (task && task.task_id) || (task && task.task && task.task.task_id) || (task && task.id) || (task && task.task && task.task.id) || null;
      if (id) url = `${window.location.origin}/v1/tasks/${encodeURIComponent(id)}/final`;
    }
    return url;
  }
  function resolveFinalUrl(currentHubOrData) {
    const finalUrl = pickFinalVideoUrl(currentHubOrData)
      || pickFinalVideoUrl((currentHubOrData && currentHubOrData.task) || null)
      || pickFinalVideoUrl(window.__TASK_JSON__ || null)
      || null;
    window.__HF_LAST_HUB__ = currentHubOrData || null;
    window.__HF_LAST_FINAL_URL__ = finalUrl;
    return finalUrl;
  }
  applyLocale(readLocale());
  const taskId = root ? root.getAttribute("data-task-id") : null;
  if (!taskId) return;

  const hubUrl = `/api/hot_follow/tasks/${encodeURIComponent(taskId)}/workbench_hub`;
  const composeUrl = `/api/tasks/${encodeURIComponent(taskId)}/compose`;
  const statusEl = document.getElementById("hf-status");
  const eventsEl = document.getElementById("hf-events");
  const audioMsgEl = document.getElementById("hf_audio_msg") || document.getElementById("hf-audio-msg");
  const ttsEngineEl = document.getElementById("hf_tts_engine");
  const ttsVoiceEl = document.getElementById("hf_tts_voice");
  const ttsPreviewBtn = document.getElementById("hf_tts_preview_btn");
  const bgmFileEl = document.getElementById("hf_bgm_file");
  const bgmMixEl = document.getElementById("hf_bgm_mix");
  const audioFitCapSliderEl = document.getElementById("hf_audio_fit_cap_slider");
  const audioFitCapValueEl = document.getElementById("hf_audio_fit_cap_value");
  const rerunAudioBtn = document.getElementById("hf_rerun_audio_btn");
  const dubOutdatedBadgeEl = document.getElementById("hf_dub_outdated_badge");
  const voiceoverAudioEl = document.getElementById("hf_voiceover_audio");
  const requestedVoiceEl = document.getElementById("hf_requested_voice");
  const actualProviderEl = document.getElementById("hf_actual_provider");
  const resolvedVoiceEl = document.getElementById("hf_resolved_voice");
  const audioReadyEl = document.getElementById("hf_audio_ready");
  const dubWarningsEl = document.getElementById("hf_dub_warnings");
  const confirmVoiceoverEl = document.getElementById("hf_confirm_voiceover");
  const scenePackDownloadEl = document.getElementById("hf_scene_pack_download");
  const scenePackHintEl = document.getElementById("hf-scene-pack-hint");
  const deliverablesGridEl = document.getElementById("hf_deliverables_grid");
  const subtitlesTextEl = document.getElementById("hf_subtitles_text");
  const subtitlesOriginEl = document.getElementById("hf_subtitles_origin");
  const subtitlesEditedPreviewEl = document.getElementById("hf_subtitles_edited_preview");
  const translationQaCountsEl = document.getElementById("hf_translation_qa_counts");
  const translationQaWarningEl = document.getElementById("hf_translation_qa_warning");
  const subtitlesRefreshBtn = document.getElementById("hf_subtitles_refresh_btn");
  const subtitlesSaveBtn = document.getElementById("hf_subtitles_save_btn");
  const subtitlesMsgEl = document.getElementById("hf_subtitles_msg");
  const sourceVideoEl = document.getElementById("hf_source_video");
  const finalVideoEl = document.getElementById("hf_final_video");
  const sourcePosterEl = document.getElementById("hf_source_poster");
  const sourceLinkEl = document.getElementById("hf_source_video_link");
  const finalLinkEl = document.getElementById("hf_final_video_link");
  const tabSourceEl = document.getElementById("hf-tab-source");
  const tabFinalEl = document.getElementById("hf-tab-final");
  const composeConfirmEl = document.getElementById("hf_compose_confirm");
  const overlaySubtitlesEl = document.getElementById("hf_overlay_subtitles");
  const freezeTailEnabledEl = document.getElementById("hf_freeze_tail_enabled");
  const composeBtnEl = document.getElementById("hf_compose_btn");
  const composeMsgEl = document.getElementById("hf_compose_msg");
  const composeFinalBlockEl = document.getElementById("hf_compose_final_block");
  const composeFinalVideoEl = document.getElementById("hf_compose_final_video");
  const composeFinalLinkEl = document.getElementById("hf_compose_final_link");
  const burnSubtitleSourceEl = document.getElementById("hf_burn_subtitle_source");
  const composeStatusValueEl = document.getElementById("hf_compose_status_value");
  const finalExistsValueEl = document.getElementById("hf_final_exists_value");
  const lipsyncPlaceholderEl = document.getElementById("hf_lipsync_placeholder");
  const previewAudioEl = new Audio();

  let currentHub = null;
  let subtitleDirty = false;
  let activeTab = "source";
  let hubLoading = false;
  let pollTimer = null;
  let composeSubmitting = false;
  let subtitlesChangedSinceDub = false;

  function escapeHtml(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;");
  }

  function setTab(tab) {
    activeTab = tab === "final" ? "final" : "source";
    const sourceActive = activeTab === "source";
    if (tabSourceEl) {
      tabSourceEl.classList.toggle("bg-gray-900", sourceActive);
      tabSourceEl.classList.toggle("text-white", sourceActive);
      tabSourceEl.classList.toggle("bg-gray-100", !sourceActive);
      tabSourceEl.classList.toggle("text-gray-600", !sourceActive);
    }
    if (tabFinalEl) {
      tabFinalEl.classList.toggle("bg-gray-900", !sourceActive);
      tabFinalEl.classList.toggle("text-white", !sourceActive);
      tabFinalEl.classList.toggle("bg-gray-100", sourceActive);
      tabFinalEl.classList.toggle("text-gray-600", sourceActive);
    }
    if (sourceVideoEl) sourceVideoEl.classList.toggle("hidden", !sourceActive || !sourceVideoEl.src);
    if (finalVideoEl) finalVideoEl.classList.toggle("hidden", sourceActive || !finalVideoEl.src);
    if (sourcePosterEl) {
      const showPoster = sourceActive ? !sourceVideoEl || !sourceVideoEl.src : !finalVideoEl || !finalVideoEl.src;
      sourcePosterEl.classList.toggle("hidden", !showPoster);
    }
  }

  function getPipelineItem(key) {
    const list = (currentHub && currentHub.pipeline) || [];
    const item = list.find((x) => x && x.key === key) || {};
    return {
      status: item.status || item.state || "pending",
      message: item.message || item.summary || "",
      error: item.error || "",
    };
  }

  function setStep(step, status, summary) {
    const stateEl = document.querySelector(`[data-hf-step-status="${step}"]`);
    const summaryEl = document.querySelector(`[data-hf-step-summary="${step}"]`);
    if (stateEl) stateEl.textContent = status || "pending";
    if (summaryEl) summaryEl.textContent = summary || "";
  }

  function renderPipeline() {
    const parse = getPipelineItem("parse");
    const subtitles = getPipelineItem("subtitles");
    const dub = getPipelineItem("dub");
    const compose = getPipelineItem("compose");
    setStep("parse", parse.status, parse.error || parse.message);
    setStep("subtitles", subtitles.status, subtitles.error || subtitles.message);
    setStep("audio", dub.status, dub.error || dub.message);
    setStep("compose", compose.status, compose.error || compose.message);
    if (statusEl) statusEl.textContent = `${compose.status || dub.status || subtitles.status || parse.status || "pending"}`;
  }

  function setLink(el, url) {
    if (!el) return;
    if (url) {
      el.href = url;
      el.classList.remove("opacity-50", "pointer-events-none");
    } else {
      el.href = "#";
      el.classList.add("opacity-50", "pointer-events-none");
    }
  }

  function normalizeUrl(url) {
    if (!url) return "";
    try {
      return new URL(url, window.location.origin).toString();
    } catch (_) {
      return String(url);
    }
  }

  function setMediaSrcStable(el, url, label, assetVersion) {
    if (!el) return;
    const base = normalizeUrl(url);
    const ver = assetVersion ? String(assetVersion) : "";
    const next = base && ver ? `${base}${base.includes("?") ? "&" : "?"}av=${encodeURIComponent(ver)}` : base;
    const prev = el.dataset.currentUrl || "";
    const prevVer = el.dataset.assetVersion || "";
    if (next === prev && prevVer === ver) return;
    if (next) {
      el.src = next;
      el.dataset.currentUrl = next;
      el.dataset.assetVersion = ver;
      console.debug(`[hf-media] ${label} changed`, { prev, next });
    } else {
      el.removeAttribute("src");
      el.dataset.currentUrl = "";
      el.dataset.assetVersion = "";
      console.debug(`[hf-media] ${label} cleared`, { prev });
    }
  }

  function shouldPollHub() {
    if (!currentHub) return true;
    const readyGate = (currentHub && currentHub.ready_gate) || {};
    if (readyGate.compose_ready === true) return false;
    const compose = getPipelineItem("compose");
    const composeDone = ["done", "ready", "success", "completed"].includes(String(compose.status || "").toLowerCase());
    return !composeDone;
  }

  function refreshPollingState() {
    if (shouldPollHub()) {
      if (!pollTimer) {
        pollTimer = setInterval(() => {
          if (document.hidden) return;
          loadHub().catch(() => {});
        }, 4000);
      }
      return;
    }
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  function renderMedia(finalUrl) {
    const media = (currentHub && currentHub.media) || {};
    const finalMeta = (currentHub && currentHub.final) || {};
    const sourceUrl = media.source_video_url || media.raw_url || null;
    const finalAssetVersion = finalMeta.asset_version || null;

    setMediaSrcStable(sourceVideoEl, sourceUrl, "sourceUrl");
    setMediaSrcStable(finalVideoEl, finalUrl, "finalUrl(main)", finalAssetVersion);
    setMediaSrcStable(composeFinalVideoEl, finalUrl, "finalUrl(compose)", finalAssetVersion);
    if (composeFinalBlockEl) composeFinalBlockEl.classList.toggle("hidden", !finalUrl);
    setLink(composeFinalLinkEl, finalUrl);
    setLink(sourceLinkEl, sourceUrl);
    setLink(finalLinkEl, finalUrl);
    setTab(activeTab);
  }

  function renderSubtitles() {
    const subtitles = (currentHub && currentHub.subtitles) || {};
    const qa = (currentHub && currentHub.translation_qa) || {};
    const origin = subtitles.origin_text || "";
    const edited = subtitles.edited_text || subtitles.srt_text || "";
    const sourcePlaceholder = t("hot_follow_workbench_source_not_generated", "Source subtitles not generated yet.");
    const targetPlaceholder = t("hot_follow_workbench_target_not_generated", "Target subtitles not generated yet.");
    if (subtitlesOriginEl) subtitlesOriginEl.textContent = origin || sourcePlaceholder;
    if (subtitlesEditedPreviewEl) subtitlesEditedPreviewEl.textContent = edited || targetPlaceholder;
    if (subtitlesTextEl && !subtitleDirty) subtitlesTextEl.value = edited || "";
    const sourceCount = Number.isFinite(Number(qa.source_count)) ? Number(qa.source_count) : 0;
    const translatedCount = Number.isFinite(Number(qa.translated_count)) ? Number(qa.translated_count) : 0;
    const hasMismatch = Boolean(qa.has_mismatch) || (sourceCount > 0 && sourceCount !== translatedCount);
    if (translationQaCountsEl) {
      translationQaCountsEl.textContent = `${t("hot_follow_workbench_translation_cues_prefix", "Translation cues")}: ${sourceCount} / ${translatedCount}`;
    }
    if (translationQaWarningEl) translationQaWarningEl.classList.toggle("hidden", !hasMismatch);
  }

  function normalizeEngineKey(value) {
    const raw = String(value || "").trim().toLowerCase();
    if (raw === "edge-tts" || raw === "edge_tts" || raw === "edge") return "edge_tts";
    if (raw === "azure-speech" || raw === "azure_speech" || raw === "azure") return "azure_speech";
    if (raw === "lovo") return "lovo";
    return raw || "none";
  }

  function renderVoiceOptions(selectedProvider) {
    if (!ttsVoiceEl) return;
    const providerKey = normalizeEngineKey(selectedProvider || (ttsEngineEl && ttsEngineEl.value) || "edge_tts");
    const optionsByProvider = (currentHub && currentHub.voice_options_by_provider) || ((window.__TASK_JSON__ || {}).voice_options_by_provider) || {};
    const options = Array.isArray(optionsByProvider[providerKey]) ? optionsByProvider[providerKey] : [];
    const requestedVoice = ((currentHub && currentHub.requested_voice) || (window.__TASK_JSON__ || {}).requested_voice || "").trim();
    ttsVoiceEl.innerHTML = "";
    if (!options.length) {
      const opt = document.createElement("option");
      opt.value = "";
      opt.textContent = "当前 provider 无可用缅语声线";
      ttsVoiceEl.appendChild(opt);
      ttsVoiceEl.disabled = true;
      return;
    }
    ttsVoiceEl.disabled = false;
    let matched = false;
    options.forEach((item, index) => {
      const opt = document.createElement("option");
      opt.value = item.value || "";
      opt.textContent = item.label || item.value || "";
      if (requestedVoice && requestedVoice === opt.value) {
        opt.selected = true;
        matched = true;
      } else if (!requestedVoice && index === 0) {
        opt.selected = true;
      }
      ttsVoiceEl.appendChild(opt);
    });
    if (!matched && ttsVoiceEl.options.length) ttsVoiceEl.options[0].selected = true;
  }

  function renderVoiceMeta() {
    if (requestedVoiceEl) requestedVoiceEl.textContent = (currentHub && currentHub.requested_voice) || "-";
    if (actualProviderEl) actualProviderEl.textContent = (currentHub && currentHub.actual_provider) || "-";
    if (resolvedVoiceEl) resolvedVoiceEl.textContent = (currentHub && currentHub.resolved_voice) || "-";
    if (audioReadyEl) audioReadyEl.textContent = (currentHub && currentHub.audio_ready) ? "yes" : "no";
  }

  function renderDubWarnings() {
    if (!dubWarningsEl) return;
    const warnings = Array.isArray(currentHub && currentHub.dub_warnings) ? currentHub.dub_warnings : [];
    if (!warnings.length) {
      dubWarningsEl.textContent = "-";
      return;
    }
    dubWarningsEl.textContent = warnings.map((item) => {
      const code = item.code || "dub_warning";
      const message = item.message || "";
      const provider = item.provider ? `provider=${item.provider}` : "";
      const voiceId = item.voice_id ? `voice=${item.voice_id}` : "";
      return [code, message, provider, voiceId].filter(Boolean).join(" | ");
    }).join("\n");
  }

  function renderConsistencyPanel() {
    if (burnSubtitleSourceEl) burnSubtitleSourceEl.textContent = (currentHub && currentHub.actual_burn_subtitle_source) || "-";
    if (composeStatusValueEl) composeStatusValueEl.textContent = (currentHub && currentHub.compose_status) || (((currentHub && currentHub.compose) || {}).last || {}).status || "-";
    if (finalExistsValueEl) finalExistsValueEl.textContent = (currentHub && currentHub.final_exists) ? "yes" : "no";
  }

  function renderLipsyncPlaceholder() {
    if (!lipsyncPlaceholderEl) return;
    lipsyncPlaceholderEl.textContent = (currentHub && currentHub.lipsync_enabled)
      ? "增强模式已启用（实验）\n增强路线，失败不影响基础成片。"
      : "默认关闭\n增强路线，当前默认不启用；失败不影响基础成片。";
  }

  function renderAudio() {
    const audio = (currentHub && currentHub.audio) || {};
    const media = (currentHub && currentHub.media) || {};
    const voiceUrl = media.voiceover_url || audio.voiceover_url || audio.audio_url || null;
    if (ttsEngineEl && audio.tts_engine) ttsEngineEl.value = audio.tts_engine;
    renderVoiceOptions(audio.tts_engine);
    if (bgmMixEl && audio.bgm_mix != null) bgmMixEl.value = String(audio.bgm_mix);
    const capRaw = Number(audio.audio_fit_max_speed);
    const cap = Number.isFinite(capRaw) ? capRaw : 1.25;
    if (audioFitCapSliderEl) audioFitCapSliderEl.value = String(Math.max(1.0, Math.min(1.6, cap)));
    if (audioFitCapValueEl) audioFitCapValueEl.textContent = `${Number(audioFitCapSliderEl ? audioFitCapSliderEl.value : cap).toFixed(2)}x`;
    setMediaSrcStable(voiceoverAudioEl, voiceUrl, "audioUrl");
    if (audioMsgEl) audioMsgEl.textContent = audio.error ? `Audio error: ${audio.error}` : "";
    renderVoiceMeta();
    renderDubWarnings();
  }

  function renderComposedReadiness() {
    const readyGate = (currentHub && currentHub.ready_gate) || {};
    const composePlan = (currentHub && currentHub.compose_plan) || {};
    if (overlaySubtitlesEl) overlaySubtitlesEl.checked = Boolean(composePlan.overlay_subtitles);
    if (freezeTailEnabledEl) freezeTailEnabledEl.checked = Boolean(composePlan.freeze_tail_enabled);
  }

  function getSelectedTtsSpeed() {
    const n = Number(audioFitCapSliderEl ? audioFitCapSliderEl.value : 1.25);
    if (!Number.isFinite(n)) return 1.25;
    return Math.max(1.0, Math.min(1.6, n));
  }

  function renderDubOutdatedBadge() {
    if (!dubOutdatedBadgeEl) return;
    dubOutdatedBadgeEl.classList.toggle("hidden", !subtitlesChangedSinceDub);
  }

  function renderScenePack() {
    const scene = (currentHub && currentHub.scenes) || {};
    const status = scene.status || t("hot_follow_scene_status_pending", "Pending");
    const url = scene.download_url || null;
    const stateEl = document.querySelector('[data-hf-step-status="scenes"]');
    if (stateEl) stateEl.textContent = status;
    setLink(scenePackDownloadEl, url);
    if (scenePackHintEl) {
      if (url) scenePackHintEl.textContent = t("hot_follow_scene_status_done", "Done");
      else scenePackHintEl.textContent = status === "failed" ? t("hot_follow_compose_reason_failed", "failed") : t("hot_follow_scene_pack_desc", "Optional; does not block main flow");
    }
  }

  function renderDeliverables() {
    if (!deliverablesGridEl) return;
    const list = (currentHub && currentHub.deliverables) || [];
    if (!Array.isArray(list) || !list.length) {
      deliverablesGridEl.innerHTML = '<div class="rounded-lg border border-gray-200 p-3 text-sm text-gray-500">No deliverables yet</div>';
      refreshLocale(deliverablesGridEl);
      return;
    }
    deliverablesGridEl.innerHTML = list.map((d) => {
      const label = escapeHtml(d.label || d.title || d.kind || "-");
      const key = escapeHtml(d.key || "-");
      const status = escapeHtml(d.status || d.state || "pending");
      const sha = d.sha256 ? `<div class="text-[10px] text-gray-400 mt-1 truncate">sha256: ${escapeHtml(d.sha256)}</div>` : "";
      const hasUrl = Boolean(d.url);
      const href = hasUrl ? d.url : "#";
      const btnClass = hasUrl ? "btn-secondary" : "btn-secondary opacity-50 pointer-events-none";
      return `
        <div class="rounded-lg border border-gray-200 p-3">
          <div class="flex items-center justify-between gap-3">
            <div class="text-sm font-semibold">${label}</div>
            <div class="text-xs rounded-full bg-gray-100 px-2 py-1">${status}</div>
          </div>
          <div class="text-xs text-gray-500 mt-1 truncate">${key}</div>
          ${sha}
          <a class="${btnClass} mt-2 inline-block text-xs" href="${href}" target="_blank" rel="noopener">${hasUrl ? "Download" : "Pending"}</a>
        </div>
      `;
    }).join("");
    refreshLocale(deliverablesGridEl);
  }

  function renderEvents() {
    if (!eventsEl) return;
    const events = (currentHub && currentHub.events) || [];
    eventsEl.innerHTML = Array.isArray(events)
      ? events.map((e) => `<div>${escapeHtml(JSON.stringify(e))}</div>`).join("")
      : "";
  }

  function renderHub(data) {
    currentHub = data || {};
    const currentHubOrData = currentHub || data || {};
    const finalUrl = resolveFinalUrl(currentHubOrData);
    const composeLast = ((currentHub && currentHub.compose) || {}).last || {};
    const composeLastStatus = String(composeLast.status || "").toLowerCase();
    if (!["running", "processing", "queued"].includes(composeLastStatus)) composeSubmitting = false;
    renderPipeline();
    renderMedia(finalUrl);
    renderSubtitles();
    renderAudio();
    renderComposedReadiness();
    renderScenePack();
    renderDeliverables();
    renderEvents();
    renderConsistencyPanel();
    renderLipsyncPlaceholder();
    updateComposeButtonState();
    const composeWarning = ((currentHub && currentHub.compose) || {}).warning;
    if (composeMsgEl && composeWarning) composeMsgEl.textContent = String(composeWarning);
    refreshLocale(root || document);
    refreshPollingState();
  }

  async function loadHub() {
    if (hubLoading) return;
    hubLoading = true;
    try {
      const res = await fetch(hubUrl);
      if (!res.ok) throw new Error((await res.text()) || "hub load failed");
      renderHub(await res.json());
    } finally {
      hubLoading = false;
    }
  }

  async function patchAudioConfig(payload) {
    const res = await fetch(`/api/hot_follow/tasks/${encodeURIComponent(taskId)}/audio_config`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload || {}),
    });
    if (!res.ok) throw new Error((await res.text()) || "save audio config failed");
    return res.json();
  }

  async function patchSubtitles(srtText) {
    const res = await fetch(`/api/hot_follow/tasks/${encodeURIComponent(taskId)}/subtitles`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ srt_text: srtText || "" }),
    });
    if (!res.ok) throw new Error((await res.text()) || "save subtitles failed");
    return res.json();
  }

  async function patchComposePlan(payload) {
    const res = await fetch(`/api/hot_follow/tasks/${encodeURIComponent(taskId)}/compose_plan`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload || {}),
    });
    if (!res.ok) throw new Error((await res.text()) || "save compose plan failed");
    return res.json();
  }

  async function refreshSubtitles() {
    const res = await fetch(`/api/tasks/${encodeURIComponent(taskId)}/subtitles`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
    if (!res.ok) throw new Error((await res.text()) || "refresh subtitles failed");
    return res.json();
  }

  async function uploadBgm(file) {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("mix_ratio", bgmMixEl ? (bgmMixEl.value || "0.3") : "0.3");
    const res = await fetch(`/api/hot_follow/tasks/${encodeURIComponent(taskId)}/bgm`, {
      method: "POST",
      body: fd,
    });
    if (!res.ok) throw new Error((await res.text()) || "upload bgm failed");
    return res.json();
  }

  async function rerunAudio() {
    const provider = ttsEngineEl ? ttsEngineEl.value : null;
    const voiceId = ttsVoiceEl ? ttsVoiceEl.value : null;
    const subtitles = (currentHub && currentHub.subtitles) || {};
    const textareaText = subtitlesTextEl ? subtitlesTextEl.value : "";
    const fallbackText = subtitles.edited_text || subtitles.srt_text || subtitles.origin_text || "";
    const dubText = (textareaText || "").trim() ? textareaText : fallbackText;
    const payload = {
      provider: provider === "edge_tts" ? "edge-tts" : provider,
      voice_id: voiceId || null,
      mm_text: dubText || "",
      tts_speed: getSelectedTtsSpeed(),
    };
    const res = await fetch(`/api/hot_follow/tasks/${encodeURIComponent(taskId)}/dub`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error((await res.text()) || "rerun audio failed");
    return res.json();
  }

  async function composeFinal() {
    const media = (currentHub && currentHub.media) || {};
    const audio = (currentHub && currentHub.audio) || {};
    const voiceUrl = media.voiceover_url || audio.voiceover_url || null;
    if (composeConfirmEl && !composeConfirmEl.checked) throw new Error("Please confirm before composing.");
    if (!voiceUrl) throw new Error("No voiceover yet; run Re-Run Audio first.");
    composeSubmitting = true;
    updateComposeButtonState();
    const res = await fetch(composeUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        bgm_mix: Number(bgmMixEl ? (bgmMixEl.value || "0.3") : "0.3"),
        overlay_subtitles: overlaySubtitlesEl ? !!overlaySubtitlesEl.checked : false,
        force: false,
      }),
    });
    if (res.status === 409) {
      let payload = null;
      try { payload = await res.json(); } catch (_) { payload = null; }
      const inProgress = payload && payload.error === "compose_in_progress";
      if (inProgress) {
        if (composeMsgEl) composeMsgEl.textContent = t("hot_follow_compose_running", "合成中…");
        await loadHub();
        updateComposeButtonState();
        return { in_progress: true, retry_after_ms: payload.retry_after_ms || 1500 };
      }
      throw new Error((payload && (payload.message || payload.detail)) || "compose conflict");
    }
    if (!res.ok) throw new Error((await res.text()) || "compose failed");
    const data = await res.json();
    await loadHub();
    const hub = currentHub || {};
    const finalUrl = resolveFinalUrl(hub || data);
    const finalMeta = (currentHub && currentHub.final) || {};
    setMediaSrcStable(composeFinalVideoEl, finalUrl, "finalUrl(compose-action)", finalMeta.asset_version || null);
    if (composeFinalBlockEl) composeFinalBlockEl.classList.toggle("hidden", !finalUrl);
    setLink(composeFinalLinkEl, finalUrl);
    composeSubmitting = false;
    updateComposeButtonState();
    return data;
  }

  function updateComposeButtonState() {
    if (!composeBtnEl) return;
    const media = (currentHub && currentHub.media) || {};
    const audio = (currentHub && currentHub.audio) || {};
    const hasRaw = Boolean(media.raw_url || media.source_video_url);
    const hasVoiceover = Boolean(media.voiceover_url || audio.voiceover_url);
    const confirmed = composeConfirmEl ? composeConfirmEl.checked : true;
    const composeLast = ((currentHub && currentHub.compose) || {}).last || {};
    const composeRunning = ["running", "processing", "queued"].includes(String(composeLast.status || "").toLowerCase());
    const enabled = hasRaw && hasVoiceover && confirmed && !composeSubmitting && !composeRunning;
    if (!composeBtnEl.dataset.defaultText) composeBtnEl.dataset.defaultText = composeBtnEl.textContent || "Compose Final";
    composeBtnEl.disabled = !enabled;
    composeBtnEl.classList.toggle("opacity-50", !enabled);
    composeBtnEl.classList.toggle("pointer-events-none", !enabled);
    composeBtnEl.textContent = composeRunning || composeSubmitting
      ? t("hot_follow_compose_running", "合成中…")
      : (composeBtnEl.dataset.defaultText || "Compose Final");
    if (composeMsgEl) {
      if (composeRunning || composeSubmitting) composeMsgEl.textContent = t("hot_follow_compose_running", "合成中…");
      else if (!hasVoiceover) composeMsgEl.textContent = "Compose disabled: run Re-Run Audio first.";
      else if (!hasRaw) composeMsgEl.textContent = "Compose disabled: missing raw video.";
      else if (!confirmed) composeMsgEl.textContent = t("hot_follow_workbench_compose_disabled_hint", "Compose disabled: check confirmation first");
      else composeMsgEl.textContent = "";
    }
  }

  async function runAction(action) {
    if (action === "compose") {
      await composeFinal();
      await loadHub();
      return;
    }
    if (action === "subtitles") {
      await refreshSubtitles();
      await loadHub();
      return;
    }
    const res = await fetch(`/api/tasks/${encodeURIComponent(taskId)}/${action}`, { method: "POST" });
    if (!res.ok) throw new Error((await res.text()) || `${action} failed`);
    await loadHub();
  }

  if (tabSourceEl) tabSourceEl.addEventListener("click", (e) => { e.preventDefault(); setTab("source"); });
  if (tabFinalEl) tabFinalEl.addEventListener("click", (e) => { e.preventDefault(); setTab("final"); });
  if (subtitlesTextEl) subtitlesTextEl.addEventListener("input", () => {
    subtitleDirty = true;
    subtitlesChangedSinceDub = true;
    renderDubOutdatedBadge();
    if (subtitlesEditedPreviewEl) subtitlesEditedPreviewEl.textContent = subtitlesTextEl.value || "-";
  });
  if (composeConfirmEl) composeConfirmEl.addEventListener("change", updateComposeButtonState);
  if (overlaySubtitlesEl) {
    overlaySubtitlesEl.addEventListener("change", async () => {
      try {
        await patchComposePlan({ overlay_subtitles: !!overlaySubtitlesEl.checked });
        await loadHub();
      } catch (e) {
        if (composeMsgEl) composeMsgEl.textContent = e.message || "save overlay failed";
      }
    });
  }
  if (freezeTailEnabledEl) {
    freezeTailEnabledEl.addEventListener("change", async () => {
      try {
        await patchComposePlan({ freeze_tail_enabled: !!freezeTailEnabledEl.checked, freeze_tail_cap_sec: 8 });
        await loadHub();
      } catch (e) {
        if (composeMsgEl) composeMsgEl.textContent = e.message || "save freeze-tail failed";
      }
    });
  }
  if (confirmVoiceoverEl && composeConfirmEl) {
    confirmVoiceoverEl.addEventListener("change", () => {
      composeConfirmEl.checked = !!confirmVoiceoverEl.checked;
      updateComposeButtonState();
    });
  }

  if (ttsEngineEl) {
    ttsEngineEl.addEventListener("change", async () => {
      renderVoiceOptions(ttsEngineEl.value);
      try { await patchAudioConfig({ tts_engine: ttsEngineEl.value }); await loadHub(); }
      catch (e) { if (audioMsgEl) audioMsgEl.textContent = e.message || "save failed"; }
    });
  }
  if (ttsVoiceEl) {
    ttsVoiceEl.addEventListener("change", async () => {
      try { await patchAudioConfig({ tts_voice: ttsVoiceEl.value }); await loadHub(); }
      catch (e) { if (audioMsgEl) audioMsgEl.textContent = e.message || "save failed"; }
    });
  }
  if (bgmMixEl) {
    bgmMixEl.addEventListener("change", async () => {
      try { await patchAudioConfig({ bgm_mix: Number(bgmMixEl.value || "0.3") }); await loadHub(); }
      catch (e) { if (audioMsgEl) audioMsgEl.textContent = e.message || "save failed"; }
    });
  }
  if (audioFitCapSliderEl) {
    audioFitCapSliderEl.addEventListener("input", () => {
      if (audioFitCapValueEl) audioFitCapValueEl.textContent = `${Number(audioFitCapSliderEl.value || "1.25").toFixed(2)}x`;
    });
    audioFitCapSliderEl.addEventListener("change", async () => {
      try { await patchAudioConfig({ audio_fit_max_speed: getSelectedTtsSpeed() }); await loadHub(); }
      catch (e) { if (audioMsgEl) audioMsgEl.textContent = e.message || "save failed"; }
    });
  }
  if (bgmFileEl) {
    bgmFileEl.addEventListener("change", async () => {
      const file = bgmFileEl.files && bgmFileEl.files[0];
      if (!file) return;
      try {
        if (audioMsgEl) audioMsgEl.textContent = "Uploading BGM...";
        await uploadBgm(file);
        await loadHub();
        if (audioMsgEl) audioMsgEl.textContent = "BGM uploaded";
      } catch (e) {
        if (audioMsgEl) audioMsgEl.textContent = e.message || "upload failed";
      }
    });
  }
  if (rerunAudioBtn) {
    rerunAudioBtn.addEventListener("click", async (e) => {
      e.preventDefault();
      try {
        if (audioMsgEl) audioMsgEl.textContent = "Rerunning audio...";
        await patchAudioConfig({
          tts_engine: ttsEngineEl ? ttsEngineEl.value : null,
          tts_voice: ttsVoiceEl ? ttsVoiceEl.value : null,
          bgm_mix: bgmMixEl ? Number(bgmMixEl.value || "0.3") : null,
          audio_fit_max_speed: getSelectedTtsSpeed(),
        });
        await rerunAudio();
        await loadHub();
        subtitlesChangedSinceDub = false;
        renderDubOutdatedBadge();
        if (audioMsgEl) audioMsgEl.textContent = "Audio rerun requested";
      } catch (err) {
        if (audioMsgEl) audioMsgEl.textContent = err.message || "rerun failed";
      }
    });
  }
  if (ttsPreviewBtn) {
    ttsPreviewBtn.addEventListener("click", async (e) => {
      e.preventDefault();
      try {
        const media = (currentHub && currentHub.media) || {};
        const audio = (currentHub && currentHub.audio) || {};
        const voiceUrl = media.voiceover_url || audio.voiceover_url || audio.audio_url || null;
        if (!voiceUrl) {
          if (audioMsgEl) audioMsgEl.textContent = "No voiceover yet; run Re-Run Audio first.";
          return;
        }
        previewAudioEl.src = voiceUrl;
        await previewAudioEl.play();
        if (audioMsgEl) audioMsgEl.textContent = "Playing current voiceover preview...";
      } catch (err) {
        if (audioMsgEl) audioMsgEl.textContent = (err && err.message) ? err.message : "preview failed";
      }
    });
  }
  if (subtitlesRefreshBtn) {
    subtitlesRefreshBtn.addEventListener("click", async (e) => {
      e.preventDefault();
      try {
        if (subtitlesMsgEl) subtitlesMsgEl.textContent = "Refreshing...";
        await refreshSubtitles();
        subtitleDirty = false;
        await loadHub();
        if (subtitlesMsgEl) subtitlesMsgEl.textContent = "Refreshed";
      } catch (err) {
        if (subtitlesMsgEl) subtitlesMsgEl.textContent = err.message || "refresh failed";
      }
    });
  }
  if (subtitlesSaveBtn) {
    subtitlesSaveBtn.addEventListener("click", async (e) => {
      e.preventDefault();
      try {
        if (subtitlesMsgEl) subtitlesMsgEl.textContent = "Saving...";
        await patchSubtitles(subtitlesTextEl ? subtitlesTextEl.value : "");
        subtitleDirty = false;
        subtitlesChangedSinceDub = true;
        renderDubOutdatedBadge();
        await loadHub();
        if (subtitlesMsgEl) subtitlesMsgEl.textContent = "Saved. You can now rerun dubbing to match the updated text.";
      } catch (err) {
        if (subtitlesMsgEl) subtitlesMsgEl.textContent = err.message || "save failed";
      }
    });
  }

  document.querySelectorAll("[data-action]").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.preventDefault();
      const action = btn.getAttribute("data-action");
      if (!action) return;
      try {
        if (action === "compose" && statusEl) statusEl.textContent = "Composing final video...";
        await runAction(action);
        if (action === "compose" && composeMsgEl) composeMsgEl.textContent = "Compose requested.";
      } catch (err) {
        if (action === "compose") composeSubmitting = false;
        if (action === "compose" && composeMsgEl) composeMsgEl.textContent = err.message || "compose failed";
        if (statusEl) statusEl.textContent = err.message || "action failed";
      } finally {
        if (action === "compose") updateComposeButtonState();
      }
    });
  });

  loadHub().then(() => setTab("source")).catch((e) => {
    if (statusEl) statusEl.textContent = e.message || "hub load failed";
  });
  renderDubOutdatedBadge();
  refreshPollingState();
})();
