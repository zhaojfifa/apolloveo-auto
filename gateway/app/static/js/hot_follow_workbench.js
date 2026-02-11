(function () {
  const root = document.querySelector(".page");
  const taskId = root ? root.getAttribute("data-task-id") : null;
  const stepsEl = document.getElementById("hf-steps");
  const eventsEl = document.getElementById("hf-events");
  const statusEl = document.getElementById("hf-status");

  if (!taskId) return;

  function setBadge(step, text) {
    const el = stepsEl ? stepsEl.querySelector(`[data-step="${step}"]`) : null;
    if (!el) return;
    el.textContent = text || "-";
  }

  async function fetchTask() {
    try {
      const res = await fetch(`/api/tasks/${encodeURIComponent(taskId)}`);
      if (!res.ok) return;
      const task = await res.json();
      setBadge("parse", task.last_step === "parse" ? "running" : (task.raw_path ? "ready" : task.status));
      setBadge("subtitles", task.subtitles_status || "-");
      setBadge("dub", task.dub_status || "-");
      setBadge("pack", task.pack_status || (task.pack_path ? "ready" : "-"));
      setBadge("scenes", task.scenes_status || (task.scenes_path ? "ready" : "-"));
      if (statusEl) statusEl.textContent = task.status || "";
    } catch (e) {
      if (statusEl) statusEl.textContent = e.message || "";
    }
  }

  async function fetchEvents() {
    try {
      const res = await fetch(`/api/tasks/${encodeURIComponent(taskId)}/events`);
      if (!res.ok) return;
      const data = await res.json();
      const events = data.events || [];
      if (eventsEl) {
        eventsEl.innerHTML = events.map((e) => `<div>${JSON.stringify(e)}</div>`).join("");
      }
    } catch (e) {
      if (eventsEl) eventsEl.textContent = e.message || "";
    }
  }

  async function runAction(kind) {
    const url = `/api/tasks/${encodeURIComponent(taskId)}/${kind}`;
    const opts = { method: "POST" };
    if (kind === "dub") {
      opts.headers = { "Content-Type": "application/json" };
      opts.body = "{}";
    }
    await fetch(url, opts);
    await fetchTask();
  }

  document.querySelectorAll("[data-action]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const action = btn.getAttribute("data-action");
      if (action) runAction(action);
    });
  });

  fetchTask();
  fetchEvents();
  setInterval(fetchTask, 5000);
  setInterval(fetchEvents, 8000);
})();
