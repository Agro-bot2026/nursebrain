import os
import base64
import subprocess
import struct
import httpx
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from app.config import GOOGLE_APPLICATION_CREDENTIALS, GCP_PROJECT_ID

TTS_MODEL = "gemini-3.1-flash-tts-preview"
TTS_LOCATION = "us-central1"

VOCES = {
    "puck": "Puck",
    "kore": "Kore",
}

_SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]


def _get_token() -> str:
    creds = service_account.Credentials.from_service_account_file(
        GOOGLE_APPLICATION_CREDENTIALS, scopes=_SCOPES
    )
    creds.refresh(Request())
    return creds.token


def _pcm_a_mp3(pcm_bytes: bytes, output_path: str, sample_rate: int = 24000):
    proc = subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "s16le", "-ar", str(sample_rate), "-ac", "1",
            "-i", "pipe:0",
            "-codec:a", "libmp3lame", "-b:a", "128k",
            output_path,
        ],
        input=pcm_bytes,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg fallo: {proc.stderr.decode()[:300]}")


def generar_audio(texto: str, output_path: str, voz: str = "puck") -> str:
    voice_name = VOCES.get(voz.lower(), "Puck")
    token = _get_token()

    url = (
        f"https://{TTS_LOCATION}-aiplatform.googleapis.com/v1beta1/projects/"
        f"{GCP_PROJECT_ID}/locations/{TTS_LOCATION}/publishers/google/models/"
        f"{TTS_MODEL}:generateContent"
    )

    payload = {
        "contents": [{"role": "user", "parts": [{"text": texto}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {"voiceName": voice_name}
                }
            },
        },
    }

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    resp = httpx.post(url, json=payload, headers=headers, timeout=120)
    resp.raise_for_status()
    data = resp.json()

    try:
        parts = data["candidates"][0]["content"]["parts"]
        audio_b64 = None
        for p in parts:
            if "inlineData" in p and p["inlineData"].get("data"):
                audio_b64 = p["inlineData"]["data"]
                break
        if not audio_b64:
            raise KeyError("sin inlineData")
    except (KeyError, IndexError):
        raise RuntimeError(f"Respuesta TTS inesperada: {str(data)[:300]}")

    pcm_bytes = base64.b64decode(audio_b64)
    _pcm_a_mp3(pcm_bytes, output_path)
    return output_path
