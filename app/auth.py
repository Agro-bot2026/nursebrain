from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db, User


def get_user_id(request: Request):
    return request.session.get("user_id")


def esta_logueado(request: Request) -> bool:
    return request.session.get("user_id") is not None


def usuario_actual(request: Request, db: Session = Depends(get_db)) -> User:
    uid = request.session.get("user_id")
    if not uid:
        raise HTTPException(status_code=401, detail="No autenticado")
    user = db.query(User).filter_by(id=uid).first()
    if not user:
        raise HTTPException(status_code=401, detail="Sesion invalida")
    return user
