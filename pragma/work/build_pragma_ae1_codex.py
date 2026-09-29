import copy
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "outputs" / "PRAGMA_Fase_A_SAM2_v4_ligero.ipynb"
OUT = ROOT / "outputs" / "PRAGMA_A-E-menos-1_diagnostico_caso_chica_Codex.ipynb"

BASE_SHA256 = "757e9722aa98a4d9420fdca4f287ef36fe78d7b09e2b9e12b3be6896e76e814a"
CLAUDE_AEM1_SHA256 = "7e832ff61d28077612b9c4cabc4274669b09884f06ab340653e4cc259ace4e91"
CLAUDE_V4_PATCH_SHA256 = "d5c05f4c2c02026e8ef34baec11b606c28bc1d6f3ae71d643b028548845fe722"


def source_lines(text: str):
    return text.strip("\n").splitlines(True) + (["\n"] if text.endswith("\n") else [])


def markdown(cell_id: str, text: str):
    return {
        "cell_type": "markdown",
        "id": cell_id,
        "metadata": {},
        "source": source_lines(text),
    }


def code(cell_id: str, text: str, *, form=False):
    metadata = {"cellView": "form"} if form else {}
    return {
        "cell_type": "code",
        "execution_count": None,
        "id": cell_id,
        "metadata": metadata,
        "outputs": [],
        "source": source_lines(text),
    }


def base_code(nb, index: int, cell_id: str, replacements=()):
    text = "".join(nb["cells"][index]["source"])
    for old, new in replacements:
        if old not in text:
            raise RuntimeError(f"No se encontró el bloque esperado en la celda {index}: {old[:80]!r}")
        text = text.replace(old, new)
    return code(cell_id, text)


nb_base = json.loads(BASE.read_text(encoding="utf-8"))

cells = [
    markdown(
        "pragma-aem1-00",
        f"""# PRAGMA · A‑E(−1) — diagnóstico controlado del caso chica

Este cuaderno de **Codex** traslada la idea útil del documento de Claude a un experimento completo, reproducible y sin JavaScript interactivo.

**Pregunta acotada:** ¿SAM 2.1 Large puede separar a la chica del frente de la tercera persona situada detrás, usando punto, caja y correcciones negativas?

**Lo que este cuaderno no afirma:** no demuestra que SAM 2 reconozca “todos los objetos”, no sustituye el inventario A‑E0, no prueba matting de pelo y no desbloquea la Fase B por sí solo.

- Foto de aceptación: `P1070614.JPG` · 4000×2248 · SHA‑256 `8f6e3b…529d`.
- Base Codex v4 ligero: SHA‑256 `{BASE_SHA256}`.
- Entrada Claude A‑E(−1): SHA‑256 `{CLAUDE_AEM1_SHA256}`.
- Parche Claude v4: archivado como antecedente; no se aplica sobre v4 porque fue escrito contra v3.

El resultado final usa estados conservadores: `PENDING_*`, `SEPARATION_DEMONSTRATED_UNDER_FIXED_AEM1_PROTOCOL` o `INCONCLUSIVE_SELECTED_OUTPUT_FAILED`. Una salida fallida no se presenta como fallo de las otras siete. El proyecto general permanece `INCONCLUSIVE_A_E0_REQUIRED` y `phase_b_blocked=true`.
""",
    ),
    markdown(
        "pragma-aem1-01",
        """## 0. Cómo usarlo

1. En Colab selecciona **GPU L4** o **A100**; T4 también funciona con fp16.  
2. Ejecuta las celdas en orden. La primera vez, instalación + checkpoint suelen dominar el tiempo; cada celda imprime sus segundos reales.  
3. Confirma visualmente la caja y los puntos prellenados. No hay selector JavaScript: se elimina el mecanismo que antes dejó el kernel esperando un panel invisible.  
4. Mira las galerías de `point` y `box`; elige manualmente una semilla 0, 1 o 2 para cada una. Nunca se usa `argmax`.  
5. Ejecuta las dos correcciones iterativas. Después elige el protocolo/candidata que realmente se vea mejor y completa la revisión visual.  
6. Descarga el ZIP auditado.

Si Brave no abre el selector de subida, **detén esa celda**, usa el panel **Archivos** de Colab, sube la foto como `/content/P1070614.JPG` y reejecuta la sección 2. Si la descarga queda girando, **detén la celda después de que imprima `ZIP_PATH`** y descarga ese archivo desde el panel; el ZIP ya quedó escrito y verificado.

Los sentinelas son **falsadores**: un punto perdido o contaminado demuestra un defecto local. Que todos pasen solo habilita la revisión visual; jamás genera PASS automáticamente.
""",
    ),
    markdown(
        "pragma-aem1-02m",
        """## 1. Instalar SAM 2 oficial y descargar SAM 2.1 Large

Se usa el repositorio oficial de Meta. El commit exacto y el hash del checkpoint quedan registrados en el informe. En una sesión nueva, esta etapa puede tardar varios minutos por red; si el entorno conserva los archivos, se reutilizan.
""",
    ),
    base_code(
        nb_base,
        4,
        "pragma-aem1-02",
        replacements=((
            '[sys.executable, "-m", "pip", "install", "-q", "-e", ".[notebooks]"]',
            '[sys.executable, "-m", "pip", "install", "-q", "-e", "."]',
        ),),
    ),
    markdown(
        "pragma-aem1-03m",
        """## 2. Verificar hardware y fotografía

La precisión se decide por capacidad real: T4→fp16, Ampere o posterior→bf16 y CPU→fp32. La fotografía se acepta por contenido, no por nombre. Se solicita una sola vez si Colab aún no la tiene.
""",
    ),
    base_code(nb_base, 6, "pragma-aem1-03"),
    markdown(
        "pragma-aem1-04m",
        """## 3. Contratos modulares

El pipeline mantiene las interfaces `detector → selector → generador de máscara → refinador → compositor`. En este diagnóstico el selector es una configuración estática validada; no se instala YOLO‑seg, BiRefNet ni ningún servicio local.
""",
    ),
    base_code(nb_base, 8, "pragma-aem1-04"),
    markdown(
        "pragma-aem1-05m",
        """## 4. Cargar el modelo, preparar una vez la imagen y ejecutar smoke test

SAM calcula una sola vez el embedding de la foto y después responde a varios prompts. El smoke comprueba forma, finitud, contenido y que el punto toca al menos una máscara; no elige una candidata.
""",
    ),
    base_code(
        nb_base,
        12,
        "pragma-aem1-05",
        replacements=(
            (
                "pipeline=SegmentationPipeline(detector,ClickSelector(90),SAM2MaskGenerator(predictor),IdentityRefiner(),AlphaCompositor())",
                "pipeline=SegmentationPipeline(detector,None,SAM2MaskGenerator(predictor),IdentityRefiner(),AlphaCompositor())",
            ),
            (
                '''    def prepare(self,image):
        synchronize(); start=time.perf_counter()
        with torch.inference_mode(),inference_precision(): self.predictor.set_image(image)
        synchronize(); return time.perf_counter()-start
''',
                '''    def prepare(self,image):
        synchronize(); start=time.perf_counter()
        try:
            with torch.inference_mode(),inference_precision(): self.predictor.set_image(image)
        except torch.cuda.OutOfMemoryError as exc:
            if DEVICE == "cuda": torch.cuda.empty_cache()
            raise RuntimeError("FAIL_ENVIRONMENT: OOM durante el embedding. Usa L4/A100 o CPU; no se degradará a Small.") from exc
        synchronize(); return time.perf_counter()-start
''',
            ),
            (
                '''        with torch.inference_mode(),inference_precision():
            hr_logits,scores,low_res=self.predictor.predict(
                point_coords=prompts.points if prompts is not None else None,
                point_labels=prompts.labels if prompts is not None else None,
                box=box,mask_input=mask_input,multimask_output=multimask_output,
                return_logits=True,
            )
''',
                '''        try:
            with torch.inference_mode(),inference_precision():
                hr_logits,scores,low_res=self.predictor.predict(
                    point_coords=prompts.points if prompts is not None else None,
                    point_labels=prompts.labels if prompts is not None else None,
                    box=box,mask_input=mask_input,multimask_output=multimask_output,
                    return_logits=True,
                )
        except torch.cuda.OutOfMemoryError as exc:
            if DEVICE == "cuda": torch.cuda.empty_cache()
            raise RuntimeError("FAIL_ENVIRONMENT: OOM durante el prompt. Reduce carga del entorno o usa L4/A100; no se degradará a Small.") from exc
''',
            ),
        ),
    ),
    markdown(
        "pragma-aem1-06m",
        """## 5. Configuración fija y sentinelas holdout

Los puntos azules/rojos son **prompts** enviados al modelo. Los verdes/magenta/cian son **holdout** y nunca se envían a SAM: sirven únicamente para examinar la salida. Así se evita medir el modelo en los mismos píxeles que recibió como orden.

La caja envuelve a la chica y, por la oclusión real, intersecta parcialmente a la persona detrás. Eso es deliberado: las correcciones negativas deben resolver la ambigüedad. Revisa el overlay y marca `AEM1_CONFIG_CONFIRMADA=True` solo si cada etiqueta cae en la región indicada.

Después de generar baselines no reejecutes las secciones 5–6 salvo que quieras invalidar y repetir todas las propuestas.
""",
    ),
    code(
        "pragma-aem1-06",
        f'''from dataclasses import asdict
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

CODEX_AEM1_SCHEMA_VERSION = "1.0.0"
BASE_NOTEBOOK_SHA256 = "{BASE_SHA256}"
CLAUDE_AEM1_SOURCE_SHA256 = "{CLAUDE_AEM1_SHA256}"
CLAUDE_V4_PATCH_SHA256 = "{CLAUDE_V4_PATCH_SHA256}"

@dataclass(frozen=True)
class SentinelSpec:
    sentinel_id: str
    xy: tuple
    group: str
    description: str

PROMPT_POSITIVE = [SentinelSpec("P+1", (2588, 1785), "prompt_positive", "torso de la chica")]
PROMPT_NEGATIVE_OTHER_PERSON = [
    SentinelSpec("P-1", (2350, 900), "prompt_negative_other_person", "torso floral posterior"),
    SentinelSpec("P-2", (2600, 400), "prompt_negative_other_person", "cabello/cabeza posterior"),
    SentinelSpec("P-3", (2450, 700), "prompt_negative_other_person", "hombro posterior"),
]

# HOLDOUT: coordenadas distintas de los prompts.
HOLDOUT_KEEP_SUBJECT = [
    SentinelSpec("K1", (2835, 635), "keep_subject", "cara"),
    SentinelSpec("K2", (2730, 650), "keep_subject", "cabello frontal"),
    SentinelSpec("K3", (2435, 1135), "keep_subject", "hombro/ropa izquierda"),
    SentinelSpec("K4", (3185, 985), "keep_subject", "mano levantada"),
    SentinelSpec("K5", (3285, 1335), "keep_subject", "manga/brazo derecho"),
    SentinelSpec("K6", (2235, 1935), "keep_subject", "mano que cuelga"),
    SentinelSpec("K7", (2785, 2035), "keep_subject", "torso inferior"),
]
HOLDOUT_DROP_OTHER_PERSON = [
    SentinelSpec("O1", (2460, 860), "drop_other_person", "ropa floral posterior"),
    SentinelSpec("O2", (2680, 300), "drop_other_person", "cabello posterior superior"),
    SentinelSpec("O3", (2680, 520), "drop_other_person", "cabello posterior central"),
    SentinelSpec("O4", (2335, 1035), "drop_other_person", "manga/torso posterior"),
]
HOLDOUT_DROP_BACKGROUND = [
    SentinelSpec("B1", (2185, 435), "drop_background", "cuadro"),
    SentinelSpec("B2", (1735, 1635), "drop_background", "mesa/mantel"),
    SentinelSpec("B3", (3485, 1485), "drop_background", "sofá/fondo"),
]

BOX_CHICA_XYXY = (2100, 300, 3500, 2247)
PATCH_RADIUS = 6
KEEP_MIN_COVERAGE = 0.80
DROP_MAX_COVERAGE = 0.20
AEM1_CONFIG_CONFIRMADA = False # @param {{type:"boolean"}}

ALL_SPECS = (PROMPT_POSITIVE + PROMPT_NEGATIVE_OTHER_PERSON + HOLDOUT_KEEP_SUBJECT +
             HOLDOUT_DROP_OTHER_PERSON + HOLDOUT_DROP_BACKGROUND)

def checked_xy(xy, width, height):
    if len(xy) != 2 or not np.isfinite(xy).all():
        raise ValueError(f"Coordenada inválida: {{xy}}")
    x, y = (int(round(float(v))) for v in xy)
    if not (0 <= x < width and 0 <= y < height):
        raise ValueError(f"Coordenada fuera de imagen tras redondear: {{xy}} → {{(x, y)}}")
    return x, y

H, W = image.shape[:2]
for spec in ALL_SPECS:
    checked_xy(spec.xy, W, H)
rounded = [checked_xy(spec.xy, W, H) for spec in ALL_SPECS]
assert len(rounded) == len(set(rounded)), "Prompts y holdouts deben ser disjuntos."
x1, y1, x2, y2 = map(float, BOX_CHICA_XYXY)
assert np.isfinite([x1, y1, x2, y2]).all() and 0 <= x1 < x2 <= W and 0 <= y1 < y2 <= H

AEM1_CONFIG = {{
    "schema_version": CODEX_AEM1_SCHEMA_VERSION,
    "image_sha256": IMAGE_SHA256,
    "target": "chica_frente",
    "box_xyxy": list(BOX_CHICA_XYXY),
    "prompt_positive": [asdict(v) for v in PROMPT_POSITIVE],
    "prompt_negative_other_person": [asdict(v) for v in PROMPT_NEGATIVE_OTHER_PERSON],
    "holdout_keep_subject": [asdict(v) for v in HOLDOUT_KEEP_SUBJECT],
    "holdout_drop_other_person": [asdict(v) for v in HOLDOUT_DROP_OTHER_PERSON],
    "holdout_drop_background": [asdict(v) for v in HOLDOUT_DROP_BACKGROUND],
    "patch_radius": PATCH_RADIUS,
    "keep_min_coverage": KEEP_MIN_COVERAGE,
    "drop_max_coverage": DROP_MAX_COVERAGE,
    "interpretation_scope": "muestras holdout locales; no equivalen a máscara GT ni prueban ausencia global de fuga",
}}
_AEM1_PREVIOUS_CONFIG_DIGEST = globals().get("AEM1_CONFIG_DIGEST")
AEM1_CONFIG_DIGEST = hashlib.sha256(
    json.dumps(AEM1_CONFIG, sort_keys=True, ensure_ascii=False).encode("utf-8")
).hexdigest()
if _AEM1_PREVIOUS_CONFIG_DIGEST is not None and _AEM1_PREVIOUS_CONFIG_DIGEST != AEM1_CONFIG_DIGEST:
    globals().get("AEM1_PROPOSALS", {{}}).clear()
    if "invalidate_aem1_review" in globals():
        invalidate_aem1_review("La configuración cambió; las propuestas anteriores quedaron caducas.")

@dataclass(frozen=True)
class AEM1PromptBundle:
    protocol: str
    prompts: Optional[PromptSet]
    box_xyxy: Optional[np.ndarray]

class FixedProtocolSelector:
    """Selector intercambiable: traduce un protocolo nombrado a prompts/caja validados."""
    def __init__(self, positive_specs, negative_specs, box_xyxy):
        self.positive_specs = list(positive_specs)
        self.negative_specs = list(negative_specs)
        self.box_xyxy = np.asarray(box_xyxy, np.float32).reshape(4)

    def select_protocol(self, protocol):
        positive = [list(v.xy) for v in self.positive_specs]
        corrected_points = [list(v.xy) for v in self.positive_specs + self.negative_specs]
        corrected_labels = [1]*len(self.positive_specs) + [0]*len(self.negative_specs)
        if protocol == "point":
            return AEM1PromptBundle(protocol, PromptSet(positive, [1]*len(positive)), None)
        if protocol == "box":
            return AEM1PromptBundle(protocol, None, self.box_xyxy.copy())
        if protocol == "point+corrections":
            return AEM1PromptBundle(protocol, PromptSet(corrected_points, corrected_labels), None)
        if protocol == "box+corrections":
            return AEM1PromptBundle(protocol, PromptSet(corrected_points, corrected_labels), self.box_xyxy.copy())
        raise KeyError(f"Protocolo desconocido: {{protocol}}")

    def select(self, image, subject, detections):
        # Cumple el contrato Selector; en este experimento `subject` es la clave del protocolo.
        return self.select_protocol(subject)

AEM1_SELECTOR = FixedProtocolSelector(PROMPT_POSITIVE, PROMPT_NEGATIVE_OTHER_PERSON, BOX_CHICA_XYXY)
pipeline.selector = AEM1_SELECTOR

def write_json(path, payload):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)
    return path

CONFIG_JSON_PATH = write_json(RUN_DIR / "aem1_config.json", {{
    "config_digest": AEM1_CONFIG_DIGEST,
    "config": AEM1_CONFIG,
}})
CONFIG_OVERLAY_PATH = RUN_DIR / "aem1_config_overlay.png"

fig, ax = plt.subplots(figsize=(22, 12))
ax.imshow(image)
ax.add_patch(Rectangle((x1, y1), x2-x1, y2-y1, fill=False, ec="yellow", lw=3))
styles = {{
    "prompt_positive": dict(marker="*", color="blue", s=180),
    "prompt_negative_other_person": dict(marker="X", color="red", s=130),
    "keep_subject": dict(marker="o", color="lime", s=95),
    "drop_other_person": dict(marker="X", color="magenta", s=105),
    "drop_background": dict(marker="s", color="cyan", s=95),
}}
for spec in ALL_SPECS:
    style = styles[spec.group]
    ax.scatter([spec.xy[0]], [spec.xy[1]], edgecolors="black", linewidths=1.2, **style)
    ax.text(spec.xy[0]+18, spec.xy[1]-18, spec.sentinel_id, color=style["color"],
            fontsize=10, weight="bold", bbox=dict(facecolor="black", alpha=.55, pad=1))
ax.set_xticks(np.arange(0, W+1, 500)); ax.set_yticks(np.arange(0, H+1, 250))
ax.grid(color="white", lw=.35, alpha=.35)
ax.set_xlim(0, W); ax.set_ylim(H, 0)
ax.set_title("CONFIRMA: azul=prompt + · rojo=prompts − · verde=KEEP holdout · magenta=otra persona holdout · cian=fondo holdout")
fig.tight_layout(); fig.savefig(CONFIG_OVERLAY_PATH, dpi=160, bbox_inches="tight"); plt.show(); plt.close(fig)

print("\\nID   grupo                         coordenada       descripción")
print("-"*88)
for spec in ALL_SPECS:
    print(f"{{spec.sentinel_id:<4}} {{spec.group:<29}} {{str(spec.xy):<16}} {{spec.description}}")
print("\\nCaja XYXY:", BOX_CHICA_XYXY, "· config_digest:", AEM1_CONFIG_DIGEST)

AEM1_CONFIG_READY = bool(AEM1_CONFIG_CONFIRMADA)
if AEM1_CONFIG_READY:
    print("CONFIGURACIÓN CONFIRMADA. Continúa con los baselines.")
else:
    print("PENDIENTE: revisa el overlay y la tabla. Si algo cae mal, no edites a ciegas: guarda captura y devuélvela a Codex.")
    print("Si todo coincide, marca AEM1_CONFIG_CONFIRMADA=True y reejecuta esta celda.")
''',
        form=True,
    ),
    markdown(
        "pragma-aem1-07m",
        """## 6. Métrica conservadora y evidencias

Cada sentinela se evalúa en un pequeño parche, no en un único píxel. Se guardan fracciones numéricas, el identificador de propuesta, la candidata, los prompts, el origen y los hashes de las imágenes. Una máscara puede superar todos los sentinelas y aun tener contaminación entre ellos; por eso `sentinel_screen_pass` nunca se convierte por sí solo en veredicto humano.
""",
    ),
    code(
        "pragma-aem1-07",
        '''@dataclass
class AEM1Proposal:
    proposal_id: str
    protocol: str
    config_digest: str
    prompts: Optional[PromptSet]
    box_xyxy: Optional[np.ndarray]
    masks: np.ndarray
    scores: np.ndarray
    low_res_logits: np.ndarray
    inference_s: float
    evidence_render_s: float
    parent_proposal_id: Optional[str]
    seed_candidate_index: Optional[int]
    candidate_metrics: list = field(default_factory=list)
    alpha_paths: list = field(default_factory=list)
    gallery_path: Optional[str] = None

AEM1_PROPOSALS = {}
AEM1_PROTOCOLS_COMPLETE = False
AEM1_SELECTED_EVIDENCE = []
AEM1_SELECTION = None
AEM1_CASE_STATUS = "PENDING_REVIEW"

def invalidate_aem1_review(reason):
    global AEM1_SELECTED_EVIDENCE, AEM1_SELECTION, AEM1_CASE_STATUS, AEM1_PROTOCOLS_COMPLETE
    AEM1_SELECTED_EVIDENCE = []
    AEM1_SELECTION = None
    AEM1_CASE_STATUS = "PENDING_REVIEW"
    AEM1_PROTOCOLS_COMPLETE = False
    print("REVISIÓN INVALIDADA:", reason)

def derive_aem1_case_status(config_ready, protocols_complete, selection_present,
                            review_complete, review_bound, visual_checks,
                            sentinel_screen_pass, notes):
    if not config_ready:
        return "PENDING_CONFIG"
    if not protocols_complete:
        return "PENDING_PROTOCOLS"
    if not selection_present or not review_complete:
        return "PENDING_REVIEW"
    if not review_bound:
        return "PENDING_REVIEW_BINDING"
    if not all(visual_checks) and not str(notes).strip():
        return "PENDING_NOTES"
    if sentinel_screen_pass and all(visual_checks):
        return "SEPARATION_DEMONSTRATED_UNDER_FIXED_AEM1_PROTOCOL"
    return "INCONCLUSIVE_SELECTED_OUTPUT_FAILED"

assert derive_aem1_case_status(False, True, True, True, True, [True]*4, True, "") == "PENDING_CONFIG"
assert derive_aem1_case_status(True, False, True, True, True, [True]*4, True, "") == "PENDING_PROTOCOLS"
assert derive_aem1_case_status(True, True, True, False, False, [True]*4, True, "") == "PENDING_REVIEW"
assert derive_aem1_case_status(True, True, True, True, False, [True]*4, True, "") == "PENDING_REVIEW_BINDING"

def checkerboard(h, w, tile=24):
    yy, xx = np.indices((h, w)); board = ((xx//tile + yy//tile) % 2)[..., None]
    return np.where(board, 210, 245).astype(np.uint8).repeat(3, axis=2)

def matte_on_checker(rgb, matte):
    m = np.clip(np.asarray(matte, np.float32), 0, 1)[..., None]
    return np.rint(rgb*m + checkerboard(*rgb.shape[:2])*(1-m)).astype(np.uint8)

def preview_on_checker(rgb, matte, max_side=1400):
    h, w = rgb.shape[:2]
    scale = min(1.0, float(max_side) / max(h, w))
    if scale < 1.0:
        size = (max(1, int(round(w*scale))), max(1, int(round(h*scale))))
        rgb = np.asarray(Image.fromarray(np.asarray(rgb, np.uint8)).resize(size, Image.Resampling.LANCZOS))
        matte_u8 = np.asarray(matte, np.uint8) * 255
        matte = np.asarray(Image.fromarray(matte_u8).resize(size, Image.Resampling.NEAREST), np.float32) / 255.0
    return matte_on_checker(rgb, matte)

def binary_preview(matte, max_side=1400):
    h, w = matte.shape[:2]
    scale = min(1.0, float(max_side) / max(h, w))
    matte_u8 = np.asarray(matte, np.uint8) * 255
    if scale < 1.0:
        size = (max(1, int(round(w*scale))), max(1, int(round(h*scale))))
        matte_u8 = np.asarray(Image.fromarray(matte_u8).resize(size, Image.Resampling.NEAREST))
    return matte_u8

def patch_coverage(mask, xy, radius=PATCH_RADIUS):
    x, y = checked_xy(xy, mask.shape[1], mask.shape[0])
    x0, x1 = max(0, x-radius), min(mask.shape[1], x+radius+1)
    y0, y1 = max(0, y-radius), min(mask.shape[0], y+radius+1)
    return float(np.asarray(mask[y0:y1, x0:x1], dtype=np.float32).mean())

def evaluate_sentinel_groups(mask, groups, radius, keep_min, drop_max):
    coverage = {group: {s.sentinel_id: patch_coverage(mask, s.xy, radius) for s in specs}
                for group, specs in groups.items()}
    missed_keep = [key for key, value in coverage["keep_subject"].items() if value < keep_min]
    leaked_other = [key for key, value in coverage["drop_other_person"].items() if value > drop_max]
    leaked_background = [key for key, value in coverage["drop_background"].items() if value > drop_max]
    screen_pass = not (missed_keep or leaked_other or leaked_background)
    return {
        "coverage": coverage,
        "keep_hits": len(groups["keep_subject"])-len(missed_keep),
        "keep_total": len(groups["keep_subject"]),
        "other_person_clean": len(groups["drop_other_person"])-len(leaked_other),
        "other_person_total": len(groups["drop_other_person"]),
        "background_clean": len(groups["drop_background"])-len(leaked_background),
        "background_total": len(groups["drop_background"]),
        "missed_keep_ids": missed_keep,
        "leaked_other_person_ids": leaked_other,
        "leaked_background_ids": leaked_background,
        "sentinel_screen_pass": screen_pass,
        "warning": "PASS de sentinelas no equivale a PASS visual ni a IoU contra GT.",
    }

def evaluate_candidate(mask):
    groups = {
        "keep_subject": HOLDOUT_KEEP_SUBJECT,
        "drop_other_person": HOLDOUT_DROP_OTHER_PERSON,
        "drop_background": HOLDOUT_DROP_BACKGROUND,
    }
    return evaluate_sentinel_groups(mask, groups, PATCH_RADIUS, KEEP_MIN_COVERAGE, DROP_MAX_COVERAGE)

def prompt_payload(prompts):
    if prompts is None:
        return {"points": [], "labels": []}
    return {"points": prompts.points.tolist(), "labels": prompts.labels.tolist()}

def save_aem1_evidence(proposal):
    render_start = time.perf_counter()
    rows = []
    proposal.alpha_paths = []
    for index, mask in enumerate(proposal.masks):
        metrics = evaluate_candidate(mask)
        metrics.update({
            "proposal_id": proposal.proposal_id,
            "protocol": proposal.protocol,
            "config_digest": proposal.config_digest,
            "candidate_index": index,
            "predicted_iou": float(proposal.scores[index]),
            "area_fraction": float(np.asarray(mask, bool).mean()),
        })
        alpha_path = RUN_DIR / f"{proposal.proposal_id}_c{index}_alpha.png"
        Image.fromarray(np.asarray(mask, np.uint8)*255).save(alpha_path)
        reopened = Image.open(alpha_path)
        assert reopened.mode == "L" and reopened.size == image_pil.size
        proposal.alpha_paths.append(str(alpha_path)); rows.append(metrics)
    proposal.candidate_metrics = rows

    fig, axes = plt.subplots(2, len(proposal.masks), figsize=(6*len(proposal.masks), 11), squeeze=False)
    for index, (mask, row) in enumerate(zip(proposal.masks, rows)):
        axes[0, index].imshow(preview_on_checker(image, mask))
        axes[0, index].set_title(f"CANDIDATA {index} · score={row['predicted_iou']:.3f} · área={100*row['area_fraction']:.2f}%")
        axes[0, index].axis("off")
        axes[1, index].imshow(binary_preview(mask), cmap="gray", vmin=0, vmax=255)
        verdict = "SCREEN OK" if row["sentinel_screen_pass"] else "REVISAR"
        detail = (f"KEEP {row['keep_hits']}/{row['keep_total']} · otra persona {row['other_person_clean']}/{row['other_person_total']} limpia · "
                  f"fondo {row['background_clean']}/{row['background_total']} limpio")
        axes[1, index].set_title(f"{verdict}\\n{detail}")
        axes[1, index].axis("off")
    fig.suptitle(f"{proposal.protocol} · {proposal.proposal_id} · ELIGE POR CONTENIDO, NO POR SCORE")
    fig.tight_layout()
    gallery_path = RUN_DIR / f"{proposal.proposal_id}_galeria.png"
    fig.savefig(gallery_path, dpi=165, bbox_inches="tight"); plt.show(); plt.close(fig)
    proposal.gallery_path = str(gallery_path)
    proposal.evidence_render_s = time.perf_counter() - render_start

def generate_aem1(protocol, prompts=None, box=None, mask_input=None, multimask_output=True,
                 parent_proposal_id=None, seed_candidate_index=None):
    generated = pipeline.generator.generate(
        prompts=prompts,
        box=None if box is None else np.asarray(box, np.float32),
        mask_input=mask_input,
        multimask_output=multimask_output,
    )
    proposal = AEM1Proposal(
        proposal_id=f"aem1_{protocol.replace('+','_')}_{uuid.uuid4().hex[:8]}",
        protocol=protocol,
        config_digest=AEM1_CONFIG_DIGEST,
        prompts=prompts,
        box_xyxy=None if box is None else np.asarray(box, np.float32),
        masks=generated.masks,
        scores=generated.scores,
        low_res_logits=generated.low_res_logits,
        inference_s=generated.inference_s,
        evidence_render_s=0.0,
        parent_proposal_id=parent_proposal_id,
        seed_candidate_index=seed_candidate_index,
    )
    save_aem1_evidence(proposal)
    AEM1_PROPOSALS[protocol] = proposal
    print(f"{protocol}: {len(proposal.masks)} candidata(s) · inferencia {proposal.inference_s:.4f} s")
    return proposal

# Prueba que impide convertir sentinelas limpios en limpieza global.
_synthetic = np.zeros((80, 80), bool)
_synthetic[20:60, 20:60] = True
_synthetic[5:12, 5:12] = True  # isla de fuga deliberada, fuera de cualquier muestra
_synthetic_groups = {
    "keep_subject": [SentinelSpec("SK", (40, 40), "keep_subject", "interior")],
    "drop_other_person": [SentinelSpec("SO", (70, 20), "drop_other_person", "limpio")],
    "drop_background": [SentinelSpec("SB", (70, 70), "drop_background", "limpio")],
}
_synthetic_result = evaluate_sentinel_groups(_synthetic, _synthetic_groups, radius=1, keep_min=.8, drop_max=.2)
assert _synthetic_result["sentinel_screen_pass"] and _synthetic[5:12, 5:12].any()
print("SELF-TEST PASS: los sentinelas producen diagnóstico local; el código no los eleva a PASS visual.")
''',
    ),
    markdown(
        "pragma-aem1-08m",
        """## 7. Baselines ambiguos: punto y caja

Se conservan las tres máscaras de cada prompt ambiguo. Inspecciona las seis vistas y decide qué índice representa mejor al objeto completo. Los scores son diagnósticos; no seleccionan por ti.
""",
    ),
    code(
        "pragma-aem1-08",
        '''if not AEM1_CONFIG_READY:
    print("PENDIENTE: confirma primero la configuración de la sección 5.")
else:
    # Una nueva ejecución de baselines invalida correcciones previas en RAM.
    invalidate_aem1_review("Se regeneraron los baselines; vuelve a revisar semillas y salida final.")
    AEM1_PROPOSALS.clear()
    point_bundle = pipeline.selector.select(image, "point", pipeline.detections)
    box_bundle = pipeline.selector.select(image, "box", pipeline.detections)
    proposal_point = generate_aem1(point_bundle.protocol, prompts=point_bundle.prompts, box=point_bundle.box_xyxy, multimask_output=True)
    proposal_box = generate_aem1(box_bundle.protocol, prompts=box_bundle.prompts, box=box_bundle.box_xyxy, multimask_output=True)
    print("Mira ambas galerías. En la siguiente celda indica la mejor semilla 0, 1 o 2 de cada una.")
''',
    ),
    markdown(
        "pragma-aem1-09m",
        """## 8. Correcciones iterativas reales

Selecciona manualmente una semilla de cada galería. Las correcciones reutilizan sus logits de 256×256 mediante `mask_input` y usan `multimask_output=False`, tal como permite la API oficial para prompts múltiples menos ambiguos. Si no has inspeccionado las semillas, deja la confirmación desmarcada: la celda queda en PENDING sin inferir.
""",
    ),
    code(
        "pragma-aem1-09",
        '''AEM1_POINT_SEED_INDEX = -1 # @param {type:"integer"}
AEM1_BOX_SEED_INDEX = -1 # @param {type:"integer"}
AEM1_SEEDS_CONFIRMADAS = False # @param {type:"boolean"}

AEM1_PROTOCOLS_COMPLETE = False
if not AEM1_CONFIG_READY or not {"point", "box"}.issubset(AEM1_PROPOSALS):
    print("PENDIENTE: ejecuta primero los baselines.")
elif not AEM1_SEEDS_CONFIRMADAS:
    print("PENDIENTE: elige las dos semillas, marca AEM1_SEEDS_CONFIRMADAS=True y reejecuta.")
else:
    seed_rows = (
        ("point", AEM1_PROPOSALS["point"], AEM1_POINT_SEED_INDEX),
        ("box", AEM1_PROPOSALS["box"], AEM1_BOX_SEED_INDEX),
    )
    invalid_seeds = [(label, index) for label, proposal, index in seed_rows if index not in range(len(proposal.masks))]
    if invalid_seeds:
        print("PENDIENTE: cada semilla debe ser 0, 1 o 2. Valores inválidos:", invalid_seeds)
    else:
        invalidate_aem1_review("Se regeneraron las correcciones; vuelve a revisar la salida final.")
        for protocol in ("point+corrections", "box+corrections"):
            AEM1_PROPOSALS.pop(protocol, None)
        point_corrected_bundle = pipeline.selector.select(image, "point+corrections", pipeline.detections)
        box_corrected_bundle = pipeline.selector.select(image, "box+corrections", pipeline.detections)

        proposal_point_corrected = generate_aem1(
            point_corrected_bundle.protocol,
            prompts=point_corrected_bundle.prompts,
            box=point_corrected_bundle.box_xyxy,
            mask_input=AEM1_PROPOSALS["point"].low_res_logits[AEM1_POINT_SEED_INDEX][None, :, :],
            multimask_output=False,
            parent_proposal_id=AEM1_PROPOSALS["point"].proposal_id,
            seed_candidate_index=AEM1_POINT_SEED_INDEX,
        )
        proposal_box_corrected = generate_aem1(
            box_corrected_bundle.protocol,
            prompts=box_corrected_bundle.prompts,
            box=box_corrected_bundle.box_xyxy,
            mask_input=AEM1_PROPOSALS["box"].low_res_logits[AEM1_BOX_SEED_INDEX][None, :, :],
            multimask_output=False,
            parent_proposal_id=AEM1_PROPOSALS["box"].proposal_id,
            seed_candidate_index=AEM1_BOX_SEED_INDEX,
        )
        AEM1_PROTOCOLS_COMPLETE = set(AEM1_PROPOSALS) == {"point", "box", "point+corrections", "box+corrections"}
        assert AEM1_PROTOCOLS_COMPLETE
        print("PROTOCOLO FIJO COMPLETO: cuatro modalidades registradas. Continúa con la revisión.")
''',
        form=True,
    ),
    markdown(
        "pragma-aem1-10m",
        """## 9. Elegir y revisar sin editar diccionarios

Escoge la salida que realmente conserve a la chica sin la persona posterior ni el fondo. Esta sección se ejecuta dos veces: primero deja `AEM1_REVIEW_COMPLETE=False` para generar la captura y el `selection_id`; después revisa los primeros planos, copia ese ID, marca los criterios y vuelve a ejecutar.

Si algún criterio es falso, las notas son obligatorias. El cuaderno guarda un token ligado al protocolo, candidata y bytes de la máscara.
""",
    ),
    code(
        "pragma-aem1-10",
        '''AEM1_SELECTED_PROTOCOL = "none" # @param ["none", "point", "box", "point+corrections", "box+corrections"]
AEM1_SELECTED_CANDIDATE = -1 # @param {type:"integer"}
AEM1_REVIEW_COMPLETE = False # @param {type:"boolean"}
AEM1_REVIEWED_SELECTION_ID = "" # @param {type:"string"}
AEM1_CORRECT_SUBJECT = False # @param {type:"boolean"}
AEM1_BODY_AND_EDGES_COMPLETE = False # @param {type:"boolean"}
AEM1_OTHER_PERSON_EXCLUDED = False # @param {type:"boolean"}
AEM1_BACKGROUND_EXCLUDED = False # @param {type:"boolean"}
AEM1_NOTES = "" # @param {type:"string"}

AEM1_SELECTED_EVIDENCE = []
AEM1_SELECTION = None
AEM1_CASE_STATUS = "PENDING_REVIEW"

available = {name: f"0..{len(proposal.masks)-1}" for name, proposal in AEM1_PROPOSALS.items()}
print("Candidatas disponibles:", available)
if not AEM1_CONFIG_READY:
    AEM1_CASE_STATUS = "PENDING_CONFIG"
    print("PENDIENTE: confirma la configuración.")
elif not AEM1_PROTOCOLS_COMPLETE:
    AEM1_CASE_STATUS = "PENDING_PROTOCOLS"
    print("PENDIENTE: ejecuta y registra los cuatro protocolos antes de revisar una salida final.")
elif AEM1_SELECTED_PROTOCOL == "none":
    print("PENDIENTE: selecciona un protocolo y una candidata tras mirar las galerías.")
elif AEM1_SELECTED_PROTOCOL not in AEM1_PROPOSALS:
    print("PENDIENTE: ese protocolo aún no fue ejecutado.")
else:
    chosen = AEM1_PROPOSALS[AEM1_SELECTED_PROTOCOL]
    if chosen.config_digest != AEM1_CONFIG_DIGEST:
        AEM1_CASE_STATUS = "PENDING_STALE_CONFIG"
        print("PENDIENTE: esta propuesta pertenece a otra configuración; regenera los baselines.")
    elif AEM1_SELECTED_CANDIDATE not in range(len(chosen.masks)):
        print(f"PENDIENTE: para {chosen.protocol} el índice válido es 0..{len(chosen.masks)-1}.")
    else:
        selection_render_start = time.perf_counter()
        mask = chosen.masks[AEM1_SELECTED_CANDIDATE]
        metrics = chosen.candidate_metrics[AEM1_SELECTED_CANDIDATE]
        packed_mask_sha256 = hashlib.sha256(np.packbits(mask).tobytes()).hexdigest()
        selection_id_payload = json.dumps({
            "proposal_id": chosen.proposal_id,
            "protocol": chosen.protocol,
            "candidate_index": AEM1_SELECTED_CANDIDATE,
            "packed_mask_sha256": packed_mask_sha256,
            "config_digest": AEM1_CONFIG_DIGEST,
        }, sort_keys=True).encode()
        selection_id = hashlib.sha256(selection_id_payload).hexdigest()[:12]
        stem = f"aem1_selected_{selection_id}"
        alpha_path = RUN_DIR / f"{stem}_alpha.png"
        rgba_path = RUN_DIR / f"{stem}_rgba.png"
        capture_path = RUN_DIR / f"{stem}_captura.png"
        closeups_path = RUN_DIR / f"{stem}_closeups.png"
        Image.fromarray(mask.astype(np.uint8)*255).save(alpha_path)
        pipeline.compositor.compose(image, mask.astype(np.float32)).save(rgba_path)

        fig, axes = plt.subplots(1, 3, figsize=(20, 7))
        axes[0].imshow(image); axes[0].set_title("Foto y prompts")
        if chosen.box_xyxy is not None:
            bx = chosen.box_xyxy
            axes[0].add_patch(Rectangle((bx[0], bx[1]), bx[2]-bx[0], bx[3]-bx[1], fill=False, ec="yellow", lw=3))
        if chosen.prompts is not None:
            axes[0].scatter(chosen.prompts.points[:,0], chosen.prompts.points[:,1],
                            c=["lime" if v else "red" for v in chosen.prompts.labels], s=100, marker="*")
        axes[1].imshow(preview_on_checker(image, mask)); axes[1].set_title("PNG sobre damero")
        axes[2].imshow(binary_preview(mask), cmap="gray", vmin=0, vmax=255); axes[2].set_title("Alpha binaria")
        for ax in axes: ax.axis("off")
        fig.suptitle(f"{chosen.protocol} · candidata {AEM1_SELECTED_CANDIDATE} · selección {selection_id}")
        fig.tight_layout(); fig.savefig(capture_path, dpi=170, bbox_inches="tight"); plt.show(); plt.close(fig)

        closeup_windows = {
            "cabeza y pelo": (2350, 150, 3300, 950),
            "contacto posterior": (2100, 450, 2850, 1350),
            "mano levantada": (2950, 500, 3550, 1400),
            "mano colgante": (2000, 1450, 2550, 2248),
            "torso inferior": (2400, 1450, 3550, 2248),
        }
        fig, axes = plt.subplots(2, len(closeup_windows), figsize=(25, 10), squeeze=False)
        for column, (label, (cx1, cy1, cx2, cy2)) in enumerate(closeup_windows.items()):
            crop_checker = matte_on_checker(image[cy1:cy2, cx1:cx2], mask[cy1:cy2, cx1:cx2].astype(np.float32))
            axes[0, column].imshow(crop_checker); axes[0, column].set_title(label + " · damero")
            axes[1, column].imshow(mask[cy1:cy2, cx1:cx2], cmap="gray", vmin=0, vmax=1); axes[1, column].set_title(label + " · alpha")
            axes[0, column].axis("off"); axes[1, column].axis("off")
        fig.suptitle("PRIMEROS PLANOS OBLIGATORIOS PARA LA REVISIÓN")
        fig.tight_layout(); fig.savefig(closeups_path, dpi=190, bbox_inches="tight"); plt.show(); plt.close(fig)

        reopened = Image.open(rgba_path)
        reopened_alpha = np.asarray(reopened)[..., 3]
        assert reopened.mode == "RGBA" and reopened.size == image_pil.size
        assert reopened_alpha.min() == 0 and reopened_alpha.max() == 255
        AEM1_SELECTED_EVIDENCE = [alpha_path, rgba_path, capture_path, closeups_path]
        evidence_sha256 = {path.name: sha256_file(path) for path in AEM1_SELECTED_EVIDENCE}
        selection_render_s = time.perf_counter() - selection_render_start

        review = {
            "complete": bool(AEM1_REVIEW_COMPLETE),
            "reviewed_selection_id": AEM1_REVIEWED_SELECTION_ID.strip(),
            "correct_subject": bool(AEM1_CORRECT_SUBJECT),
            "body_and_edges_complete": bool(AEM1_BODY_AND_EDGES_COMPLETE),
            "other_person_excluded": bool(AEM1_OTHER_PERSON_EXCLUDED),
            "background_excluded": bool(AEM1_BACKGROUND_EXCLUDED),
            "notes": AEM1_NOTES.strip(),
        }
        visual_checks = [review[k] for k in ("correct_subject", "body_and_edges_complete", "other_person_excluded", "background_excluded")]
        AEM1_CASE_STATUS = derive_aem1_case_status(
            AEM1_CONFIG_READY,
            AEM1_PROTOCOLS_COMPLETE,
            True,
            review["complete"],
            review["reviewed_selection_id"] == selection_id,
            visual_checks,
            metrics["sentinel_screen_pass"],
            review["notes"],
        )

        token_payload = json.dumps({
            "proposal_id": chosen.proposal_id,
            "protocol": chosen.protocol,
            "candidate_index": int(AEM1_SELECTED_CANDIDATE),
            "packed_mask_sha256": packed_mask_sha256,
            "config_digest": AEM1_CONFIG_DIGEST,
            "candidate_metrics": metrics,
            "human_review": review,
            "case_status": AEM1_CASE_STATUS,
            "evidence_sha256": evidence_sha256,
        }, sort_keys=True, ensure_ascii=False).encode()
        inspection_token = hashlib.sha256(token_payload).hexdigest()
        AEM1_SELECTION = {
            "proposal_id": chosen.proposal_id,
            "protocol": chosen.protocol,
            "candidate_index": int(AEM1_SELECTED_CANDIDATE),
            "config_digest": AEM1_CONFIG_DIGEST,
            "packed_mask_sha256": packed_mask_sha256,
            "inspection_token": inspection_token,
            "candidate_metrics": metrics,
            "human_review": review,
            "case_status": AEM1_CASE_STATUS,
            "evidence_files": [p.name for p in AEM1_SELECTED_EVIDENCE],
            "evidence_sha256": evidence_sha256,
            "selection_render_s": float(selection_render_s),
        }
        print("ESTADO DEL CASO:", AEM1_CASE_STATUS)
        print("selection_id que debes copiar para ligar la revisión:", selection_id)
        print("inspection_token:", inspection_token)
        if not review["complete"]:
            print("AHORA: revisa los primeros planos, copia selection_id en AEM1_REVIEWED_SELECTION_ID,")
            print("marca los criterios y vuelve a ejecutar esta misma celda.")
        elif AEM1_CASE_STATUS == "PENDING_REVIEW_BINDING":
            print("PENDIENTE: el ID revisado no coincide con esta máscara. Revisa esta salida y copia su selection_id.")
        elif AEM1_CASE_STATUS == "INCONCLUSIVE_SELECTED_OUTPUT_FAILED":
            print("La salida elegida falla; esto NO demuestra que las demás candidatas fallen. Devuelve el ZIP a Codex para agotar la revisión.")
        print("El proyecto general sigue INCONCLUSIVE y la Fase B permanece bloqueada.")
''',
        form=True,
    ),
    markdown(
        "pragma-aem1-11m",
        """## 10. Informe, manifiesto y ZIP verificado

El ZIP usa una lista blanca de archivos producidos en esta ejecución. Después de cerrarlo, el cuaderno lo reabre y comprueba nombres, tamaños y SHA‑256. Ningún residuo de una sesión anterior entra por accidente.
""",
    ),
    code(
        "pragma-aem1-11",
        '''AEM1_DOWNLOAD_ZIP = True # @param {type:"boolean"}

def proposal_record(proposal):
    return {
        "proposal_id": proposal.proposal_id,
        "protocol": proposal.protocol,
        "config_digest": proposal.config_digest,
        "prompts": prompt_payload(proposal.prompts),
        "box_xyxy": None if proposal.box_xyxy is None else proposal.box_xyxy.tolist(),
        "candidate_count": len(proposal.masks),
        "candidate_scores": [float(v) for v in proposal.scores],
        "inference_s": float(proposal.inference_s),
        "evidence_render_s": float(proposal.evidence_render_s),
        "parent_proposal_id": proposal.parent_proposal_id,
        "seed_candidate_index": proposal.seed_candidate_index,
        "candidate_metrics": proposal.candidate_metrics,
        "gallery_file": Path(proposal.gallery_path).name,
        "alpha_files": [Path(p).name for p in proposal.alpha_paths],
    }

def validate_selection_binding(selection):
    if selection is None:
        return True, ["sin selección final"]
    problems = []
    current_by_id = {proposal.proposal_id: proposal for proposal in AEM1_PROPOSALS.values()}
    proposal = current_by_id.get(selection.get("proposal_id"))
    if proposal is None:
        return False, ["proposal_id no pertenece al registro actual"]
    index = selection.get("candidate_index")
    if not isinstance(index, int) or index not in range(len(proposal.masks)):
        return False, ["candidate_index fuera de rango"]
    if proposal.config_digest != AEM1_CONFIG_DIGEST or selection.get("config_digest") != AEM1_CONFIG_DIGEST:
        problems.append("config_digest caducado")
    current_mask_sha = hashlib.sha256(np.packbits(proposal.masks[index]).tobytes()).hexdigest()
    if current_mask_sha != selection.get("packed_mask_sha256"):
        problems.append("la máscara seleccionada cambió")
    if json.dumps(proposal.candidate_metrics[index], sort_keys=True) != json.dumps(selection.get("candidate_metrics"), sort_keys=True):
        problems.append("las métricas holdout cambiaron")
    current_evidence = {}
    for filename, expected_hash in selection.get("evidence_sha256", {}).items():
        path = RUN_DIR / filename
        if path.resolve().parent != RUN_DIR.resolve():
            problems.append(f"ruta de evidencia fuera de RUN_DIR: {filename}")
        elif not path.exists():
            problems.append(f"falta evidencia: {filename}")
        else:
            current_evidence[filename] = sha256_file(path)
            if current_evidence[filename] != expected_hash:
                problems.append(f"evidencia alterada: {filename}")
    token_payload = json.dumps({
        "proposal_id": proposal.proposal_id,
        "protocol": proposal.protocol,
        "candidate_index": index,
        "packed_mask_sha256": current_mask_sha,
        "config_digest": AEM1_CONFIG_DIGEST,
        "candidate_metrics": proposal.candidate_metrics[index],
        "human_review": selection.get("human_review"),
        "case_status": selection.get("case_status"),
        "evidence_sha256": current_evidence,
    }, sort_keys=True, ensure_ascii=False).encode()
    if hashlib.sha256(token_payload).hexdigest() != selection.get("inspection_token"):
        problems.append("inspection_token no coincide")
    if selection.get("case_status") != AEM1_CASE_STATUS:
        problems.append("estado global no coincide con la revisión ligada")
    return not problems, problems

PROPOSAL_CONFIGS_CURRENT = all(p.config_digest == AEM1_CONFIG_DIGEST for p in AEM1_PROPOSALS.values())
SELECTION_BINDING_VALID, SELECTION_BINDING_PROBLEMS = validate_selection_binding(AEM1_SELECTION)
if not AEM1_CONFIG_READY:
    AEM1_CASE_STATUS = "PENDING_CONFIG"
elif not AEM1_PROTOCOLS_COMPLETE:
    AEM1_CASE_STATUS = "PENDING_PROTOCOLS"
elif not PROPOSAL_CONFIGS_CURRENT:
    AEM1_CASE_STATUS = "PENDING_STALE_CONFIG"
elif not SELECTION_BINDING_VALID:
    AEM1_CASE_STATUS = "PENDING_STALE_SELECTION"

AEM1_REPORT = {
    "schema_version": CODEX_AEM1_SCHEMA_VERSION,
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "run_id": RUN_ID,
    "question": "SAM 2.1 Large puede separar a la chica del frente de la tercera persona bajo el protocolo fijo A-E(-1)?",
    "case_status": AEM1_CASE_STATUS,
    "project_status": "INCONCLUSIVE_A_E0_REQUIRED",
    "phase_b_blocked": True,
    "sam2_rejectable": False,
    "interpretation_scope": "un caso y un presupuesto fijo de prompts; no demuestra exhaustividad de escena ni fracaso universal del modelo",
    "source_artifacts": {
        "base_notebook_sha256": BASE_NOTEBOOK_SHA256,
        "claude_aem1_sha256": CLAUDE_AEM1_SOURCE_SHA256,
        "claude_v4_patch_sha256": CLAUDE_V4_PATCH_SHA256,
    },
    "environment": ENVIRONMENT,
    "model": {
        "name": "sam2.1_hiera_large",
        "config": MODEL_CFG,
        "parameter_count": int(sum(parameter.numel() for parameter in sam2_model.parameters())),
        "checkpoint_bytes": CHECKPOINT.stat().st_size,
        "checkpoint_sha256": sha256_file(CHECKPOINT),
        "sam2_commit": SAM2_COMMIT,
        "backend": DEVICE,
        "dtype": PRECISION["dtype"],
        "peak_gpu_gib_at_export": gpu_peak_gib(),
    },
    "pipeline": {
        "detector": type(pipeline.detector).__name__,
        "selector": type(pipeline.selector).__name__,
        "mask_generator": type(pipeline.generator).__name__,
        "refiner": type(pipeline.refiner).__name__,
        "compositor": type(pipeline.compositor).__name__,
    },
    "timings_s": {
        "model_load": float(MODEL_LOAD_S),
        "image_embedding_once": float(EMBEDDING_S),
        "smoke_prompt": float(SMOKE_PROMPT_S),
        "protocols": {name: float(p.inference_s) for name, p in AEM1_PROPOSALS.items()},
        "protocol_prompt_total": float(sum(p.inference_s for p in AEM1_PROPOSALS.values())),
        "evidence_render_total": float(sum(p.evidence_render_s for p in AEM1_PROPOSALS.values())),
    },
    "configuration": AEM1_CONFIG,
    "config_confirmed": bool(AEM1_CONFIG_READY),
    "protocols_complete": bool(AEM1_PROTOCOLS_COMPLETE),
    "proposals": {name: proposal_record(p) for name, p in AEM1_PROPOSALS.items()},
    "selection": AEM1_SELECTION,
    "selection_binding": {"valid": SELECTION_BINDING_VALID, "problems": SELECTION_BINDING_PROBLEMS},
    "proposal_configs_current": PROPOSAL_CONFIGS_CURRENT,
    "candidate_exhaustion": {
        "complete": False,
        "meaning": "Una salida fallida no agota las demás candidatas; Codex debe revisar el bundle antes de atribuir FAIL al caso.",
    },
    "blocking_next_step": "A-E0: definir ontología e inventario manual antes de evaluar reconocimiento de todos los objetos.",
}

REPORT_PATH = write_json(RUN_DIR / "aem1_report.json", AEM1_REPORT)
current_proposal_artifacts = []
for proposal in AEM1_PROPOSALS.values():
    current_proposal_artifacts.extend(Path(p) for p in proposal.alpha_paths)
    if proposal.gallery_path:
        current_proposal_artifacts.append(Path(proposal.gallery_path))
payload_paths = []
for path in [CONFIG_JSON_PATH, CONFIG_OVERLAY_PATH, *current_proposal_artifacts, *AEM1_SELECTED_EVIDENCE, REPORT_PATH]:
    path = Path(path)
    if path.exists() and path.name not in {p.name for p in payload_paths}:
        assert path.resolve().parent == RUN_DIR.resolve(), f"Artefacto fuera de RUN_DIR: {path}"
        payload_paths.append(path)

manifest_entries = [{
    "name": path.name,
    "bytes": path.stat().st_size,
    "sha256": sha256_file(path),
} for path in sorted(payload_paths, key=lambda p: p.name)]
MANIFEST = {
    "schema_version": CODEX_AEM1_SCHEMA_VERSION,
    "run_id": RUN_ID,
    "entry_count_excluding_manifest": len(manifest_entries),
    "entries": manifest_entries,
}
MANIFEST_PATH = write_json(RUN_DIR / "aem1_manifest.json", MANIFEST)
archive_paths = payload_paths + [MANIFEST_PATH]

safe_status = AEM1_CASE_STATUS.replace("/", "_")
ZIP_PATH = RUN_DIR / f"PRAGMA_AEM1_{RUN_ID}_{safe_status}.zip"
ZIP_TEMP_PATH = ZIP_PATH.with_suffix(".zip.tmp")
with zipfile.ZipFile(ZIP_TEMP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
    for path in sorted(archive_paths, key=lambda p: p.name):
        archive.write(path, arcname=path.name)
ZIP_TEMP_PATH.replace(ZIP_PATH)

with zipfile.ZipFile(ZIP_PATH, "r") as archive:
    expected_names = {p.name for p in archive_paths}
    assert set(archive.namelist()) == expected_names
    manifest_by_name = {entry["name"]: entry for entry in manifest_entries}
    for name, entry in manifest_by_name.items():
        payload = archive.read(name)
        assert len(payload) == entry["bytes"]
        assert hashlib.sha256(payload).hexdigest() == entry["sha256"]
    assert hashlib.sha256(archive.read(MANIFEST_PATH.name)).hexdigest() == sha256_file(MANIFEST_PATH)

print(json.dumps({
    "case_status": AEM1_CASE_STATUS,
    "project_status": AEM1_REPORT["project_status"],
    "phase_b_blocked": True,
    "zip": str(ZIP_PATH),
    "zip_bytes": ZIP_PATH.stat().st_size,
    "manifest_sha256": sha256_file(MANIFEST_PATH),
}, indent=2, ensure_ascii=False))
if AEM1_DOWNLOAD_ZIP and not AEM1_CASE_STATUS.startswith("PENDING"):
    files.download(str(ZIP_PATH))
elif AEM1_DOWNLOAD_ZIP:
    print("ZIP PENDING guardado, pero no se descarga automáticamente hasta completar la revisión y las notas.")
''',
        form=True,
    ),
    markdown(
        "pragma-aem1-12",
        """## 11. Cómo interpretar el resultado

- `SEPARATION_DEMONSTRATED_UNDER_FIXED_AEM1_PROTOCOL`: una candidata pasó los sentinelas holdout y la inspección humana en este caso. **No** equivale a reconocer todos los objetos ni a validar generalización.
- `INCONCLUSIVE_SELECTED_OUTPUT_FAILED`: la salida elegida pierde zonas o conserva otra persona/fondo. No afirma que las otras candidatas fallen.
- `PENDING_CONFIG`, `PENDING_PROTOCOLS`, `PENDING_REVIEW`, `PENDING_REVIEW_BINDING`, `PENDING_NOTES` o `PENDING_STALE_*`: falta completar o volver a ligar una parte del protocolo; no es FAIL del modelo.

En todos los casos, el siguiente paso correcto para el objetivo nuevo “cada objeto de la foto” es A‑E0: fijar ontología e inventario manual, seguido de un baseline separado con `SAM2AutomaticMaskGenerator`. Este cuaderno no modifica la extensión, no instala YOLO‑seg/BiRefNet y no inicia Fase B.

Fuente oficial usada para la corrección iterativa: [`SAM2ImagePredictor.predict`](https://github.com/facebookresearch/sam2/blob/main/sam2/sam2_image_predictor.py), donde `mask_input` acepta logits de una iteración anterior y `multimask_output=False` se recomienda para prompts múltiples menos ambiguos.
""",
    ),
]

nb = {
    "cells": cells,
    "metadata": copy.deepcopy(nb_base["metadata"]),
    "nbformat": 4,
    "nbformat_minor": 5,
}
nb["metadata"].setdefault("colab", {})["name"] = OUT.name
nb["metadata"]["colab"]["provenance"] = []
OUT.write_text(json.dumps(nb, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

print(OUT)
print("bytes", OUT.stat().st_size, "cells", len(cells))
