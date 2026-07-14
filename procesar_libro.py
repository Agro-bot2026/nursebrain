import sys, os, glob, io, fitz, pytesseract
from PIL import Image
from dotenv import load_dotenv
load_dotenv("/opt/nursebrain/.env")
from app.database import SessionLocal, SharedDocument, UserSharedDocument
from app.rag import engine

def log(msg):
    print(msg, flush=True)

def procesar(shared_doc_id, pdf_path):
    db = SessionLocal()
    doc = db.query(SharedDocument).get(shared_doc_id)
    if not doc:
        log(f"ERROR: no existe doc id={shared_doc_id}")
        return

    carpeta = f"/opt/nursebrain/paginas_libro_{shared_doc_id}"
    os.makedirs(carpeta, exist_ok=True)

    try:
        pdf = fitz.open(pdf_path)
        total = len(pdf)
        doc.paginas_total = total
        doc.estado = "procesando"
        db.commit()
        log(f"Total paginas: {total}")

        for i in range(total):
            destino = f"{carpeta}/pag_{i+1:04d}.txt"
            if not os.path.exists(destino):
                pix = pdf[i].get_pixmap(dpi=200)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                texto = pytesseract.image_to_string(img, lang="spa")
                with open(destino, "w") as f:
                    f.write(texto)
            doc.paginas_procesadas = i + 1
            if (i+1) % 5 == 0:
                db.commit()
                log(f"  [{i+1}/{total}]")
        db.commit()

        # Juntar texto
        archivos = sorted(glob.glob(f"{carpeta}/pag_*.txt"))
        texto = ""
        for a in archivos:
            with open(a) as f:
                texto += f.read() + "\n"
        log(f"Texto: {len(texto):,} chars")

        # Borrar indice viejo si existe
        if doc.chroma_ids:
            engine.eliminar_libro_biblioteca(doc.chroma_ids.split(","))
        activaciones = db.query(UserSharedDocument).filter_by(shared_doc_id=doc.id).all()
        for a in activaciones:
            engine.desactivar_libro_para_usuario(a.user_id, doc.id)

        # Indexar completo
        nuevos = engine.indexar_biblioteca(doc.id, texto, doc.materia, doc.filename)
        doc.chroma_ids = ",".join(nuevos)
        log(f"Indexado: {len(nuevos)} chunks")

        # Re-activar
        for a in activaciones:
            engine.activar_libro_para_usuario(a.user_id, doc.id, nuevos)

        doc.estado = "listo"
        db.commit()
        log("LISTO")
    except Exception as e:
        doc.estado = "error"
        db.commit()
        log(f"ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    procesar(int(sys.argv[1]), sys.argv[2])
