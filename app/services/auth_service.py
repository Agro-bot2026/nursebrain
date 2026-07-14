import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import User


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000)
    return f"{salt}${dk.hex()}"


def verificar_password(password: str, password_hash: str) -> bool:
    try:
        salt, hash_guardado = password_hash.split("$", 1)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000)
        return hmac.compare_digest(dk.hex(), hash_guardado)
    except Exception:
        return False


def generar_token() -> str:
    return secrets.token_urlsafe(32)


def crear_usuario(db: Session, email: str, password: str, nombre: str = "") -> User:
    email = email.strip().lower()
    user = User(
        email=email,
        nombre=nombre.strip() or email.split("@")[0],
        password_hash=hash_password(password),
        verificado=False,
        token_verificacion=generar_token(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def buscar_por_email(db: Session, email: str):
    return db.query(User).filter_by(email=email.strip().lower()).first()


def autenticar(db: Session, email: str, password: str):
    user = buscar_por_email(db, email)
    if not user or not user.password_hash:
        return None
    if not verificar_password(password, user.password_hash):
        return None
    return user


def generar_reset(db: Session, user: User) -> str:
    token = generar_token()
    user.token_reset = token
    user.token_reset_expira = datetime.utcnow() + timedelta(hours=2)
    db.commit()
    return token
