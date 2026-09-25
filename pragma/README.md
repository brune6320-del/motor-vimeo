# PRAGMA · Motor de transparencia / inventario de escena

PRAGMA nació para convertir firmas escaneadas en PNG transparentes sin salir del flujo de
trabajo (extensión Chrome con motor por color e ISNet). El problema abierto es la
**segmentación por instancia**: en una foto con varias personas y objetos, elegir exactamente
qué conservar y exportarlo limpio, sin arrastrar un trozo de otra cosa.

> **Fuente de verdad:** [`PROJECT_STATE.md`](PROJECT_STATE.md) (v1.1). Léelo antes de cambiar nada.
> Este directorio convive con un proyecto no relacionado (el backend `motor-vimeo` en la raíz
> del repositorio); no lo toca.

## Estado en cinco líneas

```text
Fase A dirigida por clic (v4)   INCONCLUSIVE — el PASS histórico fue corregido por evidencia visual
A‑E(−1) diagnóstico chica       v1.1 escrito + verificado (68 Codex + 19 propias + píxeles + arnés CPU); GPU NOT_RUN
A‑E0 inventario humano          kit listo; borrador de 52 objetos DRAFT_UNVERIFIED; ontología PROPUESTA sin ratificar
A‑E1 SAM2 AMG                   métricas y gates implementados y probados con datos sintéticos; sin corrida
Fase B                          BLOQUEADA · SAM 2 todavía NO rechazable · extensión NO modificada
```

## Qué hay aquí

| Ruta | Qué es |
|---|---|
| `PROJECT_STATE.md` | Estado operativo v1.1: decisiones, pruebas, riesgos, backlog y punto de reanudación |
| `outputs/` | Artefactos Codex/Claude originales (byte a byte) + cuaderno A‑E(−1) **v1.1** y su verificación |
| `work/` | Constructores y verificadores (`*_codex.py` originales; `*_v1_1.py` nuevos) |
| `pragma_ae/` | Kit A‑E en Python (NumPy + Pillow): contrato de inventario, métricas, lámina, preflight, CLI |
| `ae0/` | Ontología propuesta, protocolo humano y `scene_inventory.draft.json` |
| `preflight/` | Informe del preflight de coordenadas de A‑E(−1) v1.0 |
| `tests/` | 22 tests (`python3 -m unittest discover -s tests`) |
| `inputs/` | **No versionado**: la foto y la extensión se colocan aquí y se verifican por SHA‑256 |
| `history/handoff_v1.0/` | Paquete de traspaso v1.0 intacto (verificable con su manifiesto original) |

## Por qué la foto no está en el repositorio

El repositorio es **público** y `P1070614.JPG` muestra a personas reales con etiquetas de
nombre visibles. La foto, la extensión y todo lo que deriva de la foto (overlays, recortes,
láminas, máscaras GT) se quedan en local (`inputs/`, `local/`, `ae0/gt/`, ignorados por git).
Las herramientas la encuentran por hash; ver [`inputs/README.md`](inputs/README.md).

## Comandos

```bash
cd pragma
pip install -r requirements.txt

# Integridad
(cd inputs && sha256sum -c INPUTS_SHA256.txt)                 # con la foto y la extensión en su sitio
sha256sum -c MANIFEST_SHA256.txt                                # árbol versionado v1.1
(cd history/handoff_v1.0 && sha256sum -c HANDOFF_MANIFEST_SHA256.txt)

# Verificación
python3 -m unittest discover -s tests
python3 work/verify_pragma_ae1_codex.py        # 68/68 sobre v1.0 (reescribe su JSON, idéntico)
python3 work/verify_pragma_ae1_v1_1.py         # v1.1: 68 + 19 + píxeles + arnés CPU (necesita la foto)

# A‑E0 (ver ae0/PROTOCOLO_A-E0.md)
python3 -m pragma_ae validate ae0/scene_inventory.draft.json
python3 -m pragma_ae sheet ae0/scene_inventory.draft.json --out local/lamina_A-E0.png
python3 -m pragma_ae preflight outputs/PRAGMA_A-E-menos-1_diagnostico_caso_chica_v1_1.ipynb
```

En macOS usa `shasum -a 256 -c` en lugar de `sha256sum -c`.

## Próxima acción única

Ejecutar **`outputs/PRAGMA_A-E-menos-1_diagnostico_caso_chica_v1_1.ipynb`** en Colab (GPU L4/A100),
confirmando la configuración **en la hoja de contactos**, ID por ID. Detalle en
`PROJECT_STATE.md` §27. En paralelo, sin GPU: ratificar `ae0/ONTOLOGIA_PROPUESTA.md`.
