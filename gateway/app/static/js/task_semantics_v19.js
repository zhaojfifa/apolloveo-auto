/**
 * task_semantics_v19.js
 * Frontend-only semantics derivation for /tasks board (PR-UI-1).
 * Contract: relies only on existing /api/tasks list payload fields.
 */

(function () {
  function lower(x) { return String(x || "").toLowerCase(); }

  function sceneKeyFromTask(t) {
    const kind = lower(t.kind || t.category || t.task_kind || t.platform || "");
    // canonical scenes: avatar / hot / baseline
    if (kind.includes("apollo_avatar") || kind.includes("apollo-avatar") || kind.includes("avatar")) return "avatar";
    if (kind.includes("hot") || kind.includes("follow")) return "hot";
    return "baseline";
  }

  function dbStatusFromTask(t) {
    // prefer explicit fields if present
    const s = lower(t.status || t.db_status || t.state || "");
    if (!s) return "unknown";
    // normalize
    if (["done", "ready", "success"].includes(s)) return "ready";
    if (["running", "processing", "in_progress"].includes(s)) return "processing";
    if (["queued", "pending"].includes(s)) return "queued";
    if (["failed", "error"].includes(s)) return "failed";
    return s;
  }

  function packExistsFromTask(t) {
    // keep loose: accept any known key/path fields from legacy
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
    // prefer backend-generated url if exists; else fallback to /v1/tasks/{id}/pack
    const id = t.task_id || t.id || "";
    return t.pack_download_url || t.pack_url || (id ? `/v1/tasks/${encodeURIComponent(id)}/pack` : null);
  }

  function detailUrl(t) {
    const id = t.task_id || t.id || "";
    return id ? `/tasks/${encodeURIComponent(id)}` : null;
  }

  function createdLabel(t) {
    // use created_ago if server provides; else fall back to created_at
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
    return parts.join(" ¡¤ ");
  }

  function derive(t) {
    const sceneKey = sceneKeyFromTask(t);
    const dbStatus = dbStatusFromTask(t);
    const packExists = packExistsFromTask(t);
    const videoExists = videoExistsFromTask(t);

    const done = packExists || dbStatus === "ready";
    const processing = !done && (dbStatus === "processing" || dbStatus === "queued");
    const needsAttention = (dbStatus === "failed" && !packExists);

    // Yellow card strategy (must):
    const yellow = (dbStatus === "failed" && packExists);

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