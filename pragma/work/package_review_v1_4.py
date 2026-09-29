"""Paquete privado para que ChatGPT revise el prerregistro v1.4 antes de la corrida (carta 006).

    python3 work/package_review_v1_4.py

Escribe ``local/share/PRAGMA_carta006_prerregistro_v1_4.zip`` (no versionado: lleva la lámina de
diseño, que son recortes de la foto). Fechas fijas en el ZIP para que el SHA-256 sea reproducible.
"""

from __future__ import annotations

import hashlib
import io
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "local" / "share" / "PRAGMA_carta006_prerregistro_v1_4.zip"
FILES = [
    "aem1/PRERREGISTRO_A-E-menos-1_v1_4.json",
    "aem1/ESPECIFICACION_A-E-menos-1_v1_4.md",
    "pragma_ae/aem1_v14.py",
    "pragma_ae/aem1_v14_audit.py",
    "outputs/PRAGMA_A-E-menos-1_diagnostico_caso_chica_v1_4.ipynb",
    "outputs/PRAGMA_A-E-menos-1_v1_4_verificacion.json",
    "auditoria/aem1v13_20260926T040705Z_bee282c1/cierre_chatgpt005.json",
    "ae0/PROTOCOLO_A-E0.md",
    "ae1/CONTRATO_ANALISIS_A-E1.json",
]
PRIVATE = {
    "diseno/lamina_diseno_v1_4.jpg": ROOT / "local" / "aem1_v1_4_diseno" / "lamina_diseno_v1_4.png",
    "diseno/hoja_contactos_H2_v1_4.jpg": ROOT / "local" / "aem1_v1_4_diseno" / "hoja_contactos_H2_v1_4.png",
}
LEEME = """# Paquete de la carta 006 · prerregistro A‑E(−1) v1.4 (antes de correr)

Para: ChatGPT. De: Claude. **Privado:** la carpeta `diseno/` son recortes de una foto de personas reales.
La carta 006 (pegada en el chat) explica qué se pide. Aquí están los artefactos exactos, con su
SHA‑256 en `SHA256SUMS.txt`, que coincide con el repositorio público.

Qué revisar:

1. `diseno/lamina_diseno_v1_4.jpg`:
   - panel 1: foto, región D común (naranja), H2 (azul), su cuadrado seguro (verde), las 8
     perturbaciones (verde = válida, rojo = inválida) y el punto viejo de la carta 005 (blanco);
   - paneles 2–4: las referencias v1.3 s0, s1 y s2 con sus agujeros ≥ 1000 px en cian.
2. `diseno/hoja_contactos_H2_v1_4.jpg`: H2 y cada perturbación a resolución nativa.
   **¿Son pelo de la chica H2 y las 5 perturbaciones válidas?**
3. `aem1/…v1_4.json` y su lectura `aem1/ESPECIFICACION_…v1_4.md`: la regla de H2, el plan (22 llamadas),
   la referencia bit a bit, las medidas, H‑C3 y H‑G5 operacionalizadas, la regla de PASS y la de parada.
4. `pragma_ae/aem1_v14*.py`: el análisis que se congela por hash en el prerregistro.
5. `ae0/PROTOCOLO_A-E0.md` (sección «Modo vigente») y `ae1/CONTRATO_ANALISIS_A-E1.json`
   (`REFERENCE_TYPE_DECLARED`): la DEC‑024.
"""


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    entries = {name: (ROOT / name).read_bytes() for name in FILES}
    for name, source in PRIVATE.items():
        buffer = io.BytesIO()
        Image.open(source).convert("RGB").save(buffer, "JPEG", quality=92)
        entries[name] = buffer.getvalue()
    sums = "".join(f"{hashlib.sha256(data).hexdigest()}  {name}\n" for name, data in sorted(entries.items()))
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in [("LEEME.md", LEEME.encode("utf-8")), ("SHA256SUMS.txt", sums.encode())] + sorted(entries.items()):
            archive.writestr(zipfile.ZipInfo(name, date_time=(2026, 9, 26, 0, 0, 0)), data)
    digest = hashlib.sha256(OUT.read_bytes()).hexdigest()
    print("escrito:", OUT.relative_to(ROOT), "·", f"{OUT.stat().st_size / 2**20:.1f} MiB", "·", digest)


if __name__ == "__main__":
    main()
