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

  if (!taskId) return;

  async function loadDeliverables() {
    try {
      const res = await fetch(`/api/hot_follow/tasks/${encodeURIComponent(taskId)}/publish_hub`);
      if (!res.ok) {
        if (emptyEl) emptyEl.style.display = "block";
        return;
      }
      const data = await res.json();
      const deliverables = data.deliverables || {};
      const keys = Object.keys(deliverables);
      const composedReady = Boolean(data.composed_ready);
      const composedReason = data.composed_reason || "final.missing";
      if (composedBadgeEl) {
        composedBadgeEl.textContent = composedReady ? "✅ Composed: Ready" : "⚠️ Not Ready";
        composedBadgeEl.classList.toggle("text-green-700", composedReady);
        composedBadgeEl.classList.toggle("text-amber-700", !composedReady);
      }
      if (composedReasonEl) composedReasonEl.textContent = composedReason;
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
      if (!keys.length) {
        if (emptyEl) emptyEl.style.display = "block";
        return;
      }
      if (emptyEl) emptyEl.style.display = "none";
      if (listEl) {
        listEl.innerHTML = keys.map((k) => {
          const item = deliverables[k];
          return `<div class="deliverable"><span>${item.label || k}</span><a class="btn-secondary" href="${item.url}" target="_blank" rel="noopener">Download</a></div>`;
        }).join("");
      }
    } catch (e) {
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
      } else {
        if (publishMsg) publishMsg.textContent = "OK";
      }
    } catch (e) {
      if (publishMsg) publishMsg.textContent = e.message || "publish error";
    } finally {
      publishBtn.disabled = false;
    }
  }

  if (publishBtn) publishBtn.addEventListener("click", (e) => {
    e.preventDefault();
    backfillPublish();
  });

  loadDeliverables();
})();
