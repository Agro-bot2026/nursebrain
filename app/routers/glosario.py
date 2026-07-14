from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db, GlossaryTerm, User
from app.auth import usuario_actual

router = APIRouter(prefix="/api/glosario", tags=["glosario"])


@router.get("/")
def listar_terminos(db: Session = Depends(get_db), user: User = Depends(usuario_actual), solo_pendientes: bool = False):
    query = db.query(GlossaryTerm).filter_by(user_id=user.id)
    if solo_pendientes:
        query = query.filter_by(aprendido=0)
    terminos = query.order_by(GlossaryTerm.termino).all()
    return [{"id": t.id, "termino": t.termino, "definicion": t.definicion, "fuente": t.fuente_documento, "aprendido": bool(t.aprendido)} for t in terminos]


@router.post("/{termino_id}/marcar-aprendido")
def marcar_aprendido(termino_id: int, db: Session = Depends(get_db), user: User = Depends(usuario_actual)):
    termino = db.query(GlossaryTerm).filter_by(id=termino_id, user_id=user.id).first()
    if termino:
        termino.aprendido = 1
        db.commit()
    return {"ok": True}
