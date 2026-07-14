from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    nombre = Column(String, nullable=True)
    password_hash = Column(String, nullable=True)
    google_id = Column(String, unique=True, nullable=True)
    verificado = Column(Boolean, default=False)
    token_verificacion = Column(String, nullable=True)
    token_reset = Column(String, nullable=True)
    token_reset_expira = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String, nullable=False)
    materia = Column(String, default="General")
    filepath = Column(String, nullable=False)
    texto_extraido = Column(Text, nullable=True)
    chroma_ids = Column(Text, nullable=True)
    estado = Column(String, default="listo")
    paginas_procesadas = Column(Integer, default=0)
    paginas_total = Column(Integer, default=0)
    uploaded_at = Column(DateTime, default=datetime.utcnow)


class GlossaryTerm(Base):
    __tablename__ = "glossary"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    termino = Column(String, nullable=False)
    definicion = Column(Text, nullable=True)
    fuente_documento = Column(String, nullable=True)
    aprendido = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    pregunta = Column(Text, nullable=False)
    respuesta = Column(Text, nullable=False)
    materia = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)




class SharedDocument(Base):
    __tablename__ = "shared_documents"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    titulo = Column(String, nullable=False)
    materia = Column(String, default="General")
    descripcion = Column(Text, nullable=True)
    filepath = Column(String, nullable=False)
    chroma_ids = Column(Text, nullable=True)
    estado = Column(String, default="listo")
    paginas_procesadas = Column(Integer, default=0)
    paginas_total = Column(Integer, default=0)
    uploaded_at = Column(DateTime, default=datetime.utcnow)


class UserSharedDocument(Base):
    __tablename__ = "user_shared_documents"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    shared_doc_id = Column(Integer, ForeignKey("shared_documents.id"), nullable=False, index=True)
    activated_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
