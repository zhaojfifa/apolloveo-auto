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
  const publishAccountEl = document.querySelector('select[name="publish_account"]');
  const taskTitleEl = document.getElementById("hf-task-title");

  let lastProbe = null;
  let debounceTimer = null;

  function getLocale() {
    const qs = new URLSearchParams(window.location.search || "");
    return qs.get("ui_locale") || "";
  }

  function withLocale(url) {
    const loc = getLocale();
    if (!loc) return url;
    return url.includes("?") ? `${url}&ui_locale=${encodeURIComponent(loc)}` : `${url}?ui_locale=${encodeURIComponent(loc)}`;
  }

  function setProbeState(ok, msg) {
    probeMsg.textContent = msg || "";
    createBtn.disabled = !ok;
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
    const locale = getLocale() || "zh";

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

      window.location.href = withLocale(`/tasks/${encodeURIComponent(taskId)}`);
    } catch (e) {
      createMsg.textContent = e.message || "create error";
      createBtn.disabled = false;
    }
  }

  if (urlEl) {
    urlEl.addEventListener("input", scheduleProbe);
  }
  if (platformEl) {
    platformEl.addEventListener("change", scheduleProbe);
  }
  if (createBtn) {
    createBtn.addEventListener("click", (e) => {
      e.preventDefault();
      createTask();
    });
  }
})();
