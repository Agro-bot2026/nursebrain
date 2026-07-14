(function () {
  let castDisponible = false;
  window.__onGCastApiAvailable = function (isAvailable) {
    if (!isAvailable) return;
    cast.framework.CastContext.getInstance().setOptions({
      receiverApplicationId: chrome.cast.media.DEFAULT_MEDIA_RECEIVER_APP_ID,
      autoJoinPolicy: chrome.cast.AutoJoinPolicy.ORIGIN_SCOPED,
    });
    castDisponible = true;
  };
  function urlAbsoluta(src) {
    try { return new URL(src, window.location.origin).href; }
    catch (e) { return src; }
  }
  function castAudio(url) {
    if (!castDisponible) {
      alert("Cast no está disponible en este navegador. Probá con Chrome en Android o en la computadora.");
      return;
    }
    const context = cast.framework.CastContext.getInstance();
    context.requestSession().then(function () {
      const session = context.getCurrentSession();
      if (!session) return;
      const mediaInfo = new chrome.cast.media.MediaInfo(url, "audio/mpeg");
      mediaInfo.metadata = new chrome.cast.media.GenericMediaMetadata();
      mediaInfo.metadata.title = "Resumen NurseBrain";
      const request = new chrome.cast.media.LoadRequest(mediaInfo);
      session.loadMedia(request).catch(function (e) {
        alert("No pude enviar el audio al Chromecast: " + e);
      });
    }).catch(function () {});
  }
  function engancharBoton() {
    const salida = document.getElementById("studio-salida");
    if (!salida) return;
    const audios = salida.querySelectorAll("audio:not([data-cast])");
    audios.forEach(function (audioEl) {
      audioEl.setAttribute("data-cast", "1");
      const src = urlAbsoluta(audioEl.getAttribute("src"));
      const btn = document.createElement("button");
      btn.className = "cast-btn";
      btn.innerHTML = "📺 Enviar a la tele (Chromecast)";
      btn.onclick = function () { castAudio(src); };
      audioEl.insertAdjacentElement("afterend", btn);
    });
  }
  const obs = new MutationObserver(engancharBoton);
  document.addEventListener("DOMContentLoaded", function () {
    const salida = document.getElementById("studio-salida");
    if (salida) obs.observe(salida, { childList: true, subtree: true });
    engancharBoton();
  });
})();
