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
  const hintSummaryEl = document.getElementById("hf-hint-summary");
  const hintNextEl = document.getElementById("hf-hint-next");
  const hintStatusEl = document.getElementById("hf-hint-status");
  const finalVideoEl = document.getElementById("hf-final-video");
  const finalVideoPlaceholderEl = document.getElementById("hf-final-video-placeholder");
  const scenePackGenerateEl = document.getElementById("hf-scene-pack-generate");
  let finalVideoSrc = "";

  if (!taskId) return;

  function reasonText(reason) {
    const mapping = {
      ready: "可发布",
      final_missing: "尚未生成最终成片",
      compose_in_progress: "合成中…",
      compose_failed: "合成失败，可重试",
      subtitles_missing: "缺少目标字幕",
      font_missing: "缺少字幕字体",
      missing_voiceover: "缺少配音",
      missing_raw: "缺少源视频",
    };
    return mapping[reason] || reason || "-";
  }

  function groupDeliverables(deliverables) {
    const groups = [
      { label: "成片", keys: ["final_mp4"] },
      { label: "剪辑包", keys: ["pack_zip", "edit_bundle_zip"] },
      { label: "字幕与脚本", keys: ["origin_srt", "mm_srt", "mm_txt"] },
      { label: "音频素材", keys: ["mm_audio", "bgm_audio"] },
      { label: "Scene Pack", keys: ["scenes_zip"] },
    ];
    return groups.map((g) => ({
      label: g.label,
      rows: g.keys.filter((k) => deliverables[k]).map((k) => ({ key: k, ...deliverables[k] })),
    }));
  }

  function withAssetVersion(url, assetVersion) {
    if (!url) return "";
    const ver = assetVersion ? String(assetVersion) : "";
    if (!ver) return url;
    return `${url}${url.includes("?") ? "&" : "?"}av=${encodeURIComponent(ver)}`;
  }

  function renderFinalPreview(data) {
    if (!finalVideoEl || !finalVideoPlaceholderEl) return;
    const finalInfo = data.final || {};
    const deliverables = data.deliverables || {};
    const baseUrl =
      finalInfo.url ||
      (deliverables.final && deliverables.final.url) ||
      (deliverables.final_mp4 && deliverables.final_mp4.url) ||
      data.final_url ||
      `/v1/tasks/${encodeURIComponent(taskId)}/final`;
    const nextSrc = withAssetVersion(baseUrl, finalInfo.asset_version);
    const ready = Boolean(data.composed_ready);
    if (ready && nextSrc) {
      if (finalVideoSrc !== nextSrc) {
        finalVideoEl.src = nextSrc;
        finalVideoEl.load();
        finalVideoSrc = nextSrc;
      }
      finalVideoEl.classList.remove("hidden");
      finalVideoPlaceholderEl.classList.add("hidden");
      return;
    }
    if (finalVideoSrc) {
      finalVideoEl.removeAttribute("src");
      finalVideoEl.load();
      finalVideoSrc = "";
    }
    finalVideoEl.classList.add("hidden");
    finalVideoPlaceholderEl.classList.remove("hidden");
  }

  function renderHintPanel(data, deliverables) {
    const hasFinal = Boolean(deliverables.final_mp4);
    const hasPack = Boolean(deliverables.pack_zip || deliverables.edit_bundle_zip);
    const hasSubs = Boolean(deliverables.origin_srt || deliverables.mm_srt || deliverables.mm_txt);
    const hasAudio = Boolean(deliverables.mm_audio || deliverables.bgm_audio);
    const hasBgm = Boolean(deliverables.bgm_audio);
    if (hintSummaryEl) {
      hintSummaryEl.textContent =
        `本次交付包含：Final ${hasFinal ? "✅" : "❌"} / Pack ${hasPack ? "✅" : "❌"} / Subtitles ${hasSubs ? "✅" : "❌"} / Audio ${hasAudio ? "✅" : "❌"} / BGM ${hasBgm ? "✅" : "❌"}`;
    }
    if (hintNextEl) {
      hintNextEl.textContent = hasFinal
        ? "下一步：可直接发布成片或下载 pack 继续精修。"
        : "下一步：先回 Workbench 执行 Compose Final。";
    }
    if (hintStatusEl) {
      const ready = Boolean(data.composed_ready);
      const scenePending = data.scene_pack_pending_reason ? "（Scene Pack Optional: pending，不阻塞发布）" : "";
      hintStatusEl.textContent = ready
        ? "当前状态：✅ 可发布"
        : `当前状态：⚠️ ${reasonText(data.composed_reason)}${scenePending}`;
    }
  }

  function renderDeliverables(data) {
    const deliverables = data.deliverables || {};
    const keys = Object.keys(deliverables);
    const composedReady = Boolean(data.composed_ready);
    const composedReason = data.composed_reason || "final_missing";

    if (composedBadgeEl) {
      composedBadgeEl.textContent = composedReady ? "✅ Composed: Ready" : "⚠️ Not Ready";
      composedBadgeEl.classList.toggle("text-green-700", composedReady);
      composedBadgeEl.classList.toggle("text-amber-700", !composedReady);
    }
    if (composedReasonEl) composedReasonEl.textContent = reasonText(composedReason);
    const scenePack = data.scene_pack || {};
    const scenePackStatus = (scenePack.status || (data.scene_pack_pending_reason ? "pending" : "ready"));
    if (scenePackStatusEl) scenePackStatusEl.textContent = scenePackStatus;
    if (scenePackReasonEl) scenePackReasonEl.textContent = data.scene_pack_pending_reason || scenePack.error_reason || "";
    if (scenePackActionEl) {
      if (data.scene_pack_pending_reason && data.scene_pack_action_url) {
        scenePackActionEl.href = data.scene_pack_action_url;
        scenePackActionEl.classList.remove("hidden");
      } else if (scenePack.url) {
        scenePackActionEl.href = scenePack.url;
        scenePackActionEl.textContent = "Download Scene Pack";
        scenePackActionEl.classList.remove("hidden");
      } else {
        scenePackActionEl.textContent = "Open Workbench";
        scenePackActionEl.classList.add("hidden");
      }
    }
    if (scenePackGenerateEl) {
      scenePackGenerateEl.disabled = scenePackStatus === "running";
      scenePackGenerateEl.textContent = scenePackStatus === "running" ? "Generating..." : "Generate Scene Pack";
    }

    renderHintPanel(data, deliverables);
    renderFinalPreview(data);
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
          <div class="deliverable-group">
            <div class="deliverable-group-title">${g.label}</div>
            <div class="deliverable-list">
              ${g.rows
                .map(
                  (item) => `
                    <div class="deliverable-item">
                      <span class="deliverable-name" title="${item.label || item.key || "-"}">${item.label || item.key || "-"}</span>
                      <a class="btn-secondary text-xs deliverable-btn" href="${item.url}" target="_blank" rel="noopener">Download</a>
                    </div>
                  `
                )
                .join("")}
            </div>
          </div>
        `;
      })
      .join("");
  }

  async function loadPublishHub() {
    try {
      const res = await fetch(`/api/hot_follow/tasks/${encodeURIComponent(taskId)}/publish_hub`);
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

  async function generateScenePack() {
    if (!scenePackGenerateEl) return;
    scenePackGenerateEl.disabled = true;
    const prev = scenePackGenerateEl.textContent;
    scenePackGenerateEl.textContent = "Generating...";
    try {
      const res = await fetch(`/api/hot_follow/tasks/${encodeURIComponent(taskId)}/scene_pack`, { method: "POST" });
      if (res.status === 409) {
        const payload = await res.json().catch(() => ({}));
        if (payload && payload.error === "scene_pack_in_progress") {
          if (scenePackReasonEl) scenePackReasonEl.textContent = "Scene Pack generation in progress";
          await loadPublishHub();
          return;
        }
      }
      if (!res.ok) {
        const text = await res.text();
        if (scenePackReasonEl) scenePackReasonEl.textContent = text || "scene pack failed";
        return;
      }
      if (scenePackReasonEl) scenePackReasonEl.textContent = "Scene Pack generation started";
      await loadPublishHub();
    } catch (e) {
      if (scenePackReasonEl) scenePackReasonEl.textContent = e.message || "scene pack failed";
    } finally {
      scenePackGenerateEl.disabled = false;
      scenePackGenerateEl.textContent = prev || "Generate Scene Pack";
    }
  }

  async function backfillPublish() {
    if (!publishBtn) return;
    publishBtn.disabled = true;
    if (publishMsg) publishMsg.textContent = "...";
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
        publishMsg.textContent = "OK";
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
  if (scenePackGenerateEl) {
    scenePackGenerateEl.addEventListener("click", (e) => {
      e.preventDefault();
      generateScenePack();
    });
  }

  loadPublishHub();
})();
