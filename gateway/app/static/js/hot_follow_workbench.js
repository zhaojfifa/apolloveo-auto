(function () {
  const root = document.querySelector(".page");
  function readHotFollowFeatureFlags() {
    const raw = window.__HF_FEATURES__ || {};
    return {
      hotFollowOpsGuideV1: Boolean(raw.hotFollowOpsGuideV1),
    };
  }
  const featureFlags = readHotFollowFeatureFlags();
  function isHotFollowOpsGuideV1Enabled() {
    return Boolean(featureFlags.hotFollowOpsGuideV1);
  }
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

  function currentTargetProfile() {
    const profile = (currentHub && currentHub.target_lang_profile) || {};
    return {
      targetLang: String(profile.target_lang || ((currentHub && currentHub.input && currentHub.input.target_lang) || "mm")).toLowerCase(),
      displayName: String(profile.display_name || "Myanmar"),
      subtitleFilename: String(profile.subtitle_filename || "mm.srt"),
      subtitleTxtFilename: String(profile.subtitle_txt_filename || "mm.txt"),
      dubFilename: String(profile.dub_filename || "audio_mm.mp3"),
    };
  }

  function translateButtonLabel() {
    const profile = currentTargetProfile();
    return profile.targetLang === "vi" ? "翻译为越南语" : "翻译为缅语";
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

  // Phase 1.6: Sidebar Tab switching
  (function initSidebarTabs() {
    const tabBtns = document.querySelectorAll(".hf-sidebar-tab");
    const tabPanels = document.querySelectorAll(".hf-tab-panel");
    tabBtns.forEach(btn => {
      btn.addEventListener("click", () => {
        const target = btn.dataset.tab;
        tabBtns.forEach(b => {
          b.classList.toggle("border-gray-900", b.dataset.tab === target);
          b.classList.toggle("text-gray-900", b.dataset.tab === target);
          b.classList.toggle("border-transparent", b.dataset.tab !== target);
          b.classList.toggle("text-gray-500", b.dataset.tab !== target);
        });
        tabPanels.forEach(p => {
          p.classList.toggle("hidden", p.dataset.tabPanel !== target);
        });
      });
    });
  })();

  const taskId = root ? root.getAttribute("data-task-id") : null;
  if (!taskId) return;

  const hubUrl = `/api/hot_follow/tasks/${encodeURIComponent(taskId)}/workbench_hub`;
  const composeUrl = `/api/hot_follow/tasks/${encodeURIComponent(taskId)}/compose`;
  const assistedInputStorageKey = `hf_assisted_input:${taskId}`;
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
  const audioChannelIntroEl = document.getElementById("hf_audio_channel_intro");
  const actualProviderEl = document.getElementById("hf_actual_provider");
  const resolvedVoiceEl = document.getElementById("hf_resolved_voice");
  const audioExistsEl = document.getElementById("hf_audio_exists");
  const audioMatchesSubtitlesEl = document.getElementById("hf_audio_matches_subtitles");
  const sourceAudioPolicyEl = document.getElementById("hf_source_audio_policy");
  const audioFlowModeEl = document.getElementById("hf_audio_flow_mode");
  const ttsVoiceoverReadyEl = document.getElementById("hf_tts_voiceover_ready");
  const audioFlowReasonEl = document.getElementById("hf_audio_flow_reason");
  const subtitleReadyEl = document.getElementById("hf_subtitle_ready");
  const audioReadyEl = document.getElementById("hf_audio_ready");
  const audioReadyReasonEl = document.getElementById("hf_audio_ready_reason");
  const audioCurrentnessHintEl = document.getElementById("hf_audio_currentness_hint");
  const audioNoDubHintEl = document.getElementById("hf_audio_no_dub_hint");
  const lastFinalExistsEl = document.getElementById("hf_last_final_exists");
  const lastFinalUpdatedAtEl = document.getElementById("hf_last_final_updated_at");
  const lastFinalAssetVersionEl = document.getElementById("hf_last_final_asset_version");
  const artifactAudioExistsEl = document.getElementById("hf_artifact_audio_exists");
  const artifactSubtitleExistsEl = document.getElementById("hf_artifact_subtitle_exists");
  const artifactPackExistsEl = document.getElementById("hf_artifact_pack_exists");
  const currentAttemptDubStatusEl = document.getElementById("hf_current_attempt_dub_status");
  const currentAttemptAudioReadyEl = document.getElementById("hf_current_attempt_audio_ready");
  const currentAttemptAudioReasonEl = document.getElementById("hf_current_attempt_audio_reason");
  const currentAttemptDubCurrentEl = document.getElementById("hf_current_attempt_dub_current");
  const currentAttemptDubReasonEl = document.getElementById("hf_current_attempt_dub_reason");
  const currentAttemptComposeStatusEl = document.getElementById("hf_current_attempt_compose_status");
  const currentAttemptComposeReasonEl = document.getElementById("hf_current_attempt_compose_reason");
  const currentAttemptSubtitleSourceEl = document.getElementById("hf_current_attempt_subtitle_source");
  const operatorLastSuccessfulEl = document.getElementById("hf_operator_last_successful");
  const operatorCurrentFailedEl = document.getElementById("hf_operator_current_failed");
  const operatorShowPreviousFinalEl = document.getElementById("hf_operator_show_previous_final");
  const operatorNextActionEl = document.getElementById("hf_operator_next_action");
  const confirmVoiceoverEl = document.getElementById("hf_confirm_voiceover");
  const scenePackDownloadEl = document.getElementById("hf_scene_pack_download");
  const scenePackHintEl = document.getElementById("hf-scene-pack-hint");
  const deliverablesGridEl = document.getElementById("hf_deliverables_grid");
  const subtitlesTextEl = document.getElementById("hf_subtitles_text");
  const subtitlesOriginEl = document.getElementById("hf_subtitles_origin");
  const subtitlesNormalizedEl = document.getElementById("hf_subtitles_normalized");
  const subtitlesEditedPreviewEl = document.getElementById("hf_subtitles_edited_preview");
  const assistedInputBlockEl = document.getElementById("hf_assisted_input_block");
  const assistedInputHintEl = document.getElementById("hf_assisted_input_hint");
  const assistedInputTextEl = document.getElementById("hf_assisted_input_text");
  const assistedFillSourceBtn = document.getElementById("hf_assisted_fill_source_btn");
  const assistedFillNormalizedBtn = document.getElementById("hf_assisted_fill_normalized_btn");
  const assistedTranslateBtn = document.getElementById("hf_assisted_translate_btn");
  const assistedInputMsgEl = document.getElementById("hf_assisted_input_msg");
  const ocrCandidateBlockEl = document.getElementById("hf_ocr_candidate_block");
  const ocrCandidateHintEl = document.getElementById("hf_ocr_candidate_hint");
  const ocrCandidateTextEl = document.getElementById("hf_ocr_candidate_text");
  const ocrCandidateSourceEl = document.getElementById("hf_ocr_candidate_source");
  const ocrCandidateConfidenceEl = document.getElementById("hf_ocr_candidate_confidence");
  const ocrCandidateModeEl = document.getElementById("hf_ocr_candidate_mode");
  const ocrFillBtn = document.getElementById("hf_ocr_fill_btn");
  const subtitleChannelIntroEl = document.getElementById("hf_subtitle_channel_intro");
  const subtitlesOriginHintEl = document.getElementById("hf_subtitles_origin_hint");
  const subtitlesEditHintEl = document.getElementById("hf_subtitles_edit_hint");
  const opsGuideCardEl = document.getElementById("hf_ops_guide_card");
  const opsGuideBadgeEl = document.getElementById("hf_ops_guide_badge");
  const opsGuideTitleEl = document.getElementById("hf_ops_guide_title");
  const opsGuideDescEl = document.getElementById("hf_ops_guide_desc");
  const opsGuideModeEl = document.getElementById("hf_ops_guide_mode");
  const opsGuidePathEl = document.getElementById("hf_ops_guide_path");
  const opsGuideReasonEl = document.getElementById("hf_ops_guide_reason");
  const advisoryCardEl = document.getElementById("hf_advisory_card");
  const advisoryLevelEl = document.getElementById("hf_advisory_level");
  const advisoryActionEl = document.getElementById("hf_advisory_action");
  const advisoryHintEl = document.getElementById("hf_advisory_hint");
  const advisoryExplanationEl = document.getElementById("hf_advisory_explanation");
  const advisoryEvidenceBlockEl = document.getElementById("hf_advisory_evidence_block");
  const advisoryEvidenceEl = document.getElementById("hf_advisory_evidence");
  const translationQaCountsEl = document.getElementById("hf_translation_qa_counts");
  const translationQaWarningEl = document.getElementById("hf_translation_qa_warning");
  const translateMmBtn = document.getElementById("hf_translate_mm_btn");
  const subtitlesRefreshBtn = document.getElementById("hf_subtitles_refresh_btn");
  const subtitlesSaveBtn = document.getElementById("hf_subtitles_save_btn");
  const subtitlesMsgEl = document.getElementById("hf_subtitles_msg");
  const sourceVideoEl = document.getElementById("hf_source_video");
  const finalVideoEl = document.getElementById("hf_final_video");
  const sourcePosterEl = document.getElementById("hf_source_poster");
  const sourceLinkEl = document.getElementById("hf_source_video_link");
  const finalLinkEl = document.getElementById("hf_final_video_link");
  const sourceUrlViewBlockEl = document.getElementById("hf_source_url_view_block");
  const sourceUrlTextEl = document.getElementById("hf_source_url_text");
  const sourceUrlEditBtn = document.getElementById("hf_source_url_edit_btn");
  const sourceUrlEditBlockEl = document.getElementById("hf_source_url_edit_block");
  const sourceUrlInputEl = document.getElementById("hf_source_url_input");
  const sourceUrlSaveBtn = document.getElementById("hf_source_url_save_btn");
  const sourceUrlCancelBtn = document.getElementById("hf_source_url_cancel_btn");
  const sourceUrlMsgEl = document.getElementById("hf_source_url_msg");
  const tabSourceEl = document.getElementById("hf-tab-source");
  const tabFinalEl = document.getElementById("hf-tab-final");
  const composeConfirmEl = document.getElementById("hf_compose_confirm");
  const overlaySubtitlesEl = document.getElementById("hf_overlay_subtitles");
  const freezeTailEnabledEl = document.getElementById("hf_freeze_tail_enabled");
  const composeBtnEl = document.getElementById("hf_compose_btn");
  const composeMsgEl = document.getElementById("hf_compose_msg");
  const composeModesIntroEl = document.getElementById("hf_compose_modes_intro");
  const composeModesEl = document.getElementById("hf_compose_modes");
  const composeModesHintEl = document.getElementById("hf_compose_modes_hint");
  const composeModeSubtitleEl = document.getElementById("hf_mode_subtitle");
  const composeModeVoiceEl = document.getElementById("hf_mode_voice");
  const composeModeBgmEl = document.getElementById("hf_mode_bgm");
  const composeModeSubtitleBadgeEl = document.getElementById("hf_mode_subtitle_badge");
  const composeModeVoiceBadgeEl = document.getElementById("hf_mode_voice_badge");
  const composeModeBgmBadgeEl = document.getElementById("hf_mode_bgm_badge");
  const cleanupModesEl = document.getElementById("hf_cleanup_modes");
  const cleanupModesHintEl = document.getElementById("hf_cleanup_modes_hint");
  const cleanupKeepEl = document.getElementById("hf_cleanup_keep");
  const cleanupMaskEl = document.getElementById("hf_cleanup_mask");
  const cleanupCleanEl = document.getElementById("hf_cleanup_clean");
  const composeFinalBlockEl = document.getElementById("hf_compose_final_block");
  const composeFinalVideoEl = document.getElementById("hf_compose_final_video");
  const composeFinalLinkEl = document.getElementById("hf_compose_final_link");
  const burnSubtitleSourceEl = document.getElementById("hf_burn_subtitle_source");
  const composeStatusValueEl = document.getElementById("hf_compose_status_value");
  const finalExistsValueEl = document.getElementById("hf_final_exists_value");
  const lipsyncStatusValueEl = document.getElementById("hf_lipsync_status_value");
  const lipsyncHintEl = document.getElementById("hf_lipsync_hint");
  const contentModeEl = document.getElementById("hf_content_mode");
  const sourceAudioLaneEl = document.getElementById("hf_source_audio_lane");
  const routeSourceAudioPolicyEl = document.getElementById("hf_route_source_audio_policy");
  const routeAudioFlowModeEl = document.getElementById("hf_route_audio_flow_mode");
  const speechPresenceEl = document.getElementById("hf_speech_presence");
  const bgmPresenceEl = document.getElementById("hf_bgm_presence");
  const audioMixModeEl = document.getElementById("hf_audio_mix_mode");
  const sourceAudioLaneReasonEl = document.getElementById("hf_source_audio_lane_reason");
  const speechDetectedEl = document.getElementById("hf_speech_detected");
  const onscreenTextDetectedEl = document.getElementById("hf_onscreen_text_detected");
  const recommendedPathEl = document.getElementById("hf_recommended_path");
  const noDubMessageEl = document.getElementById("hf_no_dub_message");
  const previewAudioEl = new Audio();

  let currentHub = null;
  let subtitleDirty = false;
  let activeTab = "source";
  let hubLoading = false;
  let pollTimer = null;
  let composeSubmitting = false;
  let subtitlesChangedSinceDub = false;
  let selectedComposeMode = "voice";
  let selectedCleanupMode = "none";
  let finalPreviewRetryKey = "";
  let finalPreviewRetried = false;
  let assistedInputDirty = false;
  let assistedInputHydrated = false;
  let composeSubmissionRevision = "";
  let sourceUrlEditing = false;

  function readAssistedInputDraft() {
    try {
      return String(window.localStorage.getItem(assistedInputStorageKey) || "");
    } catch (_) {
      return "";
    }
  }

  function persistAssistedInputDraft(text) {
    try {
      const value = String(text || "");
      if (value.trim()) window.localStorage.setItem(assistedInputStorageKey, value);
      else window.localStorage.removeItem(assistedInputStorageKey);
    } catch (_) {
      // Assisted input is an optional UI helper; local storage failure should not break the page.
    }
  }

  function hydrateAssistedInputDraft() {
    if (!assistedInputTextEl || assistedInputHydrated) return;
    const draft = readAssistedInputDraft();
    if (draft && !String(assistedInputTextEl.value || "").trim()) assistedInputTextEl.value = draft;
    assistedInputHydrated = true;
  }

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

  function resolveTtsPreviewUrl(audio) {
    const audioPayload = audio || ((currentHub && currentHub.audio) || {});
    return audioPayload.dub_preview_url || audioPayload.tts_voiceover_url || null;
  }

  function setStep(step, status, summary) {
    const stateEl = document.querySelector(`[data-hf-step-status="${step}"]`);
    const summaryEl = document.querySelector(`[data-hf-step-summary="${step}"]`);
    if (stateEl) stateEl.textContent = status || "pending";
    if (summaryEl) summaryEl.textContent = summary || "";
  }

  function getAudioDisplayState() {
    const audio = (currentHub && currentHub.audio) || {};
    const status = String(audio.status || "").trim().toLowerCase();
    const reason = String(audio.dub_current_reason || audio.audio_ready_reason || "").trim().toLowerCase();
    const hasVoiceover = Boolean(resolveTtsPreviewUrl(audio));
    const deliverableDone = Boolean(audio.deliverable_audio_done);
    const audioReady = Boolean(audio.audio_ready);
    const noDub = Boolean((currentHub && currentHub.no_dub) || audio.no_dub);
    const noDubReason = String((currentHub && currentHub.no_dub_reason) || audio.no_dub_reason || "").trim();

    if (["running", "processing", "queued"].includes(status) || reason === "dub_running") {
      return { status: "running", message: "Dubbing running..." };
    }
    if (status === "failed") {
      return { status: "failed", message: audio.error ? `Audio error: ${audio.error}` : "Audio failed." };
    }
    if (noDub) {
      return { status: "skipped", message: noDubReason ? `Dubbing skipped: ${noDubReason}` : "Dubbing skipped." };
    }
    if (status === "done" && audioReady && deliverableDone && hasVoiceover) {
      return { status: "done", message: "Current voiceover ready." };
    }
    return { status: status || "pending", message: hasVoiceover ? "Voiceover available." : "" };
  }

  function renderPipeline() {
    const parse = getPipelineItem("parse");
    const subtitles = getPipelineItem("subtitles");
    const dub = getPipelineItem("dub");
    const compose = getPipelineItem("compose");
    const audioDisplay = getAudioDisplayState();
    setStep("parse", parse.status, parse.error || parse.message);
    setStep("subtitles", subtitles.status, subtitles.error || subtitles.message);
    setStep("audio", audioDisplay.status || dub.status, audioDisplay.status === "running" ? (audioDisplay.message || dub.message) : (dub.error || audioDisplay.message || dub.message));
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

  function getCurrentSourceUrl() {
    const input = (currentHub && currentHub.input) || {};
    const task = (currentHub && currentHub.task) || {};
    const seed = window.__TASK_JSON__ || {};
    return String(input.source_url || task.source_url || seed.source_url || "").trim();
  }

  function setSourceUrlEditMode(editing) {
    sourceUrlEditing = Boolean(editing);
    if (sourceUrlViewBlockEl) sourceUrlViewBlockEl.classList.toggle("hidden", sourceUrlEditing);
    if (sourceUrlEditBlockEl) sourceUrlEditBlockEl.classList.toggle("hidden", !sourceUrlEditing);
  }

  function renderSourceUrlEditor() {
    const value = getCurrentSourceUrl();
    if (sourceUrlTextEl) sourceUrlTextEl.textContent = value || "-";
    if (sourceUrlInputEl && !sourceUrlEditing) sourceUrlInputEl.value = value;
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

  async function probeFinalUrlOnce(url) {
    if (!url) return false;
    try {
      const res = await fetch(url, { method: "HEAD" });
      return res.ok;
    } catch (_) {
      return false;
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
    const finalExists = Boolean((currentHub && currentHub.final_exists) || finalMeta.exists);
    const retryKey = `${finalExists ? (finalUrl || "") : ""}::${String(finalAssetVersion || "")}`;
    if (retryKey !== finalPreviewRetryKey) {
      finalPreviewRetryKey = retryKey;
      finalPreviewRetried = false;
    }

    setMediaSrcStable(sourceVideoEl, sourceUrl, "sourceUrl");
    setMediaSrcStable(finalVideoEl, finalExists ? finalUrl : null, "finalUrl(main)", finalAssetVersion);
    setMediaSrcStable(composeFinalVideoEl, finalExists ? finalUrl : null, "finalUrl(compose)", finalAssetVersion);
    if (composeFinalBlockEl) composeFinalBlockEl.classList.toggle("hidden", !(finalExists && finalUrl));
    setLink(composeFinalLinkEl, finalExists ? finalUrl : null);
    setLink(sourceLinkEl, sourceUrl);
    setLink(finalLinkEl, finalExists ? finalUrl : null);
    setTab(activeTab);
  }

  function renderSubtitles() {
    const subtitles = (currentHub && currentHub.subtitles) || {};
    const qa = (currentHub && currentHub.translation_qa) || {};
    const helperTranslation = subtitles.helper_translation && typeof subtitles.helper_translation === "object"
      ? subtitles.helper_translation
      : {};
    const origin = subtitles.origin_text || "";
    const normalized = subtitles.normalized_source_text || origin || "";
    const primarySrt = subtitles.primary_editable_text || subtitles.srt_text || subtitles.edited_text || "";
    const sourceAudioLane = String((currentHub && currentHub.source_audio_lane) || "").trim().toLowerCase();
    const candidateMode = String((currentHub && currentHub.screen_text_candidate_mode) || "").trim().toLowerCase();
    const candidateConfidence = String((currentHub && currentHub.screen_text_candidate_confidence) || "").trim().toLowerCase();
    const sourcePlaceholder = isHotFollowOpsGuideV1Enabled()
      ? "当前素材未提取到稳定来源字幕，这在无人声/弱语音素材中属于正常情况。"
      : t("hot_follow_workbench_source_not_generated", "Source subtitles not generated yet.");
    const targetPlaceholder = t("hot_follow_workbench_target_not_generated", "Target subtitles not generated yet.");
    if (subtitleChannelIntroEl) subtitleChannelIntroEl.classList.toggle("hidden", !isHotFollowOpsGuideV1Enabled());
    if (subtitlesOriginHintEl) {
      subtitlesOriginHintEl.textContent = isHotFollowOpsGuideV1Enabled()
        ? "这里显示来源层文本；为空时不一定代表异常，也可能是当前素材没有稳定语音字幕。"
        : "这里显示当前素材提取到的来源字幕或识别文本。";
    }
    if (subtitlesEditHintEl) {
      const profile = currentTargetProfile();
      subtitlesEditHintEl.textContent = isHotFollowOpsGuideV1Enabled()
        ? `这是当前目标语言 SRT 主编辑区。保存后会更新 ${profile.subtitleFilename}；辅助输入和 OCR 候选都只是辅助，不会自动覆盖这里。`
        : `这里是当前目标语言 SRT 主编辑区。保存后会更新 ${profile.subtitleFilename}，并影响后续配音与合成。`;
    }
    if (assistedInputBlockEl) assistedInputBlockEl.classList.toggle("hidden", !isHotFollowOpsGuideV1Enabled());
    // Auto-expand the assisted input block for no-speech tasks that need manual input
    const _noDubForInput = Boolean(currentHub && currentHub.no_dub) || Boolean(currentHub && currentHub.audio && currentHub.audio.no_dub);
    const _subReadyForInput = Boolean(currentHub && currentHub.subtitle_ready);
    if (isHotFollowOpsGuideV1Enabled() && _noDubForInput && !_subReadyForInput && assistedInputBlockEl) {
      assistedInputBlockEl.classList.remove("hidden");
    }
    if (assistedInputHintEl) {
      if (!isHotFollowOpsGuideV1Enabled()) {
        assistedInputHintEl.textContent = "这里用于暂存辅助输入。";
      } else if (candidateMode === "subtitle_led" || candidateConfidence === "high") {
        assistedInputHintEl.textContent = "当前画面文字候选较明确。建议先在这里整理原文，再翻译写入目标语言字幕区。";
      } else if (sourceAudioLane === "silent_candidate" || sourceAudioLane === "music_or_text_led") {
        assistedInputHintEl.textContent = "当前素材更偏字幕/画面驱动。这里适合暂存原文、商品文案或 OCR 候选，再翻译写入目标字幕区。";
      } else {
        assistedInputHintEl.textContent = "这里用于暂存原文手工输入、OCR 候选或商品文案。翻译后再写入下方目标语言字幕编辑区。";
      }
    }
    hydrateAssistedInputDraft();
    if (assistedInputMsgEl && helperTranslation.failed && helperTranslation.message) {
      assistedInputMsgEl.textContent = String(helperTranslation.message);
    }
    if (subtitlesOriginEl) subtitlesOriginEl.textContent = origin || sourcePlaceholder;
    if (subtitlesNormalizedEl) subtitlesNormalizedEl.textContent = normalized || sourcePlaceholder;
    if (subtitlesEditedPreviewEl) subtitlesEditedPreviewEl.textContent = primarySrt || targetPlaceholder;
    // Phase 0.7: collapse three-column preview when all empty
    const _previewGrid = subtitlesOriginEl && subtitlesOriginEl.closest(".grid");
    if (_previewGrid) {
      const _hasContent = Boolean(origin.trim() || normalized.trim() || primarySrt.trim());
      _previewGrid.style.display = _hasContent ? "" : "none";
    }
    if (subtitlesTextEl && !subtitleDirty) subtitlesTextEl.value = primarySrt || "";
    const sourceCount = Number.isFinite(Number(qa.source_count)) ? Number(qa.source_count) : 0;
    const translatedCount = Number.isFinite(Number(qa.translated_count)) ? Number(qa.translated_count) : 0;
    const hasMismatch = Boolean(qa.has_mismatch) || (sourceCount > 0 && sourceCount !== translatedCount);
    if (translationQaCountsEl) {
      translationQaCountsEl.textContent = `${t("hot_follow_workbench_translation_cues_prefix", "Translation cues")}: ${sourceCount} / ${translatedCount}`;
    }
    if (translationQaWarningEl) translationQaWarningEl.classList.toggle("hidden", !hasMismatch);
    if (translateMmBtn) {
      translateMmBtn.classList.toggle("hidden", !isHotFollowOpsGuideV1Enabled());
      translateMmBtn.textContent = translateButtonLabel();
    }
    renderOcrCandidate();
  }

  function getOcrCandidateText() {
    if (!isHotFollowOpsGuideV1Enabled()) return "";
    return String((currentHub && currentHub.screen_text_candidate) || "").trim();
  }

  function renderOcrCandidate() {
    if (!ocrCandidateBlockEl) return;
    const candidate = getOcrCandidateText();
    const candidateSource = String((currentHub && currentHub.screen_text_candidate_source) || "").trim() || "-";
    const candidateConfidence = String((currentHub && currentHub.screen_text_candidate_confidence) || "").trim() || "none";
    const candidateMode = String((currentHub && currentHub.screen_text_candidate_mode) || "").trim() || "unavailable";
    const show = isHotFollowOpsGuideV1Enabled() && (Boolean(candidate) || Boolean(currentHub && currentHub.onscreen_text_detected));
    ocrCandidateBlockEl.classList.toggle("hidden", !show);
    if (!show) return;
    if (ocrCandidateTextEl) ocrCandidateTextEl.textContent = candidate || "当前版本尚未提取到可直接使用的画面文字草稿，可手工补字幕后继续。";
    if (ocrCandidateSourceEl) ocrCandidateSourceEl.textContent = candidateSource;
    if (ocrCandidateConfidenceEl) ocrCandidateConfidenceEl.textContent = candidateConfidence;
    if (ocrCandidateModeEl) ocrCandidateModeEl.textContent = candidateMode;
    if (ocrCandidateHintEl) {
      if (!candidate) {
        ocrCandidateHintEl.textContent = "当前版本未启用完整自动识别，这里只保留候选入口，不会自动覆盖来源层。";
      } else if (candidateMode === "subtitle_led" && candidateConfidence === "high") {
        ocrCandidateHintEl.textContent = "当前画面文字候选较强，建议先填充到辅助输入区，再翻译写入目标语言字幕区。";
      } else {
        ocrCandidateHintEl.textContent = "检测到画面文字候选，可先填充到辅助输入区，再翻译写入目标语言字幕区。";
      }
    }
    if (ocrFillBtn) ocrFillBtn.disabled = !candidate;
  }

  function applyTranslatedTextToTargetEditor(text, successMessage) {
    const nextText = String(text || "");
    if (subtitlesTextEl) subtitlesTextEl.value = nextText;
    if (subtitlesEditedPreviewEl) subtitlesEditedPreviewEl.textContent = nextText || "-";
    subtitleDirty = true;
    if (subtitlesMsgEl) subtitlesMsgEl.textContent = successMessage || "翻译结果已回写当前编辑区，请检查后保存字幕。";
  }

  function fillAssistedInputFromText(text, successMessage) {
    const value = String(text || "").trim();
    if (!value) {
      if (assistedInputMsgEl) assistedInputMsgEl.textContent = "当前没有可用的来源文字，请先检查来源层内容。";
      return false;
    }
    if (assistedInputTextEl) assistedInputTextEl.value = value;
    assistedInputDirty = true;
    persistAssistedInputDraft(value);
    if (assistedInputMsgEl) assistedInputMsgEl.textContent = successMessage || "已填充到辅助输入区。";
    return true;
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
    const providerKey = normalizeEngineKey(selectedProvider || (ttsEngineEl && ttsEngineEl.value) || "azure_speech");
    const optionsByProvider = (currentHub && currentHub.voice_options_by_provider) || ((window.__TASK_JSON__ || {}).voice_options_by_provider) || {};
    const options = Array.isArray(optionsByProvider[providerKey]) ? optionsByProvider[providerKey] : [];
    const requestedVoice = ((currentHub && currentHub.requested_voice) || (window.__TASK_JSON__ || {}).requested_voice || "").trim();
    ttsVoiceEl.innerHTML = "";
    if (!options.length) {
      const opt = document.createElement("option");
      opt.value = "";
      opt.textContent = `当前 provider 无可用${currentTargetProfile().displayName}声线`;
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
    const audio = (currentHub && currentHub.audio) || {};
    const artifactFacts = (currentHub && currentHub.artifact_facts) || {};
    const operatorSummary = (currentHub && currentHub.operator_summary) || {};
    const presentation = (currentHub && currentHub.presentation) || {};
    const lastSuccessfulOutput = presentation.last_successful_output || {};
    const currentAttempt = presentation.current_attempt || {};
    const hasAudio = Boolean(
      artifactFacts.audio_exists
      || resolveTtsPreviewUrl(audio)
      || (currentHub && currentHub.deliverable_audio_done)
    );
    const noDub = Boolean(currentHub && currentHub.no_dub);
    const finalExists = Boolean(artifactFacts.final_exists || (currentHub && currentHub.final_exists));
    const audioStatus = String(audio.status || "").trim().toLowerCase();
    const showRerunHint = finalExists && !Boolean(currentHub && currentHub.dub_current) && !Boolean(currentHub && currentHub.audio_ready) && !noDub;
    if (actualProviderEl) actualProviderEl.textContent = (currentHub && currentHub.actual_provider) || "-";
    if (resolvedVoiceEl) resolvedVoiceEl.textContent = (currentHub && currentHub.resolved_voice) || "-";
    if (audioExistsEl) audioExistsEl.textContent = hasAudio ? "是" : "否";
    if (audioMatchesSubtitlesEl) audioMatchesSubtitlesEl.textContent = (currentHub && currentHub.dub_current) ? "是" : "否";
    if (sourceAudioPolicyEl) sourceAudioPolicyEl.textContent = audio.source_audio_policy || (currentHub && currentHub.source_audio_policy) || "-";
    if (audioFlowModeEl) audioFlowModeEl.textContent = audio.audio_flow_label || audio.audio_flow_mode || (currentHub && currentHub.audio_flow_label) || "-";
    if (ttsVoiceoverReadyEl) ttsVoiceoverReadyEl.textContent = (audio.tts_voiceover_ready || (currentHub && currentHub.tts_voiceover_ready)) ? "yes" : "no";
    if (audioFlowReasonEl) audioFlowReasonEl.textContent = audio.audio_flow_reason || (currentHub && currentHub.audio_flow_reason) || "-";
    if (subtitleReadyEl) subtitleReadyEl.textContent = (currentHub && currentHub.subtitle_ready) ? "yes" : "no";
    if (audioReadyEl) audioReadyEl.textContent = (currentHub && currentHub.audio_ready) ? "yes" : "no";
    if (audioReadyReasonEl) audioReadyReasonEl.textContent = (currentHub && currentHub.audio_ready_reason) || "-";
    if (lastFinalExistsEl) lastFinalExistsEl.textContent = artifactFacts.final_exists ? "yes" : (lastSuccessfulOutput.final_exists ? "yes" : "no");
    if (lastFinalUpdatedAtEl) lastFinalUpdatedAtEl.textContent = artifactFacts.final_updated_at || lastSuccessfulOutput.final_updated_at || "-";
    if (lastFinalAssetVersionEl) lastFinalAssetVersionEl.textContent = artifactFacts.final_asset_version || lastSuccessfulOutput.final_asset_version || "-";
    if (artifactAudioExistsEl) artifactAudioExistsEl.textContent = artifactFacts.audio_exists ? "yes" : "no";
    if (artifactSubtitleExistsEl) artifactSubtitleExistsEl.textContent = artifactFacts.subtitle_exists ? "yes" : "no";
    if (artifactPackExistsEl) artifactPackExistsEl.textContent = artifactFacts.pack_exists ? "yes" : "no";
    if (currentAttemptDubStatusEl) currentAttemptDubStatusEl.textContent = currentAttempt.dub_status || audioStatus || "-";
    if (currentAttemptAudioReadyEl) currentAttemptAudioReadyEl.textContent = currentAttempt.audio_ready ? "yes" : "no";
    if (currentAttemptAudioReasonEl) currentAttemptAudioReasonEl.textContent = currentAttempt.audio_ready_reason || "-";
    if (currentAttemptDubCurrentEl) currentAttemptDubCurrentEl.textContent = currentAttempt.dub_current ? "yes" : "no";
    if (currentAttemptDubReasonEl) currentAttemptDubReasonEl.textContent = currentAttempt.dub_current_reason || "-";
    if (currentAttemptComposeStatusEl) currentAttemptComposeStatusEl.textContent = currentAttempt.compose_status || "-";
    if (currentAttemptComposeReasonEl) currentAttemptComposeReasonEl.textContent = currentAttempt.compose_reason || "-";
    if (currentAttemptSubtitleSourceEl) currentAttemptSubtitleSourceEl.textContent = currentAttempt.current_subtitle_source || "-";
    if (operatorLastSuccessfulEl) operatorLastSuccessfulEl.textContent = operatorSummary.last_successful_output_available ? "yes" : "no";
    if (operatorCurrentFailedEl) operatorCurrentFailedEl.textContent = operatorSummary.current_attempt_failed ? "yes" : "no";
    if (operatorShowPreviousFinalEl) operatorShowPreviousFinalEl.textContent = operatorSummary.show_previous_final_as_primary ? "yes" : "no";
    if (operatorNextActionEl) operatorNextActionEl.textContent = operatorSummary.recommended_next_action || "-";
    if (audioCurrentnessHintEl) {
      audioCurrentnessHintEl.classList.toggle("hidden", !showRerunHint);
      if (!showRerunHint) {
        audioCurrentnessHintEl.textContent = "当前重新配音未更新，最终视频仍为上次版本。";
      } else if (["running", "processing", "queued"].includes(audioStatus)) {
        audioCurrentnessHintEl.textContent = "当前重新配音进行中，最终视频仍为上次版本。";
      } else if (audioStatus === "failed") {
        audioCurrentnessHintEl.textContent = "当前重新配音失败，最终视频仍为上次版本。";
      } else {
        audioCurrentnessHintEl.textContent = "当前重新配音未更新，最终视频仍为上次版本。";
      }
    }
    if (audioChannelIntroEl) audioChannelIntroEl.classList.toggle("hidden", !isHotFollowOpsGuideV1Enabled());
    if (audioNoDubHintEl) audioNoDubHintEl.classList.toggle("hidden", !isHotFollowOpsGuideV1Enabled() || !noDub);
  }

  function renderConsistencyPanel() {
    if (burnSubtitleSourceEl) burnSubtitleSourceEl.textContent = (currentHub && currentHub.actual_burn_subtitle_source) || "-";
    if (composeStatusValueEl) composeStatusValueEl.textContent = (currentHub && currentHub.compose_status) || (((currentHub && currentHub.compose) || {}).last || {}).status || "-";
    if (finalExistsValueEl) finalExistsValueEl.textContent = (currentHub && currentHub.final_exists) ? "yes" : "no";
    // Dub text source hint (Phase 1.3 ops iteration)
    const dubSourceEl = document.getElementById("hf_dub_text_source_value");
    if (dubSourceEl) {
      const subtitles = (currentHub && currentHub.subtitles) || {};
      const primaryFormat = String(subtitles.primary_editable_format || "srt").trim().toLowerCase();
      const dubInputFormat = String(subtitles.dub_input_format || "").trim().toLowerCase();
      const contentMode = String((currentHub && currentHub.content_mode) || "").trim().toLowerCase();
      const noDub = Boolean((currentHub && currentHub.audio || {}).no_dub);
      if (noDub || contentMode === "silent_candidate") {
        dubSourceEl.textContent = "当前无需配音（静默 / ASMR 模式），仅合成字幕版";
      } else if (primaryFormat === "srt") {
        dubSourceEl.textContent = dubInputFormat === "srt"
          ? "优先使用当前已保存的目标语言 SRT；只有目标字幕缺失时才回退到来源层。"
          : "当前目标语言字幕仍会作为主对象保存；配音输入存在兼容回退，请先检查并保存 SRT。";
      } else if (contentMode === "subtitle_led") {
        dubSourceEl.textContent = "画面文字识别（OCR），可在配音 tab 手动编辑";
      } else {
        dubSourceEl.textContent = "语音识别字幕（ASR 提取），可在配音 tab 手动编辑。BGM 不参与配音文字生成。";
      }
    }
    const lipsyncEnabled = Boolean(currentHub && currentHub.lipsync_enabled);
    if (lipsyncStatusValueEl) lipsyncStatusValueEl.textContent = lipsyncEnabled ? "Enhanced path enabled (soft-fail)" : "Off";
    if (lipsyncHintEl) {
      lipsyncHintEl.textContent = lipsyncEnabled
        ? "Enhanced path will run before compose. Stub failures do not block the basic path."
        : "Enhanced path is off by default.";
    }
  }

  function getRecommendedComposeMode() {
    const contentMode = String((currentHub && currentHub.content_mode) || "").trim().toLowerCase();
    const sourceAudioLane = String((currentHub && currentHub.source_audio_lane) || "").trim().toLowerCase();
    const noDub = Boolean(currentHub && currentHub.no_dub);
    const subtitleReady = Boolean(currentHub && currentHub.subtitle_ready);
    if ((contentMode === "silent_candidate" || noDub) && subtitleReady) return "subtitle";
    if ((contentMode === "subtitle_led" || sourceAudioLane === "music_or_text_led") && subtitleReady) return "bgm";
    if (sourceAudioLane === "mixed_audio" && subtitleReady) return "voice";
    return "voice";
  }

  function canUseSubtitleOnlyCompose() {
    const contentMode = String((currentHub && currentHub.content_mode) || "").trim().toLowerCase();
    const noDub = Boolean(currentHub && currentHub.no_dub);
    const noDubReason = String((currentHub && currentHub.no_dub_reason) || "").trim().toLowerCase();
    const subtitleReady = Boolean(currentHub && currentHub.subtitle_ready);
    const speechDetected = Boolean(currentHub && currentHub.speech_detected);
    const composeAllowed = Boolean(currentHub && currentHub.compose_allowed);
    const noDubComposeAllowed = Boolean(currentHub && currentHub.ready_gate && currentHub.ready_gate.no_dub_compose_allowed);
    if (noDub && (composeAllowed || noDubComposeAllowed) && ["target_subtitle_empty", "dub_input_empty"].includes(noDubReason)) return true;
    return Boolean(
      subtitleReady
      && (contentMode === "silent_candidate" || noDub)
      && (!speechDetected || noDubReason === "no_speech_detected")
    );
  }

  function applyComposeModePreset(mode) {
    selectedComposeMode = mode || "voice";
    if (overlaySubtitlesEl) overlaySubtitlesEl.checked = true;
    if (freezeTailEnabledEl) freezeTailEnabledEl.checked = selectedComposeMode === "voice";
    if (bgmMixEl) {
      if (selectedComposeMode === "subtitle") bgmMixEl.value = "0";
      else if (selectedComposeMode === "bgm") bgmMixEl.value = "0.35";
      else if (!bgmMixEl.value) bgmMixEl.value = "0.3";
    }
    renderComposeModes();
  }

  function applyCleanupModePreset(mode) {
    selectedCleanupMode = mode || "none";
    renderCleanupModes();
  }

  function renderComposeModes() {
    const enabled = isHotFollowOpsGuideV1Enabled();
    if (composeModesIntroEl) composeModesIntroEl.classList.toggle("hidden", !enabled);
    if (composeModesEl) composeModesEl.classList.toggle("hidden", !enabled);
    if (composeModesHintEl) composeModesHintEl.classList.toggle("hidden", !enabled);
    if (!enabled) return;

    const recommended = getRecommendedComposeMode();
    const sourceAudioLane = String((currentHub && currentHub.source_audio_lane) || "").trim().toLowerCase();
    const noDub = Boolean(currentHub && currentHub.no_dub);
    const subtitleReady = Boolean(currentHub && currentHub.subtitle_ready);
    const audioReady = Boolean(currentHub && currentHub.audio_ready);

    if (composeModeSubtitleBadgeEl) composeModeSubtitleBadgeEl.classList.toggle("hidden", recommended !== "subtitle");
    if (composeModeVoiceBadgeEl) composeModeVoiceBadgeEl.classList.toggle("hidden", recommended !== "voice");
    if (composeModeBgmBadgeEl) composeModeBgmBadgeEl.classList.toggle("hidden", recommended !== "bgm");

    const cards = [
      [composeModeSubtitleEl, "subtitle"],
      [composeModeVoiceEl, "voice"],
      [composeModeBgmEl, "bgm"],
    ];
    cards.forEach(([el, key]) => {
      if (!el) return;
      const active = selectedComposeMode === key;
      el.classList.toggle("border-gray-900", active);
      el.classList.toggle("bg-gray-50", active);
    });

    if (composeModesHintEl) {
      if (recommended === "subtitle") {
        composeModesHintEl.textContent = "当前更推荐先走快速字幕版。若字幕已就绪，可直接尝试字幕版合成；若还需解说，再补文案后生成配音。";
      } else if (recommended === "bgm") {
        composeModesHintEl.textContent = sourceAudioLane === "music_or_text_led"
          ? "当前素材更偏画面文字或音乐驱动，优先推荐字幕+BGM版。当前阶段仍沿用既有后端 compose 门控。"
          : "当前更推荐字幕+BGM版，适合商品展示或试色视频。当前阶段仍沿用既有后端 compose 门控。";
      } else if (!audioReady && subtitleReady) {
        composeModesHintEl.textContent = "当前字幕已就绪，但配音尚未就绪。若是无人声/弱语音素材，可先尝试字幕版路线；标准口播仍建议先完成配音。";
      } else if (sourceAudioLane === "mixed_audio") {
        composeModesHintEl.textContent = "当前素材像人声+配乐混合音轨。标准配音版仍是主路径，但建议同时关注背景音乐和字幕节奏。";
      } else if (noDub) {
        composeModesHintEl.textContent = "当前任务可不做配音，优先整理字幕版出片路径。";
      } else {
        composeModesHintEl.textContent = "标准配音版是当前推荐路径。快速字幕版和字幕+BGM版主要用于运营试片和商品展示。";
      }
    }
  }

  function renderCleanupModes() {
    const enabled = isHotFollowOpsGuideV1Enabled();
    if (cleanupModesEl) cleanupModesEl.classList.toggle("hidden", !enabled);
    if (cleanupModesHintEl) cleanupModesHintEl.classList.toggle("hidden", !enabled);
    if (!enabled) return;

    const composePlan = (currentHub && currentHub.compose_plan) || {};
    if (!selectedCleanupMode || selectedCleanupMode === "none") {
      selectedCleanupMode = String(composePlan.cleanup_mode || "none").trim() || "none";
    }

    const cards = [
      [cleanupKeepEl, "none"],
      [cleanupMaskEl, "bottom_mask"],
      [cleanupCleanEl, "safe_band"],
    ];
    cards.forEach(([el, key]) => {
      if (!el) return;
      const active = selectedCleanupMode === key;
      el.classList.toggle("border-gray-900", active);
      el.classList.toggle("bg-gray-50", active);
    });

    if (cleanupModesHintEl) {
      if (selectedCleanupMode === "bottom_mask") {
        cleanupModesHintEl.textContent = "当前将优先使用微遮挡原字幕模式。适合常见底部字幕干扰，失败时仍回退到普通合成。";
      } else if (selectedCleanupMode === "safe_band") {
        cleanupModesHintEl.textContent = "当前启用清洁版实验模式，会使用更高的安全带遮挡。适合字幕冲突更明显的画面。";
      } else {
        cleanupModesHintEl.textContent = "当前保留原画面，不额外处理原字幕区域。适合标准口播或原字幕干扰较轻的任务。";
      }
    }
  }

  function renderRoutingState() {
    if (contentModeEl) contentModeEl.textContent = (currentHub && currentHub.content_mode) || "-";
    if (routeSourceAudioPolicyEl) routeSourceAudioPolicyEl.textContent = (currentHub && currentHub.source_audio_policy) || ((currentHub && currentHub.audio) || {}).source_audio_policy || "-";
    if (routeAudioFlowModeEl) routeAudioFlowModeEl.textContent = (currentHub && currentHub.audio_flow_label) || ((currentHub && currentHub.audio) || {}).audio_flow_label || "-";
    if (sourceAudioLaneEl) sourceAudioLaneEl.textContent = (currentHub && currentHub.source_audio_lane) || "-";
    if (speechPresenceEl) speechPresenceEl.textContent = (currentHub && currentHub.speech_presence) || "-";
    if (bgmPresenceEl) bgmPresenceEl.textContent = (currentHub && currentHub.bgm_presence) || "-";
    if (audioMixModeEl) audioMixModeEl.textContent = (currentHub && currentHub.audio_mix_mode) || "-";
    if (speechDetectedEl) speechDetectedEl.textContent = (currentHub && currentHub.speech_detected) ? "yes" : "no";
    if (onscreenTextDetectedEl) onscreenTextDetectedEl.textContent = (currentHub && currentHub.onscreen_text_detected) ? "yes" : "no";
    if (recommendedPathEl) recommendedPathEl.textContent = (currentHub && currentHub.recommended_path) || "-";
    if (sourceAudioLaneReasonEl) sourceAudioLaneReasonEl.textContent = (currentHub && currentHub.source_audio_lane_reason) || "-";
    if (noDubMessageEl) {
      const msg = (currentHub && currentHub.no_dub_message) || "";
      noDubMessageEl.textContent = msg || "-";
      noDubMessageEl.classList.toggle("hidden", !msg);
    }
  }

  function buildOpsGuideModel() {
    const contentMode = String((currentHub && currentHub.content_mode) || "").trim().toLowerCase();
    const sourceAudioLane = String((currentHub && currentHub.source_audio_lane) || "").trim().toLowerCase();
    const sourceAudioLaneReason = String((currentHub && currentHub.source_audio_lane_reason) || "").trim();
    const candidateMode = String((currentHub && currentHub.screen_text_candidate_mode) || "").trim().toLowerCase();
    const speechDetected = Boolean(currentHub && currentHub.speech_detected);
    const noDub = Boolean(currentHub && currentHub.no_dub);
    const noDubReason = String((currentHub && currentHub.no_dub_reason) || "").trim().toLowerCase();
    const noDubMessage = String((currentHub && currentHub.no_dub_message) || "").trim();
    const recommendedPath = String((currentHub && currentHub.recommended_path) || "").trim() || "请检查当前任务路径";

    if (contentMode === "voice_led" && speechDetected && !noDub) {
      const mixedDesc = sourceAudioLane === "mixed_audio"
        ? "当前素材检测到人声，同时可能带明显配乐。建议先检查字幕与配音节奏，再决定是否需要保留或减弱原背景音乐。"
        : "建议先检查字幕，再生成配音，最后合成成片。若需要微调效果，优先先改字幕，再重生成配音。";
      return {
        badge: "标准口播",
        title: "当前素材适合走标准配音路径",
        desc: mixedDesc,
        mode: "标准口播 / 语音驱动",
        path: recommendedPath || "检查字幕 → 生成配音 → 合成",
        reason: sourceAudioLaneReason || "已检测到稳定语音内容，适合标准配音出片。",
      };
    }

    if (noDub && (contentMode === "silent_candidate" || noDubReason === "no_speech_detected")) {
      return {
        badge: "字幕驱动",
        title: "当前素材更适合字幕驱动处理",
        desc: candidateMode === "subtitle_led"
          ? "当前素材更像画面文字驱动内容。优先建议整理候选文字、翻译并保存字幕，再直接合成字幕版。"
          : "这类素材常见于无人声、ASMR 或弱语音内容。优先建议编辑字幕后直接合成字幕版，或先输入解说文案再生成配音。",
        mode: "无人声 / ASMR / 弱语音",
        path: "优先编辑字幕 → 直接合成字幕版，或补文案后再生成配音",
        reason: sourceAudioLaneReason || noDubMessage || "当前素材未检测到稳定语音内容，不建议反复重试配音。",
      };
    }

    return {
      badge: "先补文本",
      title: "来源文本暂时不足，建议先补字幕",
      desc: candidateMode === "subtitle_led"
        ? "当前更适合先整理画面文字候选或原文辅助输入，再翻译写入目标字幕区。"
        : "当前来源字幕或文本信息不足，先检查并补齐当前字幕编辑区内容，再决定是否生成配音，会更稳定。",
      mode: "来源文本不足",
      path: "先补文本 / 校对字幕 → 再决定是否配音",
      reason: sourceAudioLaneReason || noDubMessage || recommendedPath || "当前更适合先补文本，再进入配音或合成步骤。",
    };
  }

  function renderOpsGuide() {
    if (!opsGuideCardEl) return;
    const enabled = isHotFollowOpsGuideV1Enabled();
    opsGuideCardEl.classList.toggle("hidden", !enabled);
    if (!enabled) return;
    const model = buildOpsGuideModel();
    if (opsGuideBadgeEl) opsGuideBadgeEl.textContent = model.badge;
    if (opsGuideTitleEl) opsGuideTitleEl.textContent = model.title;
    if (opsGuideDescEl) opsGuideDescEl.textContent = model.desc;
    if (opsGuideModeEl) opsGuideModeEl.textContent = model.mode;
    if (opsGuidePathEl) opsGuidePathEl.textContent = model.path;
    if (opsGuideReasonEl) opsGuideReasonEl.textContent = model.reason;
  }

  function formatAdvisoryLevel(level) {
    const value = String(level || "").trim().toLowerCase();
    if (value === "warning") return "注意";
    if (value === "error") return "风险";
    return "提示";
  }

  function formatAdvisoryEvidenceValue(value) {
    if (value == null) return "-";
    if (Array.isArray(value)) return value.map((item) => String(item || "").trim()).filter(Boolean).join(", ") || "-";
    if (typeof value === "object") {
      try {
        return JSON.stringify(value);
      } catch (_) {
        return String(value);
      }
    }
    if (typeof value === "boolean") return value ? "yes" : "no";
    return String(value);
  }

  function renderAdvisory() {
    if (!advisoryCardEl) return;
    const advisory = (currentHub && currentHub.advisory) || null;
    const hasAdvisory = Boolean(advisory && typeof advisory === "object");
    advisoryCardEl.classList.toggle("hidden", !hasAdvisory);
    if (!hasAdvisory) {
      if (advisoryLevelEl) advisoryLevelEl.textContent = "-";
      if (advisoryActionEl) advisoryActionEl.textContent = "-";
      if (advisoryHintEl) advisoryHintEl.textContent = "-";
      if (advisoryExplanationEl) advisoryExplanationEl.textContent = "-";
      if (advisoryEvidenceEl) advisoryEvidenceEl.innerHTML = "";
      if (advisoryEvidenceBlockEl) advisoryEvidenceBlockEl.classList.add("hidden");
      return;
    }

    const level = String(advisory.level || "").trim().toLowerCase() || "info";
    const levelLabel = formatAdvisoryLevel(level);
    if (advisoryLevelEl) {
      advisoryLevelEl.textContent = levelLabel;
      advisoryLevelEl.className = "text-[11px] rounded-full px-2 py-1";
      if (level === "warning") advisoryLevelEl.classList.add("bg-amber-50", "text-amber-700");
      else if (level === "error") advisoryLevelEl.classList.add("bg-red-50", "text-red-700");
      else advisoryLevelEl.classList.add("bg-sky-50", "text-sky-700");
    }
    if (advisoryActionEl) advisoryActionEl.textContent = String(advisory.recommended_next_action || "-");
    if (advisoryHintEl) advisoryHintEl.textContent = String(advisory.operator_hint || "-");
    if (advisoryExplanationEl) advisoryExplanationEl.textContent = String(advisory.explanation || "-");

    const evidence = advisory.evidence && typeof advisory.evidence === "object" ? advisory.evidence : null;
    const evidenceEntries = evidence ? Object.entries(evidence).filter(([key]) => String(key || "").trim()) : [];
    if (advisoryEvidenceEl) {
      advisoryEvidenceEl.innerHTML = evidenceEntries.map(([key, value]) => (
        `<div><span class="font-semibold text-gray-700">${escapeHtml(key)}:</span> ${escapeHtml(formatAdvisoryEvidenceValue(value))}</div>`
      )).join("");
    }
    if (advisoryEvidenceBlockEl) advisoryEvidenceBlockEl.classList.toggle("hidden", evidenceEntries.length === 0);
  }

  function renderAudio() {
    const audio = (currentHub && currentHub.audio) || {};
    const voiceUrl = resolveTtsPreviewUrl(audio);
    if (ttsEngineEl) ttsEngineEl.value = audio.tts_engine || "azure_speech";
    renderVoiceOptions(audio.tts_engine || "azure_speech");
    if (bgmMixEl && audio.bgm_mix != null) bgmMixEl.value = String(audio.bgm_mix);
    const capRaw = Number(audio.audio_fit_max_speed);
    const cap = Number.isFinite(capRaw) ? capRaw : 1.25;
    if (audioFitCapSliderEl) audioFitCapSliderEl.value = String(Math.max(1.0, Math.min(1.6, cap)));
    if (audioFitCapValueEl) audioFitCapValueEl.textContent = `${Number(audioFitCapSliderEl ? audioFitCapSliderEl.value : cap).toFixed(2)}x`;
    setMediaSrcStable(voiceoverAudioEl, voiceUrl, "audioUrl");
    if (audioMsgEl) audioMsgEl.textContent = getAudioDisplayState().message;
    renderVoiceMeta();
    renderRoutingState();
    renderOpsGuide();
  }

  function renderComposedReadiness() {
    const readyGate = (currentHub && currentHub.ready_gate) || {};
    const composePlan = (currentHub && currentHub.compose_plan) || {};
    if (overlaySubtitlesEl) overlaySubtitlesEl.checked = Boolean(composePlan.overlay_subtitles);
    if (freezeTailEnabledEl) freezeTailEnabledEl.checked = Boolean(composePlan.freeze_tail_enabled);
    _renderComposeOptionWarning();
    renderComposeModes();
    renderCleanupModes();
    // Phase 0.5: update ops guide card
    _updateOpsGuideCard(readyGate);
    // Phase 0.6: update compose quick bar
    _updateComposeQuickBar(readyGate);
  }

  function _renderComposeOptionWarning() {
    const warningEl = document.getElementById("hf_compose_plan_warning");
    const warningTextEl = document.getElementById("hf_compose_plan_warning_text");
    if (!warningEl || !warningTextEl) return;
    const warning = String((currentHub && currentHub.compose && currentHub.compose.warning) || "").trim();
    if (warning) {
      warningTextEl.textContent = warning;
      warningEl.classList.remove("hidden");
    } else {
      warningTextEl.textContent = "";
      warningEl.classList.add("hidden");
    }
  }

  function _updateOpsGuideCard(readyGate) {
    const card = document.getElementById("hf_ops_guide_card");
    if (!card || !isHotFollowOpsGuideV1Enabled()) return;
    const opsSummary = (currentHub && currentHub.operator_summary) || {};
    const nextAction = String(opsSummary.recommended_next_action || "").trim();
    const pipeline = (currentHub && currentHub.pipeline) || [];
    const parseStep = pipeline.find(s => s && s.key === "parse") || {};
    const subtitlesStep = pipeline.find(s => s && s.key === "subtitles") || {};
    const subReady = Boolean(readyGate.subtitle_ready);
    const audioReady = Boolean(readyGate.audio_ready);
    const composeReady = Boolean(readyGate.compose_ready);
    const noDub = Boolean((currentHub && currentHub.no_dub) || (currentHub && currentHub.audio && currentHub.audio.no_dub));
    const noDubReason = String((currentHub && currentHub.no_dub_reason) || (currentHub && currentHub.audio && currentHub.audio.no_dub_reason) || "").trim();
    const subtitleRunning = String(subtitlesStep.status || "").toLowerCase() === "running";
    let title, desc, mode, path, badge;
    if (composeReady) {
      title = "已就绪"; desc = "成片已生成，可前往交付中心下载或发布。";
      mode = "compose_done"; path = "前往交付中心"; badge = "已完成";
    } else if (subReady && audioReady) {
      title = "可以合成"; desc = "字幕和配音均已就绪，点击下方合成按钮生成最终视频。";
      mode = "ready_to_compose"; path = "合成最终视频"; badge = "待合成";
    } else if (subReady && noDub) {
      title = "可以合成（字幕版）"; desc = "字幕已就绪，当前素材适合直接字幕版合成，无需配音。点击合成按钮生成最终视频。";
      mode = "ready_subtitle_only"; path = "合成字幕版"; badge = "待合成";
    } else if (!subReady && noDub) {
      if (subtitleRunning) {
        title = "等待字幕检测"; desc = `正在自动检测字幕，当前素材可能无可提取语音。也可直接在下方字幕编辑区手工输入${currentTargetProfile().displayName}文字，保存后即可合成。`;
        mode = "subtitle_running_no_speech"; path = "等待检测 / 手工输入字幕 → 合成"; badge = "检测中";
      } else {
        title = "请手工输入字幕"; desc = `当前素材未检测到可提取字幕，请在下方字幕编辑区手工输入${currentTargetProfile().displayName}文字并保存，然后合成字幕版。`;
        mode = "manual_subtitle_needed"; path = "手工输入字幕 → 保存 → 合成"; badge = "待输入";
      }
    } else if (subReady && !audioReady) {
      title = "请生成配音"; desc = "字幕已就绪，请选择配音音色后点击生成配音。";
      mode = "dub_needed"; path = "生成配音 → 合成"; badge = "待配音";
    } else if (String(subtitlesStep.status || "").toLowerCase() === "done") {
      title = "请编辑字幕"; desc = "原始字幕已提取，请编辑目标语言字幕并保存。";
      mode = "edit_subtitles"; path = "编辑字幕 → 配音 → 合成"; badge = "待编辑";
    } else if (String(parseStep.status || "").toLowerCase() === "done") {
      title = "等待字幕生成"; desc = "解析完成，字幕正在生成中，请稍候。";
      mode = "subtitles_pending"; path = "等待字幕 → 编辑 → 配音"; badge = "处理中";
    } else {
      title = "等待解析"; desc = "视频正在解析中，请稍候。";
      mode = "parsing"; path = "解析 → 字幕 → 配音 → 合成"; badge = "处理中";
    }
    if (nextAction) desc = nextAction;
    card.classList.remove("hidden");
    const badgeEl = document.getElementById("hf_ops_guide_badge");
    const titleEl = document.getElementById("hf_ops_guide_title");
    const descEl = document.getElementById("hf_ops_guide_desc");
    const modeEl = document.getElementById("hf_ops_guide_mode");
    const pathEl = document.getElementById("hf_ops_guide_path");
    const reasonEl = document.getElementById("hf_ops_guide_reason");
    if (badgeEl) badgeEl.textContent = badge;
    if (titleEl) titleEl.textContent = title;
    if (descEl) descEl.textContent = desc;
    if (modeEl) modeEl.textContent = mode;
    if (pathEl) pathEl.textContent = path;
    if (reasonEl) reasonEl.textContent = String(readyGate.compose_reason || "-");
  }

  function _updateComposeQuickBar(readyGate) {
    const bar = document.getElementById("hf_compose_quick_bar");
    if (!bar) return;
    const subReady = Boolean(readyGate.subtitle_ready);
    const audioReady = Boolean(readyGate.audio_ready);
    const noDub = Boolean((currentHub && currentHub.audio || {}).no_dub);
    const noDubComposeAllowed = Boolean((currentHub && currentHub.ready_gate && currentHub.ready_gate.no_dub_compose_allowed) || (currentHub && currentHub.compose_allowed && currentHub.no_dub));
    const composeReady = Boolean(readyGate.compose_ready);
    bar.classList.remove("hidden");
    const subIcon = document.getElementById("hf_cq_subtitle_icon");
    const audioIcon = document.getElementById("hf_cq_audio_icon");
    const statusText = document.getElementById("hf_cq_status_text");
    const composeBtn = document.getElementById("hf_compose_quick_btn");
    if (subIcon) {
      subIcon.textContent = subReady ? "\u2713" : "-";
      subIcon.className = "w-5 h-5 rounded-full text-center text-xs leading-5 " + (subReady ? "bg-green-100 text-green-700" : "bg-gray-200 text-gray-500");
    }
    if (audioIcon) {
      const ok = audioReady || noDub;
      audioIcon.textContent = ok ? "\u2713" : "-";
      audioIcon.className = "w-5 h-5 rounded-full text-center text-xs leading-5 " + (ok ? "bg-green-100 text-green-700" : "bg-gray-200 text-gray-500");
    }
    if (statusText) {
      if (composeReady) statusText.textContent = "已合成完成";
      else if (noDubComposeAllowed) statusText.textContent = "可以合成（无需配音）";
      else if (subReady && (audioReady || noDub)) statusText.textContent = "可以合成";
      else if (subReady) statusText.textContent = "等待配音就绪...";
      else if (noDub) statusText.textContent = "等待字幕（可手工输入）...";
      else statusText.textContent = "等待字幕就绪...";
    }
    if (composeBtn) {
      const canCompose = ((subReady && (audioReady || noDub)) || noDubComposeAllowed) && !composeReady;
      composeBtn.disabled = !canCompose;
      if (composeReady) composeBtn.textContent = "已合成";
    }
  }

  function getSelectedTtsSpeed() {
    const n = Number(audioFitCapSliderEl ? audioFitCapSliderEl.value : 1.25);
    if (!Number.isFinite(n)) return 1.25;
    return Math.max(1.0, Math.min(1.6, n));
  }

  function isLikelySrtText(text) {
    const source = String(text || "").trim();
    return source.includes("-->") && /\d{2}:\d{2}:\d{2}[,\.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,\.]\d{3}/.test(source);
  }

  function analyzeMyanmarDubCandidate(text) {
    const source = String(text || "");
    const myanmarMatches = source.match(/[\u1000-\u109F\uAA60-\uAA7F\uA9E0-\uA9FF]/g) || [];
    const cjkMatches = source.match(/[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]/g) || [];
    const latinMatches = source.match(/[A-Za-z]/g) || [];
    const total = myanmarMatches.length + cjkMatches.length + latinMatches.length;
    const myanmarRatio = total > 0 ? (myanmarMatches.length / total) : 0;
    const nonMyanmar = cjkMatches.length + latinMatches.length;
    return {
      hasCjk: cjkMatches.length > 0,
      hasLatin: latinMatches.length > 0,
      myanmarRatio,
      isLikelySrt: isLikelySrtText(source),
      text: source.trim(),
      shouldBlockMyanmarTts: source.trim() && myanmarRatio < 0.6 && nonMyanmar >= Math.max(4, myanmarMatches.length),
    };
  }

  function analyzeTargetDubCandidate(text) {
    const profile = currentTargetProfile();
    if (profile.targetLang !== "mm") {
      return {
        text: String(text || "").trim(),
        shouldBlockMyanmarTts: false,
      };
    }
    return analyzeMyanmarDubCandidate(text);
  }

  function renderDubOutdatedBadge() {
    if (!dubOutdatedBadgeEl) return;
    const audio = (currentHub && currentHub.audio) || {};
    const currentAttempt = (currentHub && currentHub.current_attempt) || {};
    const reason = String(audio.dub_current_reason || audio.audio_ready_reason || "").trim().toLowerCase();
    const serverMarkedStale = Boolean(currentAttempt.requires_redub) || ["dub_stale_after_subtitles", "dub_stale_after_speed_change", "dub_not_current"].includes(reason);
    dubOutdatedBadgeEl.classList.toggle("hidden", !(subtitlesChangedSinceDub || serverMarkedStale));
  }

  // Phase 1.7: Horizontal pipeline bar
  function _renderPipelineBar() {
    const pipeline = (currentHub && currentHub.pipeline) || [];
    const stepMap = {};
    pipeline.forEach(s => { if (s && s.key) stepMap[s.key] = s; });
    // "audio" dot maps to pipeline key "dub" (backend uses "dub", UI uses "audio")
    const keyToPipelineKey = { audio: "dub" };
    const noDub = Boolean(currentHub && (currentHub.no_dub || (currentHub.audio && currentHub.audio.no_dub)));
    const keys = ["parse", "subtitles", "audio", "compose", "publish"];
    keys.forEach(key => {
      const dot = document.querySelector(`[data-pipe-dot="${key}"]`);
      if (!dot) return;
      const pipelineKey = keyToPipelineKey[key] || key;
      const step = stepMap[pipelineKey] || {};
      // For the audio/dub step: when no_dub is true, treat as done (skipped/not needed)
      let status = String(step.status || "").toLowerCase();
      if (key === "audio" && noDub && !["done", "running", "failed", "error"].includes(status)) status = "done";
      dot.className = "w-6 h-6 rounded-full text-center text-xs leading-6 font-bold ";
      if (status === "done" || status === "ready" || status === "success") {
        dot.className += "bg-green-100 text-green-700";
        dot.textContent = "\u2713";
      } else if (status === "running" || status === "processing") {
        dot.className += "bg-blue-100 text-blue-700 animate-pulse";
        dot.textContent = "\u25CF";
      } else if (status === "failed" || status === "error") {
        dot.className += "bg-red-100 text-red-700";
        dot.textContent = "\u2717";
      } else {
        dot.className += "bg-gray-200 text-gray-400";
        dot.textContent = keys.indexOf(key) + 1;
      }
    });
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
    // Phase 1.8: Separate final from rest; show ready items first
    const finalItem = list.find(d => String(d.kind || "").toLowerCase() === "final");
    const readyItems = list.filter(d => String(d.kind || "").toLowerCase() !== "final" && String(d.status || d.state || "").toLowerCase() !== "pending");
    const pendingItems = list.filter(d => String(d.kind || "").toLowerCase() !== "final" && String(d.status || d.state || "").toLowerCase() === "pending");
    let html = "";
    // Final item — full width highlight
    if (finalItem) {
      const status = escapeHtml(finalItem.status || finalItem.state || "pending");
      const openUrl = finalItem.open_url || finalItem.url || null;
      const downloadUrl = finalItem.download_url || finalItem.url || null;
      const hasOpenUrl = Boolean(openUrl);
      const hasDownloadUrl = Boolean(downloadUrl);
      const isDone = ["done", "ready", "success"].includes(status.toLowerCase());
      html += `<div class="col-span-full rounded-xl border ${isDone ? "border-green-200 bg-green-50" : "border-gray-200"} p-4">
        <div class="flex items-center justify-between gap-3">
          <div class="text-base font-bold">${escapeHtml(finalItem.label || "Final Video")}</div>
          <div class="text-xs rounded-full ${isDone ? "bg-green-100 text-green-700" : "bg-gray-100"} px-2 py-1">${status}</div>
        </div>
        <div class="mt-3 flex flex-wrap gap-2">
          ${hasDownloadUrl ? `<a class="btn-primary inline-block text-sm" href="${downloadUrl}" target="_blank" rel="noopener">Download</a>` : ""}
          ${hasOpenUrl ? `<a class="btn-secondary inline-block text-sm" href="${openUrl}" target="_blank" rel="noopener">Open</a>` : ""}
          ${!hasDownloadUrl && !hasOpenUrl ? '<span class="text-sm text-gray-500 inline-block">Pending</span>' : ""}
        </div>
      </div>`;
    }
    // Ready items
    readyItems.forEach(d => {
      const label = escapeHtml(d.label || d.title || d.kind || "-");
      const status = escapeHtml(d.status || d.state || "pending");
      const downloadUrl = d.download_url || d.url || null;
      const openUrl = d.open_url || null;
      const hasDownloadUrl = Boolean(downloadUrl);
      const btnClass = hasDownloadUrl ? "btn-secondary" : "btn-secondary opacity-50 pointer-events-none";
      html += `<div class="rounded-lg border border-gray-200 p-3">
        <div class="flex items-center justify-between gap-3">
          <div class="text-sm font-semibold">${label}</div>
          <div class="text-xs rounded-full bg-gray-100 px-2 py-1">${status}</div>
        </div>
        <div class="mt-2 flex flex-wrap gap-2">
          <a class="${btnClass} inline-block text-xs" href="${hasDownloadUrl ? downloadUrl : "#"}" target="_blank" rel="noopener">${hasDownloadUrl ? "Download" : "Pending"}</a>
          ${openUrl ? `<a class="btn-secondary inline-block text-xs" href="${openUrl}" target="_blank" rel="noopener">Open</a>` : ""}
        </div>
      </div>`;
    });
    // Pending items — collapsed summary
    if (pendingItems.length > 0) {
      html += `<div class="col-span-full rounded-lg border border-dashed border-gray-200 p-3 text-xs text-gray-500">
        其余 ${pendingItems.length} 项产物等待生成 (${pendingItems.map(d => escapeHtml(d.label || d.kind || "")).join(", ")})
      </div>`;
    }
    deliverablesGridEl.innerHTML = html;
    refreshLocale(deliverablesGridEl);
  }

  function getComposeRevisionSnapshot() {
    const subtitles = (currentHub && currentHub.subtitles) || {};
    const audio = (currentHub && currentHub.audio) || {};
    return {
      subtitle_updated_at: String(subtitles.updated_at || "").trim() || null,
      audio_sha256: String(audio.sha256 || "").trim() || null,
    };
  }

  async function tryHandleUncertainComposeResponse(res) {
    let bodyText = "";
    try { bodyText = await res.text(); } catch (_) { bodyText = ""; }
    await loadHub().catch(() => {});
    const composeLast = ((currentHub && currentHub.compose) || {}).last || {};
    const composeRunning = ["running", "processing", "queued"].includes(String(composeLast.status || "").toLowerCase());
    const composeDone = ["done", "success", "completed", "ready"].includes(String((currentHub && currentHub.compose_status) || composeLast.status || "").toLowerCase());
    const finalMeta = (currentHub && currentHub.final) || {};
    const finalExists = Boolean((currentHub && currentHub.final_exists) || finalMeta.exists);
    if (composeRunning || composeDone || finalExists) {
      if (composeMsgEl) composeMsgEl.textContent = composeRunning ? "合成请求已发出，正在继续轮询状态…" : "合成结果已更新，正在刷新状态…";
      return { uncertain: true, in_progress: composeRunning, final_exists: finalExists };
    }
    const fallback = String(bodyText || "").trim();
    throw new Error(fallback || "compose request failed");
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
    _renderPipelineBar();
    renderMedia(finalUrl);
    renderSubtitles();
    renderAudio();
    renderAdvisory();
    renderComposedReadiness();
    renderScenePack();
    renderDeliverables();
    renderEvents();
    renderConsistencyPanel();
    renderSourceUrlEditor();
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

  async function patchSourceUrl(sourceUrl) {
    const res = await fetch(`/api/hot_follow/tasks/${encodeURIComponent(taskId)}/source_url`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source_url: String(sourceUrl || "") }),
    });
    if (!res.ok) throw new Error((await res.text()) || "save source url failed");
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

  async function readApiResponseBody(res) {
    const contentType = String(res.headers.get("content-type") || "").toLowerCase();
    if (contentType.includes("application/json")) {
      try {
        return await res.json();
      } catch (_) {
        return null;
      }
    }
    try {
      return await res.text();
    } catch (_) {
      return "";
    }
  }

  function readableApiError(payload, fallback) {
    if (payload && typeof payload === "object") {
      const detail = payload.detail;
      if (detail && typeof detail === "object") {
        return String(detail.message || detail.reason || fallback || "").trim() || fallback;
      }
      if (typeof detail === "string") return detail.trim() || fallback;
      return String(payload.message || payload.error || fallback || "").trim() || fallback;
    }
    return String(payload || fallback || "").trim() || fallback;
  }

  function isRecoverableHelperTranslateFailure(payload) {
    const detail = payload && typeof payload === "object" ? payload.detail : null;
    const reason = String((detail && typeof detail === "object" ? detail.reason : "") || "").trim().toLowerCase();
    return reason === "helper_translate_failed" || reason === "helper_translate_provider_exhausted";
  }

  function readableErrorMessage(err, fallback) {
    if (err && err.payload) return readableApiError(err.payload, fallback);
    return String((err && err.message) || fallback || "").trim() || fallback;
  }

  async function translateCurrentSubtitles(options) {
    const source = options && typeof options === "object" ? options : { text: options || "" };
    const res = await fetch(`/api/hot_follow/tasks/${encodeURIComponent(taskId)}/translate_subtitles`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text: source.text || "",
        target_lang: currentTargetProfile().targetLang,
        input_source: source.input_source || "helper_only_text",
      }),
    });
    const payload = await readApiResponseBody(res);
    if (!res.ok) {
      const err = new Error(readableApiError(payload, "translate subtitles failed"));
      err.payload = payload;
      err.recoverableHelperFailure = isRecoverableHelperTranslateFailure(payload);
      throw err;
    }
    return payload || {};
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
    const policy = String(((currentHub && currentHub.audio) || {}).source_audio_policy || (currentHub && currentHub.source_audio_policy) || "mute").trim().toLowerCase();
    fd.append("strategy", policy === "preserve" ? "keep" : "replace");
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
      provider: provider === "edge_tts" ? "edge-tts" : (provider === "azure_speech" ? "azure-speech" : provider),
      voice_id: voiceId || null,
      mm_text: dubText || "",
      tts_speed: getSelectedTtsSpeed(),
      force: true,
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
    const audio = (currentHub && currentHub.audio) || {};
    const voiceUrl = resolveTtsPreviewUrl(audio);
    const subtitleOnlyAllowed = canUseSubtitleOnlyCompose();
    if (composeConfirmEl && !composeConfirmEl.checked) throw new Error("Please confirm before composing.");
    if (!voiceUrl && !subtitleOnlyAllowed) throw new Error("No voiceover yet; run Re-Run Audio first.");
    if (composeSubmitting) return { in_progress: true };
    composeSubmitting = true;
    const revision = getComposeRevisionSnapshot();
    composeSubmissionRevision = JSON.stringify(revision);
    updateComposeButtonState();
    try {
      const res = await fetch(composeUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          bgm_mix: Number(bgmMixEl ? (bgmMixEl.value || "0.3") : "0.3"),
          overlay_subtitles: overlaySubtitlesEl ? !!overlaySubtitlesEl.checked : false,
          freeze_tail_enabled: freezeTailEnabledEl ? !!freezeTailEnabledEl.checked : false,
          force: false,
          expected_subtitle_updated_at: revision.subtitle_updated_at,
          expected_audio_sha256: revision.audio_sha256,
        }),
      });
      const contentType = String(res.headers.get("content-type") || "").toLowerCase();
      if (res.status === 409) {
        let payload = null;
        if (contentType.includes("application/json")) {
          try { payload = await res.json(); } catch (_) { payload = null; }
        } else {
          return await tryHandleUncertainComposeResponse(res);
        }
        const inProgress = payload && payload.error === "compose_in_progress";
        const revisionMismatch = payload && ((payload.reason || (payload.detail && payload.detail.reason)) === "compose_revision_mismatch");
        if (inProgress) {
          if (composeMsgEl) composeMsgEl.textContent = t("hot_follow_compose_running", "合成中…");
          await loadHub();
          updateComposeButtonState();
          return { in_progress: true, retry_after_ms: payload.retry_after_ms || 1500 };
        }
        if (revisionMismatch) {
          await loadHub();
          throw new Error((payload && (payload.message || (payload.detail && payload.detail.message))) || "当前字幕或音频已更新，请刷新后重新合成。");
        }
        throw new Error((payload && (payload.message || payload.detail)) || "compose conflict");
      }
      if (!res.ok) {
        if (!contentType.includes("application/json")) return await tryHandleUncertainComposeResponse(res);
        throw new Error((await res.text()) || "compose failed");
      }
      let data = null;
      if (contentType.includes("application/json")) {
        data = await res.json();
      } else {
        return await tryHandleUncertainComposeResponse(res);
      }
      await loadHub();
      const hub = currentHub || {};
      const finalUrl = resolveFinalUrl(hub || data);
      const finalMeta = (currentHub && currentHub.final) || {};
      const finalExists = Boolean((currentHub && currentHub.final_exists) || finalMeta.exists);
      setMediaSrcStable(composeFinalVideoEl, finalExists ? finalUrl : null, "finalUrl(compose-action)", finalMeta.asset_version || null);
      if (composeFinalBlockEl) composeFinalBlockEl.classList.toggle("hidden", !(finalExists && finalUrl));
      setLink(composeFinalLinkEl, finalExists ? finalUrl : null);
      return data;
    } finally {
      composeSubmitting = false;
      composeSubmissionRevision = "";
      updateComposeButtonState();
    }
  }

  function updateComposeButtonState() {
    if (!composeBtnEl) return;
    const media = (currentHub && currentHub.media) || {};
    const audio = (currentHub && currentHub.audio) || {};
    const hasRaw = Boolean(media.raw_url || media.source_video_url);
    const hasVoiceover = Boolean(resolveTtsPreviewUrl(audio));
    const subtitleOnlyAllowed = canUseSubtitleOnlyCompose();
    const confirmed = composeConfirmEl ? composeConfirmEl.checked : true;
    const composeLast = ((currentHub && currentHub.compose) || {}).last || {};
    const composeRunning = ["running", "processing", "queued"].includes(String(composeLast.status || "").toLowerCase());
    const composeDone = ["done", "success", "completed", "ready"].includes(String((currentHub && currentHub.compose_status) || composeLast.status || "").toLowerCase());
    const finalExists = Boolean(currentHub && currentHub.final_exists);
    const audioDisplay = getAudioDisplayState();
    const hasCurrentFinalFromPreviousRun = finalExists && !Boolean(currentHub && currentHub.dub_current) && !Boolean(currentHub && currentHub.audio_ready) && !Boolean(currentHub && currentHub.no_dub);
    const enabled = hasRaw && (hasVoiceover || subtitleOnlyAllowed) && confirmed && !composeSubmitting && !composeRunning && !(composeDone && finalExists);
    if (!composeBtnEl.dataset.defaultText) composeBtnEl.dataset.defaultText = composeBtnEl.textContent || "Compose Final";
    composeBtnEl.disabled = !enabled;
    composeBtnEl.classList.toggle("opacity-50", !enabled);
    composeBtnEl.classList.toggle("pointer-events-none", !enabled);
    composeBtnEl.textContent = composeRunning || composeSubmitting
      ? t("hot_follow_compose_running", "合成中…")
      : (composeBtnEl.dataset.defaultText || "Compose Final");
    if (composeMsgEl) {
      if (composeRunning || composeSubmitting) composeMsgEl.textContent = t("hot_follow_compose_running", "合成中…");
      else if (hasCurrentFinalFromPreviousRun && audioDisplay.status === "running") composeMsgEl.textContent = "当前重新配音进行中，最终视频仍为上次版本。";
      else if (hasCurrentFinalFromPreviousRun && audioDisplay.status === "failed") composeMsgEl.textContent = "当前重新配音失败，最终视频仍为上次版本。";
      else if (hasCurrentFinalFromPreviousRun) composeMsgEl.textContent = "当前配音未更新，最终视频仍为上次版本。";
      else if (composeDone && finalExists) composeMsgEl.textContent = "最终成片已生成，无需重复合成。";
      else if (audioDisplay.status === "running") composeMsgEl.textContent = "Compose disabled: dubbing still running.";
      else if (!hasVoiceover && subtitleOnlyAllowed) composeMsgEl.textContent = "当前任务可直接走字幕版合成。";
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
  if (sourceUrlEditBtn) {
    sourceUrlEditBtn.addEventListener("click", (e) => {
      e.preventDefault();
      if (sourceUrlMsgEl) sourceUrlMsgEl.textContent = "";
      setSourceUrlEditMode(true);
      if (sourceUrlInputEl) sourceUrlInputEl.focus();
    });
  }
  if (sourceUrlCancelBtn) {
    sourceUrlCancelBtn.addEventListener("click", (e) => {
      e.preventDefault();
      if (sourceUrlMsgEl) sourceUrlMsgEl.textContent = "";
      setSourceUrlEditMode(false);
      renderSourceUrlEditor();
    });
  }
  if (sourceUrlSaveBtn) {
    sourceUrlSaveBtn.addEventListener("click", async (e) => {
      e.preventDefault();
      const next = sourceUrlInputEl ? String(sourceUrlInputEl.value || "").trim() : "";
      try {
        sourceUrlSaveBtn.disabled = true;
        if (sourceUrlMsgEl) sourceUrlMsgEl.textContent = "保存中...";
        await patchSourceUrl(next);
        await loadHub();
        setSourceUrlEditMode(false);
        if (sourceUrlMsgEl) sourceUrlMsgEl.textContent = "链接已更新";
      } catch (err) {
        if (sourceUrlMsgEl) sourceUrlMsgEl.textContent = err.message || "save source url failed";
      } finally {
        sourceUrlSaveBtn.disabled = false;
      }
    });
  }
  if (finalVideoEl) {
    finalVideoEl.addEventListener("error", async () => {
      const finalUrl = resolveFinalUrl(currentHub || {});
      const finalExists = Boolean(currentHub && currentHub.final_exists);
      const retryKey = `${finalUrl || ""}::${String(((currentHub && currentHub.final) || {}).asset_version || "")}`;
      if (!finalExists || !finalUrl) return;
      if (retryKey !== finalPreviewRetryKey) {
        finalPreviewRetryKey = retryKey;
        finalPreviewRetried = false;
      }
      if (finalPreviewRetried) return;
      finalPreviewRetried = true;
      if (composeMsgEl) composeMsgEl.textContent = "最终成片加载中，正在重试一次…";
      const ok = await probeFinalUrlOnce(finalUrl);
      if (ok) {
        setMediaSrcStable(finalVideoEl, finalUrl, "finalUrl(retry)", ((currentHub && currentHub.final) || {}).asset_version || null);
        if (composeFinalVideoEl && activeTab === "final") {
          setMediaSrcStable(composeFinalVideoEl, finalUrl, "finalUrl(compose-retry)", ((currentHub && currentHub.final) || {}).asset_version || null);
        }
      }
    });
  }
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
  if (composeModeSubtitleEl) {
    composeModeSubtitleEl.addEventListener("click", async (e) => {
      e.preventDefault();
      applyComposeModePreset("subtitle");
      try {
        await patchComposePlan({ overlay_subtitles: true, freeze_tail_enabled: false, freeze_tail_cap_sec: 8 });
        await patchAudioConfig({ bgm_mix: 0 });
        await loadHub();
      } catch (err) {
        if (composeMsgEl) composeMsgEl.textContent = err.message || "save compose mode failed";
      }
    });
  }
  if (composeModeVoiceEl) {
    composeModeVoiceEl.addEventListener("click", async (e) => {
      e.preventDefault();
      applyComposeModePreset("voice");
      try {
        await patchComposePlan({ overlay_subtitles: true, freeze_tail_enabled: true, freeze_tail_cap_sec: 8 });
        await loadHub();
      } catch (err) {
        if (composeMsgEl) composeMsgEl.textContent = err.message || "save compose mode failed";
      }
    });
  }
  if (composeModeBgmEl) {
    composeModeBgmEl.addEventListener("click", async (e) => {
      e.preventDefault();
      applyComposeModePreset("bgm");
      try {
        await patchComposePlan({ overlay_subtitles: true, freeze_tail_enabled: false, freeze_tail_cap_sec: 8 });
        await patchAudioConfig({ bgm_mix: 0.35 });
        await loadHub();
      } catch (err) {
        if (composeMsgEl) composeMsgEl.textContent = err.message || "save compose mode failed";
      }
    });
  }
  if (cleanupKeepEl) {
    cleanupKeepEl.addEventListener("click", async (e) => {
      e.preventDefault();
      applyCleanupModePreset("none");
      try {
        await patchComposePlan({ cleanup_mode: "none" });
        await loadHub();
      } catch (err) {
        if (composeMsgEl) composeMsgEl.textContent = err.message || "save cleanup mode failed";
      }
    });
  }
  if (cleanupMaskEl) {
    cleanupMaskEl.addEventListener("click", async (e) => {
      e.preventDefault();
      applyCleanupModePreset("bottom_mask");
      try {
        await patchComposePlan({ cleanup_mode: "bottom_mask" });
        await loadHub();
      } catch (err) {
        if (composeMsgEl) composeMsgEl.textContent = err.message || "save cleanup mode failed";
      }
    });
  }
  if (cleanupCleanEl) {
    cleanupCleanEl.addEventListener("click", async (e) => {
      e.preventDefault();
      applyCleanupModePreset("safe_band");
      try {
        await patchComposePlan({ cleanup_mode: "safe_band" });
        await loadHub();
      } catch (err) {
        if (composeMsgEl) composeMsgEl.textContent = err.message || "save cleanup mode failed";
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
        const currentText = subtitlesTextEl ? subtitlesTextEl.value : "";
        const profile = currentTargetProfile();
        const subtitleReady = Boolean(currentHub && currentHub.subtitle_ready);
        const subtitleReason = String(
          (currentHub && (currentHub.target_subtitle_current_reason || currentHub.subtitle_ready_reason)) || ""
        ).trim();
        if (profile.targetLang === "vi" && !subtitleReady) {
          const warning = subtitleReason === "target_subtitle_translation_incomplete"
            ? `当前${profile.displayName}目标字幕仍未翻译完成，请先翻译并保存 ${profile.subtitleFilename}，再生成${profile.displayName}配音。`
            : `当前${profile.displayName}目标字幕还不是可配音的当前版本，请先翻译并保存 ${profile.subtitleFilename}，再生成${profile.displayName}配音。`;
          if (audioMsgEl) audioMsgEl.textContent = warning;
          if (subtitlesMsgEl) subtitlesMsgEl.textContent = warning;
          return;
        }
        const analysis = analyzeTargetDubCandidate(currentText);
        if (analysis.text && analysis.shouldBlockMyanmarTts) {
          const warning = `当前文本尚未翻译为${profile.displayName}，不建议直接生成${profile.displayName}配音。请先翻译并保存字幕成品，或直接走字幕版合成。`;
          if (audioMsgEl) audioMsgEl.textContent = warning;
          if (subtitlesMsgEl) subtitlesMsgEl.textContent = warning;
          return;
        }
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
        const audio = (currentHub && currentHub.audio) || {};
        const voiceUrl = resolveTtsPreviewUrl(audio);
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
  if (translateMmBtn) {
    translateMmBtn.addEventListener("click", async (e) => {
      e.preventDefault();
      try {
        const subtitles = (currentHub && currentHub.subtitles) || {};
        const sourceText = String(
          subtitles.normalized_source_text || subtitles.raw_source_text || subtitles.origin_text || subtitles.parse_source_text || ""
        ).trim();
        if (!sourceText) throw new Error("当前没有可用的来源字幕，请先完成解析或检查来源字幕。");
        translateMmBtn.disabled = true;
        if (subtitlesMsgEl) subtitlesMsgEl.textContent = `正在翻译为${currentTargetProfile().displayName}...`;
        const data = await translateCurrentSubtitles({ text: sourceText, input_source: "source_subtitle_lane" });
        applyTranslatedTextToTargetEditor(
          String(data.translated_text || ""),
          "来源字幕已翻译并写入目标字幕主对象。",
        );
        subtitleDirty = false;
        await loadHub();
      } catch (err) {
        const message = readableErrorMessage(err, "translate failed");
        if (subtitlesMsgEl) subtitlesMsgEl.textContent = message;
        if (assistedInputMsgEl && err && err.recoverableHelperFailure) assistedInputMsgEl.textContent = message;
        if (err && err.recoverableHelperFailure) await loadHub().catch(() => {});
      } finally {
        translateMmBtn.disabled = false;
      }
    });
  }
  if (assistedInputTextEl) {
    assistedInputTextEl.addEventListener("input", () => {
      assistedInputDirty = true;
      persistAssistedInputDraft(assistedInputTextEl.value || "");
      if (assistedInputMsgEl) assistedInputMsgEl.textContent = "";
    });
  }
  if (assistedTranslateBtn) {
    assistedTranslateBtn.addEventListener("click", async (e) => {
      e.preventDefault();
      try {
        const text = assistedInputTextEl ? String(assistedInputTextEl.value || "").trim() : "";
        if (!text) throw new Error("请先在辅助输入区填写原文或候选文本。");
        assistedTranslateBtn.disabled = true;
        if (assistedInputMsgEl) assistedInputMsgEl.textContent = "正在翻译并写入目标字幕区...";
        const data = await translateCurrentSubtitles({ text, input_source: "helper_only_text" });
        applyTranslatedTextToTargetEditor(String(data.translated_text || ""), "辅助输入已翻译并写入目标字幕区，请检查后保存字幕。");
        if (assistedInputMsgEl) assistedInputMsgEl.textContent = "辅助输入翻译完成。";
      } catch (err) {
        const message = readableErrorMessage(err, "translate failed");
        if (assistedInputMsgEl) assistedInputMsgEl.textContent = message;
        if (err && err.recoverableHelperFailure) await loadHub().catch(() => {});
      } finally {
        assistedTranslateBtn.disabled = false;
      }
    });
  }
  if (assistedFillSourceBtn) {
    assistedFillSourceBtn.addEventListener("click", (e) => {
      e.preventDefault();
      const text = subtitlesOriginEl ? String(subtitlesOriginEl.textContent || "").trim() : "";
      fillAssistedInputFromText(text, "来源字幕已填充到辅助输入区，可继续翻译写入目标字幕区。");
    });
  }
  if (assistedFillNormalizedBtn) {
    assistedFillNormalizedBtn.addEventListener("click", (e) => {
      e.preventDefault();
      const text = subtitlesNormalizedEl ? String(subtitlesNormalizedEl.textContent || "").trim() : "";
      fillAssistedInputFromText(text, "标准化来源文本已填充到辅助输入区，可继续翻译写入目标字幕区。");
    });
  }
  if (ocrFillBtn) {
    ocrFillBtn.addEventListener("click", (e) => {
      e.preventDefault();
      const candidate = getOcrCandidateText();
      if (!candidate) {
        if (assistedInputMsgEl) assistedInputMsgEl.textContent = "当前没有可用的候选文字草稿，请先手工补辅助输入。";
        return;
      }
      if (assistedInputTextEl) assistedInputTextEl.value = candidate;
      assistedInputDirty = true;
      persistAssistedInputDraft(candidate);
      if (assistedInputMsgEl) assistedInputMsgEl.textContent = "候选文本已填充到辅助输入区，可继续翻译写入目标字幕区。";
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

  // Phase 0.6: compose quick bar button binding
  const _cqBtn = document.getElementById("hf_compose_quick_btn");
  if (_cqBtn) {
    _cqBtn.addEventListener("click", async (e) => {
      e.preventDefault();
      // Always switch to compose tab first so user sees the full compose panel
      const composeTabBtn = document.querySelector('.hf-sidebar-tab[data-tab="compose"]');
      if (composeTabBtn) composeTabBtn.click();
      // Check confirmation — if not checked, guide user instead of silent failure
      if (composeConfirmEl && !composeConfirmEl.checked) {
        const confirmRow = composeConfirmEl.closest("label");
        if (confirmRow) {
          confirmRow.classList.add("bg-amber-50", "ring-2", "ring-amber-400", "rounded-lg", "px-2", "py-1");
          confirmRow.scrollIntoView({ behavior: "smooth", block: "center" });
          setTimeout(() => confirmRow.classList.remove("bg-amber-50", "ring-2", "ring-amber-400", "rounded-lg", "px-2", "py-1"), 3000);
        }
        const cqStatus = document.getElementById("hf_cq_status_text");
        if (cqStatus) cqStatus.textContent = "请先在合成面板确认就绪";
        if (composeMsgEl) composeMsgEl.textContent = "请勾选确认后再合成";
        return;
      }
      _cqBtn.disabled = true;
      _cqBtn.textContent = "合成中...";
      try {
        await composeFinal();
        await loadHub();
      } catch (err) {
        if (composeMsgEl) composeMsgEl.textContent = err.message || "compose failed";
        const cqStatus = document.getElementById("hf_cq_status_text");
        if (cqStatus) cqStatus.textContent = err.message || "合成失败";
      } finally {
        _cqBtn.disabled = false;
        _cqBtn.textContent = "合成最终视频";
        updateComposeButtonState();
      }
    });
  }

  hydrateAssistedInputDraft();
  loadHub().then(() => setTab("source")).catch((e) => {
    if (statusEl) statusEl.textContent = e.message || "hub load failed";
  });
  renderDubOutdatedBadge();
  refreshPollingState();
})();
