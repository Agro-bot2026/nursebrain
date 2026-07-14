import os, sys, fitz, pytesseract
from PIL import Image
import io

PDF = "/opt/nursebrain/uploads/u2_2024_LIBRO_13_ed_NANDA_2024_2026_Diagnósticos_Enfermeros.pdf"
OUT = "/opt/nursebrain/nanda_paginas"
os.makedirs(OUT, exist_ok=True)

doc = fitz.open(PDF)
total = len(doc)
print(f"Total paginas: {total}")

hechas = 0
for i in range(total):
    destino = f"{OUT}/pag_{i+1:04d}.txt"
    if os.path.exists(destino):
        hechas += 1
        continue
    try:
        pix = doc[i].get_pixmap(dpi=200)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        texto = pytesseract.image_to_string(img, lang="spa")
        with open(destino, "w") as f:
            f.write(texto)
        hechas += 1
        if (i+1) % 10 == 0:
            print(f"  [{i+1}/{total}] procesadas, {len(texto)} chars ultima")
            sys.stdout.flush()
    except Exception as e:
        print(f"ERROR pagina {i+1}: {e}")
        sys.stdout.flush()

print(f"LISTO. Paginas con texto: {hechas}/{total}")
