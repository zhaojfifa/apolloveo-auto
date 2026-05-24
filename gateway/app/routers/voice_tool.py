from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field

from gateway.app.auth import require_operator_session
from gateway.app.services.voice_tool import VoiceToolError, get_voice_tool_service
from gateway.app.web.templates import render_template

page_router = APIRouter(tags=["voice-tool"])
api_router = APIRouter(prefix="/api/voice-tool", tags=["voice-tool"])


class TranslateRequest(BaseModel):
    source_text: str = Field(..., min_length=1, max_length=8000)
    source_language: str
    target_language: str
    style_preset: str = "natural_human"


class SynthesizeRequest(BaseModel):
    job_id: str | None = None
    speech_text: str = Field(..., min_length=1, max_length=8000)
    target_language: str
    voice_preset: str = "natural"
    speed: str = "normal"
    voice_mode: str = "stable"


class GenerateRequest(TranslateRequest):
    voice_preset: str = "natural"
    speed: str = "normal"
    voice_mode: str = "stable"


class SpeechVariantsRequest(BaseModel):
    job_id: str | None = None
    translated_text: str | None = Field(default=None, max_length=8000)
    target_language: str
    voice_mode: str = "humanized"


class FeedbackRequest(BaseModel):
    job_id: str
    naturalness_score: int
    translation_score: int
    speed_score: int
    voice_fit_score: int
    usable_for_publish: str
    failure_reason: str | None = None
    comment: str = ""


@page_router.get("/voice-tool", response_class=HTMLResponse, include_in_schema=False)
def voice_tool_page(
    request: Request, _: Any = Depends(require_operator_session)
) -> HTMLResponse:
    return render_template(request=request, name="voice_tool.html")


@api_router.post("/translate")
def translate_voice_tool(
    payload: TranslateRequest, _: Any = Depends(require_operator_session)
) -> dict[str, Any]:
    service = get_voice_tool_service()
    try:
        job = service.translate(**payload.dict())
    except VoiceToolError as exc:
        raise HTTPException(status_code=400, detail={"code": exc.code, "message": str(exc)}) from exc
    return service.storage.public_job_payload(job)


@api_router.post("/synthesize")
async def synthesize_voice_tool(
    payload: SynthesizeRequest, _: Any = Depends(require_operator_session)
) -> dict[str, Any]:
    service = get_voice_tool_service()
    try:
        job = await service.synthesize(**payload.dict())
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="job not found") from exc
    except VoiceToolError as exc:
        raise HTTPException(status_code=400, detail={"code": exc.code, "message": str(exc)}) from exc
    return service.storage.public_job_payload(job)


@api_router.post("/generate")
async def generate_voice_tool(
    payload: GenerateRequest, _: Any = Depends(require_operator_session)
) -> dict[str, Any]:
    service = get_voice_tool_service()
    try:
        job = await service.generate(**payload.dict())
    except VoiceToolError as exc:
        raise HTTPException(status_code=400, detail={"code": exc.code, "message": str(exc)}) from exc
    return service.storage.public_job_payload(job)


@api_router.get("/jobs/{job_id}")
def get_voice_tool_job(
    job_id: str, _: Any = Depends(require_operator_session)
) -> dict[str, Any]:
    service = get_voice_tool_service()
    try:
        job = service.get_job(job_id)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail="job not found") from exc
    return service.storage.public_job_payload(job)


@api_router.get("/options")
def get_voice_tool_options(
    target_language: str = "my", _: Any = Depends(require_operator_session)
) -> dict[str, object]:
    service = get_voice_tool_service()
    try:
        return service.public_options(target_language)
    except VoiceToolError as exc:
        raise HTTPException(status_code=400, detail={"code": exc.code, "message": str(exc)}) from exc


@api_router.post("/speech-variants")
def generate_voice_tool_speech_variants(
    payload: SpeechVariantsRequest, _: Any = Depends(require_operator_session)
) -> dict[str, Any]:
    service = get_voice_tool_service()
    try:
        variants = service.generate_style_variants(**payload.dict())
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="job not found") from exc
    except VoiceToolError as exc:
        raise HTTPException(status_code=400, detail={"code": exc.code, "message": str(exc)}) from exc
    return {"speech_variants": variants}


@api_router.get("/download/{job_id}")
def download_voice_tool_audio(
    job_id: str,
    format: str = Query(default="mp3", pattern="^(mp3|wav)$"),
    _: Any = Depends(require_operator_session),
) -> FileResponse:
    service = get_voice_tool_service()
    try:
        paths = service.storage.paths_for(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="job not found") from exc
    path = paths.output_wav if format == "wav" else paths.output_mp3
    if not path.exists():
        raise HTTPException(status_code=404, detail="audio not found")
    media_type = "audio/wav" if format == "wav" else "audio/mpeg"
    return FileResponse(
        str(path),
        media_type=media_type,
        filename=f"{job_id}.{format}",
    )


@api_router.post("/feedback")
def submit_voice_tool_feedback(
    payload: FeedbackRequest, _: Any = Depends(require_operator_session)
) -> dict[str, Any]:
    service = get_voice_tool_service()
    try:
        job = service.submit_feedback(**payload.dict())
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="job not found") from exc
    except VoiceToolError as exc:
        raise HTTPException(status_code=400, detail={"code": exc.code, "message": str(exc)}) from exc
    return service.storage.public_job_payload(job)
