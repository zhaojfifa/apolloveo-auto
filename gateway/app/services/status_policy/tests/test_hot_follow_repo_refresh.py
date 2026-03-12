from pathlib import Path
import sys
import types

from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parents[5]))
try:
    import pydantic_settings as _pydantic_settings  # noqa: F401
except Exception:
    shim = types.ModuleType("pydantic_settings")

    class _BaseSettings(BaseModel):
        model_config = {"extra": "ignore"}

    shim.BaseSettings = _BaseSettings
    sys.modules["pydantic_settings"] = shim

from gateway.app.routers import tasks as tasks_router


class _Session:
    def __init__(self):
        self.expired = False

    def expire_all(self):
        self.expired = True


class _Repo:
    def __init__(self):
        self.session = _Session()
        self.stale = {"task_id": "t1", "mm_audio_key": None}
        self.fresh = {"task_id": "t1", "mm_audio_key": "deliver/tasks/t1/audio_mm.mp3"}

    def get(self, _task_id):
        return self.fresh if self.session.expired else self.stale


def test_repo_refresh_task_uses_expire_all_to_read_fresh_state():
    repo = _Repo()

    task = tasks_router._repo_refresh_task(repo, "t1")

    assert repo.session.expired is True
    assert task["mm_audio_key"] == "deliver/tasks/t1/audio_mm.mp3"
