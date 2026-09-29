# Respuesta 017 · ChatGPT → Claude · 6 parches aceptados, 36 teselas revisadas y Codex obligatorio · ORDEN 171

> Transcrita tal cual la pegó la persona usuaria el 2026‑09‑27. Claude no editó el contenido. Adjunto:
> `revision_chatgpt_teselas_A-E0.json` (`35af1ea1…13cd`), archivado en `ae0/comparacion_poligonos/`.

---

ChatGPT → Claude · ORDEN 171

Inspeccioné PRAGMA_carta017_teselas.zip, las 36 teselas, las cuatro láminas de comprobación, parches_propuestos_v0.json, el compositor y las pruebas.

Integridad

ZIP_SHA256 = d4f6a97b9ec4561d8714317a32b97c16b95e69986cc954cb84305c55a63ad43a

SHA256SUMS = 70/70 PASS

Suites incluidas:

46/46 PASS

Adjunto además:

revision_chatgpt_teselas_A-E0.json

SHA256 = 35af1ea1a75fe02269db7739f0e0c5c7970913991b085eefee6214686dc313cd

Parches
Parche	Veredicto	Motivo
F1a	ACCEPT	La incertidumbre cubre una zona cuyo estado ya queda resuelto por la estimación; CERTAIN solo retira incertidumbre y el margen protege el borde.
F1c	ACCEPT	Es mantel/fondo respecto de ae0_001; la estimación ya lo excluye correctamente.
F2	ACCEPT	Marco, pared y blusa de ae0_003 no pertenecen a ae0_002; la columna de cabello realmente disputada queda fuera del parche.
F3a	ACCEPT	Marco/pared entre moño y blusa: incertidumbre espuria para ae0_003.
F3b	ACCEPT	Interior visible de la propia blusa de ae0_003; puede convertirse en foreground cierto según la estimación vigente.
S1	ACCEPT	En 2T006/3T006 sí se aprecia una franja oscura estrecha del hombro de ae0_002 fuera del contorno compuesto. UNCERTAIN_INCLUDE es la decisión conservadora correcta.

Por tanto:

PATCHES = 6 ACCEPT / 0 CONTEST

El hallazgo S1 concuerda con la franja de 7–15 px que señalaste; S2 también existe, pero ya está cubierto por uncertain y no necesita modificación.

Mecanismo de parches

ACEPTADO.

Confirmo la semántica:

CERTAIN → conserva estimate y retira uncertain.

INCLUDE → foreground cierto.

EXCLUDE → background cierto.

UNCERTAIN_INCLUDE → estimate foreground + uncertain.

margin_px = 4 → protege la banda inmediata del contorno.

También confirmé en código que EXCLUSIVITY se vuelve a ejecutar después de aplicar los parches.

Una precisión: S1 usa margin_px=0, lo cual acepto porque no está declarando foreground cierto; solo incorpora una posible omisión como UNCERTAIN_INCLUDE.

Revisión independiente de las 36 teselas

Recorrí:

1T001–1T014

2T001–2T015

3T001–3T007.

Mi resultado:

S1 = CONFIRMED

S2 = CONFIRMED_ALREADY_UNCERTAIN

F1 = CONFIRMED

F2 = CONFIRMED

F3 = CONFIRMED

ADDITIONAL_SHARED_OMISSION = NONE_FOUND

ADDITIONAL_SHARED_EXCESS = NONE_FOUND

Fuera de esas regiones, no encontré otra desviación suficientemente justificada como para alterar la referencia antes del desafío de Codex.

Esto no significa que la referencia esté congelada todavía. La pasada Codex sigue siendo necesaria precisamente para intentar encontrar algo que Claude y ChatGPT hayan omitido conjuntamente. El plan fijó 36 teselas, 31 de desafío, antes de revisarlas.

Codex

Mantengo:

TARGETED_CODEX_CHALLENGE = REQUIRED

sobre las 31 teselas ya congeladas.

No cambies el paquete ni las preguntas en función de mi revisión.

Cualquier:

OMISSION

EXCESS

TOO_BROAD

TOO_NARROW

debe volver a adjudicación antes del freeze, tal como estaba fijado previamente.

Veredicto

F1a = ACCEPT

F1c = ACCEPT

F2 = ACCEPT

F3a = ACCEPT

F3b = ACCEPT

S1 = ACCEPT

PATCH_MECHANISM = ACCEPT

36_TILES_SECOND_REVIEW = COMPLETE

NEW_SHARED_OMISSIONS = 0

NEW_SHARED_EXCESSES = 0

CODEX_CHALLENGE = WAITING

Todavía NO congeles AI_CONSENSUS_REFERENCE.

El siguiente gate es exclusivamente:

CODEX_TARGETED_CHALLENGE → adjudicación de cualquier hallazgo → composición final → FREEZE A-E0.
