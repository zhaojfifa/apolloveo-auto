(function () {
  const root = document.querySelector(".page");
  const taskId = root ? root.getAttribute("data-task-id") : null;
  if (!taskId) return;

  const hubUrl = `/api/hot_follow/tasks/${encodeURIComponent(taskId)}/workbench_hub`;
  const composeUrl = `/api/tasks/${encodeURIComponent(taskId)}/compose`;
  const statusEl = document.getElementById("hf-status");
  const eventsEl = document.getElementById("hf-events");
  const audioMsgEl = document.getElementById("hf-audio-msg");
  const ttsEngineEl = document.getElementById("hf_tts_engine");
  const ttsVoiceEl = document.getElementById("hf_tts_voice");
  const ttsPreviewBtn = document.getElementById("hf_tts_preview_btn");
  const bgmFileEl = document.getElementById("hf_bgm_file");
  const bgmMixEl = document.getElementById("hf_bgm_mix");
  const rerunAudioBtn = document.getElementById("hf_rerun_audio_btn");
  const scenePackDownloadEl = document.getElementById("hf_scene_pack_download");
  const scenePackHintEl = document.getElementById("hf-scene-pack-hint");
  const deliverablesGridEl = document.getElementById("hf_deliverables_grid");
  const subtitlesTextEl = document.getElementById("hf_subtitles_text");
  const subtitlesOriginEl = document.getElementById("hf_subtitles_origin");
  const subtitlesEditedPreviewEl = document.getElementById("hf_subtitles_edited_preview");
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
  const composeBtn = document.getElementById("hf_compose_btn");
  const composeConfirmEl = document.getElementById("hf_compose_confirm");
  const composeMsgEl = document.getElementById("hf_compose_msg");
  const composeFinalBlockEl = document.getElementById("hf_compose_final_block");
  const composeFinalVideoEl = document.getElementById("hf_compose_final_video");
  const composeFinalLinkEl = document.getElementById("hf_compose_final_link");
  const previewAudioEl = new Audio();

  let currentHub = null;
  let subtitleDirty = false;
  let activeTab = "source";

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
    const pack = getPipelineItem("pack");
    const compose = getPipelineItem("compose");
    setStep("parse", parse.status, parse.error || parse.message);
    setStep("subtitles", subtitles.status, subtitles.error || subtitles.message);
    setStep("audio", dub.status, dub.error || dub.message);
    setStep("pack", pack.status, pack.error || pack.message);
    setStep("compose", compose.status, compose.error || compose.message);
    if (statusEl) statusEl.textContent = `${compose.status || pack.status || dub.status || "pending"}`;
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

  function renderMedia() {
    const media = (currentHub && currentHub.media) || {};
    const sourceUrl = media.source_video_url || media.raw_url || null;
    const finalUrl = media.final_video_url || null;

    if (sourceVideoEl) {
      if (sourceUrl) {
        if (sourceVideoEl.src !== sourceUrl) sourceVideoEl.src = sourceUrl;
      } else {
        sourceVideoEl.removeAttribute("src");
      }
    }
    if (finalVideoEl) {
      if (finalUrl) {
        if (finalVideoEl.src !== finalUrl) finalVideoEl.src = finalUrl;
      } else {
        finalVideoEl.removeAttribute("src");
      }
    }
    if (composeFinalVideoEl) {
      if (finalUrl) {
        if (composeFinalVideoEl.src !== finalUrl) composeFinalVideoEl.src = finalUrl;
      } else {
        composeFinalVideoEl.removeAttribute("src");
      }
    }
    if (composeFinalBlockEl) composeFinalBlockEl.classList.toggle("hidden", !finalUrl);
    setLink(composeFinalLinkEl, finalUrl);
    setLink(sourceLinkEl, sourceUrl);
    setLink(finalLinkEl, finalUrl);
    setTab(activeTab);
  }

  function renderSubtitles() {
    const subtitles = (currentHub && currentHub.subtitles) || {};
    const origin = subtitles.origin_text || "";
    const edited = subtitles.edited_text || subtitles.srt_text || "";
    if (subtitlesOriginEl) subtitlesOriginEl.textContent = origin || "-";
    if (subtitlesEditedPreviewEl) subtitlesEditedPreviewEl.textContent = edited || "-";
    if (subtitlesTextEl && !subtitleDirty) subtitlesTextEl.value = edited || "";
  }

  function renderAudio() {
    const audio = (currentHub && currentHub.audio) || {};
    if (ttsEngineEl && audio.tts_engine) ttsEngineEl.value = audio.tts_engine;
    if (ttsVoiceEl && audio.tts_voice) ttsVoiceEl.value = audio.tts_voice;
    if (bgmMixEl && audio.bgm_mix != null) bgmMixEl.value = String(audio.bgm_mix);
    if (audioMsgEl) audioMsgEl.textContent = audio.error ? `Audio error: ${audio.error}` : "";
  }

  function renderScenePack() {
    const scene = (currentHub && currentHub.scene_pack) || {};
    const status = scene.status || "pending";
    const url = scene.download_url || scene.scenes_url || null;
    const stateEl = document.querySelector('[data-hf-step-status="scenes"]');
    if (stateEl) stateEl.textContent = status;
    setLink(scenePackDownloadEl, url);
    if (scenePackHintEl) {
      if (url) scenePackHintEl.textContent = "Scene pack ready";
      else scenePackHintEl.textContent = status === "failed" ? "Scene pack failed" : "Optional and not generated yet";
    }
  }

  function renderDeliverables() {
    if (!deliverablesGridEl) return;
    const list = (currentHub && currentHub.deliverables) || [];
    if (!Array.isArray(list) || !list.length) {
      deliverablesGridEl.innerHTML = '<div class="rounded-lg border border-gray-200 p-3 text-sm text-gray-500">No deliverables yet</div>';
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
    renderPipeline();
    renderMedia();
    renderSubtitles();
    renderAudio();
    renderScenePack();
    renderDeliverables();
    renderEvents();
    updateComposeButtonState();
  }

  async function loadHub() {
    const res = await fetch(hubUrl);
    if (!res.ok) throw new Error((await res.text()) || "hub load failed");
    renderHub(await res.json());
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
    const originalSrt = subtitles.origin_text || "";
    const targetSrt = subtitlesTextEl ? subtitlesTextEl.value : (subtitles.edited_text || subtitles.srt_text || "");
    const payload = {
      tts_engine: provider || null,
      tts_voice: voiceId || null,
      provider: provider === "edge_tts" ? "edge-tts" : provider,
      voice_id: voiceId || null,
      subtitles_srt: (targetSrt || "").trim().length > 0 ? targetSrt : originalSrt,
    };
    const res = await fetch(`/api/tasks/${encodeURIComponent(taskId)}/dub`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error((await res.text()) || "rerun audio failed");
    return res.json();
  }

  async function composeFinal() {
    const payload = {
      bgm_mix: bgmMixEl ? Number(bgmMixEl.value || "0.3") : 0.3,
      force: false,
    };
    const res = await fetch(composeUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error((await res.text()) || "compose failed");
    return res.json();
  }

  function updateComposeButtonState() {
    if (!composeBtn) return;
    const media = (currentHub && currentHub.media) || {};
    const hasVoiceover = Boolean(media.voiceover_url);
    const confirmed = composeConfirmEl ? composeConfirmEl.checked : true;
    composeBtn.disabled = !(hasVoiceover && confirmed);
    composeBtn.classList.toggle("opacity-50", composeBtn.disabled);
    composeBtn.classList.toggle("pointer-events-none", composeBtn.disabled);
    if (composeMsgEl) {
      if (!hasVoiceover) composeMsgEl.textContent = "Compose disabled: run Re-Run Audio first.";
      else if (!confirmed) composeMsgEl.textContent = "Compose disabled: check confirmation first.";
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
    if (subtitlesEditedPreviewEl) subtitlesEditedPreviewEl.textContent = subtitlesTextEl.value || "-";
  });
  if (composeConfirmEl) composeConfirmEl.addEventListener("change", updateComposeButtonState);

  if (ttsEngineEl) {
    ttsEngineEl.addEventListener("change", async () => {
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
        });
        await rerunAudio();
        await loadHub();
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
        await loadHub();
        if (subtitlesMsgEl) subtitlesMsgEl.textContent = "Saved";
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
      } catch (err) {
        if (statusEl) statusEl.textContent = err.message || "action failed";
      }
    });
  });

  loadHub().then(() => setTab("source")).catch((e) => {
    if (statusEl) statusEl.textContent = e.message || "hub load failed";
  });
  setInterval(() => { loadHub().catch(() => {}); }, 4000);
})();
