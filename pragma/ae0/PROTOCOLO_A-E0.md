# A‑E0 · Protocolo del inventario humano de `P1070614.JPG`

> Requisito previo: la foto en `pragma/inputs/` (se verifica por hash) y Python 3 con NumPy y
> Pillow (`pip install -r requirements.txt`). Todos los comandos, desde `pragma/`.
> Nada de lo que se genera aquí a partir de la foto va a git: se escribe en `local/`.

## 0. Ratificar la ontología

Lee `ONTOLOGIA_PROPUESTA.md` y decide las 13 preguntas. Si aceptas las recomendaciones tal
cual, basta con decirlo; si cambias alguna, se actualiza la propuesta antes de seguir. Después,
en el inventario: `"ontology": {"ratified": true, …}`.

## 1. Pasada ciega · 10 minutos · antes de mirar el borrador

Abre solo la foto, sin lámina ni lista. Escribe en papel o en un archivo todo lo que
seleccionarías para recortar como PNG. Diez minutos, sin volver atrás.

*Por qué:* el borrador (`scene_inventory.draft.json`) lo hizo una IA mirando la foto. Si lo
lees primero, lo que falta en él tiende a faltar también en tu revisión. Tu lista ciega es la
única defensa contra ese anclaje. Ya pasó una vez: al revisar su propia lámina, el borrador
descubrió que había omitido el teléfono en la mano de la persona del frente (`ae0_050`).

## 2. Revisar el borrador con la lámina

```bash
python3 -m pragma_ae sheet ae0/scene_inventory.draft.json --out local/lamina_A-E0.png
python3 -m pragma_ae sheet ae0/scene_inventory.draft.json --out local/lamina_A-E0_AB.png --tiers A B
```

Se generan `local/lamina_A-E0.png` (cajas numeradas; amarillo = A, cian = B, rosa = C) y
`local/lamina_A-E0.md` (leyenda). Copia el borrador a `ae0/scene_inventory.json` y, objeto por
objeto:

- corrige `bbox` (coordenadas a resolución completa, semiabierta) y pon `bbox_source: "human"`;
- confirma o cambia `tier`, `occlusion`, `truncation`, `occluded_by`, `parent_id`;
- resuelve cada entrada de `review` y vacía la lista;
- añade lo que aparece en tu lista ciega y no está (`ae0_053`, `ae0_054`, …);
- los ids no se renumeran nunca, aunque borres un objeto.

Validar tantas veces como haga falta:

```bash
python3 -m pragma_ae validate ae0/scene_inventory.json
```

Cuando no haya errores, cambia `"status": "HUMAN_REVIEWED"`.

```text
BUCLE · revisión del inventario
Tipo:              producción
Objetivo:          que cada objeto del inventario sea el que tú seleccionarías
Condición de paro: validate sin errores, todas las listas `review` vacías,
                   y cada elemento de tu lista ciega está en el inventario o descartado con motivo
Cadencia:          una pasada por zona de la foto (izquierda, mesa, persona frente, pared)
Cada vuelta:       lámina → corregir JSON → validate
Al cumplirse:      status HUMAN_REVIEWED
```

## 3. Máscaras GT

Obligatorias para las **tres personas** (`gt_required: true`); para poder declarar
`PASS_PROPOSALS`, también para todos los Tier A (ver el coste y el orden por etapas en
`ONTOLOGIA_PROPUESTA.md` §6).

Formato: **PNG en escala de grises, 4000×2248, 0 = fuera, 255 = objeto**, uno por objeto, en
`ae0/gt/` (carpeta local; no se versiona porque deriva de la foto). Sirve cualquier editor que
exporte ese PNG (GIMP, Photoshop, Photopea, Krita…). Máscara **modal**: solo lo visible; lo que
tapa otra instancia no se pinta.

Para cada máscara, calcula su hash de contenido y regístralo en el inventario:

```bash
python3 - <<'EOF'
import numpy as np
from PIL import Image
from pragma_ae.masks import packed_sha256
m = np.asarray(Image.open("ae0/gt/ae0_002.png").convert("L")) > 0
print(packed_sha256(m))
EOF
```

```json
"gt_mask": {"path": "gt/ae0_002.png", "mask_sha256": "<hash>"}
```

El validador rechaza una máscara que no sea binaria, que tenga otro tamaño, cuyo hash no
coincida o que se salga de su `bbox`.

Cuidado especial en la **franja de contacto persona frente ↔ persona posterior** (cabello
recogido, hombro, O3/O4 de A‑E(−1)): es exactamente donde se mide la fuga (DEC‑013‑P/014‑P).

## 4. Congelar

```bash
python3 -m pragma_ae freeze ae0/scene_inventory.json \
  --out ae0/scene_inventory.frozen.json --frozen-by "<tu nombre o iniciales>"
python3 -m pragma_ae validate ae0/scene_inventory.frozen.json   # → A_E0_FROZEN
```

El inventario congelado sí puede versionarse (solo contiene cajas, nombres y hashes; no
transcribe texto de las etiquetas). Registra su `content_sha256` en `PROJECT_STATE.md`. Desde ese
momento es la GT de A‑E1 y **no se edita**: si hay que corregirlo, se crea una versión nueva y se
vuelve a congelar.
