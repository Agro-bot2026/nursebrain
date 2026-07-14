
async function descargarArchivo(btn, url){
  var t = btn.textContent;
  btn.textContent = 'Descargando...';
  try {
    var a = document.createElement('a');
    a.href = url;
    a.download = 'resumen-nursebrain.mp3';
    a.target = '_blank';
    document.body.appendChild(a);
    a.click();
    a.remove();
    btn.textContent = t;
  } catch(e) {
    btn.textContent = t;
    window.open(url, '_blank');
  }
}
let materiaActiva = "General";
let vozActiva = "puck";
const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);
function toast(msg){const t=$("#toast");t.textContent=msg;t.classList.remove("oculta");clearTimeout(t._t);t._t=setTimeout(()=>t.classList.add("oculta"),2600);}
async function api(url,opts={}){const res=await fetch(url,opts);let data={};try{data=await res.json();}catch(e){}if(!res.ok)throw new Error(data.detail||"Error del servidor");return data;}
function irA(v){$$(".nav-btn").forEach(b=>b.classList.toggle("activo",b.dataset.view===v));$$(".view").forEach(x=>x.classList.add("oculta"));$("#view-"+v).classList.remove("oculta");if(v==="biblioteca")cargarBiblioteca();$("#fab-fuente").style.display=(v==="fuentes")?"block":"none";window.scrollTo({top:0,behavior:"smooth"});}
$$(".nav-btn").forEach(btn=>btn.addEventListener("click",()=>irA(btn.dataset.view)));
$$("[data-goto]").forEach(btn=>btn.addEventListener("click",()=>irA(btn.dataset.goto)));
$("#materia-chip").addEventListener("click",()=>{const n=prompt("Materia activa:",materiaActiva);if(n&&n.trim()){materiaActiva=n.trim();$("#materia-chip").innerHTML="&#9873; "+materiaActiva;$("#modal-materia-input").value=materiaActiva;}});
async function cargarFuentes(){try{const docs=await api("/api/documentos/");const cont=$("#lista-fuentes");if(!docs.length){cont.innerHTML='<div class="empty">Todavía no cargaste nada.<br>Tocá <b>+ Añadir fuente</b> para empezar.</div>';return;}cont.innerHTML=docs.map(d=>`<div class="fuente-item"><div class="fi-ico">DOC</div><div class="fi-body"><div class="fi-nombre">${escapeHtml(d.filename)}</div><div class="fi-meta">${escapeHtml(d.materia||'General')}</div></div><button class="fi-del" data-id="${d.id}">&#128465;</button></div>`).join("");$$(".fi-del").forEach(b=>b.addEventListener("click",async()=>{if(!confirm("¿Borrar esta fuente?"))return;await api("/api/documentos/"+b.dataset.id,{method:"DELETE"});toast("Fuente eliminada");cargarFuentes();}));}catch(e){toast("No pude cargar las fuentes");}}
function escapeHtml(s){return (s||"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
const modal=$("#modal-fuente");
$("#fab-fuente").addEventListener("click",()=>{$("#modal-materia-input").value=materiaActiva;resetPaneles();modal.classList.remove("oculta");});
$("#modal-cerrar").addEventListener("click",()=>modal.classList.add("oculta"));
modal.addEventListener("click",e=>{if(e.target===modal)modal.classList.add("oculta");});
function resetPaneles(){$("#panel-url").classList.add("oculta");$("#panel-texto").classList.add("oculta");$("#modal-estado").textContent="";$("#modal-estado").classList.remove("error");}
function estado(msg,err=false){const e=$("#modal-estado");e.textContent=msg;e.classList.toggle("error",err);}
function getMateria(){return ($("#modal-materia-input").value||"General").trim()||"General";}
$$(".fuente-tipo").forEach(btn=>btn.addEventListener("click",()=>{resetPaneles();const tipo=btn.dataset.tipo;if(tipo==="pdf")$("#file-pdf").click();else if(tipo==="imagen")$("#file-imagen").click();else if(tipo==="audio")$("#file-audio").click();else if(tipo==="web"){$("#panel-url").classList.remove("oculta");$("#input-url").placeholder="https://...";$("#input-url").dataset.destino="web";$("#input-url").focus();}else if(tipo==="youtube"){$("#panel-url").classList.remove("oculta");$("#input-url").placeholder="Enlace de YouTube...";$("#input-url").dataset.destino="youtube";$("#input-url").focus();}else if(tipo==="texto"){$("#panel-texto").classList.remove("oculta");$("#input-texto-cuerpo").focus();}}));
async function subirArchivo(input,endpoint,etiqueta){const file=input.files[0];if(!file)return;estado(`Subiendo y procesando ${etiqueta}...`);const fd=new FormData();fd.append("materia",getMateria());fd.append("archivo",file);try{const r=await api(endpoint,{method:"POST",body:fd});estado(`Listo: ${r.filename} (${r.chunks_indexados} fragmentos).`);toast("Fuente añadida");cargarFuentes();setTimeout(()=>modal.classList.add("oculta"),1200);}catch(e){estado(e.message,true);}input.value="";}
$("#file-pdf").addEventListener("change",e=>subirArchivo(e.target,"/api/documentos/subir","PDF"));
$("#file-imagen").addEventListener("change",e=>subirArchivo(e.target,"/api/documentos/subir","imagen"));
$("#file-audio").addEventListener("change",e=>subirArchivo(e.target,"/api/documentos/subir-audio","audio"));
$("#btn-url-enviar").addEventListener("click",async()=>{const url=$("#input-url").value.trim();if(!url){estado("Pegá un enlace primero.",true);return;}const destino=$("#input-url").dataset.destino;const endpoint=destino==="youtube"?"/api/documentos/subir-youtube":"/api/documentos/subir-web";estado("Procesando enlace...");try{const r=await api(endpoint,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({url,materia:getMateria()})});estado(`Listo: ${r.filename} (${r.chunks_indexados} fragmentos).`);toast("Fuente añadida");$("#input-url").value="";cargarFuentes();setTimeout(()=>modal.classList.add("oculta"),1200);}catch(e){estado(e.message,true);}});
$("#btn-texto-enviar").addEventListener("click",async()=>{const titulo=$("#input-texto-titulo").value.trim()||"Nota pegada";const texto=$("#input-texto-cuerpo").value.trim();if(!texto){estado("Pegá algún texto primero.",true);return;}estado("Procesando texto...");try{const r=await api("/api/documentos/subir-texto",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({titulo,texto,materia:getMateria()})});estado(`Listo: ${r.filename} (${r.chunks_indexados} fragmentos).`);toast("Fuente añadida");$("#input-texto-titulo").value="";$("#input-texto-cuerpo").value="";cargarFuentes();setTimeout(()=>modal.classList.add("oculta"),1200);}catch(e){estado(e.message,true);}});
function addMsg(texto,quien,fuentes=null){const log=$("#chat-log");const div=document.createElement("div");div.className="msg msg-"+quien;div.textContent=texto;if(fuentes!==null&&quien==="bot"){const tag=document.createElement("span");tag.className="fuentes-tag";tag.textContent=fuentes>0?`${fuentes} fragmento(s) de tus fuentes`:"Sin coincidencias en tus fuentes";div.appendChild(tag);}log.appendChild(div);div.scrollIntoView({behavior:"smooth",block:"end"});return div;}
async function preguntar(texto){if(!texto.trim())return;addMsg(texto,"user");$("#input-pregunta").value="";const p=addMsg("Pensando...","bot");p.classList.add("pensando");try{const r=await api("/api/chat/preguntar",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({pregunta:texto,materia:materiaActiva})});p.remove();addMsg(r.respuesta,"bot",r.fuentes_usadas);}catch(e){p.remove();addMsg("Uf, algo falló: "+e.message,"bot");}}
$("#btn-enviar").addEventListener("click",()=>preguntar($("#input-pregunta").value));
$("#input-pregunta").addEventListener("keydown",e=>{if(e.key==="Enter")preguntar(e.target.value);});
$$("#chips-sugeridos .chip").forEach(c=>c.addEventListener("click",()=>preguntar(c.textContent)));
function tema(){return ($("#studio-tema").value||"").trim();}
$$(".studio-card").forEach(card=>card.addEventListener("click",()=>ejecutarStudio(card.dataset.accion)));
function botonesDescarga(titulo,contenido){const id="dl"+Math.random().toString(36).slice(2,8);setTimeout(()=>{const w=document.getElementById(id+"w"),p=document.getElementById(id+"p");if(w)w.onclick=()=>exportar(titulo,contenido,"docx",w);if(p)p.onclick=()=>exportar(titulo,contenido,"pdf",p);},50);return `<div class="dl-bar"><button id="${id}w" class="dl-btn">⬇ Word</button><button id="${id}p" class="dl-btn">⬇ PDF</button></div>`;}
async function exportar(titulo,contenido,formato,btn){const orig=btn.textContent;btn.textContent="Generando...";try{const r=await api("/api/exportar/",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({titulo,contenido,formato})});window.location.href=r.download_url;btn.textContent=orig;}catch(e){toast("Error al exportar: "+e.message);btn.textContent=orig;}}
async function ejecutarStudio(accion){const salida=$("#studio-salida");const t=tema();
if(accion==="glosario"){salida.innerHTML='<div class="caja">Cargando glosario...</div>';try{const terms=await api("/api/glosario/");if(!terms.length){salida.innerHTML='<div class="caja">Todavía no hay términos. Subí material y se llena solo.</div>';return;}const txt=terms.map(x=>`• ${x.termino}: ${x.definicion||''}`).join("\n");salida.innerHTML='<div class="caja"><b>Glosario</b><br>'+terms.map(x=>`• <b>${escapeHtml(x.termino)}</b>: ${escapeHtml(x.definicion||'')}`).join("<br>")+'</div>'+botonesDescarga("Glosario",txt);}catch(e){salida.innerHTML=`<div class="caja">Error: ${escapeHtml(e.message)}</div>`;}return;}
if(accion==="pae"){const caso=prompt("Pegá el caso clínico para el PAE (NANDA/NIC/NOC):");if(!caso)return;salida.innerHTML='<div class="caja">Generando PAE...</div>';try{const r=await api("/api/pae/generar",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({caso})});salida.innerHTML=`<div class="caja">${escapeHtml(r.pae)}<br><br><small style="color:var(--txt-dim)">${escapeHtml(r.disclaimer)}</small></div>`+botonesDescarga("PAE - "+caso.slice(0,40),r.pae);}catch(e){salida.innerHTML=`<div class="caja">Error: ${escapeHtml(e.message)}</div>`;}return;}
if(accion==="audio"){if(!t){toast("Escribí un tema arriba primero");$("#studio-tema").focus();return;}const voz=confirm("¿Voz femenina (Kore)?\n\nAceptar = Kore (mujer)\nCancelar = Puck (varón)")?"kore":"puck";salida.innerHTML='<div class="caja">Generando audio con voz real... (puede tardar)</div>';try{const r=await api("/api/audio/generar",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({tema:t,materia:materiaActiva,voz})});if(r.error){salida.innerHTML=`<div class="caja">${escapeHtml(r.error)}</div>`;return;}salida.innerHTML=`<div class="caja"><b>Resumen en audio</b><br><br>${escapeHtml(r.guion)}<audio controls src="${r.audio_url}"></audio><div class="dl-bar"><button class="dl-btn" onclick="descargarArchivo(this,'${r.audio_url}')">⬇ Descargar MP3</button></div></div>`;}catch(e){salida.innerHTML=`<div class="caja">Error: ${escapeHtml(e.message)}</div>`;}return;}
if(!t){toast("Escribí un tema arriba primero");$("#studio-tema").focus();return;}
salida.innerHTML='<div class="caja">Generando... (puede tardar unos segundos)</div>';
try{if(accion==="examen"){const r=await api("/api/examen/generar",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({tema:t,materia:materiaActiva,cantidad:5})});if(r.error){salida.innerHTML=`<div class="caja">${escapeHtml(r.error)}</div>`;return;}salida.innerHTML=`<div class="caja"><b>Cuestionario</b><br><br>${escapeHtml(r.examen)}</div>`+botonesDescarga("Cuestionario - "+t,r.examen);}
else if(accion==="resumen"){const r=await api("/api/studio/resumen",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({tema:t,materia:materiaActiva})});if(r.error){salida.innerHTML=`<div class="caja">${escapeHtml(r.error)}</div>`;return;}salida.innerHTML=`<div class="caja">${escapeHtml(r.resumen)}</div>`+botonesDescarga("Resumen - "+t,r.resumen);}
else if(accion==="flashcards"){const r=await api("/api/studio/flashcards",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({tema:t,materia:materiaActiva})});if(r.error){salida.innerHTML=`<div class="caja">${escapeHtml(r.error)}</div>`;return;}let cards=[];try{cards=JSON.parse(r.flashcards);}catch(e){salida.innerHTML=`<div class="caja">${escapeHtml(r.flashcards)}</div>`;return;}const txt=cards.map(c=>`P: ${c.pregunta}\nR: ${c.respuesta}\n`).join("\n");salida.innerHTML='<b>Tarjetas didácticas</b>'+cards.map(c=>`<div class="flashcard"><div class="fc-q">${escapeHtml(c.pregunta)}</div><div class="fc-a">${escapeHtml(c.respuesta)}</div></div>`).join("")+botonesDescarga("Flashcards - "+t,txt);}
}catch(e){salida.innerHTML=`<div class="caja">Error: ${escapeHtml(e.message)}</div>`;}}
$("#fab-fuente").style.display="none";
cargarFuentes();

// ===== Cuenta: cerrar sesion / borrar cuenta =====
document.getElementById("cuenta-btn")?.addEventListener("click", function(){
  document.getElementById("modal-cuenta").classList.remove("oculta");
});
document.getElementById("cuenta-cerrar")?.addEventListener("click", function(){
  document.getElementById("modal-cuenta").classList.add("oculta");
});
document.getElementById("btn-borrar-cuenta")?.addEventListener("click", async function(){
  if(!confirm("¿Seguro que queres borrar tu cuenta? Se pierden todos tus documentos, chats y glosario. Esta accion NO se puede deshacer.")) return;
  if(!confirm("Ultima confirmacion: esto es permanente. ¿Borrar la cuenta ahora?")) return;
  try{
    const res = await fetch("/api/cuenta/borrar", {method:"POST"});
    const data = await res.json();
    if(data.ok){
      alert("Tu cuenta fue borrada.");
      window.location.href = "/login";
    } else {
      alert("No pude borrar la cuenta: " + (data.error||"error desconocido"));
    }
  }catch(e){
    alert("Error al borrar la cuenta: " + e.message);
  }
});


// ===== BIBLIOTECA =====
async function cargarBiblioteca() {
  const lista = document.getElementById("biblioteca-lista");
  if (!lista) return;
  verificarAdmin();
  lista.innerHTML = "<p style='color:var(--txt-dim)'>Cargando biblioteca...</p>";
  try {
    const res = await fetch("/api/biblioteca/");
    const libros = await res.json();
    if (!libros.length) {
      lista.innerHTML = "<p style='color:var(--txt-dim)'>No hay libros en la biblioteca todavía.</p>";
      return;
    }
    lista.innerHTML = libros.map(l => {
      const procesando = l.estado === "procesando";
      const conError = l.estado === "error";
      let accion;
      if (procesando) {
        accion = `
          <div class="amb-wrap">
            <div class="amb-track">
              <div class="amb-fill" style="width:${l.porcentaje}%"></div>
              <div class="amb-veh" style="left:calc(${l.porcentaje}% - 14px)">🚑</div>
              <div class="amb-hosp">🏥</div>
            </div>
            <div class="amb-label">Procesando libro… ${l.porcentaje}%</div>
          </div>`;
      } else if (conError) {
        accion = `<div class="amb-label" style="color:#f87171">Error al procesar. Volvé a subirlo.</div>`;
      } else {
        accion = `<button class="btn-lib ${l.activado ? "btn-lib-on" : "btn-lib-off"}"
          onclick="toggleLibro(${l.id}, ${l.activado})">
          ${l.activado ? "✓ Activado" : "+ Activar"}
        </button>`;
      }
      return `
      <div class="fuente-card" id="libro-${l.id}" data-estado="${l.estado}">
        <div class="fuente-icon">📖</div>
        <div class="fuente-info">
          <div class="fuente-nombre">${l.titulo}</div>
          <div class="fuente-meta">${l.materia}</div>
          ${l.descripcion ? `<div class="fuente-meta" style="margin-top:4px">${l.descripcion}</div>` : ""}
          ${accion}
        </div>
      </div>`;
    }).join("");
    const enProceso = libros.filter(l => l.estado === "procesando");
    if (enProceso.length) {
      clearTimeout(window._bibliotecaTimer);
      window._bibliotecaTimer = setTimeout(() => actualizarProgresos(enProceso.map(l => l.id)), 3000);
    }
  } catch(e) {
    lista.innerHTML = "<p style='color:#f87171'>Error cargando la biblioteca</p>";
  }
}

async function toggleLibro(id, activado) {
  const btn = document.querySelector(`#libro-${id} .btn-lib`);
  if (btn) { btn.disabled = true; btn.textContent = "..."; }
  try {
    const endpoint = activado ? `/api/biblioteca/${id}/desactivar` : `/api/biblioteca/${id}/activar`;
    const res = await fetch(endpoint, {method: "POST"});
    const data = await res.json();
    if (data.ok) {
      await cargarBiblioteca();
      toast(activado ? "Libro quitado de tus fuentes" : "¡Libro activado! Ya podés preguntarle al chat sobre él");
    }
  } catch(e) {
    toast("Error al cambiar el libro");
    if (btn) { btn.disabled = false; }
  }
}

// --- Subida de libros (admin) ---
async function verificarAdmin() {
  try {
    const res = await fetch("/api/biblioteca/yo");
    const data = await res.json();
    if (data.es_admin) {
      const zona = document.getElementById("admin-subir-zona");
      if (zona) zona.style.display = "block";
    }
  } catch(e) {}
}

function toggleFormSubir() {
  const f = document.getElementById("form-subir");
  if (f) f.style.display = f.style.display === "none" ? "block" : "none";
}

async function enviarLibro() {
  const titulo = document.getElementById("sub-titulo").value.trim();
  const materia = document.getElementById("sub-materia").value.trim() || "General";
  const desc = document.getElementById("sub-desc").value.trim();
  const archivo = document.getElementById("sub-archivo").files[0];
  if (!titulo || !archivo) { toast("Poné al menos título y archivo PDF"); return; }
  const btn = document.getElementById("btn-enviar-libro");
  btn.disabled = true; btn.textContent = "Subiendo...";
  try {
    const fd = new FormData();
    fd.append("titulo", titulo);
    fd.append("materia", materia);
    fd.append("descripcion", desc);
    fd.append("archivo", archivo);
    const res = await fetch("/api/biblioteca/admin/subir", {method: "POST", body: fd});
    const data = await res.json();
    if (data.id) {
      toast("¡Libro subido! La ambulancia ya está en camino 🚑");
      document.getElementById("form-subir").style.display = "none";
      document.getElementById("sub-titulo").value = "";
      document.getElementById("sub-materia").value = "";
      document.getElementById("sub-desc").value = "";
      document.getElementById("sub-archivo").value = "";
      await cargarBiblioteca();
    } else {
      toast(data.detail || "Error al subir");
    }
  } catch(e) {
    toast("Error al subir el libro");
  } finally {
    btn.disabled = false; btn.textContent = "Subir y procesar";
  }
}

// Actualiza solo las barras de progreso sin redibujar toda la lista (evita parpadeo)
async function actualizarProgresos(ids) {
  let algunoTermino = false;
  const siguen = [];
  for (const id of ids) {
    try {
      const res = await fetch(`/api/biblioteca/${id}/progreso`);
      const p = await res.json();
      if (p.estado === "procesando") {
        siguen.push(id);
        const card = document.getElementById(`libro-${id}`);
        if (card) {
          const fill = card.querySelector(".amb-fill");
          const veh = card.querySelector(".amb-veh");
          const label = card.querySelector(".amb-label");
          if (fill) fill.style.width = p.porcentaje + "%";
          if (veh) veh.style.left = `calc(${p.porcentaje}% - 14px)`;
          if (label) label.textContent = `Procesando libro… ${p.porcentaje}%`;
        }
      } else {
        algunoTermino = true;
      }
    } catch(e) {}
  }
  if (algunoTermino) {
    cargarBiblioteca();
  } else if (siguen.length) {
    clearTimeout(window._bibliotecaTimer);
    window._bibliotecaTimer = setTimeout(() => actualizarProgresos(siguen), 3000);
  }
}
