import os
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel
from app.database import User
from app.auth import usuario_actual
from app.services.export_docs import generar_docx, generar_pdf, EXPORT_DIR

router = APIRouter(prefix="/api/exportar", tags=["exportar"])


class ExportRequest(BaseModel):
    titulo: str = "Material de estudio"
    contenido: str
    formato: str


@router.post("/")
def exportar(req: ExportRequest, user: User = Depends(usuario_actual)):
    if req.formato == "docx":
        nombre = generar_docx(req.titulo, req.contenido)
    elif req.formato == "pdf":
        nombre = generar_pdf(req.titulo, req.contenido)
    else:
        raise HTTPException(status_code=400, detail="Formato no valido (usa docx o pdf).")
    return {"download_url": f"/api/exportar/descargar/{nombre}"}


@router.get("/descargar/{nombre}")
def descargar(nombre: str):
    ruta = os.path.join(EXPORT_DIR, nombre)
    if not os.path.exists(ruta):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    ext = nombre.rsplit(".", 1)[-1]
    media = "application/vnd.openxmlformats-officedocument.wordprocessingml.document" if ext == "docx" else "application/pdf"
    return FileResponse(ruta, media_type=media, filename=f"nursebrain.{ext}")
