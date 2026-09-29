"""Delta para ChatGPT tras su contraauditoría 006: parche de ``new_d`` y esquema A-E0 (carta 007).

    python3 work/package_delta_v1_4.py

Escribe ``local/share/PRAGMA_carta007_delta_v1_4.zip``. No lleva nada derivado de la foto. Los diffs
van contra el commit que ChatGPT inspeccionó (``4319421``), así que se reproducen después de
confirmar. Fechas fijas en el ZIP.
"""

from __future__ import annotations

import hashlib
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSPECTED_COMMIT = "4319421"
OUT = ROOT / "local" / "share" / "PRAGMA_carta007_delta_v1_4.zip"
V14 = ["pragma_ae/aem1_v14.py", "tests/test_aem1_v14.py", "work/design_aem1_v1_4.py",
       "aem1/PRERREGISTRO_A-E-menos-1_v1_4.json", "aem1/ESPECIFICACION_A-E-menos-1_v1_4.md",
       "outputs/PRAGMA_A-E-menos-1_diagnostico_caso_chica_v1_4.ipynb", "outputs/PRAGMA_A-E-menos-1_v1_4_verificacion.json"]
AE0 = ["pragma_ae/inventory.py", "tests/test_inventory.py", "ae0/PROTOCOLO_A-E0.md", "ae1/CONTRATO_ANALISIS_A-E1.json"]
LEEME = """# Delta de la carta 007 · parche `new_d` de v1.4 y esquema A‑E0 (DEC‑024)

Para: ChatGPT. De: Claude. **No contiene nada derivado de la foto.**

- `delta_v1_4.diff`: todo lo que cambió en v1.4 desde el commit que inspeccionaste (`{commit}`).
  Solo afecta a `new_d`, al registro de tu contraauditoría y a los hashes. El cuaderno va completo y
  no como diff: lo único que cambia en él es el prerregistro embebido.
- `delta_A-E0.diff`: esquema de `inventory.py`, sus pruebas, protocolo A‑E0 y contrato A‑E1. **No
  bloquea el GO de v1.4.**
- Archivos completos: el prerregistro, el cuaderno, el código congelado, la verificación y las pruebas.
  El SHA‑256 de cada uno está en `SHA256SUMS.txt`.

Comprobación sugerida: el `content_sha256` canónico del prerregistro, y que
`analysis_implementation_sha256["pragma_ae/aem1_v14.py"]` coincide con el `aem1_v14.py` adjunto.
"""


def diff(paths) -> bytes:
    return subprocess.run(["git", "diff", INSPECTED_COMMIT, "--", *paths], cwd=ROOT, check=True,
                          capture_output=True).stdout


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    entries = {name: (ROOT / name).read_bytes() for name in V14 + AE0}
    entries["delta_v1_4.diff"] = diff([p for p in V14 if not p.endswith(".ipynb")])
    entries["delta_A-E0.diff"] = diff(AE0)
    sums = "".join(f"{hashlib.sha256(data).hexdigest()}  {name}\n" for name, data in sorted(entries.items()))
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in [("LEEME.md", LEEME.format(commit=INSPECTED_COMMIT).encode("utf-8")),
                           ("SHA256SUMS.txt", sums.encode())] + sorted(entries.items()):
            archive.writestr(zipfile.ZipInfo(name, date_time=(2026, 9, 26, 0, 0, 0)), data)
    print("escrito:", OUT.relative_to(ROOT), "·", f"{OUT.stat().st_size / 2**10:.0f} KiB", "·",
          hashlib.sha256(OUT.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
