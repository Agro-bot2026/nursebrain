import httpx
from bs4 import BeautifulSoup


def extraer_texto_web(url: str) -> str:
    """Descarga una página web y extrae su texto principal, limpio."""
    headers = {"User-Agent": "Mozilla/5.0 (compatible; NurseBrain/1.0)"}
    resp = httpx.get(url, timeout=30, follow_redirects=True, headers=headers)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()

    texto = soup.get_text(separator="\n")
    lineas = [l.strip() for l in texto.splitlines() if l.strip()]
    return "\n".join(lineas)


def titulo_de_web(url: str, html: str = "") -> str:
    """Intenta sacar un título legible de la página."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; NurseBrain/1.0)"}
        if not html:
            html = httpx.get(url, timeout=15, follow_redirects=True, headers=headers).text
        soup = BeautifulSoup(html, "html.parser")
        if soup.title and soup.title.string:
            return soup.title.string.strip()[:120]
    except Exception:
        pass
    return url[:120]
