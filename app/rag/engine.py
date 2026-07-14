import chromadb
from sentence_transformers import SentenceTransformer
from app.config import CHROMA_PERSIST_DIR

_modelo = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
_cliente_chroma = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
_col_personal = _cliente_chroma.get_or_create_collection(name="nursebrain_docs")
_col_biblioteca = _cliente_chroma.get_or_create_collection(name="nursebrain_biblioteca")


def _chunk_texto(texto: str, tamano: int = 800, solapamiento: int = 100):
    chunks = []
    inicio = 0
    while inicio < len(texto):
        chunks.append(texto[inicio:inicio + tamano])
        inicio += tamano - solapamiento
    return [c.strip() for c in chunks if c.strip()]


def indexar_documento(user_id: int, doc_id: int, texto: str, materia: str, filename: str) -> list[str]:
    chunks = _chunk_texto(texto)
    if not chunks:
        return []
    embeddings = _modelo.encode(chunks).tolist()
    ids = [f"u{user_id}_doc{doc_id}_chunk{i}" for i in range(len(chunks))]
    metadatas = [{"user_id": user_id, "materia": materia, "filename": filename, "doc_id": doc_id} for _ in chunks]
    _col_personal.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)
    return ids


def indexar_biblioteca(shared_doc_id: int, texto: str, materia: str, filename: str) -> list[str]:
    chunks = _chunk_texto(texto)
    if not chunks:
        return []
    embeddings = _modelo.encode(chunks).tolist()
    ids = [f"shared{shared_doc_id}_chunk{i}" for i in range(len(chunks))]
    metadatas = [{"shared_doc_id": shared_doc_id, "materia": materia, "filename": filename} for _ in chunks]
    _col_biblioteca.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)
    return ids


def activar_libro_para_usuario(user_id: int, shared_doc_id: int, chroma_ids_libro: list[str]):
    if not chroma_ids_libro:
        return []
    resultado = _col_biblioteca.get(ids=chroma_ids_libro, include=["documents", "metadatas", "embeddings"])
    if not resultado["documents"]:
        return []
    nuevos_ids = [f"u{user_id}_lib{shared_doc_id}_chunk{i}" for i in range(len(resultado["documents"]))]
    nuevos_metadatas = []
    for m in resultado["metadatas"]:
        nuevo_m = dict(m)
        nuevo_m["user_id"] = user_id
        nuevo_m["desde_biblioteca"] = True
        nuevos_metadatas.append(nuevo_m)
    _col_personal.add(
        ids=nuevos_ids,
        embeddings=resultado["embeddings"],
        documents=resultado["documents"],
        metadatas=nuevos_metadatas,
    )
    return nuevos_ids


def desactivar_libro_para_usuario(user_id: int, shared_doc_id: int):
    prefijo = f"u{user_id}_lib{shared_doc_id}_"
    resultado = _col_personal.get(where={"user_id": user_id})
    ids_a_borrar = [id for id in resultado["ids"] if id.startswith(prefijo)]
    if ids_a_borrar:
        _col_personal.delete(ids=ids_a_borrar)


def buscar_contexto(user_id: int, pregunta: str, n_resultados: int = 5, materia: str = None) -> list[str]:
    embedding = _modelo.encode([pregunta]).tolist()
    _filtrar = materia and materia != "General"
    where = {"$and": [{"user_id": user_id}, {"materia": materia}]} if _filtrar else {"user_id": user_id}
    try:
        resultados = _col_personal.query(query_embeddings=embedding, n_results=n_resultados, where=where)
        docs = resultados.get("documents", [[]])
        return docs[0] if docs else []
    except Exception as e:
        print(f"[RAG] Error buscar_contexto user_id={user_id} where={where}: {e}")
        # Intentar sin filtro de materia si fallo
        try:
            resultados = _col_personal.query(query_embeddings=embedding, n_results=n_resultados, where={"user_id": user_id})
            docs = resultados.get("documents", [[]])
            return docs[0] if docs else []
        except Exception as e2:
            print(f"[RAG] Error fallback: {e2}")
            return []


def eliminar_documento(chroma_ids: list[str]):
    if chroma_ids:
        try:
            _col_personal.delete(ids=chroma_ids)
        except Exception:
            pass


def eliminar_libro_biblioteca(chroma_ids: list[str]):
    if chroma_ids:
        try:
            _col_biblioteca.delete(ids=chroma_ids)
        except Exception:
            pass
