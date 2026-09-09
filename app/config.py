import os
import shutil
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]

IMPROVED_MODEL_PATH = Path(os.getenv("VOICECLONEGUARD_MODEL", str(ROOT_DIR / "models" / "improved_voice_model.pkl")))
ORIGINAL_MODEL_PATH = ROOT_DIR / "models" / "voice_cloning_model.pkl"

WINDOW_SECONDS = float(os.getenv("VCG_WINDOW_SECONDS", "4"))
HOP_SECONDS = float(os.getenv("VCG_HOP_SECONDS", "1"))


def resolve_model_path() -> Path:
    if IMPROVED_MODEL_PATH.exists():
        return IMPROVED_MODEL_PATH
    return ORIGINAL_MODEL_PATH


def ffmpeg_binary() -> str | None:
    configured = os.getenv("FFMPEG_BIN")
    if configured and Path(configured).exists():
        return configured
    return shutil.which("ffmpeg")
