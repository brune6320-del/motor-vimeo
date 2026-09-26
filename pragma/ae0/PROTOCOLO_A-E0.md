# A‑E0 · Protocolo del inventario de referencia de `P1070614.JPG`

> Requisito previo: la foto en `pragma/inputs/` (se verifica por hash) y Python 3 con NumPy y
> Pillow (`pip install -r requirements.txt`). Todos los comandos, desde `pragma/`.
> Nada de lo que se genera aquí a partir de la foto va a git: se escribe en `local/`.

## Modo vigente: referencia por doble llave de IA (DEC‑024)

Desde ChatGPT 005, A‑E0 lo producen **las dos IAs** con doble llave. La persona usuaria no
fiscaliza píxeles (DEC‑018‑P).

| Quién | Hace |
|---|---|
| Persona usuaria | Ratifica la ontología v0.2 (§0), decide qué es «objeto» para el producto, resuelve solo ambigüedades semánticas irreducibles y conserva el veto |
| Claude y ChatGPT | Inventario exhaustivo, cajas y máscaras, partes y enteros, oclusión y truncamiento; auditoría mutua; adjudicación por evidencia objetiva; tercera revisión si hace falta |

**Naturaleza de la referencia.** Lo que produzcan y adjudiquen solo las IAs se etiqueta
`reference_type = AI_CONSENSUS_REFERENCE`, **nunca** `HUMAN_GT`. A‑E1 puede medirse contra ella para
ingeniería y comparación interna, declarando siempre contra qué tipo de referencia se calculó cada
métrica. Una afirmación fuerte de exactitud frente a «verdad humana» exigiría una muestra anotada o
ratificada de forma independiente por personas.

**Contra el anclaje (sustituye en parte a DEC‑015‑P).** El borrador `scene_inventory.draft.json` es
la llave de Claude. La llave de ChatGPT se hace **solo desde la foto**, sin abrir ese borrador;
después se comparan objeto a objeto.

**Contra la circularidad.** Una máscara de referencia obtenida con prompts de SAM 2 favorece a SAM 2
cuando A‑E1 mida SAM 2 AMG. Cada máscara declara su `derivation`, y A‑E1 separa las métricas por
derivación. La forma concreta de producir las máscaras de las tres personas está pendiente de
acordar con ChatGPT.

**Pendiente de implementar antes de producir A‑E0:** el esquema de `pragma_ae/inventory.py` todavía
exige `HUMAN_REVIEWED` y una firma humana para congelar. Hay que añadir `reference_type`,
`derivation` y un estado de revisión por doble llave de IA.

Las secciones 1–4 describen el modo humano (`HUMAN_GT`), que sigue disponible si la persona usuaria
lo prefiere.

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
