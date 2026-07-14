from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from datetime import datetime

from app.config import APP_SECRET_KEY
from app.database import init_db, get_db, User, Document, GlossaryTerm, ChatHistory
from app.auth import esta_logueado
from app.services import auth_service, mail_service
from app.routers import documentos, chat, examen, pae, audio, glosario, studio, exportar, biblioteca

app = FastAPI(title="NurseBrain AI")
app.add_middleware(SessionMiddleware, secret_key=APP_SECRET_KEY, max_age=60*60*24*30)
init_db()

for r in [documentos, chat, examen, pae, audio, glosario, studio, exportar, biblioteca]:
    app.include_router(r.router)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    if not esta_logueado(request):
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/registro", response_class=HTMLResponse)
def registro_page(request: Request):
    if esta_logueado(request):
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse("registro.html", {"request": request, "error": None, "ok": None})


@app.post("/registro", response_class=HTMLResponse)
async def registro_post(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    email = (form.get("email") or "").strip().lower()
    password = form.get("password") or ""
    nombre = form.get("nombre") or ""
    if not email or "@" not in email or len(password) < 6:
        return templates.TemplateResponse("registro.html", {"request": request, "error": "Email invalido o contraseña muy corta (min 6).", "ok": None}, status_code=400)
    if auth_service.buscar_por_email(db, email):
        return templates.TemplateResponse("registro.html", {"request": request, "error": "Ya existe una cuenta con ese email.", "ok": None}, status_code=400)
    user = auth_service.crear_usuario(db, email, password, nombre)
    mail_service.enviar_verificacion(user.email, user.token_verificacion)
    return templates.TemplateResponse("registro.html", {"request": request, "error": None, "ok": "¡Listo! Te mandamos un mail para confirmar tu cuenta. Revisá tu casilla (y el spam)."})


@app.get("/verificar", response_class=HTMLResponse)
def verificar(request: Request, token: str = "", db: Session = Depends(get_db)):
    user = db.query(User).filter_by(token_verificacion=token).first() if token else None
    if not user:
        return templates.TemplateResponse("mensaje.html", {"request": request, "titulo": "Enlace invalido", "texto": "El enlace de verificacion no es valido o ya fue usado.", "link": "/login"})
    user.verificado = True
    user.token_verificacion = None
    db.commit()
    return templates.TemplateResponse("mensaje.html", {"request": request, "titulo": "¡Cuenta activada!", "texto": "Tu cuenta quedo confirmada. Ya podes ingresar.", "link": "/login"})


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if esta_logueado(request):
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    email = (form.get("email") or "").strip().lower()
    password = form.get("password") or ""
    user = auth_service.autenticar(db, email, password)
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Email o contraseña incorrectos."}, status_code=401)
    if not user.verificado:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Tenes que confirmar tu cuenta desde el mail que te enviamos."}, status_code=403)
    request.session["user_id"] = user.id
    return RedirectResponse("/", status_code=303)


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


@app.get("/recuperar", response_class=HTMLResponse)
def recuperar_page(request: Request):
    return templates.TemplateResponse("recuperar.html", {"request": request, "error": None, "ok": None})


@app.post("/recuperar", response_class=HTMLResponse)
async def recuperar_post(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    email = (form.get("email") or "").strip().lower()
    user = auth_service.buscar_por_email(db, email)
    if user:
        token = auth_service.generar_reset(db, user)
        mail_service.enviar_reset(user.email, token)
    return templates.TemplateResponse("recuperar.html", {"request": request, "error": None, "ok": "Si el email existe, te enviamos instrucciones para recuperar la contraseña."})


@app.get("/reset", response_class=HTMLResponse)
def reset_page(request: Request, token: str = ""):
    return templates.TemplateResponse("reset.html", {"request": request, "token": token, "error": None})


@app.post("/reset", response_class=HTMLResponse)
async def reset_post(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    token = form.get("token") or ""
    password = form.get("password") or ""
    user = db.query(User).filter_by(token_reset=token).first() if token else None
    if not user or not user.token_reset_expira or user.token_reset_expira < datetime.utcnow():
        return templates.TemplateResponse("reset.html", {"request": request, "token": token, "error": "El enlace venció o es invalido. Pedí uno nuevo."}, status_code=400)
    if len(password) < 6:
        return templates.TemplateResponse("reset.html", {"request": request, "token": token, "error": "La contraseña debe tener al menos 6 caracteres."}, status_code=400)
    user.password_hash = auth_service.hash_password(password)
    user.token_reset = None
    user.token_reset_expira = None
    db.commit()
    return templates.TemplateResponse("mensaje.html", {"request": request, "titulo": "Contraseña cambiada", "texto": "Ya podes ingresar con tu nueva contraseña.", "link": "/login"})


@app.post("/api/cuenta/borrar")
async def borrar_cuenta(request: Request, db: Session = Depends(get_db)):
    from app.rag.engine import eliminar_documento as borrar_chroma
    import os
    uid = request.session.get("user_id")
    if not uid:
        return {"error": "No autenticado"}
    docs = db.query(Document).filter_by(user_id=uid).all()
    for d in docs:
        if d.chroma_ids:
            borrar_chroma(d.chroma_ids.split(","))
        if d.filepath and os.path.exists(d.filepath):
            try: os.remove(d.filepath)
            except Exception: pass
    db.query(Document).filter_by(user_id=uid).delete()
    db.query(GlossaryTerm).filter_by(user_id=uid).delete()
    db.query(ChatHistory).filter_by(user_id=uid).delete()
    db.query(User).filter_by(id=uid).delete()
    db.commit()
    request.session.clear()
    return {"ok": True}


@app.get("/onboarding", response_class=HTMLResponse)
def onboarding_page(request: Request):
    return templates.TemplateResponse("onboarding.html", {"request": request})


@app.get("/privacidad", response_class=HTMLResponse)
def privacidad_page(request: Request):
    return templates.TemplateResponse("privacidad.html", {"request": request})


@app.get("/health")
def health():
    return {"status": "ok"}
