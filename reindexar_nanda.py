import os, glob
from dotenv import load_dotenv
load_dotenv("/opt/nursebrain/.env")
from app.database import SessionLocal, SharedDocument, UserSharedDocument
from app.rag import engine

db = SessionLocal()
doc = db.query(SharedDocument).filter(SharedDocument.filename.contains("NANDA")).first()
print(f"Libro: id={doc.id}, chunks viejos={len(doc.chroma_ids.split(',')) if doc.chroma_ids else 0}")

# 1. Borrar chunks viejos de biblioteca
ids_viejos = doc.chroma_ids.split(",") if doc.chroma_ids else []
if ids_viejos:
    engine.eliminar_libro_biblioteca(ids_viejos)
    print(f"Borrados {len(ids_viejos)} chunks viejos de biblioteca")

# 2. Borrar copias activadas viejas de cada usuario
activaciones = db.query(UserSharedDocument).filter_by(shared_doc_id=doc.id).all()
usuarios_activos = [a.user_id for a in activaciones]
for uid in usuarios_activos:
    engine.desactivar_libro_para_usuario(uid, doc.id)
print(f"Copias activadas borradas para usuarios: {usuarios_activos}")

# 3. Juntar las 871 paginas en orden
archivos = sorted(glob.glob("/opt/nursebrain/nanda_paginas/pag_*.txt"))
texto_completo = ""
for a in archivos:
    with open(a) as f:
        texto_completo += f.read() + "\n"
print(f"Texto completo: {len(texto_completo):,} caracteres de {len(archivos)} paginas")

# 4. Reindexar biblioteca completa
nuevos_ids = engine.indexar_biblioteca(doc.id, texto_completo, "Diagnósticos de Enfermería", doc.filename)
print(f"Reindexado: {len(nuevos_ids)} chunks nuevos")

# 5. Actualizar chroma_ids en la base
doc.chroma_ids = ",".join(nuevos_ids)
db.commit()

# 6. Re-activar para los usuarios que lo tenian
for uid in usuarios_activos:
    engine.activar_libro_para_usuario(uid, doc.id, nuevos_ids)
print(f"Re-activado para usuarios: {usuarios_activos}")

print("LISTO - reindexado completo")
db.close()
