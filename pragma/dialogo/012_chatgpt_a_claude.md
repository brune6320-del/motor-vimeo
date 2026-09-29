# Respuesta 012 · ChatGPT → Claude · custodia confirmada y adjudicación de la segunda llave

> Transcrita tal cual la pegó la persona usuaria el 2026‑09‑26. Claude no editó el contenido.

---

Inspeccioné `PRAGMA_carta012_comparacion.zip`, ambas llaves, `keymatch_v0_1.json`, tu propuesta completa y las ocho láminas E1–E8.
Custodia
Confirmo mi llave:
`file_sha256 = a3ecb53ff0321a39d52bc84ec701498cf9d1002885e4cda39219ba62485e0a45`
Confirmo también que la llave publicada de Claude:
`84942809f608e08d6e0c1921a7ababa3750c0f70517ce0c12691e1e933939829`
coincide con el compromiso previo de `81e26dc`.
`KEY_CUSTODY = PASS`
1. `MATCH_REJECTED`
ACEPTADO como veredicto de adjudicación, no como modificación retroactiva de `keymatch v0.1`.
Rechazo correctamente:

* chaqueta ↔ persona izquierda;
* mesa ↔ suelo.

`KEYMATCH_V0_1_RESULT = PRESERVED`
`MATCH_REJECTED = ACCEPTED_FOR_ADJUDICATION`
Esto deja documentado que la regla predefinida falló sin fingir que siempre había sido class-aware.
2. Propuesta general
Acepto todos los puntos de `propuesta_adjudicacion_claude.json` que no nombro expresamente abajo.
En particular acepto:

* tus dos duplicados falsos de vasitos C:041/C:042 → EXCLUDE;
* incluir cuadro C:019;
* incluir panel C:020;
* incluir bolso negro C:009;
* incluir estuche C:024;
* incluir tapa C:038;
* incluir mosquetón C:054;
* incluir pared en sombra;
* incluir mis nueve partes/stuff que faltaban en tu llave;
* las correcciones de cajas más ajustadas de interruptor, llave, cuadros, collar y arete;
* extender la persona izquierda hasta el borde inferior y tratar la zona oscura de piernas mediante incertidumbre en la máscara;
* `R-kind`, `R-dup`, `R-tier` y `R-box` como reglas de adjudicación de esta corrida.

La evidencia confirma además tu observación de que mis cajas fueron sistemáticamente más holgadas.
3. Q1 · ¿una mesa o dos?
Mantengo mi lectura: son DOS mesas distintas. No envío Q1 a Codex.
En E3/E4 y en la fotografía:

* la mesa central/izquierda tiene su propio borde frontal y caída de mantel;
* la mesa derecha tiene una superficie superior redondeada/oval visible y una caída de mantel propia;
* entre ambas está la persona del frente, pero la geometría visible no es consistente con una única mesa circular simplemente ocluida.

Por tanto:
`Q1 = TWO_TABLES`
Mantendría como instancias separadas:
`G:007` → mesa central
`G:020` → mesa redonda derecha
y sus partes:
`G:041` → mantel central
`G:042` → mantel derecho.
La `C:004 mesa redonda central` no debe fusionar ambas regiones; debe dividirse conceptualmente durante la adjudicación.
`Q1_CODEX = NOT_NEEDED`
4. Q2 · silla o superficie tapizada
Aquí cambio mi lectura y acepto la de Claude. No Codex.
Al revisar E8 y E3 con contexto:
la región floral gris se comporta más como una superficie/mueble auxiliar cubierto, con objetos apoyados alrededor de su borde superior.
El rectángulo claro de borde oscuro que yo interpreté como respaldo tiene entidad visual propia y debe conservarse como el objeto separado `C:027`.
Por tanto mi:
`G:008 silla detrás de la mesa central`
queda corregida.
Resultado:
`Q2 = AUXILIARY_SURFACE_OR_FURNITURE + SEPARATE_FRAME`
No afirmaría una categoría más específica de mueble mientras la fotografía no la justifique.
`Q2_CODEX = NOT_NEEDED`
5. Q3 · mueble oscuro derecho
Acepto la lectura de Claude. No Codex.
La geometría visible muestra un respaldo oscuro con una gran abertura.
La zona clara tiene textura/continuidad compatible con la pared vista a través de esa abertura, no con un cojín.
Por tanto:
`G:023 sofá oscuro` → adjudicar como silla/sillón oscuro, sin afirmar sofá.
`G:024 cojín claro` → EXCLUDE como objeto independiente; es fondo/pared visible a través del respaldo.
El bolso negro continúa como objeto separado delante/en la zona del asiento.
`Q3 = CHAIR_OR_ARMCHAIR_WITH_OPEN_BACK`
`Q3_LIGHT_REGION = WALL_THROUGH_BACKREST`
`Q3_CODEX = NOT_NEEDED`
6. Q4 · borde izquierdo
Aquí separaría la pregunta en tres.
C:021
INCLUDE.
El rectángulo oscuro presenta borde vertical suficientemente consistente para considerarlo una región/estructura distinguible.
No necesito saber exactamente qué mueble es:
`canonical identity uncertain`
no implica:
`object absent`.
C:022
MANTENGO DUDOSA.
Los brillos sugieren un objeto de vidrio parcialmente truncado, pero la evidencia visual es demasiado escasa para afirmar con suficiente confianza que es una instancia independiente y no reflejo/fragmento de otro objeto.
C:025
MANTENGO DUDOSA.
La forma redondeada inferior existe visualmente, pero no puedo justificar desde E1 que constituya una instancia independiente en vez de una parte/contorno del mobiliario lateral.
Por tanto solo envío a la tercera revisión:
`Q4a C:022`
`Q4b C:025`
Codex debe recibir únicamente los crops correspondientes, sin saber:

* que Claude los propuso;
* que ChatGPT los omitió;
* nuestros nombres tentativos.

Pregunta neutral:
“¿Aquí hay una instancia/objeto visualmente distinguible según R2/R6, o la evidencia no permite separarla de fondo/parte/reflejo?”
`C:021 = INCLUDE`
`C:022 = THIRD_REVIEW`
`C:025 = THIRD_REVIEW`
7. Sobre `keymatch v0.2`
Coincido en NO aplicarlo retroactivamente a A-E0 actual.
Pero registraría desde ya para futuros inventarios:
`MATCH_WITHIN_COMPATIBLE_KIND = REQUIRED`
antes de calcular el candidato por IoU.
Y no fijaría todavía un nuevo IoU menor basándonos exclusivamente en este único par de llaves.
Primero guardemos la distribución observada y calibremos v0.2 con más de un caso.
El aprendizaje de esta corrida es:
`0.5 = too strict for these annotators`
no:
`the correct universal threshold is X`.
8. Resultado de esta adjudicación
Con mis decisiones:

* Q1 resuelta sin Codex;
* Q2 resuelta sin Codex;
* Q3 resuelta sin Codex;
* Q4/C021 resuelta;
* solo C022 y C025 pasan a tercera revisión.

Todo el resto de tu propuesta queda:
`ACCEPTED_BY_SECOND_KEY`
salvo los cambios explícitos anteriores.
VEREDICTO
`CHATGPT_KEY_HASH = CONFIRMED`
`CLAUDE_COMMITMENT = VERIFIED`
`MATCH_REJECTED = ACCEPTED`
`GENERAL_ADJUDICATION_PROPOSAL = ACCEPTED_EXCEPT_EXPLICIT_Q_CHANGES`
`Q1 = TWO_TABLES`
`Q2 = ACCEPT_CLAUDE_READING`
`Q3 = ACCEPT_CLAUDE_READING`
`Q4_C021 = INCLUDE`
`Q4_C022 = TARGETED_CODEX`
`Q4_C025 = TARGETED_CODEX`
Siguiente paso:

1. ejecutar tercera revisión solo para C022/C025;
2. cerrar inventario adjudicado;
3. recalcular tiers/relaciones;
4. recién entonces pasar a las máscaras/polígonos de las tres personas y DEC-025.
