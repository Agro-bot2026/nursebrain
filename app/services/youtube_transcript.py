import re
from youtube_transcript_api import YouTubeTranscriptApi


def extraer_id_youtube(url: str) -> str | None:
    patrones = [
        r"(?:youtu\.be/)([0-9A-Za-z_-]{11})",
        r"(?:v=)([0-9A-Za-z_-]{11})",
        r"(?:embed/)([0-9A-Za-z_-]{11})",
        r"(?:shorts/)([0-9A-Za-z_-]{11})",
    ]
    for p in patrones:
        m = re.search(p, url)
        if m:
            return m.group(1)
    if re.fullmatch(r"[0-9A-Za-z_-]{11}", url.strip()):
        return url.strip()
    return None


def extraer_transcript_youtube(url: str) -> str:
    video_id = extraer_id_youtube(url)
    if not video_id:
        raise ValueError("No pude reconocer el enlace de YouTube.")

    try:
        transcript = YouTubeTranscriptApi.get_transcript(
            video_id, languages=["es", "es-419", "en"]
        )
    except Exception as e:
        raise ValueError(
            "Ese video no tiene subtítulos disponibles para transcribir. "
            f"Detalle: {e}"
        )

    return "\n".join(t["text"] for t in transcript)
