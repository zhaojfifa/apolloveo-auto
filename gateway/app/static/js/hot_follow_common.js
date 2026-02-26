(function () {
  function pickFinalVideoUrl(task) {
    var media = (task && task.media) || {};
    return (
      media.final_video_url ||
      media.final_url ||
      (task && task.final_video_url) ||
      (task && task.final_url) ||
      null
    );
  }

  window.__HF_PICK_FINAL_URL__ = pickFinalVideoUrl;
})();
