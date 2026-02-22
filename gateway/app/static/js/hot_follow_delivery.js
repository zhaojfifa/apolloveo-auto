(function () {
  const root = document.querySelector(".page");
  function readLocale() {
    const i18n = window.__V185_I18N__ || {};
    if (typeof i18n.readLocale === "function") return i18n.readLocale();
    const qs = new URLSearchParams(window.location.search || "");
    return (qs.get("ui_locale") || "zh").toLowerCase();
  }
  function applyLocale(locale) {
    const i18n = window.__V185_I18N__ || {};
    if (typeof i18n.applyLocale === "function") i18n.applyLocale(locale);
  }
  function t(key, fallback) {
    const i18n = window.__V185_I18N__ || {};
    if (typeof i18n.t === "function") {
      const text = i18n.t(key);
      if (typeof text === "string" && !text.startsWith("【MISSING:")) return text;
    }
    return fallback;
  }
  applyLocale(readLocale());
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
  const translationQaStatusEl = document.getElementById("hf-translation-qa-status");

  if (!taskId) return;

  function reasonText(reason) {
    const mapping = {
      ready: t("hot_follow_compose_reason_ready", "可发布"),
      final_missing: t("hot_follow_compose_reason_final_missing", "尚未生成最终成片"),
      compose_in_progress: t("hot_follow_compose_reason_in_progress", "合成中…"),
      compose_failed: t("hot_follow_compose_reason_failed", "合成失败，可重试"),
      missing_voiceover: t("hot_follow_compose_reason_missing_voice", "缺少配音"),
      missing_raw: t("hot_follow_compose_reason_missing_raw", "缺少源视频"),
    };
    return mapping[reason] || reason || "-";
  }

  function groupDeliverables(deliverables) {
    const groups = [
      { label: t("hot_follow_delivery_group_final", "成片"), keys: ["final_mp4"] },
      { label: t("hot_follow_delivery_group_pack", "剪辑包"), keys: ["pack_zip", "edit_bundle_zip"] },
      { label: t("hot_follow_delivery_group_subtitles", "字幕与脚本"), keys: ["origin_srt", "mm_srt", "mm_txt"] },
      { label: t("hot_follow_delivery_group_audio", "音频素材"), keys: ["mm_audio", "bgm_audio"] },
      { label: "Scene Pack", keys: ["scenes_zip"] },
    ];
    return groups.map((g) => ({
      label: g.label,
      rows: g.keys.filter((k) => deliverables[k]).map((k) => ({ key: k, ...deliverables[k] })),
    }));
  }

  function renderHintPanel(data, deliverables) {
    const hasFinal = Boolean(deliverables.final_mp4);
    const hasPack = Boolean(deliverables.pack_zip || deliverables.edit_bundle_zip);
    const hasSubs = Boolean(deliverables.origin_srt || deliverables.mm_srt || deliverables.mm_txt);
    const hasAudio = Boolean(deliverables.mm_audio || deliverables.bgm_audio);
    const hasBgm = Boolean(deliverables.bgm_audio);
    if (hintSummaryEl) {
      hintSummaryEl.textContent =
        `${t("hot_follow_delivery_summary_prefix", "本次交付包含：")}Final ${hasFinal ? "✅" : "❌"} / Pack ${hasPack ? "✅" : "❌"} / Subtitles ${hasSubs ? "✅" : "❌"} / Audio ${hasAudio ? "✅" : "❌"} / BGM ${hasBgm ? "✅" : "❌"}`;
    }
    if (hintNextEl) {
      hintNextEl.textContent = hasFinal
        ? t("hot_follow_delivery_next_ready", "下一步：可直接发布成片或下载 pack 继续精修。")
        : t("hot_follow_delivery_next_compose", "下一步：先回 Workbench 执行 Compose Final。");
    }
    if (hintStatusEl) {
      const ready = Boolean(data.composed_ready);
      const scenePending = data.scene_pack_pending_reason ? t("hot_follow_delivery_scene_pending_suffix", "（Scene Pack pending，不阻塞发布）") : "";
      hintStatusEl.textContent = ready
        ? t("hot_follow_delivery_status_ready", "当前状态：✅ 可发布")
        : `${t("hot_follow_delivery_status_prefix", "当前状态：⚠️")} ${reasonText(data.composed_reason)}${scenePending}`;
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
    if (translationQaStatusEl) {
      const qaStatus = String(data.translation_qa_status || "PASS").toUpperCase();
      translationQaStatusEl.textContent = qaStatus === "WARN"
        ? t("hot_follow_translation_qa_warn", "Translation QA: WARN")
        : t("hot_follow_translation_qa_pass", "Translation QA: PASS");
    }
    if (scenePackStatusEl) scenePackStatusEl.textContent = data.scene_pack_pending_reason ? "pending" : "ready";
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
              ${g.rows
                .map(
                  (item) =>
                    `<div class="deliverable"><span>${item.label || item.key}</span><a class="btn-secondary" href="${item.url}" target="_blank" rel="noopener">Download</a></div>`
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

  loadPublishHub();
})();
