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

**Contra la circularidad** (acordado en ChatGPT 006). Una máscara de referencia obtenida con prompts
de SAM 2 favorecería a SAM 2 cuando A‑E1 mida SAM 2 AMG. Por eso:

- **Derivación principal:** `AI_POLYGON_RASTER` o `AI_POLYGON_CLASSICAL_REFINEMENT`. Cada IA traza,
  por su cuenta y desde la foto, el polígono modal de cada persona, sin ver el de la otra.
  - Se rasteriza a 4000×2248.
  - Opcionalmente se refina con un método determinista que solo use píxeles (graph‑cut, GrabCut o
    ajuste a bordes en una banda de frontera), **sin SAM 2**.
  - Se conservan la máscara cruda y la refinada.
- **Comparación:** las dos llaves se comparan por IoU y diferencia de frontera, y solo se adjudican las
  regiones en discrepancia.
- **SAM 2:** una máscara `SAM2_ASSISTED` puede existir como comparación, pero es **secundaria y no
  bloqueante**. El validador la rechaza como referencia en el modo de doble llave.
- **Pelo y contacto:** si el trazado no alcanza la precisión suficiente, esas zonas se marcan con
  incertidumbre o se excluyen de cualquier afirmación de exactitud de borde. No se finge una GT
  perfecta.

**Esquema (ya implementado en `pragma_ae/inventory.py`).**

- **Estado:** `AI_DOUBLE_KEY_REVIEWED`, que congela como `AI_CONSENSUS_REFERENCE`.
- **Obligatorio en este modo:**
  - `double_key.keys`: dos auditores distintos, cada uno con el `inventory_sha256` de su llave;
  - `ontology.ratified_by`: la persona usuaria;
  - `gt_mask.derivation` en cada máscara.
- **Excepción humana:** solo una máscara con `human_ratified` (y `human_ratified_by`) cuenta como
  `HUMAN_GT`.

**Orden (ChatGPT 006 §8):**

1. La persona usuaria ratifica la ontología v0.2. Antes de eso **no se produce ni se congela** A‑E0.
2. Claude hace la llave 1 desde su borrador.
3. ChatGPT hace la llave 2 desde la foto, sin ver ese borrador.
4. Se comparan y se adjudica.

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
