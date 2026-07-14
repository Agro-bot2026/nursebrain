from google.cloud import speech


def transcribir_audio(filepath: str) -> str:
    """
    Transcribe audio a texto con Speech-to-Text de Vertex.
    La transcripcion sincrona anda bien con audios de hasta ~1 minuto.
    """
    client = speech.SpeechClient()

    with open(filepath, "rb") as f:
        content = f.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        language_code="es-ES",
        alternative_language_codes=["es-419", "en-US"],
        enable_automatic_punctuation=True,
    )

    response = client.recognize(config=config, audio=audio)

    partes = [r.alternatives[0].transcript for r in response.results if r.alternatives]
    texto = "\n".join(partes).strip()

    if not texto:
        raise ValueError(
            "No pude transcribir el audio. Puede ser muy largo (proba un clip corto) "
            "o el formato no es compatible."
        )
    return texto
