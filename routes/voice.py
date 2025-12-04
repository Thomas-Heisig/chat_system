"""
🎤 Voice & Audio Routes

API endpoints for voice processing features.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from config.settings import logger
from voice.audio_processor import get_audio_processor
from voice.text_to_speech import get_tts_service
from voice.transcription import get_transcription_service

router = APIRouter(prefix="/api/voice", tags=["voice"])


@router.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: Optional[str] = Form(None),
    include_timestamps: bool = Form(False),
) -> Dict[str, Any]:
    """Transcribe audio file to text"""
    transcription_service = get_transcription_service()
    audio_processor = get_audio_processor()

    try:
        # Check file format
        if not audio_processor.is_supported_format(audio.filename or ""):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio format. Supported: {audio_processor.supported_formats}",
            )

        # Save uploaded file
        file_path = audio_processor.upload_dir / (audio.filename or "audio.wav")
        with open(file_path, "wb") as f:
            content = await audio.read()
            f.write(content)

        # Process and transcribe
        process_result = await audio_processor.process_upload(str(file_path))
        transcription_result = await transcription_service.transcribe_audio(
            str(file_path), language=language, include_timestamps=include_timestamps
        )

        return {**transcription_result, "audio_info": process_result}

    except Exception as e:
        logger.error(f"❌ Transcription failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/synthesize")
async def synthesize_speech(
    text: str = Form(...), voice: Optional[str] = Form(None), speed: float = Form(1.0)
) -> Dict[str, Any]:
    """Generate speech from text"""
    tts_service = get_tts_service()

    try:
        result = await tts_service.generate_speech(text=text, voice=voice, speed=speed)
        return result

    except Exception as e:
        logger.error(f"❌ TTS failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voices")
async def get_available_voices():
    """Get list of available TTS voices"""
    tts_service = get_tts_service()
    return {"voices": tts_service.get_available_voices(), "engine": tts_service.tts_engine}


@router.get("/languages")
async def get_supported_languages():
    """Get list of supported transcription languages"""
    transcription_service = get_transcription_service()
    return {"languages": transcription_service.get_supported_languages()}


@router.get("/status")
async def get_voice_service_status():
    """Get voice services status"""
    transcription_service = get_transcription_service()
    tts_service = get_tts_service()
    audio_processor = get_audio_processor()

    return {
        "transcription": transcription_service.get_service_info(),
        "text_to_speech": tts_service.get_service_info(),
        "audio_processor": audio_processor.get_service_info(),
    }
