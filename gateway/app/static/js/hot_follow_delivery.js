(function () {
  const root = document.querySelector(".page");
  const taskId = root ? root.getAttribute("data-task-id") : null;
  const listEl = document.getElementById("hf-deliverables");
  const emptyEl = document.getElementById("hf-deliverables-empty");
  const publishBtn = document.getElementById("hf-publish");
  const publishUrl = document.getElementById("hf-publish-url");
  const publishNotes = document.getElementById("hf-publish-notes");
  const publishMsg = document.getElementById("hf-publish-msg");
  const composedBadgeEl = document.getElementById("hf-composed-badge");
  const composedReasonEl = document.getElementById("hf-composed-reason");
  const scenePackStatusEl = document.getElementById("hf-scene-pack-status");
  const scenePackReasonEl = document.getElementById("hf-scene-pack-reason");
  const scenePackActionEl = document.getElementById("hf-scene-pack-action");
  const scenePackGenerateBtn = document.getElementById("hf-scene-pack-generate");
  const hintSummaryEl = document.getElementById("hf-hint-summary");
  const hintNextEl = document.getElementById("hf-hint-next");
  const hintStatusEl = document.getElementById("hf-hint-status");
  const finalPreviewBoxEl = document.getElementById("hf_final_preview_box");
  const translationQaEl = document.getElementById("hf-translation-qa");
  const translationQaWarnEl = document.getElementById("hf-translation-qa-warn");
  const voiceAlignmentEl = document.getElementById("hf-voice-alignment");
  const burnedModeEl = document.getElementById("hf-burned-mode");

  let currentTaskDetail = null;

  if (!taskId) return;

  function readLocale() {
    const i18n = window.__V185_I18N__ || {};
    if (typeof i18n.readLocale === "function") return i18n.readLocale();
    const qs = new URLSearchParams(window.location.search || "");
    return (qs.get("ui_locale") || "zh").toLowerCase();
  }

  function refreshLocale(rootEl) {
    const i18n = window.__V185_I18N__ || {};
    if (typeof i18n.applyLocaleFor === "function") i18n.applyLocaleFor(rootEl || document);
    else if (typeof i18n.applyLocale === "function") i18n.applyLocale(readLocale(), rootEl || document);
    else if (typeof window.__I18N_REAPPLY__ === "function") window.__I18N_REAPPLY__();
  }

  function t(key, fallback, vars) {
    const i18n = window.__V185_I18N__ || {};
    if (typeof i18n.t === "function") {
      const text = i18n.t(key, vars);
      if (typeof text === "string" && text.trim() !== "" && text.indexOf("MISSING:") === -1) return text;
    }
    return fallback;
  }

  function pickFinalVideoUrl(task) {
    if (typeof window.__HF_PICK_FINAL_URL__ === "function") return window.__HF_PICK_FINAL_URL__(task);
    const media = (task && task.media) || {};
    const finalMeta = (task && task.final) || {};
    return media.final_video_url || media.final_url || finalMeta.url || (task && task.final_video_url) || (task && task.final_url) || null;
  }
  function escapeAttr(value) {
    return String(value || "").replace(/"/g, "&quot;");
  }
  function renderFinalPreview(finalUrl) {
    if (!finalPreviewBoxEl) return;
    if (finalUrl) {
      finalPreviewBoxEl.innerHTML = `<video controls playsinline preload="metadata" class="w-full h-48 rounded-xl bg-slate-100" src="${escapeAttr(finalUrl)}"></video><div class="text-xs text-green-700 mt-2">Final video ready for publishing.</div>`;
      return;
    }
    finalPreviewBoxEl.innerHTML = '<div class="w-full h-48 rounded-xl bg-gray-100 border border-dashed border-gray-300 flex items-center justify-center text-xs text-gray-500">Final video not ready yet.</div>';
  }

  function reasonText(reason) {
    const mapping = {
      ready: t("hot_follow_compose_reason_ready", "Ready"),
      final_missing: t("hot_follow_compose_reason_final_missing", "Final video missing"),
      compose_in_progress: t("hot_follow_compose_reason_in_progress", "Composing..."),
      compose_failed: t("hot_follow_compose_reason_failed", "Compose failed"),
      missing_voiceover: t("hot_follow_compose_reason_missing_voice", "Missing voiceover"),
      missing_raw: t("hot_follow_compose_reason_missing_raw", "Missing source video"),
    };
    return mapping[reason] || reason || "-";
  }

  function groupDeliverables(deliverables) {
    const groups = [
      { label: t("hot_follow_delivery_group_final", "Final"), keys: ["final_mp4"] },
      { label: t("hot_follow_delivery_group_pack", "Pack"), keys: ["pack_zip", "edit_bundle_zip"] },
      { label: t("hot_follow_delivery_group_subtitles", "Subtitles"), keys: ["origin_srt", "mm_srt", "mm_txt"] },
      { label: t("hot_follow_delivery_group_audio", "Audio"), keys: ["mm_audio", "bgm_audio"] },
      { label: t("hot_follow_scene_pack_title", "Scene Pack (optional)"), keys: ["scenes_zip"] },
    ];
    return groups.map((g) => ({
      label: g.label,
      rows: g.keys.filter((k) => deliverables[k]).map((k) => ({ key: k, ...deliverables[k] })),
    }));
  }

  function renderHintPanel(data, deliverables) {
    const readyGate = (data && data.ready_gate) || {};
    const hasFinal = Boolean(deliverables.final_mp4);
    const hasPack = Boolean(deliverables.pack_zip || deliverables.edit_bundle_zip);
    const hasSubs = Boolean(deliverables.origin_srt || deliverables.mm_srt || deliverables.mm_txt);
    const hasAudio = Boolean(deliverables.mm_audio || deliverables.bgm_audio);
    const hasBgm = Boolean(deliverables.bgm_audio);
    if (hintSummaryEl) {
      hintSummaryEl.textContent = `${t("hot_follow_delivery_soft_subtitle_hint", "This delivery includes: Final / Pack / Subtitles / Audio / BGM…")} (${hasFinal ? "Y" : "N"}/${hasPack ? "Y" : "N"}/${hasSubs ? "Y" : "N"}/${hasAudio ? "Y" : "N"}/${hasBgm ? "Y" : "N"})`;
    }
    if (hintNextEl) {
      hintNextEl.textContent = hasFinal
        ? t("hot_follow_delivery_next_ready", "Next: publish final video or download pack for further edits.")
        : t("hot_follow_delivery_next_compose", "Next: return to Workbench and run Compose Final.");
    }
    if (hintStatusEl) {
      const ready = Boolean(readyGate.publish_ready);
      const scenePending = data.scene_pack_pending_reason ? ` ${t("hot_follow_delivery_scene_pending_suffix", "(Scene Pack pending, does not block publish)")}` : "";
      hintStatusEl.textContent = ready
        ? t("hot_follow_delivery_status_ready", "Status: ready to publish")
        : `${t("hot_follow_delivery_status_prefix", "Status")}: ${reasonText(data.composed_reason)}${scenePending}`;
    }
  }

  function renderDeliverables(data) {
    const deliverables = data.deliverables || {};
    const keys = Object.keys(deliverables);
    const readyGate = (data && data.ready_gate) || {};
    const composedReady = Boolean(readyGate.publish_ready);
    const composedReason = data.composed_reason || "final_missing";

    if (composedBadgeEl) {
      composedBadgeEl.textContent = composedReady ? t("hot_follow_compose_reason_ready", "Ready") : t("hot_follow_workbench_composed_not_ready", "Not Ready");
      composedBadgeEl.classList.toggle("text-green-700", composedReady);
      composedBadgeEl.classList.toggle("text-amber-700", !composedReady);
    }
    if (composedReasonEl) composedReasonEl.textContent = reasonText(composedReason);
    if (scenePackStatusEl) scenePackStatusEl.textContent = data.scene_pack_pending_reason ? t("common_status_pending", "pending") : t("common_status_ready", "ready");
    if (scenePackReasonEl) scenePackReasonEl.textContent = data.scene_pack_pending_reason || "";
    if (scenePackActionEl) {
      if (data.scene_pack_pending_reason && data.scene_pack_action_url) {
        scenePackActionEl.href = data.scene_pack_action_url;
        scenePackActionEl.classList.remove("hidden");
      } else {
        scenePackActionEl.classList.add("hidden");
      }
    }

    renderHintPanel(data, deliverables);
    renderDiagnostics(data);

    const finalUrl = pickFinalVideoUrl(data) || pickFinalVideoUrl(currentTaskDetail);
    if (finalUrl) {
      deliverables.final_mp4 = deliverables.final_mp4 || { label: "final.mp4" };
      deliverables.final_mp4.url = finalUrl;
    }
    renderFinalPreview(finalUrl);

    if (!keys.length) {
      if (emptyEl) emptyEl.style.display = "block";
      if (listEl) listEl.innerHTML = "";
      return;
    }
    if (emptyEl) emptyEl.style.display = "none";
    if (!listEl) return;
    const grouped = groupDeliverables(deliverables);
    listEl.innerHTML = grouped
      .map((g) => {
        if (!g.rows.length) return "";
        return `
          <div class="rounded-xl border border-gray-200 p-3">
            <div class="text-xs font-semibold text-gray-700 mb-2">${g.label}</div>
            <div class="space-y-2">
              ${g.rows.map((item) => `<div class="deliverable"><span>${item.label || item.key}</span><a class="btn-secondary" href="${item.url}" target="_blank" rel="noopener">${t("common_buttons_download", "Download")}</a>${item.description ? `<div class="text-[11px] text-gray-500 mt-1">${item.description}</div>` : ""}</div>`).join("")}
            </div>
          </div>
        `;
      })
      .join("");
    refreshLocale(listEl);
  }

  function renderDiagnostics(data) {
    const pipelineConfig = (currentTaskDetail && currentTaskDetail.pipeline_config) || {};
    const composePlan = ((currentTaskDetail && currentTaskDetail.compose_plan) || data.compose_plan || {});

    const sourceRaw = pipelineConfig.translation_source_count;
    const translatedRaw = pipelineConfig.translation_translated_count;
    const sourceCount = sourceRaw === undefined || sourceRaw === null || sourceRaw === "" ? "-" : Number(sourceRaw);
    const translatedCount = translatedRaw === undefined || translatedRaw === null || translatedRaw === "" ? "-" : Number(translatedRaw);
    const translationIncomplete = pipelineConfig.translation_incomplete === "true" || pipelineConfig.translation_incomplete === true;
    if (translationQaEl) translationQaEl.textContent = `Translation QA: source_count=${sourceCount}, translated_count=${translatedCount}`;
    if (translationQaWarnEl) translationQaWarnEl.textContent = translationIncomplete ? "Warning: translation incomplete" : "";

    const avgRateRaw = pipelineConfig.voice_alignment_avg_rate;
    const overBudgetRaw = pipelineConfig.voice_alignment_over_budget_cues;
    const avgRate = avgRateRaw === undefined || avgRateRaw === null || avgRateRaw === "" ? "-" : Number(avgRateRaw);
    const overBudget = overBudgetRaw === undefined || overBudgetRaw === null || overBudgetRaw === "" ? "-" : Number(overBudgetRaw);
    if (voiceAlignmentEl) voiceAlignmentEl.textContent = `Voice alignment: avg_rate=${avgRate}, over_budget_cues=${overBudget}`;

    if (burnedModeEl) burnedModeEl.textContent = `Burned subtitles mode: ${composePlan.burned_subtitles_mode || "none"}`;
  }

  async function loadPublishHub() {
    try {
      try {
        const detailRes = await fetch(`/api/tasks/${encodeURIComponent(taskId)}`, { cache: "no-store", credentials: "same-origin" });
        if (detailRes.ok) currentTaskDetail = await detailRes.json();
      } catch (_) {}
      const res = await fetch(`/api/hot_follow/tasks/${encodeURIComponent(taskId)}/publish_hub`, { cache: "no-store", credentials: "same-origin" });
      if (!res.ok) {
        if (emptyEl) emptyEl.style.display = "block";
        return;
      }
      const data = await res.json();
      renderDeliverables(data);
    } catch (_) {
      if (emptyEl) emptyEl.style.display = "block";
    }
  }

  async function backfillPublish() {
    if (!publishBtn) return;
    publishBtn.disabled = true;
    if (publishMsg) publishMsg.textContent = t("common_loading", "...");
    try {
      const res = await fetch(`/api/hot_follow/tasks/${encodeURIComponent(taskId)}/publish_backfill`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          publish_url: publishUrl ? publishUrl.value : "",
          note: publishNotes ? publishNotes.value : "",
          status: "ready",
        }),
      });
      if (!res.ok) {
        const text = await res.text();
        if (publishMsg) publishMsg.textContent = text || "publish failed";
      } else if (publishMsg) {
        publishMsg.textContent = t("common_ok", "OK");
      }
    } catch (e) {
      if (publishMsg) publishMsg.textContent = e.message || "publish error";
    } finally {
      publishBtn.disabled = false;
    }
  }

  if (publishBtn) {
    publishBtn.addEventListener("click", (e) => {
      e.preventDefault();
      backfillPublish();
    });
  }

  if (scenePackGenerateBtn) {
    scenePackGenerateBtn.addEventListener("click", async (e) => {
      e.preventDefault();
      scenePackGenerateBtn.disabled = true;
      try {
        const res = await fetch(`/api/tasks/${encodeURIComponent(taskId)}/scenes`, { method: "POST" });
        if (!res.ok) throw new Error(await res.text());
      } finally {
        scenePackGenerateBtn.disabled = false;
        loadPublishHub();
      }
    });
  }

  refreshLocale(document);
  loadPublishHub();
})();
