import httpx
from app.config import RESEND_API_KEY, MAIL_FROM, BASE_URL

LOGO_URL = "https://nursebrain.charly-tricks.dev/static/img/logo-mail.jpg"


def _enviar(to: str, subject: str, html: str, texto_plano: str) -> bool:
    if not RESEND_API_KEY:
        print("[mail] Falta RESEND_API_KEY, no se envia")
        return False
    try:
        resp = httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
            json={
                "from": MAIL_FROM,
                "to": [to],
                "subject": subject,
                "html": html,
                "text": texto_plano,
                "reply_to": "nursebrain@charly-tricks.dev",
            },
            timeout=20,
        )
        return resp.status_code in (200, 201)
    except Exception as e:
        print("[mail] error:", e)
        return False


def _plantilla(titulo: str, cuerpo: str, boton_texto: str, boton_url: str, extra: str = "") -> str:
    return f"""
    <div style="font-family:system-ui,-apple-system,sans-serif;max-width:520px;margin:0 auto;background:#ffffff;color:#1a1a2e;border-radius:12px;padding:0;border:1px solid #e5e5e5;overflow:hidden;">
      <div style="background:#0c0a1a;padding:24px 32px;display:flex;align-items:center;gap:12px;">
        <img src="{LOGO_URL}" width="44" height="44" style="border-radius:12px;display:block;border:2px solid rgba(167,139,250,.4);">
        <div>
          <span style="color:#a78bfa;font-size:20px;font-weight:bold;display:block;">NurseBrain AI</span>
          <span style="color:#a5a0c4;font-size:12px;">Tu copiloto de estudio para enfermería</span>
        </div>
      </div>
      <div style="padding:32px;">
        <h2 style="font-size:18px;margin:0 0 12px;color:#1a1a2e;">{titulo}</h2>
        <p style="color:#444;line-height:1.7;font-size:14px;">{cuerpo}</p>
        <p style="color:#444;line-height:1.7;font-size:14px;">
          NurseBrain te ayuda a estudiar con tu propio material: subís tus apuntes, PDFs o guías,
          y la plataforma responde preguntas, genera resúmenes, cuestionarios y audio a partir
          de lo que vos misma cargaste.
        </p>
        <div style="text-align:center;margin:28px 0;">
          <a href="{boton_url}" style="display:inline-block;background:#4f46e5;color:#ffffff;text-decoration:none;font-weight:bold;padding:14px 32px;border-radius:8px;font-size:15px;">{boton_texto}</a>
        </div>
        <p style="color:#888;font-size:12px;line-height:1.6;">
          Si el botón no funciona, copiá y pegá este enlace en tu navegador:<br>
          <span style="color:#4f46e5;word-break:break-all;">{boton_url}</span>
        </p>
        {extra}
        <hr style="border:none;border-top:1px solid #eee;margin:24px 0;">
        <p style="color:#999;font-size:11px;line-height:1.6;">
          Recibiste este mail porque te registraste en NurseBrain AI (nursebrain.charly-tricks.dev).
          Si no fuiste vos, podés ignorar este mensaje sin problema.<br>
          ¿Dudas? Respondé este mail, lo leemos.
        </p>
      </div>
    </div>
    """


def enviar_verificacion(email: str, token: str) -> bool:
    url = f"{BASE_URL}/verificar?token={token}"
    html = _plantilla(
        "Confirmá tu cuenta para empezar a estudiar",
        "¡Gracias por sumarte a NurseBrain! Con tu cuenta activada vas a poder cargar tus apuntes y empezar a usar el tutor de inteligencia artificial ya mismo.",
        "Activar mi cuenta", url,
    )
    texto = (f"Confirma tu cuenta en NurseBrain AI\n\nGracias por registrarte. Para activar tu cuenta, entra a este enlace:\n{url}\n\nSi no fuiste vos, ignora este mensaje.")
    return _enviar(email, "Confirmá tu cuenta - NurseBrain AI", html, texto)


def enviar_reset(email: str, token: str) -> bool:
    url = f"{BASE_URL}/reset?token={token}"
    html = _plantilla(
        "Recuperá el acceso a tu cuenta",
        "Recibimos un pedido para cambiar tu contraseña en NurseBrain. Si fuiste vos, elegí una nueva contraseña con el botón de abajo. El enlace vence en 2 horas.",
        "Cambiar mi contraseña", url,
    )
    texto = (f"Recuperar contraseña - NurseBrain AI\n\nPediste cambiar tu contraseña. Entra a este enlace (vence en 2 horas):\n{url}\n\nSi no fuiste vos, ignora este mensaje.")
    return _enviar(email, "Recuperá tu contraseña - NurseBrain AI", html, texto)
