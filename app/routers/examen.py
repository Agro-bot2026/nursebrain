from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.database import User
from app.auth import usuario_actual
from app.rag.engine import buscar_contexto
from app.services import deepseek_client

router = APIRouter(prefix="/api/examen", tags=["examen"])


class ExamenRequest(BaseModel):
    tema: str
    materia: str = None
    cantidad: int = 5


@router.post("/generar")
def generar_examen(req: ExamenRequest, user: User = Depends(usuario_actual)):
    contexto = buscar_contexto(user.id, req.tema, n_resultados=8, materia=req.materia)
    if not contexto:
        return {"error": "No hay material indexado sobre ese tema todavia."}
    return {"examen": deepseek_client.generar_examen(contexto, cantidad=req.cantidad)}
