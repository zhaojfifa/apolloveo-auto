(function () {
  const root = document.querySelector(".page");
  const taskId = root ? root.getAttribute("data-task-id") : null;
  const listEl = document.getElementById("hf-deliverables");
  const emptyEl = document.getElementById("hf-deliverables-empty");
  const hubMsg = document.getElementById("hf-publish-hub-msg");
  const publishBtn = document.getElementById("hf-publish");
  const publishUrl = document.getElementById("hf-publish-url");
  const publishNotes = document.getElementById("hf-publish-notes");
  const publishMsg = document.getElementById("hf-publish-msg");

  if (!taskId) return;

  async function apiGet(path) {
    const res = await fetch(path, { method: "GET" });
    if (res.status === 401) return { __unauthorized: true };
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  }

  async function loadDeliverables() {
    try {
      const data = await apiGet(`/api/tasks/${encodeURIComponent(taskId)}/publish_hub`);
      if (data && data.__unauthorized) {
        if (hubMsg) hubMsg.textContent = "Unauthorized: please login and refresh.";
        if (emptyEl) emptyEl.style.display = "block";
        return;
      }
      const deliverables = data.deliverables || {};
      const keys = Object.keys(deliverables);
      if (!keys.length) {
        if (emptyEl) emptyEl.style.display = "block";
        return;
      }
      if (emptyEl) emptyEl.style.display = "none";
      if (hubMsg) hubMsg.textContent = "";
      if (listEl) {
        listEl.innerHTML = keys.map((k) => {
          const item = deliverables[k];
          return `<div class="deliverable"><span>${item.label || k}</span><a class="btn-secondary" href="${item.url}" target="_blank" rel="noopener">Download</a></div>`;
        }).join("");
      }
    } catch (e) {
      if (hubMsg) hubMsg.textContent = e.message || "";
      if (emptyEl) emptyEl.style.display = "block";
    }
  }

  async function backfillPublish() {
    if (!publishBtn) return;
    publishBtn.disabled = true;
    if (publishMsg) publishMsg.textContent = "...";
    try {
      const res = await fetch(`/api/tasks/${encodeURIComponent(taskId)}/publish`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          published: true,
          published_url: publishUrl ? publishUrl.value : "",
          notes: publishNotes ? publishNotes.value : "",
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
