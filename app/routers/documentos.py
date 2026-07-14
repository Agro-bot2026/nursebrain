import os
import json
import uuid
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from pypdf import PdfReader
from app.database import get_db, Document, GlossaryTerm, User
from app.config import UPLOAD_DIR
from app.auth import usuario_actual
from app.rag.engine import indexar_documento
from app.services import deepseek_client
from app.services.ocr_vertex import extraer_texto_pdf_o_imagen
from app.services.web_scraper import extraer_texto_web, titulo_de_web
from app.services.youtube_transcript import extraer_transcript_youtube
from app.services.speech_vertex import transcribir_audio

router = APIRouter(prefix="/api/documentos", tags=["documentos"])


def _es_pdf_con_texto(filepath):
    try:
        reader = PdfReader(filepath)
        texto = "\n".join(page.extract_text() or "" for page in reader.pages)
        return texto.strip() or None
    except Exception:
        return None


def _procesar_y_guardar(db, user_id, texto, filename, materia, filepath="", tipo="documento"):
    if not texto or not texto.strip():
        raise HTTPException(status_code=422, detail="No se pudo extraer texto de la fuente.")
    doc = Document(user_id=user_id, filename=filename, materia=materia, filepath=filepath, texto_extraido=texto)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    chroma_ids = indexar_documento(user_id, doc.id, texto, materia, filename)
    doc.chroma_ids = ",".join(chroma_ids)
    db.commit()
    try:
        resultado = deepseek_client.extraer_terminos_nuevos(texto[:4000])
        terminos = json.loads(resultado)
        for t in terminos:
            existe = db.query(GlossaryTerm).filter_by(termino=t["termino"], user_id=user_id).first()
            if not existe:
                db.add(GlossaryTerm(user_id=user_id, termino=t["termino"], definicion=t.get("definicion", ""), fuente_documento=filename))
        db.commit()
    except Exception:
        pass
    return {"id": doc.id, "filename": doc.filename, "materia": doc.materia, "tipo": tipo, "chunks_indexados": len(chroma_ids)}


@router.post("/subir")
async def subir_documento(materia: str = Form("General"), archivo: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(usuario_actual)):
    filepath = os.path.join(UPLOAD_DIR, f"u{user.id}_{archivo.filename}")
    contenido = await archivo.read()
    with open(filepath, "wb") as f:
        f.write(contenido)
    nombre = archivo.filename.lower()
    texto = None
    tipo = "documento"
    if nombre.endswith(".pdf"):
        tipo = "pdf"
        texto = _es_pdf_con_texto(filepath)
        if not texto:
            texto = extraer_texto_pdf_o_imagen(filepath, mime_type="application/pdf")
    elif nombre.endswith((".jpg", ".jpeg", ".png", ".webp")):
        tipo = "imagen"
        mime = "image/png" if nombre.endswith(".png") else "image/jpeg"
        try:
            texto = extraer_texto_pdf_o_imagen(filepath, mime_type=mime)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error en OCR Vertex: {e}")
    else:
        try:
            texto = contenido.decode("utf-8", errors="ignore")
            tipo = "texto"
        except Exception:
            raise HTTPException(status_code=415, detail="Tipo de archivo no soportado.")
    return _procesar_y_guardar(db, user.id, texto, archivo.filename, materia, filepath, tipo)


class TextoRequest(BaseModel):
    titulo: str = "Nota pegada"
    texto: str
    materia: str = "General"


@router.post("/subir-texto")
def subir_texto(req: TextoRequest, db: Session = Depends(get_db), user: User = Depends(usuario_actual)):
    return _procesar_y_guardar(db, user.id, req.texto, req.titulo, req.materia, tipo="texto")


class WebRequest(BaseModel):
    url: str
    materia: str = "General"


@router.post("/subir-web")
def subir_web(req: WebRequest, db: Session = Depends(get_db), user: User = Depends(usuario_actual)):
    try:
        texto = extraer_texto_web(req.url)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"No pude leer esa web: {e}")
    return _procesar_y_guardar(db, user.id, texto, titulo_de_web(req.url), req.materia, filepath=req.url, tipo="web")


class YoutubeRequest(BaseModel):
    url: str
    materia: str = "General"


@router.post("/subir-youtube")
def subir_youtube(req: YoutubeRequest, db: Session = Depends(get_db), user: User = Depends(usuario_actual)):
    try:
        texto = extraer_transcript_youtube(req.url)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return _procesar_y_guardar(db, user.id, texto, f"YouTube: {req.url[:80]}", req.materia, filepath=req.url, tipo="youtube")


@router.post("/subir-audio")
async def subir_audio(materia: str = Form("General"), archivo: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(usuario_actual)):
    nombre = f"u{user.id}_{uuid.uuid4().hex}_{archivo.filename}"
    filepath = os.path.join(UPLOAD_DIR, nombre)
    contenido = await archivo.read()
    with open(filepath, "wb") as f:
        f.write(contenido)
    try:
        texto = transcribir_audio(filepath)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error transcribiendo audio: {e}")
    return _procesar_y_guardar(db, user.id, texto, archivo.filename, materia, filepath, tipo="audio")


@router.get("/")
def listar_documentos(db: Session = Depends(get_db), user: User = Depends(usuario_actual)):
    docs = db.query(Document).filter_by(user_id=user.id).order_by(Document.id.desc()).all()
    return [{"id": d.id, "filename": d.filename, "materia": d.materia, "uploaded_at": d.uploaded_at} for d in docs]


@router.delete("/{doc_id}")
def eliminar_documento(doc_id: int, db: Session = Depends(get_db), user: User = Depends(usuario_actual)):
    from app.rag.engine import eliminar_documento as borrar_chroma
    doc = db.query(Document).filter_by(id=doc_id, user_id=user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    if doc.chroma_ids:
        borrar_chroma(doc.chroma_ids.split(","))
    if doc.filepath and os.path.exists(doc.filepath):
        os.remove(doc.filepath)
    db.delete(doc)
    db.commit()
    return {"ok": True}
