import os
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db, SharedDocument, UserSharedDocument, User
from app.config import UPLOAD_DIR, ADMIN_USER
from app.auth import usuario_actual
from app.rag.engine import indexar_biblioteca, activar_libro_para_usuario, desactivar_libro_para_usuario
from app.services.ocr_vertex import extraer_texto_pdf_o_imagen
from pypdf import PdfReader

router = APIRouter(prefix="/api/biblioteca", tags=["biblioteca"])
BIBLIOTECA_DIR = os.path.join(UPLOAD_DIR, "biblioteca")
os.makedirs(BIBLIOTECA_DIR, exist_ok=True)


def _es_pdf_con_texto(filepath: str):
    try:
        reader = PdfReader(filepath)
        texto = "\n".join(page.extract_text() or "" for page in reader.pages)
        return texto.strip() or None
    except Exception:
        return None


@router.post("/admin/subir")
async def admin_subir_libro(
    titulo: str = Form(...),
    materia: str = Form("General"),
    descripcion: str = Form(""),
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(usuario_actual),
):
    if user.email != ADMIN_USER:
        raise HTTPException(status_code=403, detail="Solo el administrador puede subir libros.")
    import subprocess
    filepath = os.path.join(BIBLIOTECA_DIR, archivo.filename)
    contenido = await archivo.read()
    with open(filepath, "wb") as f:
        f.write(contenido)
    doc = SharedDocument(filename=archivo.filename, titulo=titulo, materia=materia,
                         descripcion=descripcion, filepath=filepath, estado="procesando",
                         paginas_procesadas=0, paginas_total=0)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    subprocess.Popen(
        ["/opt/nursebrain/venv/bin/python", "/opt/nursebrain/procesar_libro.py", str(doc.id), filepath],
        cwd="/opt/nursebrain",
        stdout=open(f"/opt/nursebrain/proc_libro_{doc.id}.log", "w"),
        stderr=subprocess.STDOUT,
    )
    return {"id": doc.id, "titulo": doc.titulo, "estado": "procesando"}


@router.delete("/admin/{libro_id}")
def admin_borrar_libro(libro_id: int, db: Session = Depends(get_db), user: User = Depends(usuario_actual)):
    from app.rag.engine import eliminar_libro_biblioteca
    if user.email != ADMIN_USER:
        raise HTTPException(status_code=403, detail="Solo el administrador.")
    libro = db.query(SharedDocument).filter_by(id=libro_id).first()
    if not libro:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    if libro.chroma_ids:
        eliminar_libro_biblioteca(libro.chroma_ids.split(","))
    if os.path.exists(libro.filepath):
        os.remove(libro.filepath)
    db.query(UserSharedDocument).filter_by(shared_doc_id=libro_id).delete()
    db.delete(libro)
    db.commit()
    return {"ok": True}


@router.get("/yo")
def quien_soy(user: User = Depends(usuario_actual)):
    return {"email": user.email, "es_admin": user.email == ADMIN_USER}


@router.get("/")
def listar_biblioteca(db: Session = Depends(get_db), user: User = Depends(usuario_actual)):
    libros = db.query(SharedDocument).all()
    activados = {r.shared_doc_id for r in db.query(UserSharedDocument).filter_by(user_id=user.id).all()}
    def _pct(l):
        t = l.paginas_total or 0
        return round(100 * (l.paginas_procesadas or 0) / t) if t > 0 else 0
    return [
        {"id": l.id, "titulo": l.titulo, "filename": l.filename, "materia": l.materia,
         "descripcion": l.descripcion, "activado": l.id in activados, "uploaded_at": l.uploaded_at,
         "estado": l.estado or "listo", "porcentaje": _pct(l)}
        for l in libros
    ]


@router.get("/{libro_id}/progreso")
def progreso_libro(libro_id: int, db: Session = Depends(get_db), user: User = Depends(usuario_actual)):
    libro = db.query(SharedDocument).filter_by(id=libro_id).first()
    if not libro:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    total = libro.paginas_total or 0
    hechas = libro.paginas_procesadas or 0
    pct = round(100 * hechas / total) if total > 0 else 0
    return {"id": libro.id, "estado": libro.estado, "procesadas": hechas,
            "total": total, "porcentaje": pct}


@router.post("/{libro_id}/activar")
def activar_libro(libro_id: int, db: Session = Depends(get_db), user: User = Depends(usuario_actual)):
    libro = db.query(SharedDocument).filter_by(id=libro_id).first()
    if not libro:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    ya = db.query(UserSharedDocument).filter_by(user_id=user.id, shared_doc_id=libro_id).first()
    if ya:
        return {"ok": True, "mensaje": "Ya estaba activado"}
    chroma_ids = libro.chroma_ids.split(",") if libro.chroma_ids else []
    nuevos_ids = activar_libro_para_usuario(user.id, libro_id, chroma_ids)
    db.add(UserSharedDocument(user_id=user.id, shared_doc_id=libro_id))
    db.commit()
    return {"ok": True, "chunks_agregados": len(nuevos_ids)}


@router.post("/{libro_id}/desactivar")
def desactivar_libro(libro_id: int, db: Session = Depends(get_db), user: User = Depends(usuario_actual)):
    rel = db.query(UserSharedDocument).filter_by(user_id=user.id, shared_doc_id=libro_id).first()
    if not rel:
        return {"ok": True, "mensaje": "No estaba activado"}
    desactivar_libro_para_usuario(user.id, libro_id)
    db.delete(rel)
    db.commit()
    return {"ok": True}
