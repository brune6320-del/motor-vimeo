"""Construye el cuaderno A-E(−1) v1.4 a partir del prerregistro (sin editar a mano ninguna celda).

    python3 work/build_pragma_aem1_v1_4.py

Reutiliza las celdas del cuaderno v1.3 (congelado, commit y checkpoint, foto por hash, luma de todos
los prompts, un único embedding, ejecución literal del ``call_plan`` y ZIP con manifiesto), con los
nombres de v1.4. Cada sustitución se comprueba: si el texto de v1.3 cambiara, la construcción se
detiene. **No muestra máscaras, áreas, scores ni sentinelas.**
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "work"))

import build_pragma_aem1_v1_3 as v13  # noqa: E402

PREREG = ROOT / "aem1" / "PRERREGISTRO_A-E-menos-1_v1_4.json"
OUT = ROOT / "outputs" / "PRAGMA_A-E-menos-1_diagnostico_caso_chica_v1_4.ipynb"

INTRO = """
# PRAGMA · A‑E(−1) v1.4 — una sola intervención (H2) · un clic

> **No tienes que decidir ni mirar nada.** Arrastra la foto `P1070614.JPG` al panel **Archivos**
> (icono de carpeta, a la izquierda) y pulsa **Entorno de ejecución → Ejecutar todas**. Al final se
> descarga un ZIP: **adjúntalo solo a Claude**.

Qué hace, sin intervención:

1. Instala SAM 2 **en el commit exacto** `2b90b9f5` y descarga SAM 2.1 Large. **Se detiene** si el
   commit o el checkpoint no son los congelados.
2. Encuentra la foto por su huella SHA‑256 y **se detiene** si la luma de cualquiera de los prompts
   se desvía más de 3,0 de lo registrado.
3. Ejecuta las **{calls} llamadas** del prerregistro: las semillas, la cadena ganadora de v1.3 (que
   debe salir idéntica), la misma cadena con el positivo H2 y las perturbaciones de H2.
4. Empaqueta las {masks} máscaras con un manifiesto de hashes en
   `PRAGMA_AEM1v14_<run>_PENDING_EXTERNAL_AUDIT.zip`.

**Por qué no enseña resultados:** la auditoría es **ciega y a doble llave**. No compartas capturas de
este cuaderno con ChatGPT ni con nadie: el paquete ciego lo prepara Claude.

Prerregistro: `aem1/PRERREGISTRO_A-E-menos-1_v1_4.json` (SHA‑256 del archivo `{prereg_sha}`;
`content_sha256` `{content_sha}`). Auditoría: `auditoria/PROTOCOLO_AUDITORIA_AEM1_v2.md` (rev. 1).
"""

HOWTO = """
## 0. Antes de pulsar «Ejecutar todas»

1. **Entorno de ejecución → Cambiar tipo de entorno de ejecución → GPU → L4.** Usa **L4**, como en
   las dos corridas anteriores: la comparación exige que la referencia salga idéntica bit a bit, y
   eso solo está probado en L4.
2. Arrastra `P1070614.JPG` al panel **Archivos**. Si no lo haces, la celda 2 te pedirá la foto con
   un botón **Elegir archivos**. El nombre no importa: se reconoce por su huella.
3. **Entorno de ejecución → Ejecutar todas.** Tarda unos minutos: casi todo es instalar SAM 2 y
   descargar 857 MiB. Al terminar, el navegador descarga el ZIP.

Si aparece un error en rojo, copia el texto y pégalo a Claude. No cambies nada del cuaderno.
"""

OUTRO = """
## 7. Qué hacer ahora

1. Busca el ZIP `PRAGMA_AEM1v14_…_PENDING_EXTERNAL_AUDIT.zip` en tu carpeta de descargas.
2. **Adjúntalo a Claude** en la sesión de Claude Code. No se lo mandes a ChatGPT.
3. Claude verifica la integridad sin mirar resultados, prepara el paquete ciego y te lo da. Ese
   paquete es lo único que recibe ChatGPT, sin carta.
"""


def replaced(text: str, pairs) -> str:
    for old, new in pairs:
        if old not in text:
            raise SystemExit(f"la celda de v1.3 ya no contiene {old!r}: revisar el constructor v1.4")
        text = text.replace(old, new)
    return text


def build() -> dict:
    prereg_bytes = PREREG.read_bytes()
    prereg_text = prereg_bytes.decode("utf-8")
    prereg = json.loads(prereg_text)
    if prereg["status"] != "PREREGISTERED":
        raise SystemExit("El prerregistro no está en PREREGISTERED: no se construye el cuaderno")
    prereg_sha = hashlib.sha256(prereg_bytes).hexdigest()
    counts = prereg["candidate_counts"]
    intro = (INTRO.replace("{prereg_sha}", prereg_sha).replace("{content_sha}", prereg["content_sha256"])
             .replace("{calls}", str(counts["calls"])).replace("{masks}", str(counts["total_masks"])))
    env = replaced(v13.CELL_ENV, [('WORK_DIR / "runs_v13"', 'WORK_DIR / "runs_v14"')])
    run = replaced(v13.CELL_RUN, [
        ("# Celda 5 · las 178 llamadas del prerregistro", f"# Celda 5 · las {counts['calls']} llamadas del prerregistro"),
        ('PNG_BRANCHES = ("BASE", "+POS_HAIR", "+POS_SLEEVE", "+POS_HAIR+SLEEVE", "RECIPROCAL")',
         'PNG_BRANCHES = ("BASE", "+POS_HAIR+SLEEVE", "+POS_HAIR+SLEEVE+H2")'),
        ("if number % 20 == 0", "if number % 5 == 0"),
    ])
    zip_cell = replaced(v13.CELL_ZIP, [
        ('"aem1v13_perturbaciones.npz"', '"aem1v14_perturbaciones.npz"'),
        ('"aem1v13_config.json"', '"aem1v14_config.json"'),
        ('"notebook_version": "1.3"', '"notebook_version": "1.4"'),
        ('"aem1v13_calls.json"', '"aem1v14_calls.json"'),
        ('"aem1v13_report.json"', '"aem1v14_report.json"'),
        ('p.name != "aem1v13_manifest.json"', 'p.name != "aem1v14_manifest.json"'),
        ('RUN_DIR / "aem1v13_manifest.json", manifest', 'RUN_DIR / "aem1v14_manifest.json", manifest'),
        ('[RUN_DIR / "aem1v13_manifest.json"]', '[RUN_DIR / "aem1v14_manifest.json"]'),
        ('f"PRAGMA_AEM1v13_{RUN_ID}_PENDING_EXTERNAL_AUDIT.zip"', 'f"PRAGMA_AEM1v14_{RUN_ID}_PENDING_EXTERNAL_AUDIT.zip"'),
    ])
    if "aem1v13" in zip_cell or "AEM1v13" in zip_cell:
        raise SystemExit("quedó un nombre de v1.3 en la celda del ZIP")
    cells = [
        v13.md("pragma-aem1v14-00", intro),
        v13.md("pragma-aem1v14-00b", HOWTO),
        v13.code("pragma-aem1v14-01", v13.CELL_INSTALL),
        v13.code("pragma-aem1v14-02", env),
        v13.code("pragma-aem1v14-03", v13.CELL_PREREG.format(prereg_sha=prereg_sha,
                                                             prereg_literal=json.dumps(prereg_text, ensure_ascii=False))),
        v13.code("pragma-aem1v14-04", v13.CELL_MODEL),
        v13.code("pragma-aem1v14-05", run),
        v13.code("pragma-aem1v14-06", zip_cell),
        v13.md("pragma-aem1v14-07", OUTRO),
    ]
    return {"cells": cells, "metadata": {"accelerator": "GPU", "colab": {"name": OUT.name, "provenance": []},
                                         "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                         "language_info": {"name": "python", "version": "3.x"}},
            "nbformat": 4, "nbformat_minor": 5}


def main():
    notebook = build()
    OUT.write_text(json.dumps(notebook, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("escrito:", OUT.relative_to(ROOT), "·", hashlib.sha256(OUT.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
