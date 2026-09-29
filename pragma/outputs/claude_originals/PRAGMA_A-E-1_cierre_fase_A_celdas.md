# PRAGMA · A-E(-1) · cierre honesto de Fase A

Celdas para pegar al final de `PRAGMA_Fase_A_SAM2_v4_ligero.ipynb`, con el
modelo **ya cargado** y el embedding de la imagen ya calculado. No reinstala
nada, no vuelve a descargar el checkpoint, no toca la extensión.

**Qué responde:** si SAM 2.1 Large separa a la chica de la tercera persona
cuando se le da caja y puntos negativos. Es la pregunta que dejó Fase A en
`INCONCLUSIVE`, y su respuesta cambia qué GT merece la pena pintar en A-E0.

**Coste:** ~15 min. Inferencia por prompt: 0.033 s. El resto es tu lectura.

---

## La idea: sentinelas como GT de bolsillo

Todavía no hay máscaras GT, así que "conserva parte de la tercera persona" es
una opinión. Con quince clics deja de serlo.

Declaras dos listas de puntos sobre la foto:

- **KEEP** — puntos que *deben* estar dentro de la máscara de la chica
  (pelo, cabeza, hombro, brazo, mano, torso, pierna). Son exactamente las
  zonas que el state file reporta como perdidas.
- **DROP** — puntos que *no* deben estar dentro (torso floral y cabeza de la
  tercera persona, cuadro, mesa).

Dos números objetivos por candidata:

```text
recall_sujeto = KEEP cubiertos / KEEP totales     → mide la pérdida
fuga          = DROP cubiertos / DROP totales     → mide la contaminación
```

No sustituyen al GT de A-E0. Lo anticipan por el 2% del coste, y son
reutilizables: estos mismos puntos se convierten después en la primera
validación cruzada del inventario.

---

## CELDA 1 · Leer coordenadas sobre la foto

Sin JavaScript. El selector por clic de este proyecto ya colgó 46 minutos una
vez; para quince puntos, leer de una rejilla es más rápido y no puede fallar.

```python
import matplotlib.pyplot as plt, numpy as np

fig, ax = plt.subplots(figsize=(22, 12))
ax.imshow(image)
ax.set_xticks(np.arange(0, image.shape[1], 250))
ax.set_yticks(np.arange(0, image.shape[0], 250))
ax.set_xticks(np.arange(0, image.shape[1], 50), minor=True)
ax.set_yticks(np.arange(0, image.shape[0], 50), minor=True)
ax.grid(which="major", color="lime", lw=0.8, alpha=0.9)
ax.grid(which="minor", color="lime", lw=0.3, alpha=0.4)
ax.tick_params(labelsize=7); ax.tick_params(which="minor", length=0)
ax.set_title("Lee coordenadas (x, y) en píxeles originales. "
             "Amplía la salida de la celda para afinar.", fontsize=13)
plt.tight_layout(); plt.show()
```

Amplía la imagen en Colab y anota las coordenadas. Referencia conocida: el
punto que aceptaste para la chica fue `(2588, 1785)`.

---

## CELDA 2 · Declarar sentinelas y la caja

Rellena a ojo. La precisión de ±20 px es suficiente: son sondas, no anotación.

```python
# Puntos que DEBEN quedar dentro de la chica. Cubre las zonas que se perdieron.
KEEP_CHICA = [
    # (x, y),  comentario
    (2588, 1785),   # torso  (el punto que ya aceptaste)
    (   0,    0),   # pelo
    (   0,    0),   # cabeza / cara
    (   0,    0),   # hombro
    (   0,    0),   # brazo
    (   0,    0),   # mano
    (   0,    0),   # pierna o falda
]

# Puntos que NO deben quedar dentro. La tercera persona, sobre todo.
DROP_CHICA = [
    (0, 0),   # torso floral de la tercera persona
    (0, 0),   # cabeza / cabello de la tercera persona
    (0, 0),   # hombro de la tercera persona
    (0, 0),   # cuadro del fondo
    (0, 0),   # mesa o mueble
]

# Caja envolvente de la chica en XYXY. Ajústala pegada al sujeto:
# si la caja se come a la tercera persona, el experimento no prueba nada.
BOX_CHICA = (x_min, y_min, x_max, y_max)   # <-- rellenar

assert all(p != (0, 0) for p in KEEP_CHICA + DROP_CHICA), "Faltan sentinelas."
H, W = image.shape[:2]
for x, y in KEEP_CHICA + DROP_CHICA:
    assert 0 <= x < W and 0 <= y < H, f"Punto fuera de la imagen: {(x, y)}"

# Verificación visual antes de gastar inferencia.
fig, ax = plt.subplots(figsize=(20, 11)); ax.imshow(image)
ax.add_patch(plt.Rectangle((BOX_CHICA[0], BOX_CHICA[1]),
                           BOX_CHICA[2]-BOX_CHICA[0], BOX_CHICA[3]-BOX_CHICA[1],
                           fill=False, ec="yellow", lw=3))
for x, y in KEEP_CHICA: ax.plot(x, y, "o", ms=13, mfc="lime",    mec="black", mew=2)
for x, y in DROP_CHICA: ax.plot(x, y, "X", ms=15, mfc="red",     mec="black", mew=2)
ax.set_title("Verde = debe conservarse · Rojo = debe eliminarse · Amarillo = caja")
ax.axis("off"); plt.tight_layout(); plt.show()
```

**Mira esta imagen antes de seguir.** Un sentinela mal puesto invalida los tres
experimentos y no te vas a dar cuenta después.

---

## CELDA 3 · La métrica

```python
def sentinel_report(proposal, keep_pts, drop_pts):
    filas = []
    for i, m in enumerate(proposal.masks):
        kept = sum(1 for x, y in keep_pts if m[int(round(y)), int(round(x))])
        leak = sum(1 for x, y in drop_pts if m[int(round(y)), int(round(x))])
        filas.append({
            "modalidad":     proposal.modality,
            "candidata":     i,
            "score":         round(float(proposal.scores[i]), 3),
            "area_%":        round(100.0 * float(m.mean()), 2),
            "recall_sujeto": f"{kept}/{len(keep_pts)}",
            "fuga":          f"{leak}/{len(drop_pts)}",
            "limpia":        kept == len(keep_pts) and leak == 0,
        })
    return filas

def mostrar(proposal):
    filas = sentinel_report(proposal, KEEP_CHICA, DROP_CHICA)
    print(f"\n=== {proposal.modality} · {proposal.proposal_id} ===")
    for f in filas:
        marca = "  <<< LIMPIA" if f["limpia"] else ""
        print(f"  c{f['candidata']}  score={f['score']:.3f}  area={f['area_%']:>5.2f}%  "
              f"recall={f['recall_sujeto']}  fuga={f['fuga']}{marca}")
    return filas

RESULTADOS_AE_1 = {}
```

---

## CELDA 4 · Los tres intentos

Ejecuta una por una y **mira la galería de cada una** antes de pasar a la
siguiente. Los números dicen si hubo fuga; solo el ojo dice si el borde sirve.

```python
# --- Intento 1: caja sola -------------------------------------------------
p_box = propose_with_box("chica del frente", "chica_frente", BOX_CHICA)
RESULTADOS_AE_1["box"] = mostrar(p_box)
```

```python
# --- Intento 2: caja + negativos sobre la tercera persona -----------------
# Los tres primeros DROP son la tercera persona; no metas cuadro ni mesa aquí.
p_box_neg = propose_with_box(
    "chica del frente", "chica_frente", BOX_CHICA,
    positive_points=[KEEP_CHICA[0]],
    negative_points=DROP_CHICA[:3],
)
RESULTADOS_AE_1["box+points"] = mostrar(p_box_neg)
```

```python
# --- Intento 3: punto + negativos, sin caja -------------------------------
p_pt_neg = propose_with_points(
    "chica del frente", "chica_frente",
    positive_points=[KEEP_CHICA[0]],
    negative_points=DROP_CHICA[:3],
)
RESULTADOS_AE_1["point+corrections"] = mostrar(p_pt_neg)
```

Si una candidata sale con `recall` alto y `fuga = 0/5` pero el borde se ve mal,
**refina esa y solo esa** — no vuelvas a empezar:

```python
p_ref = refine_with_click(p_box_neg, seed_candidate_index=<i>, point_label=1)  # 1 añade, 0 quita
mostrar(p_ref)
```

---

## CELDA 5 · Cerrar el veredicto de forma defendible

El objetivo **no es sacar un PASS**. Es dejar un veredicto que aguante que lo
lean dentro de seis meses.

```python
import json
print(json.dumps({
    "modalidades_probadas": {m: [f for f in v] for m, v in RESULTADOS_AE_1.items()},
    "modality_attempts":    {k: list(v) for k, v in MODALITY_ATTEMPTS["chica_frente"].items()},
}, indent=2, ensure_ascii=False))
```

Después rellena `MODALITY_REVIEWS["chica_frente"][modalidad]` para las tres
modalidades: `proposal_id` real, `result`, **todos** los `candidate_indices_reviewed`
y `notes`. Sin eso el veredicto seguirá saliendo `INCONCLUSIVE`, que es
correcto: significa que el protocolo no se agotó.

Y aplica la regla nueva — los dos criterios que ahora son calculables **no se
marcan a mano**:

```python
mejor = <la candidata elegida>
kept  = sum(1 for x, y in KEEP_CHICA if mejor[int(round(y)), int(round(x))])
leak  = sum(1 for x, y in DROP_CHICA if mejor[int(round(y)), int(round(x))])

CHECKLIST["chica_frente"]["other_people_excluded"]  = (leak == 0)
CHECKLIST["chica_frente"]["body_and_edges_complete"] = (kept == len(KEEP_CHICA))
# Los otros tres los sigues marcando tú: ninguna métrica los ve.
```

Esto cierra el agujero por el que salió el `PASS` falso: el criterio más fácil
de marcar con optimismo pasa a ser el único que no puedes marcar.

---

## Cómo leer el resultado

| Resultado | Significa | Qué cambia en A-E0 |
|---|---|---|
| Alguna candidata con `fuga=0/5` y `recall` 6-7/7 | La frontera ocluida es un **problema de prompt**, no del modelo. | El GT prioritario es el de instancias completas. La ruta interactiva funciona; el inventario es mejora de producto, no rescate. |
| `fuga=0` pero `recall` bajo en todas | SAM 2 **separa** pero **fragmenta** a esta resolución. | Pinta GT fino de pelo/mano. El problema real es el borde, y BiRefNet sube de prioridad. |
| Ninguna baja de `fuga≥1` ni con caja ni con negativos | El contacto chica / tercera persona es **irresoluble por prompt** en este modelo. | Es el primer `FAIL_COMPONENT` legítimo del proyecto. Justifica el inventario exhaustivo como camino principal, con argumento, no por intuición. |

Los tres desenlaces son útiles. Por eso vale la pena gastar los quince minutos
antes de las horas de A-E0.

---

## Fuente

- `SAM2ImagePredictor.predict(..., box=..., point_coords=..., point_labels=...)`,
  concatenación de caja y puntos en `_predict`:
  https://github.com/facebookresearch/sam2/blob/main/sam2/sam2_image_predictor.py
