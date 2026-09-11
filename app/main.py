import json
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Optional

import librosa
import numpy as np
from fastapi import (
    FastAPI,
    File,
    HTTPException,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import BaseModel, Field

from .config import (
    HOP_SECONDS,
    WINDOW_SECONDS,
    ffmpeg_binary,
    resolve_model_path,
)
from .feature_extractor import extract_features
from .improved_model_adapter import ImprovedVoiceModelAdapter
from .model_adapter import VoiceCloningModelAdapter
from .models import Context, DetectionResult
from .ood_detector import OODDetector
from .privacy import make_event
from .risk_engine import RollingRiskEngine


# ============================================================
# MODEL LOADING
# ============================================================

MODEL_PATH = resolve_model_path()

if MODEL_PATH.name == "improved_voice_model.pkl":
    model = ImprovedVoiceModelAdapter(MODEL_PATH)
    MODEL_TYPE = "rich-feature Random Forest"
elif MODEL_PATH.exists():
    model = VoiceCloningModelAdapter(MODEL_PATH)
    MODEL_TYPE = "original 13-MFCC Random Forest"
else:
    model = None
    MODEL_TYPE = "unavailable"


# ============================================================
# OOD DETECTOR
# ============================================================

OOD_MODEL_PATH = MODEL_PATH.parent / "ood_detector_v2.pkl"
OOD_CALIBRATION_PATH = MODEL_PATH.parent / "ood_calibration_v2.pkl"

if OOD_MODEL_PATH.exists():
    ood_detector = OODDetector(
        OOD_MODEL_PATH,
        OOD_CALIBRATION_PATH,
    )
    OOD_STATUS = "connected"
else:
    ood_detector = None
    OOD_STATUS = "unavailable"


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="VoiceCloneGuard API",
    version="0.2.0",
    description=(
        "Privacy-first AI voice authenticity screening "
        "and rolling risk assessment."
    ),
)


SUPPORTED_AUDIO_EXTENSIONS = {
    ".wav",
    ".flac",
    ".mp3",
    ".ogg",
    ".m4a",
    ".aac",
    ".mpeg",
    ".mpg",
}


# ============================================================
# REQUEST MODELS
# ============================================================

class ScoreRequest(BaseModel):
    spoof_probability: float = Field(ge=0, le=1)
    ood_score: float = Field(default=0, ge=0, le=1)
    speaker_consistency: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
    )
    transaction_risk: float = Field(
        default=0,
        ge=0,
        le=1,
    )
    verified_contact: bool = False


# ============================================================
# AUDIO CONVERSION
# ============================================================

def convert_to_wav(
    input_path: str,
    output_path: str,
) -> None:
    binary = ffmpeg_binary()

    if binary is None:
        raise RuntimeError(
            "FFmpeg is required for MP3/OGG/M4A/AAC/MPEG/MPG uploads. "
            "Install FFmpeg or set FFMPEG_BIN."
        )

    command = [
        binary,
        "-y",
        "-i",
        input_path,
        "-ac",
        "1",
        "-ar",
        "16000",
        "-sample_fmt",
        "s16",
        output_path,
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg conversion failed: {result.stderr[-1500:]}"
        )


# ============================================================
# OOD SCORING
# ============================================================

def compute_ood(
    waveform: np.ndarray,
    sample_rate: int,
) -> Optional[dict]:
    """
    Compute calibrated OOD evidence for one waveform.

    OOD is a secondary uncertainty signal.
    It does not alter the model's spoof probability.
    """

    if ood_detector is None:
        return None

    try:
        features = extract_features(
            waveform,
            sample_rate,
        )

        return ood_detector.score(features)

    except Exception:
        # OOD is optional.
        # A failure must never break primary analysis.
        return None


# ============================================================
# DETECTION + OOD -> RISK INPUT
# ============================================================

def detection_with_ood(
    detection: DetectionResult,
    ood_result: Optional[dict],
) -> DetectionResult:
    """
    Preserve the classifier's spoof probability while attaching
    calibrated OOD evidence to the DetectionResult consumed by
    RollingRiskEngine.

    Important:
        OOD does NOT increase spoof_probability.
    """

    if ood_result is not None:
        try:
            ood_score = float(
                ood_result.get("ood_risk", 0.0)
            )
        except (TypeError, ValueError):
            ood_score = float(detection.ood_score)
    else:
        ood_score = float(detection.ood_score)

    return DetectionResult(
        spoof_probability=float(
            detection.spoof_probability
        ),
        ood_score=max(
            0.0,
            min(1.0, ood_score),
        ),
        speaker_consistency=detection.speaker_consistency,
    )


# ============================================================
# WINDOW RESULT
# ============================================================

def window_result(
    start: float,
    end: float,
    detection: DetectionResult,
    risk,
    ood: Optional[dict] = None,
) -> dict:
    """
    Build a backward-compatible window result and attach
    calibrated OOD evidence when available.
    """

    result = {
        "start_seconds": round(start, 2),
        "end_seconds": round(end, 2),
        "spoof_probability": round(
            float(detection.spoof_probability),
            6,
        ),
        "ood_score": round(
            float(detection.ood_score),
            6,
        ),
        "risk_score": round(
            float(risk.risk_score),
            6,
        ),
        "confidence": round(
            float(risk.confidence),
            6,
        ),
        "action": risk.action,
        "explanation": detection.explanation,
        "reasons": risk.reasons,
    }

    if ood is not None:
        result["ood"] = {
            "raw_score": round(
                float(ood["raw_score"]),
                6,
            ),
            "ood_risk": round(
                float(ood["ood_risk"]),
                6,
            ),
            "percentile": (
                round(
                    float(ood["percentile"]),
                    2,
                )
                if ood["percentile"] is not None
                else None
            ),
            "status": ood["status"],
            "interpretation": ood["interpretation"],
        }

    return result


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root() -> dict:
    return {
        "service": "VoiceCloneGuard",
        "version": app.version,
        "model_type": MODEL_TYPE,
        "model_connected": model is not None,
        "ood_connected": ood_detector is not None,
        "docs": "/docs",
        "health": "/health",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "model_connected": model is not None,
        "model_type": MODEL_TYPE,
        "model_path": (
            MODEL_PATH.name
            if MODEL_PATH.exists()
            else None
        ),
        "ood_connected": ood_detector is not None,
        "ood_model_path": (
            OOD_MODEL_PATH.name
            if OOD_MODEL_PATH.exists()
            else None
        ),
        "ood_calibration_path": (
            OOD_CALIBRATION_PATH.name
            if OOD_CALIBRATION_PATH.exists()
            else None
        ),
        "ood_feature_count": (
            ood_detector.feature_count
            if ood_detector is not None
            else None
        ),
        "ood_feature_version": (
            ood_detector.feature_version
            if ood_detector is not None
            else None
        ),
        "window_seconds": WINDOW_SECONDS,
        "hop_seconds": HOP_SECONDS,
    }


# ============================================================
# SIMPLE SCORE ENDPOINT
# ============================================================

@app.post("/score")
def score(req: ScoreRequest) -> dict:
    engine = RollingRiskEngine()

    result = engine.update(
        DetectionResult(
            spoof_probability=req.spoof_probability,
            ood_score=req.ood_score,
            speaker_consistency=req.speaker_consistency,
        ),
        Context(
            transaction_risk=req.transaction_risk,
            verified_contact=req.verified_contact,
        ),
    )

    event = make_event(
        risk_score=result.risk_score,
        confidence=result.confidence,
        action=result.action,
        reasons=result.reasons,
        session_id="single-score",
    )

    return {
        "result": result.__dict__,
        "evidence": event,
    }


# ============================================================
# AUDIO ANALYSIS
# ============================================================

@app.post("/analyze")
async def analyze_audio(
    file: UploadFile = File(...),
) -> dict:
    if model is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "No model artifact is available. Add "
                "models/improved_voice_model.pkl or "
                "models/voice_cloning_model.pkl."
            ),
        )

    original_suffix = Path(
        file.filename or ""
    ).suffix.lower()

    if original_suffix not in SUPPORTED_AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=(
                "Supported formats: WAV, FLAC, MP3, OGG, M4A, "
                "AAC, MPEG, MPG."
            ),
        )

    input_temp_path: Optional[str] = None
    analysis_path: Optional[str] = None

    try:
        file_bytes = await file.read()

        if not file_bytes:
            raise HTTPException(
                status_code=400,
                detail="The uploaded audio file is empty.",
            )

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=original_suffix,
        ) as temp_file:
            temp_file.write(file_bytes)
            input_temp_path = temp_file.name

        if original_suffix in {".wav", ".flac"}:
            analysis_path = input_temp_path
        else:
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".wav",
            ) as converted_file:
                analysis_path = converted_file.name

            convert_to_wav(
                input_temp_path,
                analysis_path,
            )

        waveform, sample_rate = librosa.load(
            analysis_path,
            sr=None,
            mono=True,
        )

        if waveform.size == 0:
            raise HTTPException(
                status_code=400,
                detail="No audio samples could be decoded.",
            )

        window_size = max(
            1,
            int(WINDOW_SECONDS * sample_rate),
        )

        hop_size = max(
            1,
            int(HOP_SECONDS * sample_rate),
        )

        engine = RollingRiskEngine()
        windows: list[dict] = []

        # ----------------------------------------------------
        # SINGLE WINDOW
        # ----------------------------------------------------

        if len(waveform) <= window_size:
            detection = model.predict(
                waveform,
                sample_rate,
            )

            # FIX:
            # Compute OOD BEFORE risk update.
            ood_result = compute_ood(
                waveform,
                sample_rate,
            )

            detection_for_risk = detection_with_ood(
                detection,
                ood_result,
            )

            risk = engine.update(
                detection_for_risk,
                Context(),
            )

            windows.append(
                window_result(
                    0.0,
                    len(waveform) / sample_rate,
                    detection_for_risk,
                    risk,
                    ood_result,
                )
            )

        # ----------------------------------------------------
        # ROLLING WINDOWS
        # ----------------------------------------------------

        else:
            for start in range(
                0,
                len(waveform) - window_size + 1,
                hop_size,
            ):
                end = start + window_size
                window_waveform = waveform[start:end]

                detection = model.predict(
                    window_waveform,
                    sample_rate,
                )

                # FIX:
                # Compute OOD BEFORE risk update.
                ood_result = compute_ood(
                    window_waveform,
                    sample_rate,
                )

                detection_for_risk = detection_with_ood(
                    detection,
                    ood_result,
                )

                risk = engine.update(
                    detection_for_risk,
                    Context(),
                )

                windows.append(
                    window_result(
                        start / sample_rate,
                        end / sample_rate,
                        detection_for_risk,
                        risk,
                        ood_result,
                    )
                )

            # ------------------------------------------------
            # REMAINING TAIL
            # ------------------------------------------------

            last_start = len(waveform) - window_size
            covered_end = windows[-1]["end_seconds"]
            duration = len(waveform) / sample_rate

            if (
                covered_end < duration - 1e-3
                and last_start > 0
            ):
                tail_waveform = waveform[last_start:]

                detection = model.predict(
                    tail_waveform,
                    sample_rate,
                )

                # FIX:
                # Compute OOD BEFORE risk update.
                ood_result = compute_ood(
                    tail_waveform,
                    sample_rate,
                )

                detection_for_risk = detection_with_ood(
                    detection,
                    ood_result,
                )

                risk = engine.update(
                    detection_for_risk,
                    Context(),
                )

                windows.append(
                    window_result(
                        last_start / sample_rate,
                        duration,
                        detection_for_risk,
                        risk,
                        ood_result,
                    )
                )

        if not windows:
            raise HTTPException(
                status_code=400,
                detail="No analysis windows were produced.",
            )

        final_result = windows[-1]
        final_ood = final_result.get("ood")

        session_id = str(uuid.uuid4())

        evidence = make_event(
            risk_score=final_result["risk_score"],
            confidence=final_result["confidence"],
            action=final_result["action"],
            reasons=final_result["reasons"],
            session_id=session_id,
        )

        return {
            "filename": file.filename,
            "original_format": original_suffix,
            "sample_rate": int(sample_rate),
            "duration_seconds": round(
                len(waveform) / sample_rate,
                2,
            ),
            "windows_analyzed": len(windows),
            "model_type": MODEL_TYPE,
            "ood": final_ood,
            "final": final_result,
            "windows": windows,
            "evidence": evidence,
        }

    finally:
        if input_temp_path:
            Path(input_temp_path).unlink(
                missing_ok=True,
            )

        if (
            analysis_path
            and analysis_path != input_temp_path
        ):
            Path(analysis_path).unlink(
                missing_ok=True,
            )


# ============================================================
# STREAMING ENDPOINT
# ============================================================

@app.websocket("/stream")
async def stream(
    ws: WebSocket,
) -> None:
    await ws.accept()

    if model is None:
        await ws.send_text(
            json.dumps(
                {
                    "error": (
                        "No model artifact is available."
                    )
                }
            )
        )

        await ws.close(code=1011)
        return

    session_id = str(uuid.uuid4())
    engine = RollingRiskEngine()

    try:
        while True:
            raw = await ws.receive_bytes()

            waveform = np.frombuffer(
                raw,
                dtype=np.float32,
            )

            if waveform.size == 0:
                continue

            det = model.predict(
                waveform,
                16000,
            )

            # Streaming OOD is kept separate for now.
            # This preserves the existing WebSocket contract.
            result = engine.update(
                det,
                Context(),
            )

            event = make_event(
                risk_score=result.risk_score,
                confidence=result.confidence,
                action=result.action,
                reasons=result.reasons,
                session_id=session_id,
            )

            await ws.send_text(
                json.dumps(
                    {
                        "result": result.__dict__,
                        "evidence": event,
                    }
                )
            )

    except WebSocketDisconnect:
        return