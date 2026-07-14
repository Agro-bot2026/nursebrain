# NurseBrain AI

Asistente de estudio con IA para estudiantes de enfermería. Chat inteligente sobre una biblioteca de libros de referencia (NANDA-I y más), con recuperación aumentada (RAG), OCR automático y panel de administración.

## Características

- **Chat con IA** sobre el contenido de los libros de la biblioteca (RAG con ChromaDB)
- **Biblioteca compartida** de libros que las estudiantes pueden activar para consultar
- **Panel de administración** para subir libros nuevos (solo admin)
- **OCR automático** de PDFs escaneados, procesados página por página con checkpoints (a prueba de interrupciones)
- **Barra de progreso** en tiempo real durante el procesamiento de libros
- **RAG por usuario**: cada estudiante tiene su propio espacio de documentos personales
- **Multi-usuario** con registro por email y verificación

## Stack

- **Backend**: FastAPI (Python)
- **Base de datos**: SQLite + SQLAlchemy
- **Vector store**: ChromaDB
- **Embeddings**: SentenceTransformers
- **OCR**: Tesseract (local) + PyMuPDF
- **IA**: DeepSeek / Vertex AI
- **Frontend**: HTML + CSS + JavaScript vanilla (PWA)

## Arquitectura

- `app/` — código de la aplicación (routers, servicios, RAG engine)
- `static/` — frontend (JS, CSS, PWA)
- `templates/` — plantillas HTML
- `procesar_libro.py` — pipeline de OCR e indexación reutilizable
- La biblioteca compartida se indexa una vez y se activa por usuario

## Procesamiento de libros

Los PDFs se procesan en segundo plano con un pipeline robusto:
1. OCR página por página (guardando cada página, permite reanudar si se interrumpe)
2. Indexación completa en ChromaDB
3. Activación por usuario bajo demanda

## Notas

Proyecto desarrollado por CHARLY_TRICKS DEV.
