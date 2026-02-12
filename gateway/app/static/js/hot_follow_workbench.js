(function () {
  const root = document.querySelector(".page");
  const taskId = root ? root.getAttribute("data-task-id") : null;
  const eventsEl = document.getElementById("hf-events");
  const statusEl = document.getElementById("hf-status");
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

  if (!taskId) return;

  let currentHub = null;

  function setStep(step, status, summary) {
    const statusEl = document.querySelector(`[data-hf-step-status="${step}"]`);
    const summaryEl = document.querySelector(`[data-hf-step-summary="${step}"]`);
    if (statusEl) statusEl.textContent = status || "none";
    if (summaryEl) summaryEl.textContent = summary || "-";
  }

  function escapeHtml(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function renderDeliverables(items) {
    if (!deliverablesGridEl) return;
    const list = Array.isArray(items) ? items : [];
    if (!list.length) {
      deliverablesGridEl.innerHTML = '<div class="rounded-lg border border-gray-200 p-3 text-sm text-gray-500">暂无交付物</div>';
      return;
    }
    deliverablesGridEl.innerHTML = list.map((d) => {
      const title = escapeHtml(d.title || d.kind || "-");
      const key = escapeHtml(d.key || "-");
      const status = escapeHtml(d.status || "none");
      const hasUrl = Boolean(d.url);
      const btnClass = hasUrl ? "btn-secondary" : "btn-secondary opacity-50 pointer-events-none";
      const href = hasUrl ? d.url : "#";
      const btnText = hasUrl ? "下载" : "暂无";
      return `
        <div class="rounded-lg border border-gray-200 p-3">
          <div class="flex items-center justify-between gap-3">
            <div class="text-sm font-semibold">${title}</div>
            <div class="text-xs rounded-full bg-gray-100 px-2 py-1">${status}</div>
          </div>
          <div class="text-xs text-gray-500 mt-1 truncate">${key}</div>
          <a class="${btnClass} mt-2 inline-block text-xs" href="${href}" target="_blank" rel="noopener">${btnText}</a>
        </div>
      `;
    }).join("");
  }

  function renderScenePack(scenePack) {
    if (!scenePackDownloadEl) return;
    const status = (scenePack && scenePack.status) || "none";
    const url = scenePack && scenePack.scenes_url;
    const statusEl = document.querySelector('[data-hf-step-status="scenes"]');
    if (statusEl) statusEl.textContent = status;
    if (url) {
      scenePackDownloadEl.href = url;
      scenePackDownloadEl.classList.remove("opacity-50", "pointer-events-none");
      if (scenePackHintEl) scenePackHintEl.textContent = "Scene Pack 已生成";
    } else {
      scenePackDownloadEl.href = "#";
      scenePackDownloadEl.classList.add("opacity-50", "pointer-events-none");
      if (scenePackHintEl) scenePackHintEl.textContent = status === "failed" ? "Scene Pack 生成失败" : "可选，未生成时不影响主流程";
    }
  }

  function renderAudioConfig(cfg) {
    if (!cfg) return;
    if (ttsEngineEl && cfg.tts_engine) ttsEngineEl.value = cfg.tts_engine;
    if (ttsVoiceEl && cfg.tts_voice) ttsVoiceEl.value = cfg.tts_voice;
    if (bgmMixEl && cfg.bgm_mix != null) bgmMixEl.value = String(cfg.bgm_mix);
  }

  function renderHub(hub) {
    currentHub = hub || {};
    const pipeline = currentHub.pipeline || {};
    setStep("parse", pipeline.parse && pipeline.parse.status, pipeline.parse && pipeline.parse.summary);
    setStep("subtitles", pipeline.subtitles && pipeline.subtitles.status, pipeline.subtitles && pipeline.subtitles.summary);
    setStep("audio", pipeline.audio && pipeline.audio.status, pipeline.audio && pipeline.audio.summary);
    setStep("synthesis", pipeline.synthesis && pipeline.synthesis.status, pipeline.synthesis && pipeline.synthesis.summary);
    renderScenePack(currentHub.scene_pack || {});
    renderDeliverables(currentHub.deliverables || []);
    renderAudioConfig(currentHub.audio_config || {});
    if (statusEl) statusEl.textContent = (currentHub.pipeline && currentHub.pipeline.synthesis && currentHub.pipeline.synthesis.status) || "";

    const audioErr = currentHub.errors && currentHub.errors.audio;
    if (audioMsgEl) {
      audioMsgEl.textContent = audioErr && audioErr.message ? `Audio error: ${audioErr.message}` : "";
    }
  }

  async function loadHub() {
    try {
      const res = await fetch(`/api/hot_follow/tasks/${encodeURIComponent(taskId)}/workbench_hub`);
      if (!res.ok) return;
      const data = await res.json();
      renderHub(data);
    } catch (e) {
      if (statusEl) statusEl.textContent = e.message || "hub load failed";
    }
  }

  async function loadEvents() {
    try {
      const res = await fetch(`/api/tasks/${encodeURIComponent(taskId)}/events`);
      if (!res.ok) return;
      const data = await res.json();
      const events = data.events || [];
      if (eventsEl) eventsEl.innerHTML = events.map((e) => `<div>${escapeHtml(JSON.stringify(e))}</div>`).join("");
    } catch (e) {
      if (eventsEl) eventsEl.textContent = e.message || "events load failed";
    }
  }

  async function patchAudioConfig(next) {
    const res = await fetch(`/api/hot_follow/tasks/${encodeURIComponent(taskId)}/audio_config`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(next || {}),
    });
    if (!res.ok) {
      const txt = await res.text();
      throw new Error(txt || "save audio config failed");
    }
    return res.json();
  }

  async function uploadBgm(file) {
    const fd = new FormData();
    fd.append("file", file);
    if (bgmMixEl) fd.append("mix_ratio", bgmMixEl.value || "0.3");
    const res = await fetch(`/api/hot_follow/tasks/${encodeURIComponent(taskId)}/bgm`, { method: "POST", body: fd });
    if (!res.ok) {
      const txt = await res.text();
      throw new Error(txt || "upload bgm failed");
    }
    return res.json();
  }

  async function rerunAudio() {
    const provider = ttsEngineEl ? ttsEngineEl.value : null;
    const voiceId = ttsVoiceEl ? ttsVoiceEl.value : null;
    const payload = {
      provider: provider === "edge_tts" ? "edge-tts" : provider,
      voice_id: voiceId || null,
    };
    const res = await fetch(`/api/tasks/${encodeURIComponent(taskId)}/dub`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const txt = await res.text();
      throw new Error(txt || "rerun audio failed");
    }
    return res.json();
  }

  async function runAction(kind) {
    const step = kind === "synthesis" ? "pack" : kind;
    const opts = { method: "POST" };
    const res = await fetch(`/api/tasks/${encodeURIComponent(taskId)}/${step}`, opts);
    if (!res.ok) {
      const txt = await res.text();
      throw new Error(txt || `${step} failed`);
    }
    await loadHub();
  }

  if (ttsEngineEl) {
    ttsEngineEl.addEventListener("change", async () => {
      try {
        await patchAudioConfig({ tts_engine: ttsEngineEl.value });
      } catch (e) {
        if (audioMsgEl) audioMsgEl.textContent = e.message || "save failed";
      }
    });
  }
  if (ttsVoiceEl) {
    ttsVoiceEl.addEventListener("change", async () => {
      try {
        await patchAudioConfig({ tts_voice: ttsVoiceEl.value });
      } catch (e) {
        if (audioMsgEl) audioMsgEl.textContent = e.message || "save failed";
      }
    });
  }
  if (bgmMixEl) {
    bgmMixEl.addEventListener("change", async () => {
      try {
        await patchAudioConfig({ bgm_mix: Number(bgmMixEl.value || "0.3") });
      } catch (e) {
        if (audioMsgEl) audioMsgEl.textContent = e.message || "save failed";
      }
    });
  }
  if (bgmFileEl) {
    bgmFileEl.addEventListener("change", async () => {
      const file = bgmFileEl.files && bgmFileEl.files[0];
      if (!file) return;
      try {
        if (audioMsgEl) audioMsgEl.textContent = "uploading bgm...";
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
        if (audioMsgEl) audioMsgEl.textContent = "rerun audio...";
        await patchAudioConfig({
          tts_engine: ttsEngineEl ? ttsEngineEl.value : null,
          tts_voice: ttsVoiceEl ? ttsVoiceEl.value : null,
          bgm_mix: bgmMixEl ? Number(bgmMixEl.value || "0.3") : null,
        });
        await rerunAudio();
        await loadHub();
        if (audioMsgEl) audioMsgEl.textContent = "Audio rerun requested";
      } catch (e2) {
        if (audioMsgEl) audioMsgEl.textContent = e2.message || "rerun failed";
      }
    });
  }
  if (ttsPreviewBtn) {
    ttsPreviewBtn.addEventListener("click", (e) => {
      e.preventDefault();
      if (audioMsgEl) audioMsgEl.textContent = "当前版本试听入口已保留，请使用 Re-Run Audio 获取最新结果";
    });
  }

  document.querySelectorAll("[data-action]").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.preventDefault();
      const action = btn.getAttribute("data-action");
      if (!action) return;
      try {
        await runAction(action);
      } catch (err) {
        if (statusEl) statusEl.textContent = err.message || "action failed";
      }
    });
  });

  loadHub();
  loadEvents();
  setInterval(loadHub, 5000);
  setInterval(loadEvents, 8000);
})();
