(function () {
  function pickFinalVideoUrl(task) {
    var media = (task && task.media) || {};
    var url = (
      media.final_video_url ||
      media.final_url ||
      (task && task.final_video_url) ||
      (task && task.final_url) ||
      null
    );
    if (!url) {
      var id = (task && task.task_id) ||
        (task && task.task && task.task.task_id) ||
        (task && task.id) ||
        (task && task.task && task.task.id) ||
        null;
      if (id) url = window.location.origin + "/v1/tasks/" + encodeURIComponent(id) + "/final";
    }
    return url;
  }

  window.__HF_PICK_FINAL_URL__ = pickFinalVideoUrl;
})();
