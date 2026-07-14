from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.database import User
from app.auth import usuario_actual
from app.services import deepseek_client

router = APIRouter(prefix="/api/pae", tags=["pae"])


class CasoClinicoRequest(BaseModel):
    caso: str


@router.post("/generar")
def generar_pae(req: CasoClinicoRequest, user: User = Depends(usuario_actual)):
    resultado = deepseek_client.generar_pae(req.caso)
    return {"pae": resultado, "disclaimer": "Sugerencia de estudio generada por IA. Debe ser validada por un docente o profesional de enfermeria antes de usarse en la practica real."}
