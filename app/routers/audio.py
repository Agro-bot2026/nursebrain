import os
import uuid
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel
from app.config import UPLOAD_DIR
from app.database import User
from app.auth import usuario_actual
from app.rag.engine import buscar_contexto
from app.services import deepseek_client
from app.services.tts_vertex import generar_audio

router = APIRouter(prefix="/api/audio", tags=["audio"])
AUDIO_DIR = os.path.join(UPLOAD_DIR, "audios")
os.makedirs(AUDIO_DIR, exist_ok=True)


class AudioResumenRequest(BaseModel):
    tema: str
    materia: str = None
    voz: str = "puck"


@router.post("/generar")
def generar_audio_resumen(req: AudioResumenRequest, user: User = Depends(usuario_actual)):
    contexto = buscar_contexto(user.id, req.tema, n_resultados=6, materia=req.materia)
    if not contexto:
        return {"error": "No hay material indexado sobre ese tema todavia."}
    guion = deepseek_client.resumir_para_audio("\n".join(contexto))
    nombre = f"{uuid.uuid4().hex}.mp3"
    filepath = os.path.join(AUDIO_DIR, nombre)
    try:
        generar_audio(guion, filepath, voz=req.voz)
    except Exception as e:
        return {"error": f"No pude generar el audio: {e}", "guion": guion}
    return {"guion": guion, "audio_url": f"/api/audio/descargar/{nombre}"}


@router.get("/descargar/{nombre_archivo}")
def descargar_audio(nombre_archivo: str):
    filepath = os.path.join(AUDIO_DIR, nombre_archivo)
    return FileResponse(filepath, media_type="audio/mpeg", filename="resumen-nursebrain.mp3")
