# Guía paso a paso · A‑E(−1) v1.1 en Google Colab

Para quien ejecuta, sin necesidad de saber programar. Tiempo total: **30–45 min** la primera vez
(la instalación y la descarga del modelo, ~900 MB, tardan varios minutos), más tu revisión.

## Qué necesitas antes de empezar

| Qué | Dónde está |
|---|---|
| El cuaderno `PRAGMA_A-E-menos-1_diagnostico_caso_chica_v1_1.ipynb` | Te lo adjunto en el chat; también en GitHub: `pragma/outputs/` de la rama `claude/genesis-emerge-proyecto-6mdcs0` |
| La foto original `P1070614.JPG` (4,3 MB) | Tu Escritorio. **La original**, no una copia editada o exportada: se valida por hash |
| Una cuenta de Google | — |
| Navegador | Mejor **Chrome**. En Brave, subir/descargar archivos se quedó colgado antes |

## Paso 1 · Abrir el cuaderno

1. Descarga el `.ipynb` que te adjunto.
2. Entra en <https://colab.research.google.com> → menú **Archivo → Subir cuaderno** → elige el archivo.
3. Comprueba que el título diga **“PRAGMA · A‑E(−1) v1.1”**. Si dice solo “A‑E(−1)”, es el v1.0: no lo uses.

## Paso 2 · Elegir la GPU

1. Menú **Entorno de ejecución → Cambiar tipo de entorno de ejecución**.
2. En **Acelerador de hardware** elige **L4** o **A100** si los tienes (Colab Pro o unidades de
   cómputo); si no, **T4** (gratis) también sirve. **No** elijas CPU.
3. **Guardar**. Anota qué GPU elegiste: me lo tendrás que decir.

## Paso 3 · Secciones 1 a 4: instalar, subir la foto, cargar el modelo

Ejecuta **cada celda por separado** con el botón ▶ de su izquierda (o Ctrl/Cmd + Enter), de arriba
abajo, esperando a que termine cada una. **No uses “Ejecutar todo”.**

| Sección | Qué verás si va bien |
|---|---|
| **1. Instalar SAM 2** | Varios minutos. `Descarga: …%` y al final `Commit SAM 2: …` |
| **2. Hardware y fotografía** | Aparece el botón **Elegir archivos** → selecciona `P1070614.JPG`. Luego `Foto validada` y un bloque con `"device": "cuda"` y `"dtype": "bfloat16"` (L4/A100) o `"float16"` (T4) |
| **3. Contratos** | `SELF-TEST PASS: matte 0.5 → alpha 128.` |
| **4. Cargar el modelo** | Un bloque con `"status": "PASS"` |

**Si algo falla aquí:**

- Dice `"device": "cpu"` → no se activó la GPU: repite el Paso 2 y vuelve a ejecutar desde la sección 1.
- El botón de subir no aparece o se queda girando → pulsa ■ para detener la celda, abre el panel
  **Archivos** (icono de carpeta a la izquierda), arrastra la foto hasta que quede como
  `/content/P1070614.JPG` y vuelve a ejecutar la sección 2.
- `No se recibió exactamente la fotografía de aceptación` → subiste otra versión de la foto. Usa la original.
- `FAIL_ENVIRONMENT` u otro error rojo → no sigas: copia **todo** el texto del error (desde
  `Traceback` hasta el final) y mándamelo con el número de sección.

## Paso 4 · Sección 5: confirmar los puntos · DECISIÓN HUMANA 1

Ejecuta la celda. Verás tres cosas: la foto con puntos de colores, una tabla y la **hoja de
contactos** (18 recuadros, uno por punto, ampliados). **Decide en la hoja de contactos, no en la foto
completa.**

Qué significa cada color:

| Color | Qué es | Dónde debe caer |
|---|---|---|
| Azul `P+1` | orden “esta es la persona” | dentro de la chica (overol) |
| Rojo `P‑1…P‑3` | orden “esto NO” | sobre la persona de atrás |
| Verde `K1…K7` | control que debe quedar **dentro** | cara, pelo, hombro, mano en V, manga, mano que cuelga, overol |
| Magenta `O1…O4` | control que debe quedar **fuera** | persona de atrás |
| Cian `B1…B3` | control que debe quedar **fuera** | cuadro, mesa, silla |

Mira con especial cuidado:

- **P‑2 y O2:** dentro del pelo recogido de la persona de atrás, no en la pared.
- **P‑3:** sobre la tela oscura del hombro de la persona de atrás.
- **O3** (pelo oscuro justo encima y a la izquierda de la cabeza de la chica): ¿ese pelo es **de la persona de atrás** o **de la chica**?
- **O4** (borde entre la blusa floral y el hombro de la chica): ¿de quién es ese punto?

Entonces:

- **Todo bien, y O3 y O4 son de la persona de atrás** → marca la casilla
  `AEM1_CONFIG_CONFIRMADA` y vuelve a ejecutar la celda. Debe decir `CONFIGURACIÓN CONFIRMADA`.
- **Algún punto está mal, o O3/O4 son de la chica, o no puedes decidir** → **no marques nada**.
  Haz una captura de la hoja de contactos, mándamela diciendo qué punto y por qué, y te preparo una
  v1.2. No edites coordenadas a mano.

Después ejecuta la **sección 6**: debe decir `SELF-TEST PASS: los sentinelas producen diagnóstico local…`.

## Paso 5 · Sección 7: primeras máscaras · DECISIÓN HUMANA 2

Ejecuta. Aparecen **dos galerías** (`point` y `box`), cada una con **3 candidatas numeradas 0, 1 y 2**:
arriba el recorte sobre damero; abajo la máscara en blanco y negro, con `SCREEN OK` o `REVISAR`.

Para cada galería elige la candidata que **contiene a la chica más completa**, aunque todavía arrastre
algo de la persona de atrás (eso se corrige en el paso siguiente). **No elijas por el número de score.**
Anota: *punto → candidata __; caja → candidata __*.

## Paso 6 · Sección 8: correcciones

En el formulario de la celda:

1. `AEM1_POINT_SEED_INDEX` = tu candidata de `point`.
2. `AEM1_BOX_SEED_INDEX` = tu candidata de `box`.
3. Marca `AEM1_SEEDS_CONFIRMADAS`.
4. Ejecuta. Salen dos galerías más, con una sola candidata cada una (la `0`):
   `point+corrections` y `box+corrections`. Debe decir `PROTOCOLO FIJO COMPLETO`.

## Paso 7 · Sección 9: elegir y revisar · DECISIÓN HUMANA 3 (la celda se ejecuta dos veces)

Compara las cuatro modalidades y elige **la que mejor tenga a la chica completa y nada más**.

**Primera ejecución:**

1. `AEM1_SELECTED_PROTOCOL` = la modalidad elegida (por ejemplo `box+corrections`).
2. `AEM1_SELECTED_CANDIDATE` = su número (en las corregidas siempre es `0`).
3. Deja **sin marcar** `AEM1_REVIEW_COMPLETE`. Ejecuta.
4. Verás una captura (foto · damero · máscara) y los **PRIMEROS PLANOS**: *cabeza y pelo, contacto
   posterior, mano levantada, mano colgante, torso inferior*. La celda imprime
   `selection_id que debes copiar …: xxxxxxxxxxxx`.

**Revisa los primeros planos con zoom** (clic derecho sobre la imagen → abrir en una pestaña nueva) y
pregúntate:

- ¿Falta algo de la chica? (mechones de pelo, dedos de la mano en V, hombro, mano que cuelga)
- ¿Aparece algo de la persona de atrás? (pelo recogido, blusa floral, hombro)
- ¿Se cuela fondo? (mesa, cuadros, pared, silla)

**Segunda ejecución:**

1. Pega el `selection_id` en `AEM1_REVIEWED_SELECTION_ID`.
2. Marca `AEM1_REVIEW_COMPLETE`.
3. Marca **solo lo que sea verdad**:
   - `AEM1_CORRECT_SUBJECT`: es la chica.
   - `AEM1_BODY_AND_EDGES_COMPLETE`: está entera, sin huecos ni partes perdidas.
   - `AEM1_OTHER_PERSON_EXCLUDED`: no hay **nada** de la persona de atrás.
   - `AEM1_BACKGROUND_EXCLUDED`: no hay mesa, cuadros, pared ni silla.
4. Si dejas alguna sin marcar, escribe en `AEM1_NOTES` qué falla y dónde (por ejemplo: *“se lleva
   el moño de la persona de atrás; falta la punta del índice”*).
5. Ejecuta. Imprime `ESTADO DEL CASO: …`.

> **Si dudas, no marques.** El falso PASS de la v4 salió de casillas marcadas con optimismo. Un
> “no” honesto con notas es un resultado útil; un “sí” dudoso vuelve inútil toda la corrida.

## Paso 8 · Sección 10: el ZIP

Ejecuta. Descarga sola un archivo `PRAGMA_AEM1_<fecha>_<estado>.zip`.
Si la descarga se queda girando: detén la celda **después** de que imprima `ZIP_PATH`, abre el panel
**Archivos** → `/content/pragma_run/runs/<carpeta>/` → clic derecho sobre el `.zip` → **Descargar**.

## Paso 9 · Guardar el cuaderno ejecutado

Menú **Archivo → Descargar → Descargar .ipynb**.

## Qué me adjuntas en el chat

1. **El ZIP** `PRAGMA_AEM1_….zip` (obligatorio).
2. **El `.ipynb` ejecutado** (obligatorio).
3. Un mensaje con: la GPU que usaste, tus dos semillas, la modalidad y candidata finales, y qué
   decidiste sobre **O3 y O4**.
4. Si algo falló: el texto completo del error, en qué sección ocurrió y una captura.

Nada de esto se sube a GitHub (el repositorio es público y el ZIP contiene recortes de la foto): lo
audito aquí, verifico cada hash del manifiesto, reviso las imágenes y en el repo solo registro
hashes y conclusiones en `PROJECT_STATE.md`.
