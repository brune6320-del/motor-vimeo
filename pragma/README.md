# PRAGMA · Motor de transparencia / inventario de escena

PRAGMA nació para convertir firmas escaneadas en PNG transparentes sin salir del flujo de
trabajo (extensión Chrome con motor por color e ISNet). El problema abierto es la
**segmentación por instancia**: en una foto con varias personas y objetos, elegir exactamente
qué conservar y exportarlo limpio, sin arrastrar un trozo de otra cosa.

> **Fuente de verdad:** [`PROJECT_STATE.md`](PROJECT_STATE.md) (v1.7). Léelo antes de cambiar nada.
> Este directorio convive con un proyecto no relacionado (el backend `motor-vimeo` en la raíz
> del repositorio); no lo toca.

## Estado en cinco líneas

```text
Fase A dirigida por clic (v4)   INCONCLUSIVE — el PASS histórico fue corregido por evidencia visual
A‑E(−1) diagnóstico chica       v1.3 (L4): CLOSED_INCONCLUSIVE por doble llave · subproblema de separación DEMOSTRADO; segmentación completa no · v1.4 (H2) PRERREGISTRADO, espera revisión
A‑E0 inventario de referencia   DEC‑024: doble llave de IA → AI_CONSENSUS_REFERENCE; borrador de 52 objetos = llave de Claude; ontología sin ratificar
A‑E1 SAM2 AMG                   sweep prerregistrado (verificado en el commit exacto); DEC‑013‑Q adoptada; sin corrida
Revisión                        la hace la IA (auditoría + contraauditoría de ChatGPT); la persona usuaria solo veta
Fase B                          BLOQUEADA · SAM 2 todavía NO rechazable · extensión NO modificada
```

## Qué hay aquí

| Ruta | Qué es |
|---|---|
| `PROJECT_STATE.md` | Estado operativo v1.7: decisiones, pruebas, riesgos, backlog y punto de reanudación |
| `auditoria/` | Protocolos de auditoría ciega (v1 congelado; v2 para v1.3) y la auditoría de cada corrida real, con su doble llave |
| `aem1/` | A‑E(−1) v1.3 y v1.4: especificaciones y prerregistros (`python3 work/design_aem1_v1_3.py --check`, `python3 work/design_aem1_v1_4.py --check`) |
| `ae1/` | Sweep A‑E1 prerregistrado |
| `GUIA_COLAB_A-E-menos-1_v1_4.md` | **Pasos vigentes** para la corrida v1.4 (solo tras el `GO` de ChatGPT): un clic en L4, a ciegas |
| `GUIA_COLAB_A-E-menos-1_v1_3.md` | Guía de la corrida v1.3 (hecha) |
| `GUIA_COLAB_A-E-menos-1_v1_2.md` | Guía v1.2 (modo delegado con Colab CLI, que sigue valiendo) |
| `dialogo/` | Ping‑pong Claude ↔ ChatGPT: protocolo y cartas numeradas |
| `GUIA_COLAB_A-E-menos-1_v1_1.md` | Guía anterior (v1.1, con decisiones humanas); histórica |
| `CLAUDE.md` | Reglas para agentes (incluye: cerrar siempre con los pasos del usuario) |
| `outputs/` | Artefactos Codex/Claude originales (byte a byte) + cuadernos A‑E(−1) v1.1 y **v1.2** con sus verificaciones |
| `work/` | Constructores y verificadores (`*_codex.py` originales; `*_v1_1.py`, `*_v1_2.py`, `harness_aem1.py`), auditoría ciega, doble llave, diseño y desciegue v1.3, diseño y cuaderno v1.4 |
| `pragma_ae/` | Kit A‑E en Python (NumPy + Pillow): contrato de inventario, métricas, lámina, preflight, auditoría IA de ZIPs, CLI |
| `ae0/` | Ontología propuesta, protocolo humano y `scene_inventory.draft.json` |
| `preflight/` | Preflight de coordenadas: v1.0 (3 puntos mal ubicados) y v1.2 (confirmación 18/18 del auditor IA) |
| `tests/` | 86 tests (`python3 -m unittest discover -s tests`) |
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
sha256sum -c MANIFEST_SHA256.txt                                # árbol versionado
(cd history/handoff_v1.0 && sha256sum -c HANDOFF_MANIFEST_SHA256.txt)

# Verificación
python3 -m unittest discover -s tests
python3 work/verify_pragma_ae1_codex.py        # 68/68 sobre v1.0 (reescribe su JSON, idéntico)
python3 work/verify_pragma_ae1_v1_1.py         # v1.1: 68 + 19 + píxeles + arnés CPU (necesita la foto)
python3 work/verify_pragma_ae1_v1_2.py         # v1.2: 68 + 39 + píxeles + E2E simulado + auditoría (necesita la foto)
python3 -m pragma_ae audit-aem1 <ZIP de Colab>  # auditoría IA automática de una corrida real
python3 work/double_key_aem1.py --zip <ZIP>     # comparación de las dos llaves (corrida 1)
python3 work/design_aem1_v1_3.py --check       # el prerregistro v1.3 se reproduce byte a byte (necesita la foto)
python3 work/build_pragma_aem1_v1_3.py         # genera el cuaderno v1.3 desde el prerregistro
python3 work/verify_pragma_aem1_v1_3.py        # v1.3: estático + E2E con SAM simulado + auditoría (necesita la foto)
python3 work/ae1_analysis_contract.py --check  # contrato de análisis A‑E1 (borrador; se congela con A‑E0)
python3 work/unblind_aem1_v1_3.py --zip <ZIP> --mapping <mapeo sellado local>  # desciegue y doble llave v1.3
python3 work/design_aem1_v1_4.py --check       # prerregistro v1.4 byte a byte (necesita la foto y el ZIP v1.3)
python3 work/build_pragma_aem1_v1_4.py         # genera el cuaderno v1.4 desde el prerregistro
python3 work/verify_pragma_aem1_v1_4.py        # v1.4: estático + E2E con SAM simulado + auditoría (necesita la foto)

# A‑E0 (ver ae0/PROTOCOLO_A-E0.md)
python3 -m pragma_ae validate ae0/scene_inventory.draft.json
python3 -m pragma_ae sheet ae0/scene_inventory.draft.json --out local/lamina_A-E0.png
python3 -m pragma_ae preflight outputs/PRAGMA_A-E-menos-1_diagnostico_caso_chica_v1_1.ipynb
```

En macOS usa `shasum -a 256 -c` en lugar de `sha256sum -c`.

## Próxima acción única

Pegar en ChatGPT la carta [`dialogo/006_claude_a_chatgpt.md`](dialogo/006_claude_a_chatgpt.md) y
adjuntar el paquete privado `PRAGMA_carta006_prerregistro_v1_4.zip`. ChatGPT revisa el prerregistro
de A‑E(−1) v1.4 ([`aem1/ESPECIFICACION_A-E-menos-1_v1_4.md`](aem1/ESPECIFICACION_A-E-menos-1_v1_4.md))
y la DEC‑024 **antes** de ejecutar nada. Con su `GO`, la corrida sigue
[`GUIA_COLAB_A-E-menos-1_v1_4.md`](GUIA_COLAB_A-E-menos-1_v1_4.md).
