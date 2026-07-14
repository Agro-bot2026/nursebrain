import os
import uuid
import base64
import httpx
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from app.config import GOOGLE_APPLICATION_CREDENTIALS, GCP_PROJECT_ID

OCR_MODEL = "gemini-2.5-flash"
OCR_LOCATION = "us-central1"
GCS_BUCKET = f"{GCP_PROJECT_ID}-nursebrain-ocr-temp"
_SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]
PAGINAS_POR_CHUNK = 50

PROMPT_OCR = (
    "Extrae TODO el texto de este documento, tal cual aparece, "
    "respetando el orden de lectura. Es material de estudio de enfermeria "
    "(apuntes, guias, libros). Devolve SOLO el texto extraido, sin comentarios "
    "ni explicaciones tuyas. Si hay tablas, transcribilas de forma legible."
)


def _get_token() -> str:
    creds = service_account.Credentials.from_service_account_file(
        GOOGLE_APPLICATION_CREDENTIALS, scopes=_SCOPES
    )
    creds.refresh(Request())
    return creds.token


def _gemini_inline(filepath: str, mime_type: str, token: str) -> str:
    with open(filepath, "rb") as f:
        data_b64 = base64.b64encode(f.read()).decode("utf-8")
    url = (f"https://{OCR_LOCATION}-aiplatform.googleapis.com/v1/projects/"
           f"{GCP_PROJECT_ID}/locations/{OCR_LOCATION}/publishers/google/models/"
           f"{OCR_MODEL}:generateContent")
    payload = {
        "contents": [{"role": "user", "parts": [
            {"inlineData": {"mimeType": mime_type, "data": data_b64}},
            {"text": PROMPT_OCR},
        ]}],
        "generationConfig": {"temperature": 0.0, "maxOutputTokens": 8192},
    }
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    resp = httpx.post(url, json=payload, headers=headers, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    parts = data["candidates"][0]["content"]["parts"]
    return "".join(p.get("text", "") for p in parts).strip()


def _subir_a_gcs(filepath: str, mime_type: str, token: str):
    nombre_objeto = f"ocr-temp/{uuid.uuid4().hex}/{os.path.basename(filepath)}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    httpx.post(
        f"https://storage.googleapis.com/storage/v1/b?project={GCP_PROJECT_ID}",
        json={"name": GCS_BUCKET, "location": "US"},
        headers=headers, timeout=30
    )
    with open(filepath, "rb") as f:
        contenido = f.read()
    url_upload = (f"https://storage.googleapis.com/upload/storage/v1/b/"
                  f"{GCS_BUCKET}/o?uploadType=media&name={nombre_objeto}")
    resp = httpx.post(url_upload, content=contenido,
                      headers={"Authorization": f"Bearer {token}", "Content-Type": mime_type},
                      timeout=300)
    resp.raise_for_status()
    return f"gs://{GCS_BUCKET}/{nombre_objeto}", nombre_objeto


def _borrar_de_gcs(nombre_objeto: str, token: str):
    url = (f"https://storage.googleapis.com/storage/v1/b/{GCS_BUCKET}/o/"
           f"{nombre_objeto.replace('/', '%2F')}")
    httpx.delete(url, headers={"Authorization": f"Bearer {token}"}, timeout=30)


def _gemini_gcs(gcs_uri: str, mime_type: str, token: str) -> str:
    url = (f"https://{OCR_LOCATION}-aiplatform.googleapis.com/v1/projects/"
           f"{GCP_PROJECT_ID}/locations/{OCR_LOCATION}/publishers/google/models/"
           f"{OCR_MODEL}:generateContent")
    payload = {
        "contents": [{"role": "user", "parts": [
            {"fileData": {"mimeType": mime_type, "fileUri": gcs_uri}},
            {"text": PROMPT_OCR},
        ]}],
        "generationConfig": {"temperature": 0.0, "maxOutputTokens": 8192},
    }
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    resp = httpx.post(url, json=payload, headers=headers, timeout=300)
    resp.raise_for_status()
    data = resp.json()
    parts = data["candidates"][0]["content"]["parts"]
    return "".join(p.get("text", "") for p in parts).strip()


def _ocr_pdf_por_chunks(filepath: str, token: str) -> str:
    from pypdf import PdfReader, PdfWriter
    import tempfile

    reader = PdfReader(filepath)
    total = len(reader.pages)
    textos = []

    print(f"[OCR] PDF con {total} paginas, procesando en chunks de {PAGINAS_POR_CHUNK}...")

    for inicio in range(0, total, PAGINAS_POR_CHUNK):
        fin = min(inicio + PAGINAS_POR_CHUNK, total)
        print(f"[OCR] Chunk paginas {inicio+1}-{fin}...")

        writer = PdfWriter()
        for i in range(inicio, fin):
            writer.add_page(reader.pages[i])

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            writer.write(tmp)
            tmp_path = tmp.name

        try:
            tam_mb = os.path.getsize(tmp_path) / (1024 * 1024)
            if tam_mb <= 15:
                texto = _gemini_inline(tmp_path, "application/pdf", token)
            else:
                gcs_uri, nombre_objeto = _subir_a_gcs(tmp_path, "application/pdf", token)
                try:
                    texto = _gemini_gcs(gcs_uri, "application/pdf", token)
                finally:
                    try:
                        _borrar_de_gcs(nombre_objeto, token)
                    except Exception:
                        pass
            textos.append(texto)
        except Exception as e:
            print(f"[OCR] Error en chunk {inicio+1}-{fin}: {e}")
            textos.append(f"[Error en paginas {inicio+1}-{fin}]")
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    resultado = "\n\n".join(textos)
    print(f"[OCR] Completado: {len(resultado)} caracteres extraidos")
    return resultado


def extraer_texto_pdf_o_imagen(filepath: str, mime_type: str = "application/pdf") -> str:
    token = _get_token()

    # Si es imagen, siempre inline
    if not mime_type == "application/pdf":
        return _gemini_inline(filepath, mime_type, token)

    # Para PDFs: verificar si tiene muchas paginas
    try:
        from pypdf import PdfReader
        reader = PdfReader(filepath)
        total_paginas = len(reader.pages)
    except Exception:
        total_paginas = 0

    if total_paginas > PAGINAS_POR_CHUNK:
        # PDF grande: procesar por chunks
        return _ocr_pdf_por_chunks(filepath, token)

    # PDF chico: inline si <= 15MB, GCS si es mayor
    tam_mb = os.path.getsize(filepath) / (1024 * 1024)
    if tam_mb <= 15:
        return _gemini_inline(filepath, mime_type, token)

    gcs_uri, nombre_objeto = None, None
    try:
        gcs_uri, nombre_objeto = _subir_a_gcs(filepath, mime_type, token)
        return _gemini_gcs(gcs_uri, mime_type, token)
    finally:
        if nombre_objeto:
            try:
                _borrar_de_gcs(nombre_objeto, token)
            except Exception:
                pass
