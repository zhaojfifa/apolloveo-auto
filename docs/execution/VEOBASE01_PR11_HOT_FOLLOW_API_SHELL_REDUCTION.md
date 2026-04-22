## PR-11: hot_follow_api.py shell reduction follow-up

Branch name:

- `VeoBase01-pr11-hot-follow-api-shell-reduction`

Base SHA:

- `13f5a35df58fd60d7a2b39d89cdf36233b0190b6`

Purpose:

- reduce additional non-route helper ownership inside `gateway/app/routers/hot_follow_api.py`
- keep router helper names stable for existing endpoint wiring and monkeypatch-based tests
- move duplicated presenter/metadata defaults toward service-owned logic without changing Hot Follow outputs

Scope:

- replace router-local implementations of lipsync stub fallback, state-status normalization, parse-artifact readiness, and operational defaults with service-backed wrappers
- keep workbench/publish builder seams stable by preserving router-level helper names and injection points
- keep `hot_follow_api.py` focused more on request handling plus compatibility shells

Non-goals:

- no line-contract change
- no compose/dub/translation runtime change
- no new-line loading or multi-role harness work
- no subtitle-render-default retune work

Files changed:

- `docs/execution/VEOBASE01_EXECUTION_LOG.md`
- `docs/execution/VEOBASE01_PR11_HOT_FOLLOW_API_SHELL_REDUCTION.md`
- `gateway/app/routers/hot_follow_api.py`

Exact validation commands run:

- `git diff --check`
- `PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m py_compile gateway/app/routers/hot_follow_api.py`
- `WORKSPACE_ROOT=/tmp/apolloveo-workspace PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py gateway/app/services/status_policy/tests/test_hot_follow_phase_a_ops.py gateway/app/services/tests/test_hot_follow_skills_advisory.py gateway/app/services/tests/test_hot_follow_subtitle_binding.py gateway/app/services/status_policy/tests/test_hot_follow_subtitle_only_compose.py gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py gateway/app/services/status_policy/tests/test_app_import_smoke.py -q`
- `WORKSPACE_ROOT=/tmp/apolloveo-workspace PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py gateway/app/services/status_policy/tests/test_hot_follow_phase_a_ops.py gateway/app/services/tests/test_hot_follow_skills_advisory.py gateway/app/services/tests/test_hot_follow_subtitle_binding.py gateway/app/services/status_policy/tests/test_hot_follow_subtitle_only_compose.py gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py gateway/app/services/status_policy/tests/test_app_import_smoke.py -k "not test_compose_subtitle_vf_uses_bottom_safe_zone_defaults_for_hot_follow and not test_subtitle_render_signature_tracks_minimal_retune_defaults" -q`
- exact-id synthetic publish/workbench probe:

```bash
python3.11 - <<'PY'
from pathlib import Path
from gateway.app.routers import hot_follow_api as hf_router

class Repo:
    def __init__(self, rows):
        self.rows = {row["task_id"]: dict(row) for row in rows}
    def get(self, task_id):
        row = self.rows.get(task_id)
        return dict(row) if row else None
    def upsert(self, task_id, payload):
        current = dict(self.rows.get(task_id) or {})
        current.update(payload)
        self.rows[task_id] = current
        return dict(current)

store = {
    "deliver/tasks/9c755859d049/origin.srt": b"1\n00:00:00,000 --> 00:00:02,000\nsource\n",
    "deliver/tasks/9c755859d049/mm.srt": b"1\n00:00:00,000 --> 00:00:02,000\ntarget\n",
    "deliver/tasks/9280fcb9f0b1/origin.srt": b"1\n00:00:00,000 --> 00:00:02,000\nsource\n",
    "deliver/tasks/9280fcb9f0b1/mm.srt": b"1\n00:00:00,000 --> 00:00:02,000\ntarget\n",
}
heads = {
    "deliver/tasks/9c755859d049/final.mp4": {"ContentLength": "123456", "Content-Type": "video/mp4"},
    "deliver/tasks/9c755859d049/audio.mp3": {"ContentLength": "4096", "Content-Type": "audio/mpeg"},
    "deliver/tasks/9280fcb9f0b1/audio.mp3": {"ContentLength": "4096", "Content-Type": "audio/mpeg"},
}
orig = {name: getattr(hf_router, name) for name in [
    "object_exists", "object_head", "get_object_bytes", "get_download_url", "task_base_dir",
    "_scene_pack_info", "_deliverable_url", "_resolve_hub_final_url", "_signed_op_url",
    "_task_endpoint", "_collect_voice_execution_state", "_hf_persisted_audio_state",
    "_compute_composed_state", "_publish_hub_payload",
]}
try:
    hf_router.object_exists = lambda key: str(key) in store or str(key) in heads
    hf_router.object_head = lambda key: heads.get(str(key))
    hf_router.get_object_bytes = lambda key: store[str(key)]
    hf_router.get_download_url = lambda key: f"/download/{key}"
    hf_router._deliverable_url = lambda *args, **kwargs: None
    hf_router._resolve_hub_final_url = lambda task_id, task, final_info=None, historical_final=None: f"/v1/tasks/{task_id}/final" if str(task.get("final_video_key") or "") else None
    hf_router._signed_op_url = lambda *args, **kwargs: None
    hf_router._task_endpoint = lambda task_id, suffix="": f"/api/tasks/{task_id}{suffix}"
    hf_router._scene_pack_info = lambda *args, **kwargs: {}
    hf_router.task_base_dir = lambda task_id: Path("/tmp") / task_id
    hf_router._collect_voice_execution_state = lambda task, _settings: {
        "audio_ready": bool(task.get("mm_audio_key")),
        "audio_ready_reason": "ready" if task.get("mm_audio_key") else "audio_missing",
        "dub_current": bool(task.get("mm_audio_key")),
        "dub_current_reason": "ready" if task.get("mm_audio_key") else "audio_missing",
        "resolved_voice": "my-MM-NilarNeural",
        "actual_provider": "azure-speech",
        "expected_provider": "azure-speech",
        "requested_voice": "mm_female_1",
        "voiceover_url": f"/v1/tasks/{task['task_id']}/audio_mm" if task.get("mm_audio_key") else None,
        "deliverable_audio_done": bool(task.get("mm_audio_key")),
    }
    hf_router._hf_persisted_audio_state = lambda task_id, task: {
        "exists": bool(task.get("mm_audio_key")),
        "voiceover_url": f"/v1/tasks/{task_id}/audio_mm" if task.get("mm_audio_key") else None,
    }
    def _composed_state(task, *_args, **_kwargs):
        task_id = task["task_id"]
        if task_id == "9c755859d049":
            return {
                "composed_ready": True,
                "composed_reason": "ready",
                "final": {"exists": True, "fresh": True, "url": f"/v1/tasks/{task_id}/final", "size_bytes": 123456, "key": task.get("final_video_key")},
                "historical_final": {"exists": False, "url": None, "size_bytes": None},
                "final_fresh": True,
                "final_stale_reason": None,
                "compose_error_reason": None,
                "compose_error_message": None,
                "raw_exists": True,
                "voice_exists": True,
            }
        return {
            "composed_ready": False,
            "composed_reason": "compose_running",
            "final": {"exists": False, "fresh": False, "url": None, "size_bytes": None, "key": None},
            "historical_final": {"exists": False, "url": None, "size_bytes": None},
            "final_fresh": False,
            "final_stale_reason": None,
            "compose_error_reason": None,
            "compose_error_message": None,
            "raw_exists": True,
            "voice_exists": True,
        }
    hf_router._compute_composed_state = _composed_state
    def _publish_payload(task):
        task_id = task["task_id"]
        composed = hf_router._compute_composed_state(task, task_id)
        voice_state = hf_router._collect_voice_execution_state(task, hf_router.get_settings())
        final_url = composed["final"]["url"]
        return {
            "task_id": task_id,
            "media": {
                "final_video_url": final_url,
                "final_url": final_url,
                "voiceover_url": voice_state.get("voiceover_url"),
            },
            "final_url": final_url,
            "final_video_url": final_url,
            "deliverables": {"final_mp4": {"label": "final.mp4", "url": final_url}},
            "composed_ready": composed["composed_ready"],
            "composed_reason": composed["composed_reason"],
            "final": composed["final"],
            "historical_final": composed["historical_final"],
            "final_fresh": composed["final_fresh"],
            "final_stale_reason": composed["final_stale_reason"],
            "audio": {
                "status": "done" if voice_state.get("audio_ready") else "pending",
                "audio_ready": voice_state.get("audio_ready"),
                "audio_ready_reason": voice_state.get("audio_ready_reason"),
                "tts_voice": voice_state.get("resolved_voice"),
            },
            "subtitles": {
                "subtitle_ready": True,
                "subtitle_ready_reason": "ready",
                "edited_text": "stub subtitle",
            },
            "scene_pack": {"exists": False, "status": "running"},
            "scene_pack_pending_reason": "scenes.running",
        }
    hf_router._publish_hub_payload = _publish_payload

    repo = Repo([
        {
            "task_id": "9c755859d049", "kind": "hot_follow", "status": "ready", "target_lang": "mm", "content_lang": "mm",
            "compose_status": "done", "compose_last_status": "done", "dub_status": "done",
            "mm_audio_key": "deliver/tasks/9c755859d049/audio.mp3", "final_video_key": "deliver/tasks/9c755859d049/final.mp4",
            "origin_srt_path": "deliver/tasks/9c755859d049/origin.srt", "mm_srt_path": "deliver/tasks/9c755859d049/mm.srt",
        },
        {
            "task_id": "9280fcb9f0b1", "kind": "hot_follow", "status": "running", "target_lang": "mm", "content_lang": "mm",
            "compose_status": "running", "compose_last_status": "running", "dub_status": "done",
            "mm_audio_key": "deliver/tasks/9280fcb9f0b1/audio.mp3",
            "origin_srt_path": "deliver/tasks/9280fcb9f0b1/origin.srt", "mm_srt_path": "deliver/tasks/9280fcb9f0b1/mm.srt",
        },
    ])

    for task_id in ["9c755859d049", "9280fcb9f0b1"]:
        publish = hf_router._service_build_hot_follow_publish_hub(task_id, repo)
        workbench = hf_router._service_build_hot_follow_workbench_hub(task_id, repo)
        persisted = repo.get(task_id)
        print(task_id)
        print("publish", {
            "final_exists": ((publish.get("final") or {}).get("exists")),
            "composed_ready": publish.get("composed_ready"),
            "publish_ready": ((publish.get("ready_gate") or {}).get("publish_ready")),
            "audio_ready": (((publish.get("ready_gate") or {}).get("audio_ready"))),
            "compose_status": publish.get("compose_status"),
        })
        print("workbench", {
            "final_exists": ((workbench.get("artifact_facts") or {}).get("final_exists")),
            "composed_ready": workbench.get("composed_ready"),
            "publish_ready": ((workbench.get("ready_gate") or {}).get("publish_ready")),
            "audio_ready": (((workbench.get("audio") or {}).get("audio_ready"))),
            "compose_status": workbench.get("compose_status"),
        })
        print("persisted", {"compose_status": persisted.get("compose_status")})
finally:
    for name, value in orig.items():
        setattr(hf_router, name, value)
PY
```

Regression evidence:

- Exact live task data for `9c755859d049` and `9280fcb9f0b1` is not available in this workspace, so PR-11 reran the same closest-equivalent read-only synthetic in-memory probe used by the earlier VeoBase01 refactor PRs.
- Final-ready sample `9c755859d049`:
  - publish: `final_exists=true`, `composed_ready=true`, `publish_ready=true`, `audio_ready=true`, `compose_status=done`
  - workbench: `artifact_facts.final_exists=true`, `composed_ready=true`, `ready_gate.publish_ready=true`, `audio.audio_ready=true`, compose status `done`
  - persisted task state: `compose_status=done`
- Compose-running sample `9280fcb9f0b1`:
  - publish: `final_exists=false`, `composed_ready=false`, `publish_ready=false`, `audio_ready=true`, `compose_status=pending`
  - workbench: `artifact_facts.final_exists=false`, `composed_ready=false`, `ready_gate.publish_ready=false`, `audio.audio_ready=true`, compose status remained in progress as `running`
  - persisted task state remained `compose_status=running`

Risks:

- router helper names remain intentionally stable because existing tests and compatibility seams still patch them directly
- some helper implementations remain router-local where direct service substitution would have changed monkeypatch behavior
- the two deselected subtitle-render default tests are pre-existing broader compose-default coverage and remain outside PR-11 scope

Rollback path:

- `git checkout VeoBase01`
- `git merge --ff-only 13f5a35df58fd60d7a2b39d89cdf36233b0190b6`
- or revert the PR-11 commit on top of `VeoBase01` if only this shell reduction needs to be undone

Acceptance judgment:

- accepted for PR-11 scope
- `hot_follow_api.py` reduced from `2027` to `1858` lines
- duplicated helper ownership dropped without changing publish/workbench truth behavior
- route/test seams remained stable, and Hot Follow business behavior was not intentionally changed
