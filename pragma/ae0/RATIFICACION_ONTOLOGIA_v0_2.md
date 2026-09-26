# A‑E0 · Hoja de ratificación de la ontología v0.2

> **Para la persona usuaria.** Esta es la única decisión que A‑E0 necesita de ti antes de empezar. La
> hoja resume en lenguaje llano lo que `ONTOLOGIA_PROPUESTA.md` (§2 y §5) propone, actualizado con
> las decisiones posteriores (DEC‑013‑Q, DEC‑024 y DEC‑025).
>
> **Se puede compartir con ChatGPT.** No contiene nada del borrador de inventario de Claude
> (`scene_inventory.draft.json`), que ChatGPT **no debe abrir** hasta entregar su propia llave, hecha
> solo desde la foto.

## Qué significa ratificar

Decides **qué cuenta como objeto** en la foto. Con eso, las dos IAs hacen el inventario y las
máscaras, cada una por su lado; un comparador automático encuentra cada diferencia entre ellas, y se
adjudica. **No tienes que pintar ni revisar píxeles.** Conservas el veto sobre todo.

- **Si aceptas todo:** escribe «**acepto la ontología v0.2**».
- **Si quieres cambiar algo:** di el número y el cambio (por ejemplo, «R4: las sombras sí cuentan»).

## Las decisiones

| # | Propuesta | Si decides otra cosa |
|---:|---|---|
| R1 | **Toda persona cuenta siempre**, aunque esté casi tapada, y tiene máscara de referencia. | — |
| R2 | **Cuenta un objeto** que alguien sin contexto sabría identificar, con el lado corto de su caja de **al menos 32 px** en la foto completa (4000 × 2248). Es **principal (A)** si está poco o medio tapado y mide al menos 64 px, y **secundario (B)** si está muy tapado o mide entre 32 y 63 px. | Bajar a 16 px mete ruido de compresión y joyería diminuta. |
| R3 | **Partes** (mano, cara, ropa), **superficies** (pared, suelo) y **textos** se anotan como una tercera clase (C), sin bloquear la evaluación. Una parte **nunca** cuenta como «fusión» con su entero: la mano de una persona no es un error de la máscara de esa persona. | Si las partes bloquearan, el trabajo se triplica y A‑E1 fallaría por detalles que aún no importan. |
| R4 | **No cuentan:** lo que mide menos de 32 px (salvo que esté justo en una frontera de contacto que se mide), las sombras, los reflejos y los brillos. Un objeto tapado en más del 90 % cuenta como B si se identifica; si no, no cuenta. | — |
| R5 | **El texto de las etiquetas con nombre** se anota como «texto» y **nunca se transcribe**. La foto y todo lo que derive de ella siguen fuera del repositorio público. | — |
| R6 | **Basta una región seleccionable, aunque no tenga nombre**, para la primera meta. Ponerle nombre a cada objeto es una fase posterior (A‑E2). | — |
| R7 | **Idioma:** español en el inventario y la interfaz, más un concepto corto en inglés para los modelos. | — |
| R8 | **Producto:** se exporta el objeto que eliges. «Exportar todos» queda solo como diagnóstico. | — |
| R9 | **Regla de aprobación:** una máscara que se lleva al menos el 10 % de otra persona u objeto, y que invade su interior, **falla aunque se parezca mucho a la referencia** (DEC‑013‑Q; es el defecto que tuvo la v4). La fuga en la franja de contacto se reporta sin bloquear en la primera corrida, hasta calibrarla con datos reales. | Sin esta regla, el contrato aprobaría el defecto de la v4 (hay una prueba que lo demuestra). |
| R10 | **Quién hace la referencia:** las dos IAs, cada una por su cuenta y sin usar SAM 2 (que es lo que se va a medir). Un comparador encuentra cada diferencia, y cada diferencia se adjudica. Donde ninguna llave puede justificar el borde se marca «incierto» y se reporta aparte. Se etiqueta **«referencia de consenso de IA»**, nunca «verdad humana». | Si prefieres una verdad humana, tendrías que pintar tú las máscaras de las tres personas (1,5–3 h). |
| R11 | **Recursos:** Colab con GPU L4. Ningún modelo restringido ni API de pago hasta cerrar A‑E1; SAM 3 se decide en A‑E2. El barrido de A‑E1 ya está fijado de antemano (4 configuraciones), y la galería de primer nivel muestra como máximo 60 propuestas. | — |

## Lo que no se decide ahora

- **Otras imágenes de validación** (una firma escaneada, un producto sobre fondo liso, un grupo sin
  oclusión, una mesa con objetos pequeños): no bloquean A‑E0 y se piden más adelante.
- **La carpeta histórica v4:** si algún día aparece en Descargas, Drive o la Papelera
  (`PRAGMA_Fase_A_v4_20260811T001154Z_6e6a9ae1`), se verifica; si no, no bloquea nada.

## Qué pasa después

1. Claude congela su llave de inventario.
2. ChatGPT hace la suya **solo desde la foto**.
3. Se comparan objeto a objeto y, para las tres personas, máscara a máscara (DEC‑025).
4. Se congela la referencia y el contrato de A‑E1.
5. Se corre A‑E1 en Colab, a un clic, como las corridas anteriores.
