(function () {
  const urlEl = document.getElementById("hf-url");
  const platformEl = document.getElementById("hf-platform");
  const probeCard = document.getElementById("hf-probe");
  const coverEl = document.getElementById("hf-cover");
  const titleEl = document.getElementById("hf-title");
  const durationEl = document.getElementById("hf-duration");
  const platformTextEl = document.getElementById("hf-platform-text");
  const probeMsg = document.getElementById("hf-probe-msg");
  const createBtn = document.getElementById("hf-create");
  const createMsg = document.getElementById("hf-create-msg");
  const bgmFile = document.getElementById("hf-bgm");
  const mixEl = document.getElementById("hf-mix");
  const targetLangEl = document.querySelector('select[name="target_lang"]');
  const voiceIdEl = document.getElementById("hf-voice-id");
  const publishAccountEl = document.querySelector('select[name="publish_account"]');
  const taskTitleEl = document.getElementById("hf-task-title");
  const languageProfiles = Array.isArray(window.__HF_LANGUAGE_PROFILES__) ? window.__HF_LANGUAGE_PROFILES__ : [];
  const profileByLang = new Map(languageProfiles.map((profile) => [String(profile.target_lang || "").toLowerCase(), profile]));

  let lastProbe = null;
  let debounceTimer = null;

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

  function withLocale(url) {
    const loc = readLocale();
    if (!loc) return url;
    return url.includes("?") ? `${url}&ui_locale=${encodeURIComponent(loc)}` : `${url}?ui_locale=${encodeURIComponent(loc)}`;
  }

  function setProbeState(ok, msg) {
    probeMsg.textContent = msg || "";
    createBtn.disabled = !ok;
    refreshLocale(probeCard || document);
  }

  function currentProfile() {
    const lang = String((targetLangEl && targetLangEl.value) || "mm").toLowerCase();
    return profileByLang.get(lang) || profileByLang.get("mm") || null;
  }

  function refreshVoiceOptions() {
    if (!voiceIdEl) return;
    const profile = currentProfile();
    const allowed = Array.isArray(profile && profile.allowed_voice_options) ? profile.allowed_voice_options : ["mm_female_1", "mm_male_1"];
    const labels = {
      female: "女声",
      male: "男声",
    };
    const current = String(voiceIdEl.value || "");
    voiceIdEl.innerHTML = "";
    allowed.forEach((voiceId) => {
      const option = document.createElement("option");
      option.value = voiceId;
      option.textContent = voiceId.indexOf("male") >= 0 ? labels.male : labels.female;
      voiceIdEl.appendChild(option);
    });
    voiceIdEl.value = allowed.includes(current) ? current : String((((profile || {}).default_voice_by_provider || {})["azure-speech"]) || allowed[0] || "");
  }

  async function doProbe() {
    const url = (urlEl.value || "").trim();
    if (!url) {
      setProbeState(false, "");
      return;
    }
    probeMsg.textContent = "...";
    try {
      const res = await fetch("/api/tasks/probe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ platform: platformEl.value || "auto", url }),
      });
      if (!res.ok) {
        const text = await res.text();
        setProbeState(false, text || "probe failed");
        return;
      }
      const data = await res.json();
      lastProbe = data;
      coverEl.src = data.cover || "";
      coverEl.style.visibility = data.cover ? "visible" : "hidden";
      titleEl.textContent = data.title || "-";
      durationEl.textContent = data.duration_sec ? `${data.duration_sec}s` : "";
      platformTextEl.textContent = data.platform || "";
      setProbeState(true, "");
      refreshLocale(probeCard || document);
    } catch (e) {
      setProbeState(false, e.message || "probe error");
    }
  }

  function scheduleProbe() {
    if (debounceTimer) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(doProbe, 600);
  }

  async function createTask() {
    if (!lastProbe) return;
    createBtn.disabled = true;
    createMsg.textContent = "...";

    const url = (urlEl.value || "").trim();
    const platform = platformEl.value || "auto";
    const locale = readLocale() || "zh";

    try {
      const processModeEl = document.querySelector('input[name="process_mode"]:checked');
      const processMode = processModeEl ? processModeEl.value : "fast_clone";
      const pipelineConfig = {
        process_mode: processMode,
      };
      if (publishAccountEl && publishAccountEl.value) pipelineConfig.publish_account = publishAccountEl.value;

      const res = await fetch("/api/hot_follow/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source_url: url,
          platform: platform === "auto" ? null : platform,
          title: (taskTitleEl && taskTitleEl.value ? taskTitleEl.value : "") || lastProbe.title || null,
          category_key: "hot_follow",
          kind: "hot_follow",
          account_id: publishAccountEl ? publishAccountEl.value : null,
          account_name: publishAccountEl ? publishAccountEl.value : null,
          content_lang: targetLangEl ? targetLangEl.value : "mm",
          voice_id: voiceIdEl ? voiceIdEl.value : "mm_female_1",
          ui_lang: locale,
          pipeline_config: pipelineConfig,
          auto_start: true,
        }),
      });
      if (!res.ok) {
        const text = await res.text();
        createMsg.textContent = text || "create failed";
        createBtn.disabled = false;
        return;
      }
      const task = await res.json();
      const taskId = task.task_id || task.id;
      if (!taskId) {
        createMsg.textContent = "invalid task id";
        createBtn.disabled = false;
        return;
      }

      const strategyEl = document.querySelector('input[name="bgm_strategy"]:checked');
      const strategy = strategyEl ? strategyEl.value : "replace";
      if (bgmFile && bgmFile.files && bgmFile.files[0]) {
        const fd = new FormData();
        fd.append("file", bgmFile.files[0]);
        fd.append("mix_ratio", mixEl ? mixEl.value : "0.8");
        fd.append("strategy", strategy);
        await fetch(`/api/hot_follow/tasks/${encodeURIComponent(taskId)}/bgm`, {
          method: "POST",
          body: fd,
        });
      }
      await fetch(`/api/hot_follow/tasks/${encodeURIComponent(taskId)}/run`, { method: "POST" });

      window.location.href = withLocale(`/tasks/${encodeURIComponent(taskId)}`);
    } catch (e) {
      createMsg.textContent = e.message || "create error";
      createBtn.disabled = false;
    }
  }

  if (urlEl) urlEl.addEventListener("input", scheduleProbe);
  if (platformEl) platformEl.addEventListener("change", scheduleProbe);
  if (targetLangEl) targetLangEl.addEventListener("change", refreshVoiceOptions);
  if (createBtn) {
    createBtn.addEventListener("click", (e) => {
      e.preventDefault();
      createTask();
    });
  }

  refreshVoiceOptions();
  refreshLocale(document);
})();
