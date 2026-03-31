/**
 * task_semantics_v19.js
 * Frontend-only semantics derivation for /tasks board (PR-UI-1).
 * Contract: relies only on existing /api/tasks list payload fields.
 */

(function () {
  function lower(x) { return String(x || "").toLowerCase(); }

  function sceneKeyFromTask(t) {
    const kind = lower(t.kind || t.category || t.task_kind || t.platform || "");
    if (kind.includes("apollo_avatar") || kind.includes("apollo-avatar") || kind.includes("avatar")) return "avatar";
    if (kind.includes("hot") || kind.includes("follow")) return "hot";
    return "baseline";
  }

  function dbStatusFromTask(t) {
    const s = lower(t.status || t.db_status || t.state || "");
    if (!s) return "unknown";
    if (["done", "ready", "success"].includes(s)) return "ready";
    if (["running", "processing", "in_progress"].includes(s)) return "processing";
    if (["queued", "pending"].includes(s)) return "queued";
    if (["failed", "error"].includes(s)) return "failed";
    return s;
  }

  function packExistsFromTask(t) {
    return !!(
      t.pack_key || t.pack_path || t.deliver_pack_key || t.deliverables_pack_key ||
      t.pack_url || t.pack_download_url || (t.deliverables && (t.deliverables.pack || t.deliverables.pack_zip))
    );
  }

  function videoExistsFromTask(t) {
    return !!(
      t.raw_url || t.video_url || t.preview_url || t.raw_path || t.raw_key ||
      (t.deliverables && (t.deliverables.raw || t.deliverables.video))
    );
  }

  function downloadUrlForPack(t) {
    const id = t.task_id || t.id || "";
    return t.pack_download_url || t.pack_url || (id ? `/v1/tasks/${encodeURIComponent(id)}/pack` : null);
  }

  function detailUrl(t) {
    const id = t.task_id || t.id || "";
    return id ? `/tasks/${encodeURIComponent(id)}` : null;
  }

  function createdLabel(t) {
    return t.created_ago || t.created_at || t.created || "";
  }

  function titleText(t) {
    return t.title || t.name || t.summary || "";
  }

  function subtitleText(t) {
    const platform = t.platform || t.source_platform || "";
    const id = t.task_id || t.id || "";
    const account = t.account || t.author || t.owner || "";
    const parts = [];
    if (platform) parts.push(platform);
    if (id) parts.push(`ID: ${id}`);
    if (account) parts.push(`@${account}`);
    return parts.join(" · ");
  }

  function derive(t) {
    const sceneKey = sceneKeyFromTask(t);
    const hotFollow = sceneKey === "hot" || sceneKey === "hot_follow";
    const dbStatus = dbStatusFromTask(t);
    const packExists = packExistsFromTask(t);
    const videoExists = videoExistsFromTask(t);

    let done = packExists || dbStatus === "ready";
    let processing = !done && (dbStatus === "processing" || dbStatus === "queued");
    let needsAttention = (dbStatus === "failed" && !packExists);
    let yellow = (dbStatus === "failed" && packExists);

    if (hotFollow) {
      done = dbStatus === "ready";
      processing = !done && (dbStatus === "processing" || dbStatus === "queued");
      needsAttention = dbStatus === "failed";
      yellow = false;
    }

    return {
      raw: t,
      id: t.task_id || t.id || "",
      sceneKey,
      dbStatus,
      packExists,
      videoExists,
      done,
      processing,
      needsAttention,
      yellow,
      packDownloadUrl: packExists ? downloadUrlForPack(t) : null,
      detailUrl: detailUrl(t),
      title: titleText(t),
      subtitle: subtitleText(t),
      createdLabel: createdLabel(t),
    };
  }

  window.TaskSemanticsV19 = { derive };
})();
