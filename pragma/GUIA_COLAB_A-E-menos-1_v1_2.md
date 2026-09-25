# Guía · A‑E(−1) v1.2 · tú no fiscalizas nada

Desde v1.2 la verificación la hace la IA: yo confirmo la configuración con evidencia, audito todas
las candidatas a resolución completa y registro el veredicto; ChatGPT lo contraaudita. A ti solo te
tocan pasos mecánicos. Hay dos modos; elige uno.

---

## Modo A · Un clic en el navegador (≈5 minutos tuyos, cero decisiones)

1. **Cierra** el cuaderno v1.1 que tengas abierto y **descarga el v1.2** que te adjunto
   (`PRAGMA_A-E-menos-1_diagnostico_caso_chica_v1_2.ipynb`).
2. En Colab: **Archivo → Subir cuaderno** → elige el v1.2. El título debe decir **"v1.2 … un clic"**.
3. **Entorno de ejecución → Cambiar tipo de entorno de ejecución → L4** (o A100; T4 también sirve) → Guardar.
4. Abre el panel **Archivos** (icono de carpeta a la izquierda) y **arrastra `P1070614.JPG`** dentro.
   Espera a que aparezca en la lista. El nombre da igual: se reconoce por su huella SHA‑256.
5. **Entorno de ejecución → Ejecutar todas.** Si Colab avisa que el cuaderno no es de Google,
   pulsa **Ejecutar de todos modos**. No toques ningún formulario.
6. Espera. La primera vez tarda más porque descarga el modelo (~900 MB).
7. Al final se descarga `PRAGMA_AEM1_…_PENDING_EXTERNAL_AUDIT.zip`. Si no arranca la descarga
   (Brave a veces la bloquea): panel **Archivos → pragma_run → runs → (carpeta) →** clic derecho en
   el `.zip` → **Descargar**.
8. **Adjunta ese ZIP en el chat conmigo.** Opcional: *Archivo → Descargar → Descargar .ipynb*, y
   adjúntalo también.

**Si aparece algo en rojo:** no intentes arreglarlo. Copia el texto completo del error, dime la
sección y adjunta una captura.

**`PENDING_EXTERNAL_AUDIT` no es un error:** significa "terminó bien; falta la auditoría", que hago yo.

---

## Modo B · Me lo delegas todo con Colab CLI (tú solo das dos permisos, una vez)

El Colab **MCP** solo funciona con el agente corriendo en tu propio Mac, junto a una pestaña de
Colab abierta. El Colab **CLI** (`google-colab-cli`), en cambio, sí puede funcionar desde esta
sesión en la nube, si le das dos permisos:

1. **Abrir la red de este entorno a Colab.** En la barra de título de esta sesión, abre el menú del
   entorno cloud → **Edit** → **Network access** → añade el dominio **`colab.research.google.com`**
   (o elige un nivel de acceso más amplio). Hoy está bloqueado. Si en el primer intento aparece otro
   host bloqueado (el del runtime de Colab), te digo exactamente cuál añadir.
2. Escríbeme **"red lista"**. Instalo el CLI y te paso un **enlace de autorización de Google**.
3. Ábrelo con tu cuenta de **Colab Pro** y acepta. Google te muestra un **código**: **pégamelo en el chat.**
   - Qué permisos pide el CLI: tu perfil y correo, Colab, `drive.file` (solo los archivos que cree
     la propia app) y **`cloud-platform`**, que da acceso a tus proyectos de Google Cloud si tienes
     alguno. Es un permiso amplio: decide tú.
   - El token vive solo en este contenedor temporal y desaparece con él. Puedes revocarlo cuando
     quieras en <https://myaccount.google.com/permissions>.
4. A partir de ahí lo hago yo:
   - creo un runtime L4 (`colab new --gpu L4`);
   - subo la foto (`colab upload`);
   - ejecuto el cuaderno v1.2 sin navegador (`colab exec -f … --env PRAGMA_HEADLESS=1 --timeout …`);
   - descargo el ZIP (`colab download`), lo audito y apago el runtime (`colab stop`) para no gastar
     unidades de cómputo.

Coste aproximado: 10–20 minutos de L4 de tus unidades de Colab Pro por corrida.

---

## Qué pasa después (en los dos modos)

1. Verifico el ZIP byte a byte (manifiesto, hashes, configuración) y que la corrida sea real (GPU, no simulada).
2. Reviso **las 12 candidatas** a resolución completa: pelo, contacto con la persona de atrás, las
   dos manos, costado derecho. Elijo por contenido y registro el veredicto con evidencia
   (`aem1_audit_verdict.json`).
3. Te preparo la carta para ChatGPT con el veredicto y las cifras, para su contraauditoría.
4. Actualizo `PROJECT_STATE.md`. Tú puedes vetar cualquier veredicto.

Nada derivado de la foto se sube a GitHub (el repositorio es público).
