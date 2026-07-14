from openai import OpenAI
from app.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)


def preguntar(system_prompt: str, user_prompt: str, temperature: float = 0.4) -> str:
    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
    )
    return response.choices[0].message.content


def responder_con_contexto(pregunta: str, contexto_chunks: list[str]) -> str:
    contexto = "\n\n---\n\n".join(contexto_chunks)
    system_prompt = (
        "Sos un asistente de IA especializado en el estudio de enfermeria. Tu objetivo es "
        "responder con absoluta precision tecnica basandote UNICAMENTE en los fragmentos de "
        "material que se te proporcionan (apuntes, guias, protocolos o leyes de la estudiante).\n\n"
        "Reglas obligatorias:\n"
        "1. LECTURA SEMANTICA COMPLETA: cuando te pregunten por requisitos, condiciones, sintomas "
        "o pasos de un procedimiento, no te limites a palabras clave exactas. Lee los fragmentos "
        "completos para rescatar todas las condicionales (ej: 'bajo supervision', 'en caso de', "
        "'contraindicado si...').\n"
        "2. FIDELIDAD ABSOLUTA AL TEXTO: al listar clasificaciones, criterios, tareas, dosis o "
        "diagnosticos de enfermeria, incluí TODOS los elementos presentes en el fragmento. No "
        "resumas ni recortes listas tecnicas si el material las detalla completas.\n"
        "3. MITIGACION DE ALUCINACIONES: si preguntan por patologias, farmacos, unidades medicas, "
        "normativas o procedimientos que NO aparecen explicitamente en el material entregado, "
        "rechaza la premisa con seguridad: 'El material cargado no contiene informacion sobre ese "
        "aspecto especifico.' Esta PROHIBIDO usar conocimiento general para rellenar huecos o "
        "asumir datos en temas de salud si no estan respaldados por el archivo de la estudiante.\n"
        "4. Cita de que parte del material sale cada respuesta cuando sea posible (articulo, "
        "seccion, inciso)."
    )
    user_prompt = f"Contexto de mis apuntes:\n{contexto}\n\nPregunta: {pregunta}"
    return preguntar(system_prompt, user_prompt)


def generar_examen(contexto_chunks: list[str], cantidad: int = 5) -> str:
    contexto = "\n\n---\n\n".join(contexto_chunks)
    system_prompt = (
        "Sos un generador de examenes de simulacion para una estudiante de enfermeria. "
        "Genera preguntas de opcion multiple SOLO basadas en el contexto entregado, "
        "con 4 opciones cada una, indicando la correcta y una breve justificacion."
    )
    user_prompt = f"Contexto:\n{contexto}\n\nGenera {cantidad} preguntas de examen."
    return preguntar(system_prompt, user_prompt, temperature=0.6)


def generar_pae(caso_clinico: str) -> str:
    system_prompt = (
        "Sos un asistente de enfermeria experto en el Proceso de Atencion de Enfermeria (PAE). "
        "A partir del caso clinico dado, sugeri: diagnosticos NANDA relevantes, "
        "intervenciones NIC asociadas, y resultados esperados NOC. Aclara siempre que "
        "esto es una sugerencia de estudio y debe ser validada por un docente o profesional."
    )
    return preguntar(system_prompt, caso_clinico, temperature=0.5)


def extraer_terminos_nuevos(texto: str) -> str:
    system_prompt = (
        "Analiza el siguiente texto de apuntes de enfermeria y extrae una lista de "
        "terminos tecnicos/medicos importantes que podrian no ser conocidos por una "
        "estudiante. Devolve SOLO un JSON valido: una lista de objetos con 'termino' "
        "y 'definicion' breve. Sin texto extra, sin markdown."
    )
    return preguntar(system_prompt, texto, temperature=0.3)


def generar_flashcards(contexto_chunks: list[str], cantidad: int = 10) -> str:
    contexto = "\n\n---\n\n".join(contexto_chunks)
    system_prompt = (
        "Sos un generador de tarjetas de estudio (flashcards) para enfermeria. "
        "Basandote SOLO en el contexto entregado, genera tarjetas pregunta/respuesta. "
        "Devolve SOLO un JSON valido: una lista de objetos con 'pregunta' y 'respuesta'. "
        "Sin texto extra, sin markdown, sin ```."
    )
    user_prompt = f"Contexto:\n{contexto}\n\nGenera {cantidad} flashcards."
    return preguntar(system_prompt, user_prompt, temperature=0.5)


def generar_resumen(contexto_chunks: list[str]) -> str:
    contexto = "\n\n---\n\n".join(contexto_chunks)
    system_prompt = (
        "Sos un tutor de enfermeria. Hace un resumen claro y estructurado del material "
        "entregado, con titulos y vinetas cuando ayude, pensado para repasar antes de un "
        "parcial. Usa SOLO la informacion del contexto."
    )
    user_prompt = f"Contexto:\n{contexto}\n\nHace un resumen de estudio."
    return preguntar(system_prompt, user_prompt, temperature=0.4)


def resumir_para_audio(texto: str) -> str:
    system_prompt = (
        "Converti el siguiente contenido de estudio en un guion breve, hablado, tipo "
        "podcast educativo de 2-3 minutos, en espanol neutro/argentino, tono cercano "
        "y claro, para que una estudiante lo escuche mientras viaja."
    )
    return preguntar(system_prompt, texto, temperature=0.5)
