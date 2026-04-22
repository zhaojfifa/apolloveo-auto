## PR-13: steps_v1.py compatibility-pressure reduction audit

Branch name:

- `VeoBase01-pr13-steps-v1-compatibility-reduction`

Base SHA:

- `dead681a10b0773b662c092cd62ced016373465c`

Purpose:

- reduce neutral compatibility/helper pressure inside `gateway/app/services/steps_v1.py`
- move reusable SRT/text normalization helpers closer to a specialized support module
- preserve step execution semantics, ordering, and lifecycle behavior

Scope:

- extract stateless SRT/text helpers into `gateway/app/services/steps_text_support.py`
- keep legacy helper names in `steps_v1.py` as thin wrappers for existing callers and tests
- add direct tests for the new support module

Non-goals:

- no step ordering change
- no pipeline lifecycle change
- no new line-aware execution
- no business-flow change in subtitles, dub, pack, or publish steps

Files changed:

- `docs/execution/VEOBASE01_EXECUTION_LOG.md`
- `docs/execution/VEOBASE01_PR13_STEPS_V1_COMPATIBILITY_REDUCTION.md`
- `gateway/app/services/steps_v1.py`
- `gateway/app/services/steps_text_support.py`
- `gateway/app/services/tests/test_steps_text_support.py`

Exact validation commands run:

- `git diff --check`
- `PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m py_compile gateway/app/services/steps_v1.py gateway/app/services/steps_text_support.py gateway/app/services/tests/test_steps_text_support.py`
- `WORKSPACE_ROOT=/tmp/apolloveo-workspace PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m pytest gateway/app/services/tests/test_steps_text_support.py gateway/app/services/status_policy/tests/test_dub_voice_and_text_guard.py gateway/app/services/tests/test_steps_v1_subtitles_step.py gateway/app/services/status_policy/tests/test_hot_follow_subtitle_only_compose.py gateway/app/services/tests/test_hf_compose_freshness.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py -q`
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

- Exact live task data for `9c755859d049` and `9280fcb9f0b1` is not available in this workspace, so PR-13 reran the same closest-equivalent read-only synthetic in-memory probe used by the earlier VeoBase01 refactor PRs.
- Final-ready sample `9c755859d049`:
  - publish: `final_exists=true`, `composed_ready=true`, `publish_ready=true`, `audio_ready=true`, `compose_status=done`
  - workbench: `artifact_facts.final_exists=true`, `composed_ready=true`, `ready_gate.publish_ready=true`, `audio.audio_ready=true`, compose status `done`
  - persisted task state: `compose_status=done`
- Compose-running sample `9280fcb9f0b1`:
  - publish: `final_exists=false`, `composed_ready=false`, `publish_ready=false`, `audio_ready=true`, `compose_status=pending`
  - workbench: `artifact_facts.final_exists=false`, `composed_ready=false`, `ready_gate.publish_ready=false`, `audio.audio_ready=true`, compose status remained in progress as `running`
  - persisted task state remained `compose_status=running`

Risks:

- `steps_v1.py` still owns step orchestration and several step-specific side-effect helpers; this PR only moves the neutral text/SRT compatibility cluster
- compatibility wrappers remain in `steps_v1.py` intentionally for import stability

Rollback path:

- `git checkout VeoBase01`
- `git merge --ff-only dead681a10b0773b662c092cd62ced016373465c`
- or revert the PR-13 commit if only the helper extraction must be undone

Acceptance judgment:

- accepted for PR-13 scope
- `steps_v1.py` reduced from `2413` to `2349` lines
- neutral SRT/text compatibility helpers now live in a dedicated support module
- no pipeline ordering, lifecycle, or hidden state-path behavior was intentionally changed
