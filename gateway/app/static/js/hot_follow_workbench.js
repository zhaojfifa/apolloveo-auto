(function () {
  const root = document.querySelector('.page');
  const taskId = root ? root.getAttribute('data-task-id') : null;
  if (!taskId) return;

  const hubUrl = `/api/hot_follow/tasks/${encodeURIComponent(taskId)}/workbench_hub`;
  const statusEl = document.getElementById('hf-status');
  const eventsEl = document.getElementById('hf-events');
  const audioMsgEl = document.getElementById('hf-audio-msg');
  const ttsEngineEl = document.getElementById('hf_tts_engine');
  const ttsVoiceEl = document.getElementById('hf_tts_voice');
  const ttsPreviewBtn = document.getElementById('hf_tts_preview_btn');
  const bgmFileEl = document.getElementById('hf_bgm_file');
  const bgmMixEl = document.getElementById('hf_bgm_mix');
  const rerunAudioBtn = document.getElementById('hf_rerun_audio_btn');
  const scenePackDownloadEl = document.getElementById('hf_scene_pack_download');
  const scenePackHintEl = document.getElementById('hf-scene-pack-hint');
  const deliverablesGridEl = document.getElementById('hf_deliverables_grid');
  const subtitlesTextEl = document.getElementById('hf_subtitles_text');
  const subtitlesSaveBtn = document.getElementById('hf_subtitles_save_btn');
  const subtitlesMsgEl = document.getElementById('hf_subtitles_msg');
  const sourceVideoEl = document.getElementById('hf_source_video');
  const sourcePosterEl = document.getElementById('hf_source_poster');
  const sourceLinkEl = document.getElementById('hf_source_video_link');

  let currentHub = null;
  console.log('[HF] workbench boot', { taskId, hubUrl });

  function escapeHtml(s) {
    return String(s || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function getPipelineItem(key) {
    const list = (currentHub && currentHub.pipeline) || [];
    return list.find((x) => x && x.key === key) || { state: 'pending', message: '' };
  }

  function setStep(step, state, summary) {
    const stateEl = document.querySelector(`[data-hf-step-status="${step}"]`);
    const summaryEl = document.querySelector(`[data-hf-step-summary="${step}"]`);
    if (stateEl) stateEl.textContent = state || 'pending';
    if (summaryEl) summaryEl.textContent = summary || '';
  }

  function renderPipeline() {
    const parse = getPipelineItem('parse');
    const subtitles = getPipelineItem('subtitles');
    const audio = getPipelineItem('audio');
    const pack = getPipelineItem('pack');
    setStep('parse', parse.state, parse.message);
    setStep('subtitles', subtitles.state, subtitles.message);
    setStep('audio', audio.state, audio.message);
    setStep('synthesis', pack.state, pack.message);
    if (statusEl) statusEl.textContent = pack.state || '';
  }

  function renderSourceVideo() {
    if (!sourceVideoEl) return;
    const source = (currentHub && currentHub.source_video) || {};
    const url = source.url;
    if (url) {
      sourceVideoEl.src = url;
      sourceVideoEl.classList.remove('hidden');
      if (sourcePosterEl) sourcePosterEl.classList.add('hidden');
      if (sourceLinkEl) {
        sourceLinkEl.href = url;
        sourceLinkEl.classList.remove('opacity-50', 'pointer-events-none');
      }
    } else {
      sourceVideoEl.removeAttribute('src');
      sourceVideoEl.classList.add('hidden');
      if (sourcePosterEl) sourcePosterEl.classList.remove('hidden');
      if (sourceLinkEl) {
        sourceLinkEl.href = '#';
        sourceLinkEl.classList.add('opacity-50', 'pointer-events-none');
      }
    }
  }

  function renderSubtitles() {
    const subtitles = (currentHub && currentHub.subtitles) || {};
    if (subtitlesTextEl) subtitlesTextEl.value = subtitles.srt_text || '';
  }

  function renderAudio() {
    const audio = (currentHub && currentHub.audio) || {};
    if (ttsEngineEl && audio.tts_engine) ttsEngineEl.value = audio.tts_engine;
    if (ttsVoiceEl && audio.tts_voice) ttsVoiceEl.value = audio.tts_voice;
    if (bgmMixEl && audio.bgm_mix != null) bgmMixEl.value = String(audio.bgm_mix);
    const err = currentHub && currentHub.errors && currentHub.errors.audio;
    if (audioMsgEl) audioMsgEl.textContent = (err && err.message) ? `Audio error: ${err.message}` : '';
  }

  function renderScenePack() {
    const scene = (currentHub && currentHub.scene_pack) || {};
    const status = scene.status || 'pending';
    const url = scene.download_url || scene.scenes_url;
    const stateEl = document.querySelector('[data-hf-step-status="scenes"]');
    if (stateEl) stateEl.textContent = status;
    if (scenePackDownloadEl) {
      if (url) {
        scenePackDownloadEl.href = url;
        scenePackDownloadEl.classList.remove('opacity-50', 'pointer-events-none');
        if (scenePackHintEl) scenePackHintEl.textContent = 'Scene pack ready';
      } else {
        scenePackDownloadEl.href = '#';
        scenePackDownloadEl.classList.add('opacity-50', 'pointer-events-none');
        if (scenePackHintEl) scenePackHintEl.textContent = status === 'failed' ? 'Scene pack failed' : 'Optional and not generated yet';
      }
    }
  }

  function renderDeliverables() {
    if (!deliverablesGridEl) return;
    const list = (currentHub && currentHub.deliverables) || [];
    if (!list.length) {
      deliverablesGridEl.innerHTML = '<div class="rounded-lg border border-gray-200 p-3 text-sm text-gray-500">No deliverables yet</div>';
      return;
    }
    deliverablesGridEl.innerHTML = list.map((d) => {
      const title = escapeHtml(d.title || d.kind || '-');
      const key = escapeHtml(d.key || '-');
      const state = escapeHtml(d.state || d.status || 'pending');
      const hasUrl = Boolean(d.url);
      const href = hasUrl ? d.url : '#';
      const btnClass = hasUrl ? 'btn-secondary' : 'btn-secondary opacity-50 pointer-events-none';
      return `
        <div class="rounded-lg border border-gray-200 p-3">
          <div class="flex items-center justify-between gap-3">
            <div class="text-sm font-semibold">${title}</div>
            <div class="text-xs rounded-full bg-gray-100 px-2 py-1">${state}</div>
          </div>
          <div class="text-xs text-gray-500 mt-1 truncate">${key}</div>
          <a class="${btnClass} mt-2 inline-block text-xs" href="${href}" target="_blank" rel="noopener">${hasUrl ? 'Download' : 'Pending'}</a>
        </div>
      `;
    }).join('');
  }

  function renderEvents() {
    if (!eventsEl) return;
    const events = (currentHub && currentHub.events) || [];
    eventsEl.innerHTML = events.map((e) => `<div>${escapeHtml(JSON.stringify(e))}</div>`).join('');
  }

  function renderHub(data) {
    currentHub = data || {};
    renderPipeline();
    renderSourceVideo();
    renderSubtitles();
    renderAudio();
    renderScenePack();
    renderDeliverables();
    renderEvents();
  }

  async function loadHub() {
    const res = await fetch(hubUrl);
    if (!res.ok) throw new Error(await res.text() || 'hub load failed');
    const data = await res.json();
    renderHub(data);
  }

  async function patchAudioConfig(payload) {
    const res = await fetch(`/api/hot_follow/tasks/${encodeURIComponent(taskId)}/audio_config`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload || {}),
    });
    if (!res.ok) throw new Error(await res.text() || 'save audio config failed');
    return res.json();
  }

  async function patchSubtitles(srtText) {
    const res = await fetch(`/api/hot_follow/tasks/${encodeURIComponent(taskId)}/subtitles`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ srt_text: srtText || '' }),
    });
    if (!res.ok) throw new Error(await res.text() || 'save subtitles failed');
    return res.json();
  }

  async function uploadBgm(file) {
    const fd = new FormData();
    fd.append('file', file);
    fd.append('mix_ratio', bgmMixEl ? (bgmMixEl.value || '0.3') : '0.3');
    const res = await fetch(`/api/hot_follow/tasks/${encodeURIComponent(taskId)}/bgm`, {
      method: 'POST',
      body: fd,
    });
    if (!res.ok) throw new Error(await res.text() || 'upload bgm failed');
    return res.json();
  }

  async function rerunAudio() {
    const provider = ttsEngineEl ? ttsEngineEl.value : null;
    const voiceId = ttsVoiceEl ? ttsVoiceEl.value : null;
    const payload = {
      provider: provider === 'edge_tts' ? 'edge-tts' : provider,
      voice_id: voiceId || null,
    };
    const res = await fetch(`/api/tasks/${encodeURIComponent(taskId)}/dub`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(await res.text() || 'rerun audio failed');
    return res.json();
  }

  async function runAction(kind) {
    const step = kind === 'synthesis' ? 'pack' : kind;
    const opts = { method: 'POST' };
    if (step === 'subtitles') {
      opts.headers = { 'Content-Type': 'application/json' };
      opts.body = JSON.stringify({});
    }
    const res = await fetch(`/api/tasks/${encodeURIComponent(taskId)}/${step}`, opts);
    if (!res.ok) throw new Error(await res.text() || `${step} failed`);
    await loadHub();
  }

  if (ttsEngineEl) {
    ttsEngineEl.addEventListener('change', async () => {
      try { await patchAudioConfig({ tts_engine: ttsEngineEl.value }); await loadHub(); }
      catch (e) { if (audioMsgEl) audioMsgEl.textContent = e.message || 'save failed'; }
    });
  }
  if (ttsVoiceEl) {
    ttsVoiceEl.addEventListener('change', async () => {
      try { await patchAudioConfig({ tts_voice: ttsVoiceEl.value }); await loadHub(); }
      catch (e) { if (audioMsgEl) audioMsgEl.textContent = e.message || 'save failed'; }
    });
  }
  if (bgmMixEl) {
    bgmMixEl.addEventListener('change', async () => {
      try { await patchAudioConfig({ bgm_mix: Number(bgmMixEl.value || '0.3') }); await loadHub(); }
      catch (e) { if (audioMsgEl) audioMsgEl.textContent = e.message || 'save failed'; }
    });
  }
  if (bgmFileEl) {
    bgmFileEl.addEventListener('change', async () => {
      const file = bgmFileEl.files && bgmFileEl.files[0];
      if (!file) return;
      try {
        if (audioMsgEl) audioMsgEl.textContent = 'Uploading BGM...';
        await uploadBgm(file);
        await loadHub();
        if (audioMsgEl) audioMsgEl.textContent = 'BGM uploaded';
      } catch (e) {
        if (audioMsgEl) audioMsgEl.textContent = e.message || 'upload failed';
      }
    });
  }
  if (rerunAudioBtn) {
    rerunAudioBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      try {
        if (audioMsgEl) audioMsgEl.textContent = 'Rerunning audio...';
        await patchAudioConfig({
          tts_engine: ttsEngineEl ? ttsEngineEl.value : null,
          tts_voice: ttsVoiceEl ? ttsVoiceEl.value : null,
          bgm_mix: bgmMixEl ? Number(bgmMixEl.value || '0.3') : null,
        });
        await rerunAudio();
        await loadHub();
        if (audioMsgEl) audioMsgEl.textContent = 'Audio rerun requested';
      } catch (err) {
        if (audioMsgEl) audioMsgEl.textContent = err.message || 'rerun failed';
      }
    });
  }
  if (ttsPreviewBtn) {
    ttsPreviewBtn.addEventListener('click', (e) => {
      e.preventDefault();
      if (audioMsgEl) audioMsgEl.textContent = 'Preview is reserved in this version. Use Re-Run Audio.';
    });
  }
  if (subtitlesSaveBtn) {
    subtitlesSaveBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      try {
        if (subtitlesMsgEl) subtitlesMsgEl.textContent = 'Saving...';
        await patchSubtitles(subtitlesTextEl ? subtitlesTextEl.value : '');
        await loadHub();
        if (subtitlesMsgEl) subtitlesMsgEl.textContent = 'Saved';
      } catch (err) {
        if (subtitlesMsgEl) subtitlesMsgEl.textContent = err.message || 'save failed';
      }
    });
  }

  document.querySelectorAll('[data-action]').forEach((btn) => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      const action = btn.getAttribute('data-action');
      if (!action) return;
      try { await runAction(action); }
      catch (err) { if (statusEl) statusEl.textContent = err.message || 'action failed'; }
    });
  });

  loadHub().catch((e) => { if (statusEl) statusEl.textContent = e.message || 'hub load failed'; });
  setInterval(() => { loadHub().catch(() => {}); }, 5000);
})();
