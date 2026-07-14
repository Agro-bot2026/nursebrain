from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db, ChatHistory, User
from app.auth import usuario_actual
from app.rag.engine import buscar_contexto
from app.services import deepseek_client

router = APIRouter(prefix="/api/chat", tags=["chat"])


class PreguntaRequest(BaseModel):
    pregunta: str
    materia: str = None


@router.post("/preguntar")
def preguntar(req: PreguntaRequest, db: Session = Depends(get_db), user: User = Depends(usuario_actual)):
    contexto = buscar_contexto(user.id, req.pregunta, n_resultados=5, materia=req.materia)
    if not contexto:
        respuesta = "Todavia no tengo material tuyo sobre este tema. Subi algun PDF o apunte relacionado y volve a preguntar."
    else:
        respuesta = deepseek_client.responder_con_contexto(req.pregunta, contexto)
    db.add(ChatHistory(user_id=user.id, pregunta=req.pregunta, respuesta=respuesta, materia=req.materia))
    db.commit()
    return {"respuesta": respuesta, "fuentes_usadas": len(contexto)}


@router.get("/historial")
def historial(db: Session = Depends(get_db), user: User = Depends(usuario_actual), limit: int = 50):
    items = db.query(ChatHistory).filter_by(user_id=user.id).order_by(ChatHistory.id.desc()).limit(limit).all()
    return [{"pregunta": i.pregunta, "respuesta": i.respuesta, "materia": i.materia, "fecha": i.created_at} for i in items]
