from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.database import User
from app.auth import usuario_actual
from app.rag.engine import buscar_contexto
from app.services import deepseek_client

router = APIRouter(prefix="/api/studio", tags=["studio"])


class StudioRequest(BaseModel):
    tema: str
    materia: str = None


@router.post("/flashcards")
def flashcards(req: StudioRequest, user: User = Depends(usuario_actual)):
    contexto = buscar_contexto(user.id, req.tema, n_resultados=8, materia=req.materia)
    if not contexto:
        return {"error": "No hay material indexado sobre ese tema todavia."}
    return {"flashcards": deepseek_client.generar_flashcards(contexto)}


@router.post("/resumen")
def resumen(req: StudioRequest, user: User = Depends(usuario_actual)):
    contexto = buscar_contexto(user.id, req.tema, n_resultados=8, materia=req.materia)
    if not contexto:
        return {"error": "No hay material indexado sobre ese tema todavia."}
    return {"resumen": deepseek_client.generar_resumen(contexto)}
