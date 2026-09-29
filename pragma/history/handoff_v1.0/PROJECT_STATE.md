# 0. Identidad del State File

- **Proyecto:** PRAGMA · Motor de Transparencia / Inventario exhaustivo de escena
- **Archivo:** `PROJECT_STATE.md`
- **Fecha de generación:** 22 de septiembre de 2026 (America/Lima)
- **Versión:** `v1.0`
- **Estado general:** `INCONCLUSIVE_A_E0_REQUIRED`
- **Fase B:** `BLOQUEADA`
- **Último hito documentado:** port a un cuaderno independiente A‑E(−1), con 68/68 verificaciones estáticas y experimento GPU todavía `NOT_RUN`
- **Propósito:** fuente de verdad operativa para continuar PRAGMA en ChatGPT 6 Sol, otra IA o una nueva sesión sin depender de la conversación original.
- **Confianza general:** alta para archivos, hashes, decisiones y estado lógico; media para la antigua ejecución v4 porque sus evidencias ya no están presentes en el disco.

> Este archivo debe actualizarse cada vez que una decisión, implementación o prueba cambie el estado real del proyecto.

## Leyenda de certeza

- `✅ VERIFICADO`: existe evidencia ejecutada, medida o comprobada.
- `🟡 IMPLEMENTADO / ESCRITO, SIN VERIFICACIÓN`: el artefacto existe, pero falta ejecución real suficiente.
- `🔵 DISEÑADO / DECIDIDO`: arquitectura o criterio acordado todavía no implementado.
- `🟣 HIPÓTESIS / EXPLORACIÓN`: idea en evaluación.
- `❌ PENDIENTE`: trabajo identificado y no realizado.
- `⛔ DESCARTADO`: alternativa que no debe usarse en el estado actual.

## Orden de autoridad

Ante contradicciones, usar este orden:

1. evidencia nueva ejecutada y sus hashes;
2. este `PROJECT_STATE.md`;
3. `PRAGMA-ESTADO-FASE-A-E-INVENTARIO-ESCENA.md`;
4. `PRAGMA-ESTADO-TRASPASO-CLAUDE-A-CODEX.md`;
5. cuaderno A‑E(−1) y su verificación estática;
6. auditorías v4/v3;
7. documentos históricos y conversación.

Un nombre de archivo que contenga `PASS` no prevalece sobre evidencia visual contradictoria.

---

# 1. Resumen Ejecutivo

PRAGMA nació para quitar fondos de imágenes sin abandonar el flujo de trabajo. El caso original era convertir firmas escaneadas con fondo en PNG transparentes para cotizaciones dirigidas a la Universidad Nacional de Ingeniería (Perú). La extensión de Chrome existente resolvía firmas y sellos con un motor por color y ofrecía ISNet para fotografías generales.

El problema no resuelto pasó a ser la **segmentación por instancia**: en una foto con varias personas u objetos, elegir exactamente qué conservar y eliminar todo lo demás. La primera Fase A intentó conservar por separado al señor de la izquierda y a la chica del frente de `P1070614.JPG` mediante SAM 2.1.

La ejecución histórica v4 probó que SAM 2.1 Large funciona técnicamente en Colab/L4 y genera máscaras exportables. Sin embargo, su `PASS` manual fue falso: el señor quedó con erosiones y la chica arrastró parte de una tercera persona. El veredicto vigente es `INCONCLUSIVE`, no `PASS`.

Después, el usuario amplió el objetivo: **descubrir, reconocer, segmentar y hacer seleccionable cada objeto visible posible de la fotografía**. Este objetivo requiere primero definir qué cuenta como objeto y congelar un inventario humano. Por ello se creó la línea A‑E (inventario exhaustivo de escena).

El artefacto ejecutable más reciente es un diagnóstico intermedio A‑E(−1): prueba si SAM 2.1 Large puede separar a la chica de la persona posterior usando punto, caja y correcciones negativas. Está escrito y pasó 68 comprobaciones estáticas, pero no existe evidencia de una ejecución GPU real. Aunque pase, no demostraría inventario total.

Resultado final esperado del producto: una arquitectura modular que proponga, reconozca, seleccione, refine y exporte instancias individuales como PNG transparentes, sin soldar modelos concretos a la interfaz.

---

# 2. Visión, Objetivos y Alcance

## 2.1 Visión central

Permitir que una persona seleccione cualquier instancia relevante de una imagen y obtenga un PNG transparente limpio sin salir de su flujo de trabajo.

## 2.2 Objetivo principal vigente

`🔵 DISEÑADO / DECIDIDO` Construir y validar un pipeline modular para inventariar, reconocer, segmentar y seleccionar objetos individuales en escenas reales.

## 2.3 Objetivos secundarios

- medir cobertura geométrica separada de reconocimiento semántico;
- conservar propuestas etiquetadas y no etiquetadas;
- representar relaciones parte/entero y solapamientos sin borrar evidencia;
- permitir refinamiento interactivo posterior a la selección;
- exportar PNG y evidencia ligados por hashes;
- registrar modelo, peso, entorno, tiempos, memoria, licencia y fallback.

## 2.4 Casos de uso previstos

- firmas y sellos sobre fondo plano;
- extracción de una persona entre varias;
- selección de muebles, cuadros y objetos individuales;
- conservación o eliminación de una instancia concreta;
- exportación de PNG transparente verificable.

## 2.5 Alcance actual

- `🟡` ejecutar A‑E(−1) sobre la chica y la persona posterior;
- `❌` definir A‑E0: ontología e inventario humano de `P1070614.JPG`;
- `❌` ejecutar A‑E1 con `SAM2AutomaticMaskGenerator` y comparar contra el inventario.

## 2.6 Fuera de alcance actualmente

- modificar o rehacer `pragma-extension.zip`;
- FastAPI, servidor local o integración `localhost`;
- Fase B;
- integración de YOLO‑seg;
- integración de BiRefNet;
- reconocimiento automático mediante VLM/captioner;
- afirmar generalización usando una sola fotografía.

## 2.7 Posibles expansiones futuras

- Grounding DINO → SAM 2 con vocabulario oracle;
- SAM 3/3.1, sujeto a licencia, acceso y hardware;
- YOLO‑seg como baseline de vocabulario cerrado;
- BiRefNet como refinador de borde, no como descubridor;
- vocabulario automático después de validar vocabulario oracle;
- FastAPI local y tercer motor de la extensión solo tras superar Fase A‑E.

---

# 3. Evolución del Proyecto

## Hito 1 — Problema original y extensión

- **Problema:** firmas escaneadas rechazadas por conservar fondo.
- **Intento:** extensión Chrome MV3 con motor por color y motor IA ISNet.
- **Resultado reportado:** color funciona bien para firmas/sellos; ISNet sirve para fondos generales, pero no separa selectivamente una persona entre varias.
- **Decisión:** añadir segmentación por instancia sin rehacer la extensión.
- **Certeza:** `ZIP, MANIFEST Y ESTRUCTURA VERIFICADOS`; el código no está extraído en el workspace, sino contenido en `pragma-extension.zip`. El funcionamiento runtime no se reejecutó en esta sesión.

## Hito 2 — Definición de Fase A

- **Objetivo:** validar SAM 2 por clic sobre la foto real antes de construir FastAPI o integración.
- **Aceptación:** conservar por separado al señor y a la chica, eliminar otras personas, cuadros y fondo, registrar tiempos y capturas.
- **Regla:** no avanzar a Fase B hasta validar el método.

## Hito 3 — Primer cuaderno defectuoso

- **Archivo:** `PRAGMA_Fase_A_SAM2.ipynb`.
- **Problemas confirmados:** modelo Small, BF16 fijo pese a recomendar T4, `argmax(scores)`, nombre exacto de foto, ausencia de outputs, veredicto débil.
- **Incidencias observadas durante iteraciones:** carga de foto frágil, `NameError` por ejecutar celdas fuera de orden, `ModuleNotFoundError: sam2`, selector JavaScript invisible y esperas de varios minutos en Brave.
- **Decisión:** rehacer el experimento con contratos, estados y evidencia más rigurosos.

## Hito 4 — v3 autocontenida

- **Cambio:** SAM 2.1 Large, dtype por hardware, tres candidatas visibles, elección manual, historial, `mask_input`, pipeline modular y ZIP por lista blanca.
- **Prueba:** 11/11 controles locales estáticos/sintéticos.
- **Límite:** no se guardó ejecución GPU real del cuaderno en `outputs/`.

## Hito 5 — v4 y ejecución histórica

- **Cambio:** soporte de caja, logits diagnósticos, revisión por modalidades y tokens ligados a evidencia.
- **Prueba estática:** 15/15.
- **Ejecución histórica:** SAM 2.1 Large sobre NVIDIA L4, registrada en documentos de estado.
- **Resultado formal antiguo:** `PASS` por checklist manual.
- **Auditoría posterior:** evidencia visual contradijo el checklist; veredicto corregido a `INCONCLUSIVE`.
- **Contradicción vigente:** el directorio se llamaba `_PASS`, pero no debe interpretarse como aceptación científica.

## Hito 6 — Cambio de alcance a “cada objeto”

- **Solicitud nueva:** reconocer cada objeto posible de la foto.
- **Aprendizaje:** “cada objeto” no es medible sin ontología, granularidad, tiers y ground truth humano.
- **Decisión:** abrir Fase A‑E y separar proponer máscaras, reconocer nombres y refinar bordes.

## Hito 7 — A‑E(−1) portado a un cuaderno independiente

- **Objetivo acotado:** separar la chica de la tercera persona mediante cuatro protocolos.
- **Artefacto:** `PRAGMA_A-E-menos-1_diagnostico_caso_chica_Codex.ipynb`.
- **Verificación:** 68/68 controles estáticos; `experiment_status=NOT_RUN`.
- **Decisión:** ejecutarlo primero si aún interesa el diagnóstico de separación; después realizar A‑E0 antes de probar inventario automático.

## Hito 8 — Transferencia a ChatGPT 6 Sol

- **Solicitud actual:** continuar fuera de Codex, usando ChatGPT 6 Sol.
- **Decisión:** transferencia manual mediante este state file y un paquete con archivos y hashes.
- **Estado:** `✅` paquete preparado; la continuación científica aún no se ha ejecutado.

---

# 4. Estado Actual del Proyecto

- **Último componente trabajado:** diagnóstico A‑E(−1) del caso chica.
- **Último artefacto de implementación vigente:** `outputs/PRAGMA_A-E-menos-1_diagnostico_caso_chica_Codex.ipynb`.
- **Último documento modificado en este traspaso:** `outputs/PROJECT_STATE.md`.
- **Último comando de verificación científica ejecutado:** `python3 work/verify_pragma_ae1_codex.py`.
- **Última operación de entrega:** reconstrucción del ZIP, comprobación del manifiesto SHA‑256 y `unzip -tq`; el hash de transporte queda en `PRAGMA_ChatGPT_6_Sol_Handoff.zip.sha256`.
- **Último resultado observado:** 68 comprobaciones aprobadas, `STATIC_VERIFICATION_PASS`, `experiment_status=NOT_RUN`.
- **Último error material de ejecución:** no existe un error nuevo de A‑E(−1) porque todavía no se ejecutó; errores de importación/JS pertenecen a iteraciones antiguas.
- **Última decisión:** Fase B permanece bloqueada; ejecutar A‑E(−1) y luego crear A‑E0.
- **Último elemento confirmado como funcional:** lógica, sintaxis, estados e integridad estática del cuaderno A‑E(−1).
- **Escrito pero no probado en GPU:** los cuatro protocolos y el flujo de exportación A‑E(−1).
- **Evidencia histórica faltante:** la carpeta `/Users/usuario/Desktop/PRAGMA_Fase_A_v4_20260811T001154Z_6e6a9ae1_PASS/` ya no existe en el filesystem actual. Sus resultados sobreviven solo en documentos de estado.
- **Foto disponible:** `/Users/usuario/Desktop/P1070614.JPG`, hash confirmado.
- **Extensión:** `/Users/usuario/Desktop/pragma-extension.zip` está presente y fue verificado por hash/estructura; no se modificó durante este traspaso.

Estado resumido:

```text
Fase A dirigida por clic       INCONCLUSIVE
A‑E(−1) diagnóstico chica     ESCRITO + STATIC PASS; GPU NOT_RUN
A‑E0 inventario humano        PENDIENTE
A‑E1 SAM2 AMG                 PENDIENTE
Fase B                        BLOQUEADA
SAM 2                         NO RECHAZABLE TODAVÍA
Extensión                     ZIP v1.2.0 VERIFICADO / NO MODIFICADA
```

---

# 5. Avance Fiel y Logros Consolidados

## 5.1 Extensión histórica

**Elemento:** extensión Chrome MV3 con motores Color e ISNet  
**Estado:** `✅ ZIP, MANIFEST Y ESTRUCTURA VERIFICADOS; FUNCIONAMIENTO NO REEJECUTADO`  
**Archivos reportados:** `manifest.json`, `app.html`, `app.js`, `sandbox.html`, `sandbox.js`, `background.js`, `icons/`, `vendor/`  
**Qué hace:** remoción de fondo por color y por IA.  
**Observaciones:** versión 1.2.0; no modificar durante Fase A‑E.

## 5.2 Imagen de aceptación

**Elemento:** `P1070614.JPG`  
**Estado:** `✅ VERIFICADO`  
**Ruta actual:** `/Users/usuario/Desktop/P1070614.JPG`  
**Dimensiones:** `4000 × 2248`  
**Bytes:** `4,260,352`  
**SHA‑256:** `8f6e3b6f5013265a45c7e89121e3f0a18e3386951e2e75378b28da6d02ec529d`  
**Contenido relevante:** señor izquierda, chica al frente, tercera persona posterior, cuadros, mesa, muebles y objetos pequeños.

## 5.3 Pipeline modular

**Estado:** `🟡 IMPLEMENTADO EN CUADERNOS; EVOLUCIÓN FUTURA DISEÑADA`  
**Flujo validado lógicamente:** `NoDetector → Selector → SAM2MaskGenerator → IdentityRefiner → AlphaCompositor`  
**Flujo objetivo A‑E:** propuesta/detección → registro → grafo de solapamiento → etiquetas → selector → refinamiento → compositor.

## 5.4 Verificación de dtype

**Estado:** `✅ VERIFICADO EN LÓGICA; HISTÓRICAMENTE EJECUTADO EN L4`  
**Política:** T4/CC 7.5 → FP16; Ampere+ → BF16; CPU → FP32.  
**Motivo:** evitar BF16 nativo no soportado en T4.

## 5.5 Candidatas y selección

**Estado:** `✅ VERIFICADO EN DISEÑO/LÓGICA; CONFIRMADO COMO NECESARIO POR CORRIDA HISTÓRICA`  
**Regla:** mostrar todas las candidatas; nunca elegir por `argmax` para representar intención humana.

## 5.6 Evidencia e integridad

**Estado:** `🟡 IMPLEMENTADO, SIN EJECUCIÓN A‑E(−1)`  
**Incluye:** IDs, hashes, alpha, RGBA, galerías, closeups, manifiesto, ZIP por lista blanca y reapertura verificable.

## 5.7 A‑E(−1)

**Estado:** `🟡 IMPLEMENTADO / ESCRITO, SIN VERIFICACIÓN GPU`  
**Protocolos:** `point`, `box`, `point+corrections`, `box+corrections`.  
**Protecciones:** sin JavaScript obligatorio; prompts separados de holdouts; revisión humana ligada por `selection_id`; fallo de una candidata no se eleva a fallo del caso.

---

# 6. Arquitectura Actual

## 6.1 Arquitectura de validación vigente

```text
P1070614.JPG verificada por SHA‑256
            │
            ▼
      NoDetector / prompts fijos
            │
            ▼
  Selector de protocolo (punto/caja/correcciones)
            │
            ▼
     SAM2MaskGenerator (Large)
            │
            ├── 3 candidatas iniciales
            └── 1 candidata por refinamiento con mask_input
            │
            ▼
      Revisión humana + sentinelas holdout
            │
            ▼
 AlphaCompositor → PNG/alpha/capturas/closeups
            │
            ▼
 reporte + manifiesto + ZIP verificado
```

## 6.2 Arquitectura objetivo A‑E

```text
Imagen verificada
  → SceneInventory / ground truth humano
  ├─ ClassAgnosticProposer
  └─ ConceptSegmenter
  → ProposalRegistry inmutable
  → OverlapContainmentGraph
  → LabelResolver
  → GallerySelector por ID estable
  → InteractiveRefiner
  → AlphaRefiner (fase posterior)
  → Compositor + evidencias + manifiesto
```

## 6.3 Flujo de datos principal

1. validar foto por hash y dimensiones;
2. obtener propuestas geométricas;
3. conservar máscara, bbox, score, procedencia y parámetros;
4. mapear propuestas contra inventario/GT;
5. seleccionar por ID estable;
6. refinar solo la propuesta elegida;
7. componer alpha y PNG;
8. guardar evidencia y hashes;
9. calcular estado sin confundir componentes.

---

# 7. Estructura de Directorios

`TREE PARCIAL BASADO EN ARCHIVOS CONFIRMADOS`

```text
referenced-chatgpt-conversation-this-is-an/
├── outputs/
│   ├── PROJECT_STATE.md
│   ├── START_HERE_CHATGPT_6_SOL.md
│   ├── PRAGMA_ChatGPT_6_Sol_Handoff/
│   │   ├── PROJECT_STATE.md
│   │   ├── START_HERE_CHATGPT_6_SOL.md
│   │   ├── HANDOFF_MANIFEST_SHA256.txt
│   │   ├── inputs/
│   │   ├── outputs/
│   │   └── work/
│   ├── PRAGMA_ChatGPT_6_Sol_Handoff.zip
│   ├── PRAGMA_ChatGPT_6_Sol_Handoff.zip.sha256
│   ├── PRAGMA-ESTADO-FASE-A-E-INVENTARIO-ESCENA.md
│   ├── PRAGMA-ESTADO-FASE-A-v3.md
│   ├── PRAGMA-ESTADO-TRASPASO-CLAUDE-A-CODEX.md
│   ├── PRAGMA_A-E-menos-1_diagnostico_caso_chica_Codex.ipynb
│   ├── PRAGMA_A-E-menos-1_Codex_verificacion.json
│   ├── PRAGMA_Fase_A_SAM2.ipynb
│   ├── PRAGMA_Fase_A_SAM2_v3_autocontenido.ipynb
│   ├── PRAGMA_Fase_A_SAM2_v4_autocontenido.ipynb
│   ├── PRAGMA_Fase_A_SAM2_v4_ligero.ipynb
│   ├── PRAGMA_Fase_A_v3_auditoria.md
│   ├── PRAGMA_Fase_A_v3_verificacion.json
│   ├── PRAGMA_Fase_A_v4_auditoria.md
│   ├── PRAGMA_Fase_A_v4_verificacion.json
│   └── claude_originals/
│       ├── PRAGMA_A-E-1_cierre_fase_A_celdas.md
│       └── PRAGMA_Fase_A_v4_parche.md
└── work/
    ├── build_pragma_ae1_codex.py
    ├── verify_pragma_ae1_codex.py
    ├── build_pragma_phase_a_v3.py
    ├── build_pragma_phase_a_v4.py
    ├── build_pragma_phase_a_v4_light.py
    └── otros scripts/celdas históricos
```

Fuera del workspace:

```text
/Users/usuario/Desktop/P1070614.JPG    # presente y verificada
```

El código de la extensión no está extraído en este workspace, pero el ZIP verificado existe en `/Users/usuario/Desktop/pragma-extension.zip`.

---

# 8. Inventario de Archivos

| Archivo | Ruta | Función | Estado | Última información conocida |
|---|---|---|---|---|
| `PROJECT_STATE.md` | `outputs/` | Fuente de verdad portable | ✅ | v1.0, 2026‑09‑22 |
| `START_HERE_CHATGPT_6_SOL.md` | `outputs/` | instrucciones y prompt inicial | ✅ | entregar con el bundle |
| `PRAGMA_ChatGPT_6_Sol_Handoff/` | `outputs/` | árbol portable con layout ejecutable | ✅ | manifiesto interno verifica payloads |
| `HANDOFF_MANIFEST_SHA256.txt` | dentro del handoff | hashes internos | ✅ | validado con `shasum -c` |
| `PRAGMA_ChatGPT_6_Sol_Handoff.zip` | `outputs/` | archivo único de transferencia | ✅ | integridad comprobada con `unzip -tq`; hash en sidecar externo |
| `PRAGMA_ChatGPT_6_Sol_Handoff.zip.sha256` | `outputs/` | hash de transporte no autorreferencial | ✅ | adjuntar junto al ZIP |
| `P1070614.JPG` | Desktop / paquete de transferencia | Foto de aceptación | ✅ | hash `8f6e3b…529d` |
| `PRAGMA_A-E-menos-1_diagnostico_caso_chica_Codex.ipynb` | `outputs/` | Experimento A‑E(−1) | 🟡 | 23 celdas, 10 de código, 0 outputs, hash `5941be…b706` |
| `PRAGMA_A-E-menos-1_Codex_verificacion.json` | `outputs/` | 68 controles estáticos | ✅ estático | `experiment_status=NOT_RUN`, hash `7067f1…9581` |
| `PRAGMA-ESTADO-FASE-A-E-INVENTARIO-ESCENA.md` | `outputs/` | Estado científico previo | ✅ documental | autoridad anterior, hash `798c48…e46` |
| `PRAGMA-ESTADO-TRASPASO-CLAUDE-A-CODEX.md` | `outputs/` | Provenance del port | ✅ documental | hash `8e3ea6…6c02` |
| `PRAGMA_Fase_A_SAM2_v4_ligero.ipynb` | `outputs/` | Base histórica inmediata | 🟡 / supersedida | no se prueba que sea byte a byte la corrida antigua; hash `757e97…814a` |
| `PRAGMA_Fase_A_v4_auditoria.md` | `outputs/` | Auditoría de v4 | ✅ documental | hash `632f59…281d` |
| `PRAGMA_Fase_A_v4_verificacion.json` | `outputs/` | 15 pruebas estáticas/sintéticas | ✅ estático | hash `a7f92d…97cd9` |
| `PRAGMA_Fase_A_v3_auditoria.md` | `outputs/` | auditoría v3 | ✅ documental / histórica | hash `8cdf04…fde3` |
| `PRAGMA_Fase_A_v3_verificacion.json` | `outputs/` | 11 pruebas estáticas/sintéticas | ✅ estático / histórico | hash `86d9c2…5479` |
| `PRAGMA_Fase_A_SAM2_v4_autocontenido.ipynb` | `outputs/` | v4 histórica con foto | ⛔ supersedida | 0 outputs, hash `148ea1…f1270db` |
| `PRAGMA_Fase_A_SAM2_v3_autocontenido.ipynb` | `outputs/` | v3 histórica con foto | ⛔ supersedida | 0 outputs, hash `3d9b75…0a4157` |
| `PRAGMA_Fase_A_SAM2.ipynb` | `outputs/` | primer cuaderno | ⛔ no usar | Small/BF16/argmax, hash `56a6e2…a33d` |
| `PRAGMA-ESTADO-FASE-A-v3.md` | `outputs/` | estado v3 | ⛔ supersedido | hash `43ccd5…4290` |
| `PRAGMA_A-E-1_cierre_fase_A_celdas.md` | `outputs/claude_originals/` | propuesta histórica Claude | ⛔ no aplicar literalmente | hash `7e832f…4e91` |
| `PRAGMA_Fase_A_v4_parche.md` | `outputs/claude_originals/` | parche histórico Claude | ⛔ no aplicar literalmente | hash `d5c05f…fe722` |
| `build_pragma_ae1_codex.py` | `work/` | genera el cuaderno vigente | ✅ archivo presente | uso de mantenimiento |
| `verify_pragma_ae1_codex.py` | `work/` | verificación local | ✅ ejecutado | produjo 68/68 |
| carpeta histórica `_PASS` | ruta Desktop documentada | 16 evidencias v4 | INFORMACIÓN HISTÓRICA; ARCHIVOS AUSENTES | no transferible actualmente |
| `pragma-extension.zip` | `/Users/usuario/Desktop/` | extensión Chrome MV3 v1.2.0 | ✅ ZIP/estructura | 3,528,382 bytes; hash `a7fa93…9d80`; no modificar |

---

# 9. Componentes y Responsabilidades

## 9.1 Motor Color de la extensión

- **Responsabilidad:** eliminar un color de fondo elegido o detectado.
- **Entrada:** imagen y color/tolerancia.
- **Salida:** capa RGBA.
- **Estado:** `✅ CÓDIGO VERIFICADO EN EL ZIP; FUNCIONAMIENTO ACTUAL NO REEJECUTADO EN ESTA SESIÓN`.
- **Uso previsto:** firmas, sellos y fondos planos.

## 9.2 Motor IA ISNet

- **Responsabilidad:** remoción general de fondo.
- **Entrada:** imagen.
- **Salida:** RGBA base que después recibe acabado sin repetir inferencia.
- **Dependencias:** `@imgly/background-removal`, ONNX Runtime WASM, modelo `isnet_fp16` medium descargado y guardado en Cache Storage.
- **Estado:** `✅ ESTRUCTURA/CÓDIGO VERIFICADOS EN EL ZIP; INFERENCIA NO REEJECUTADA AQUÍ`.
- **Problema conocido:** no resuelve selección arbitraria de una instancia entre varias.

## 9.3 Sandbox MV3

- **Responsabilidad:** ejecutar el motor IA en un origen aislado compatible con las restricciones de Manifest V3.
- **Entradas/salidas:** mensajes entre `app.js` y `sandbox.js`.
- **Estado:** `✅ PRESENTE EN ZIP`.

## 9.4 `FixedProtocolSelector`

- **Responsabilidad:** convertir un protocolo nombrado en puntos, etiquetas y/o caja.
- **Entrada:** imagen, clave de protocolo, detecciones.
- **Salida:** `AEM1PromptBundle`.
- **Estado:** `🟡 ESCRITO Y VERIFICADO ESTÁTICAMENTE`.

## 9.5 `SAM2MaskGenerator`

- **Responsabilidad:** generar candidatas SAM 2.1 y devolver máscara, scores y logits.
- **Entrada:** imagen embebida, puntos/caja, `mask_input` opcional.
- **Salida:** candidatas iniciales o refinada.
- **Estado:** `🟡 ESCRITO; A‑E(−1) NO EJECUTADO`.

## 9.6 Sentinelas holdout

- **Responsabilidad:** falsar localmente pérdidas o contaminación sin reutilizar puntos enviados al modelo.
- **Entrada:** máscara candidata.
- **Salida:** cobertura KEEP y fuga separada para otra persona/fondo.
- **Estado:** `✅ LÓGICA PROBADA CON DATOS SINTÉTICOS; COORDENADAS REALES REQUIEREN CONFIRMACIÓN VISUAL`.
- **Límite:** pasar los sentinelas no prueba que toda la máscara sea correcta.

## 9.7 Revisión y binding

- **Responsabilidad:** impedir que checkboxes antiguos se apliquen a una máscara nueva.
- **Entrada:** propuesta, candidata, configuración, revisión humana.
- **Salida:** `selection_id`, `inspection_token`, estado y evidencia ligada.
- **Estado:** `✅ LÓGICA ESTÁTICA; FLUJO HUMANO NO EJECUTADO`.

## 9.8 Compositor y exportador

- **Responsabilidad:** producir RGBA/alpha/capturas y un ZIP verificable.
- **Estado:** `🟡 ESCRITO; EXPORT A‑E(−1) NO EJECUTADO`.

## 9.9 Componentes A‑E futuros

- `SceneInventory`: ground truth humano — `❌`.
- `ClassAgnosticProposer`: SAM2 AMG — `🔵`.
- `ConceptSegmenter`: SAM3 o Grounding DINO→SAM2 — `🟣`.
- `ProposalRegistry`: inmutable y addressable — `🔵`.
- `OverlapContainmentGraph`: relaciones/duplicados — `🔵`.
- `LabelResolver`: nombres/sinónimos/unlabeled — `🔵`.
- `InteractiveRefiner`: puntos/caja sobre propuesta — parcialmente implementado en A‑E(−1).
- `AlphaRefiner`: BiRefNet futuro — `❌`.

---

# 10. Decisiones Técnicas y de Diseño

### DEC-001 — Validar antes de integrar

**Decisión:** demostrar el modelo sobre la foto real antes de FastAPI o extensión.  
**Motivación:** evitar construir infraestructura alrededor de un método que no resuelve el caso.  
**Alternativas:** integrar primero.  
**Descarte:** aumentaría coste y ocultaría el fallo del modelo.  
**Estado:** vigente.

### DEC-002 — Pipeline intercambiable

**Decisión:** separar propuesta/detección, selector, máscara, refinamiento y compositor.  
**Consecuencia:** YOLO, SAM y BiRefNet no son “modos” soldados a UI.  
**Estado:** vigente.

### DEC-003 — SAM 2.1 Large como techo de validación

**Decisión:** no rechazar SAM tras probar únicamente Small.  
**Consecuencia:** más peso/coste, pero menor riesgo de falso rechazo.  
**Estado:** vigente en A‑E(−1).

### DEC-004 — Dtype por hardware

**Decisión:** T4→FP16, Ampere+→BF16, CPU→FP32.  
**Alternativa descartada:** BF16 fijo.  
**Estado:** vigente.

### DEC-005 — Prohibido `argmax` semántico

**Decisión:** la persona elige entre candidatas visibles.  
**Motivación:** IoU predicho no expresa “objeto completo deseado”.  
**Estado:** vigente.

### DEC-006 — Alpha binaria y logits diagnósticos separados

**Decisión:** no llamar matting a una sigmoid de logits.  
**Estado:** vigente.

### DEC-007 — PASS ligado a evidencia

**Decisión:** propuesta, índice, máscara, configuración, revisión y archivos deben quedar ligados por hashes/tokens.  
**Estado:** vigente.

### DEC-008 — A‑E(−1) no equivale a A‑E1

**Decisión:** renombrar el diagnóstico de chica como A‑E(−1), reservando A‑E1 para SAM2 AMG.  
**Estado:** vigente.

### DEC-009 — Ontología antes de “todo”

**Decisión:** no medir exhaustividad sin inventario/tiers humanos.  
**Estado:** vigente; implementación pendiente.

### DEC-010 — Separar segmentación de reconocimiento

**Decisión:** una máscara sin nombre puede ser éxito geométrico; una etiqueta con mala máscara no lo es.  
**Estado:** vigente.

### DEC-011 — No usar JS interactivo como camino obligatorio

**Decisión:** A‑E(−1) usa coordenadas y formularios, con fallback de archivos para Brave.  
**Motivación:** los `eval_js` previos podían quedar invisibles/bloqueados.  
**Estado:** vigente.

### DEC-012 — Mantener Fase B bloqueada

**Decisión:** ningún PASS textual antiguo ni éxito A‑E(−1) desbloquea el producto.  
**Estado:** vigente.

---

# 11. Tecnologías, Dependencias y Entorno

| Tecnología | Versión | Uso | Estado |
|---|---:|---|---|
| Python | versión de Colab, no fijada | cuadernos y verificación | 🟡 |
| PyTorch | versión de Colab, no fijada | inferencia SAM 2 | 🟡 |
| SAM 2 oficial | commit se registra al ejecutar; no pin previo | segmentación | 🟡 |
| `sam2.1_hiera_large` | SAM 2.1 | modelo A‑E(−1) | 🟡 |
| Checkpoint Large | históricamente 898,083,611 bytes | pesos | ✅ histórico / ❌ nuevo run |
| NumPy | no fijada | máscaras y métricas | 🟡 |
| Pillow | no fijada | imagen/PNG | 🟡 |
| Matplotlib | no fijada | galerías y overlays | 🟡 |
| Google Colab | servicio actual | GPU y ejecución | ❌ run A‑E(−1) pendiente |
| NVIDIA L4 | histórica | corrida v4 | ✅ histórico |
| T4/A100/L4 | según disponibilidad | ejecución futura | 🔵 |
| Chrome Manifest V3 | `manifest_version: 3` | extensión | ✅ archivo |
| ONNX Runtime Web/WASM | vendorizado | ISNet | ✅ archivo |
| Brave | versión no disponible | navegador usado con Colab | riesgo UX conocido |
| macOS | versión no disponible | host del usuario | ✅ contexto |
| ChatGPT Work | servicio | destino del traspaso | ✅ documentado por OpenAI; disponibilidad/UI según cuenta |
| GPT‑6 Sol | `gpt-6-sol` en API; UI según selector | agente deseado | ✅ modelo documentado / ejecución aún pendiente |

Dependencias de red de A‑E(−1): GitHub de Meta para repositorio y servidor de Meta para checkpoint. No hay credenciales incluidas.

Referencias oficiales de la transferencia: <https://learn.chatgpt.com/docs/get-started-with-work> y <https://developers.openai.com/api/docs/models> (consultadas el 2026‑09‑22). Si la interfaz real no muestra `Work locally` o `6 Sol`, registrar lo que aparece y no afirmar que se usó esa opción.

---

# 12. Configuración Importante

## 12.1 Imagen

```text
SHA256 = 8f6e3b6f5013265a45c7e89121e3f0a18e3386951e2e75378b28da6d02ec529d
WIDTH  = 4000
HEIGHT = 2248
```

El nombre puede variar; el contenido no.

## 12.2 Rutas Colab A‑E(−1)

```text
repo       /content/pragma_sam2_official
work       /content/pragma_run
checkpoint /content/pragma_run/checkpoints/sam2.1_hiera_large.pt
runs       /content/pragma_run/runs/<RUN_ID>
```

La foto se busca en `/mnt/data/P1070614.JPG`, `/content/P1070614.JPG` o la carpeta de trabajo y se valida por hash.

## 12.3 Protocolos obligatorios A‑E(−1)

```text
point
box
point+corrections
box+corrections
```

## 12.4 Configuración de sentinelas

- caja chica XYXY: `(2100, 300, 3500, 2247)`;
- prompt positivo principal: `(2588, 1785)`;
- tres prompts negativos sobre la persona posterior;
- siete KEEP del sujeto;
- cuatro DROP de otra persona;
- tres DROP de fondo;
- radio de parche: `6`;
- KEEP mínimo local: `0.80`;
- DROP máximo local: `0.20`.

Estas coordenadas están escritas, pero `AEM1_CONFIG_CONFIRMADA` debe permanecer `False` hasta revisar el overlay.

## 12.5 Modelo y precisión

```text
config     configs/sam2.1/sam2.1_hiera_l.yaml
checkpoint sam2.1_hiera_large.pt
T4         float16
Ampere+    bfloat16
CPU        float32
```

No degradar silenciosamente a Small.

## 12.6 Extensión verificada

```text
archivo      /Users/usuario/Desktop/pragma-extension.zip
versión      1.2.0
SHA‑256      a7fa93d23e4ca81c2dd261049760a0841a1169e1c6f57c087192d9ffc48a9d80
comprimido   3,528,382 bytes
descomprimido listado 13,719,897 bytes
modelo ISNet medium = isnet_fp16
```

El manifiesto declara `contextMenus`, `clipboardWrite` y `host_permissions: <all_urls>`. No cambiar permisos durante Fase A‑E.

## 12.7 Secretos

No se encontraron claves, tokens ni credenciales. Si en el futuro se usa Hugging Face/API:

```text
<SECRET_REDACTED>
```

Nunca guardar secretos en el cuaderno, state file o ZIP.

---

# 13. Contratos, Protocolos y Formatos

## 13.1 Contrato conceptual vigente

```text
detección/propuestas → selector → máscara → refinamiento → compositor
```

Cada etapa debe poder sustituirse sin rehacer la UI.

## 13.2 `SceneObject` futuro

Campos diseñados:

```text
id, canonical_name, synonyms, tier, bbox, optional_gt_mask,
occlusion, truncation, parent_id, ignore_reason
```

Estado: `🔵 DISEÑADO`.

## 13.3 `Proposal` futuro

```text
stable_id, mask_or_rle, bbox, area, score, source_model,
prompt, parameters, elapsed_s, sha256, parent_child_relations
```

Estado: parcialmente implementado en A‑E(−1), contrato completo A‑E pendiente.

## 13.4 Estados A‑E(−1)

- `PENDING_CONFIG`
- `PENDING_PROTOCOLS`
- `PENDING_REVIEW`
- `PENDING_REVIEW_BINDING`
- `PENDING_NOTES`
- `PENDING_STALE_*`
- `SEPARATION_DEMONSTRATED_UNDER_FIXED_AEM1_PROTOCOL`
- `INCONCLUSIVE_SELECTED_OUTPUT_FAILED`

El reporte siempre mantiene:

```json
{
  "project_status": "INCONCLUSIVE_A_E0_REQUIRED",
  "phase_b_blocked": true,
  "sam2_rejectable": false
}
```

## 13.5 Bundle de ejecución esperado

El ZIP A‑E(−1) debe incluir configuración, overlay, propuestas, galerías, selección, alpha, RGBA, captura, closeups, reporte y manifiesto. Cada payload queda listado con bytes y SHA‑256 y el ZIP se reabre para comprobarlos.

---

# 14. Fragmentos de Código Críticos

## 14.1 Política de dtype

```python
if not torch.cuda.is_available():
    device, dtype = "cpu", torch.float32
elif torch.cuda.get_device_capability()[0] >= 8:
    device, dtype = "cuda", torch.bfloat16
else:
    device, dtype = "cuda", torch.float16
```

Estado: lógica verificada; el código exacto vigente debe leerse del cuaderno.

## 14.2 Refinamiento iterativo

```python
mask_input = previous.low_res_logits[seed_index][None, :, :]
multimask_output = False
```

Estado: implementado en A‑E(−1), no ejecutado.

## 14.3 Regla de evidencia

El estado terminal depende de configuración confirmada, cuatro protocolos, selección válida, revisión ligada, cuatro criterios visuales y sentinelas. Los sentinelas por sí solos nunca producen éxito.

---

# 15. Comandos Importantes

## 15.1 Verificación vigente

```bash
python3 work/verify_pragma_ae1_codex.py
```

**Propósito:** validar estructura, sintaxis, estados, hashes y lógica del cuaderno A‑E(−1).  
**Resultado conocido:** 68/68, `STATIC_VERIFICATION_PASS`, `NOT_RUN`.  
**Estado:** `✅ EJECUTADO`.

## 15.2 Regeneración del cuaderno

```bash
python3 work/build_pragma_ae1_codex.py
```

**Propósito:** reconstruir el notebook a partir del script generador.  
**Resultado conocido:** produjo el artefacto actual durante la sesión anterior.  
**Estado:** `✅ USADO HISTÓRICAMENTE`; no ejecutar sin revisar porque puede sobrescribir el cuaderno vigente.

## 15.3 Carga de extensión futura

La regla histórica exige probar cualquier modificación mediante Chrome con `--load-extension`. El comando exacto no está preservado en el contexto actual: `INFORMACIÓN NO DISPONIBLE`.

---

# 16. Pruebas y Evidencia

| Prueba | Componente | Esperado | Observado | Estado |
|---|---|---|---|---|
| JSON/AST A‑E(−1) | notebook | válido | 10/10 celdas parsean | ✅ |
| Suite A‑E(−1) | lógica | todos los checks | 68/68 | ✅ estático |
| Ejecución GPU A‑E(−1) | SAM 2 | cuatro protocolos y ZIP | no ejecutada | ❌ |
| Foto/hash | entrada | exacta | coincide | ✅ |
| Dtype T4/Ampere/CPU | entorno | FP16/BF16/FP32 | matriz lógica aprobada | ✅ lógica |
| Alpha 0.5→128 | compositor | preservar matte | self-test pasa | ✅ sintético |
| Estado anti-falso PASS | auditor | bloquear evidencia caduca | tabla lógica pasa | ✅ sintético |
| ZIP A‑E(−1) | exportador | roundtrip y hashes | solo lógica; no ZIP real | 🟡 |
| v3 | notebook | controles locales | 11/11 | ✅ estático; supersedido |
| v4 | notebook | controles locales | 15/15 | ✅ estático; supersedido |
| v4 histórica L4 | SAM 2 | aislar dos sujetos | técnicamente ejecutó; calidad insuficiente | ✅ ejecución / ❌ aceptación |
| Señor histórico | máscara | limpio/completo | aislamiento grueso con erosiones | ❌ aceptación |
| Chica histórica | máscara | excluir persona posterior | contaminación y pérdidas | ❌ aceptación |
| Inventario humano A‑E0 | GT | lista/tiers/bboxes/máscaras | inexistente | ❌ |
| SAM2 AMG A‑E1 | propuesta | métricas vs GT | no ejecutado | ❌ |
| Reconocimiento abierto | etiquetas | oracle y negativos | no ejecutado | ❌ |
| Generalización | producto | varias imágenes | una sola foto | ❌ |

Todos los notebooks conservados en `outputs/` tienen `execution_count=null` y cero outputs. No presentar sus suites estáticas como evidencia de inferencia real.

---

# 17. Errores, Incidencias y Debugging

### BUG-001 — BF16 fijo sobre T4

**Síntoma:** riesgo de `RuntimeError` o emulación/ineficiencia.  
**Contexto:** primer cuaderno recomendaba T4 y forzaba BF16.  
**Corrección escrita:** dispatch por capability.  
**Estado:** solucionado en artefactos nuevos; no ejecutar el original.

### BUG-002 — Foto no encontrada o nombre rígido

**Síntoma:** `FileNotFoundError` tras subida; antes se esperaba nombre exacto.  
**Corrección:** validación por hash y búsqueda en rutas conocidas.  
**Estado:** implementado; requiere prueba A‑E(−1).

### BUG-003 — `EXPECTED_IMAGE_SHA256` no definido

**Síntoma:** `NameError` al ejecutar una celda sin haber ejecutado la anterior.  
**Contexto:** versión ligera intermedia.  
**Mitigación:** cuaderno actual ordenado y autocontenido por flujo.  
**Estado:** histórico; no reproducido en A‑E(−1).

### BUG-004 — `ModuleNotFoundError: sam2`

**Síntoma:** import falló en una ejecución intermedia.  
**Hipótesis:** instalación/celda previa no ejecutada o path no incorporado.  
**Corrección escrita:** instalación editable desde repo nombrado y `sys.path` explícito.  
**Estado:** histórico; A‑E(−1) sin prueba runtime.

### BUG-005 — Selector invisible y espera prolongada en Brave

**Síntoma:** celda girando 4–46 minutos esperando clic.  
**Causa:** `eval_js` bloqueante dentro de outputframe y Promise/UI invisible.  
**Corrección vigente:** A‑E(−1) elimina ese camino obligatorio.  
**Estado:** evitado por diseño; `files.upload/download` aún pueden depender del frontend.

### BUG-006 — PASS manual falso

**Síntoma:** carpeta/reporte decía PASS pese a contaminación visible.  
**Causa:** checklist editable no ligado suficientemente al agotamiento/evidencia visual.  
**Corrección:** tokens, hashes, closeups y estados conservadores.  
**Estado:** el resultado histórico permanece corregido a `INCONCLUSIVE`; el nuevo mecanismo no tiene prueba humana real.

### BUG-007 — Evidencia histórica ausente

**Síntoma:** la carpeta v4 de 16 archivos ya no se encuentra.  
**Impacto:** una nueva IA no puede reauditar directamente capturas/raw outputs.  
**Siguiente prueba:** recuperar el ZIP/carpeta original si existe en Drive, Descargas, Papelera o respaldo.  
**Estado:** abierto.

---

# 18. Bloqueos y Riesgos

## Bloqueos actuales

| Bloqueo | Probabilidad | Impacto | Mitigación |
|---|---:|---:|---|
| A‑E(−1) no ejecutado | segura | alto | ejecutar en Colab y conservar notebook+ZIP |
| A‑E0 inexistente | segura | crítico para “todos los objetos” | definir ontología/inventario/GT antes de modelos exhaustivos |
| Evidencia v4 raw ausente | alta mientras no se recupere | medio | recuperar respaldo; mantener conclusión documental como histórica |
| Definición de “objeto” no ratificada | segura | crítico | resolver preguntas de granularidad/tier/tamaño |

## Riesgos técnicos

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---:|---:|---|
| SAM2 repo usa HEAD no fijado antes del run | media | alta | fijar commit después de primera corrida validada o registrar y repetir con ese commit |
| OOM/entorno Colab | baja-media en L4/A100 | alta | capturar estado, no degradar modelo en silencio, limpiar cache y reportar `INCONCLUSIVE_ENVIRONMENT` |
| errores humanos de inspección | media | alta | closeups, checklist ligado, segunda revisión independiente |
| sentinelas pasan pero hay fuga entre ellos | media | alta | no auto-PASS; inspección completa y luego GT real |
| `files.upload/download` se bloquea en Brave | media | media | detener celda y usar panel Archivos |

## Riesgos de arquitectura

- fusionar destructivamente propuestas parte/entero;
- confundir labeler con segmentador;
- permitir que la UI llame directamente a modelos globales;
- introducir BiRefNet antes de resolver cobertura/selección;
- convertir un benchmark de una foto en decisión de producto.

## Riesgos de compatibilidad

- cambios futuros en API de SAM 2 por no fijar commit;
- versiones de Python/PyTorch/Colab no congeladas;
- Manifest V3 y políticas del navegador pueden evolucionar;
- permisos `<all_urls>` requieren revisión de seguridad antes de distribución.

## Riesgos de producto / UX

- galería con demasiadas propuestas duplicadas;
- “cada objeto” produce partes/objetos solapados difíciles de entender;
- una máscara técnicamente válida puede no coincidir con la intención del usuario;
- exportar todos los objetos puede resultar lento y abrumador.

## Dependencias externas críticas

- Google Colab/GPU;
- repositorio y checkpoint oficiales de Meta;
- licencia/acceso de modelos futuros;
- navegador y conectividad;
- revisión humana del usuario.

---

# 19. Backlog Pendiente

## P0 — Crítico / siguiente paso obligatorio

### P0-1 — Ejecutar A‑E(−1)

- **Acción:** ejecutar el cuaderno vigente sobre la foto exacta y completar los cuatro protocolos.
- **Motivo:** el artefacto actual solo tiene verificación estática.
- **Dependencia:** Colab con GPU y la foto.
- **Criterio de finalización:** notebook ejecutado + ZIP íntegro + revisión visual independiente.

### P0-2 — Auditar el resultado A‑E(−1)

- **Acción:** verificar manifiesto/hashes y revisar alpha, damero y closeups.
- **Motivo:** evitar otro PASS basado solo en checkboxes.
- **Criterio:** estado defendible y state file actualizado.

### P0-3 — Ratificar definición de objeto

- **Acción:** responder las preguntas de granularidad, tamaño, partes, stuff, texto, reflejos y nomenclatura.
- **Criterio:** contrato A‑E0 firmado conceptualmente por el usuario.

### P0-4 — Crear A‑E0

- **Acción:** producir `scene_inventory.json`, lámina numerada, bboxes y GT de las tres personas.
- **Dependencia:** P0-3.
- **Criterio:** inventario congelado por hash y revisado.

## P1 — Alta prioridad

### P1-1 — Implementar A‑E1 con SAM2 AMG

- **Acción:** sweep pequeño prefijado, salida RLE y registro inmutable.
- **Dependencia:** A‑E0.
- **Criterio:** métricas de cobertura, duplicación, fraccionamiento, separación, tiempo y memoria.

### P1-2 — Recuperar evidencia histórica v4

- **Acción:** buscar ZIP/carpeta en Drive/Descargas/Papelera/backups.
- **Criterio:** bytes y hashes coinciden con reporte documentado o se declara pérdida definitiva.

### P1-3 — Fijar reproducibilidad

- **Acción:** pinnear commit SAM2 y documentar versiones tras corrida válida.
- **Criterio:** segunda corrida reproduce resultados dentro de tolerancia declarada.

## P2 — Media prioridad

### P2-1 — A‑E2 reconocimiento oracle

- comparar una opción a la vez: SAM3 o Grounding DINO→SAM2;
- usar vocabulario humano completo y conceptos negativos;
- separar label recall/precision de IoU.

### P2-2 — A‑E3 unión y selección

- construir grafo de solapamiento/containment;
- conservar `unlabeled` y jerarquías;
- probar selección/exportación por ID estable.

### P2-3 — Dataset adicional

- añadir al menos cuatro casos no bloqueantes de dificultad distinta;
- definir criterios de generalización.

## P3 — Baja prioridad / futuro

- vocabulario automático;
- BiRefNet como AlphaRefiner;
- FastAPI local/MPS;
- tercer motor en extensión;
- UX final de galería y refinamiento;
- endurecimiento de permisos/distribución de extensión.

---

# 20. Ideas y Exploraciones No Comprometidas

- `HIPÓTESIS / EXPLORACIÓN — NO IMPLEMENTADA`: SAM 3/3.1 para todas las instancias de un concepto abierto.
- `HIPÓTESIS / EXPLORACIÓN — NO IMPLEMENTADA`: Grounding DINO→SAM2 con vocabulario oracle.
- `HIPÓTESIS / EXPLORACIÓN — NO IMPLEMENTADA`: YOLO‑seg como baseline rápido de clases cerradas.
- `HIPÓTESIS / EXPLORACIÓN — NO IMPLEMENTADA`: VLM/captioner como `AutoVocabularyProvider` después de validar oracle.
- `HIPÓTESIS / EXPLORACIÓN — NO IMPLEMENTADA`: interfaz jerárquica que permita seleccionar persona, cara o ropa.
- `HIPÓTESIS / EXPLORACIÓN — NO IMPLEMENTADA`: exportación masiva de un PNG por objeto.

---

# 21. Alternativas Descartadas

## BF16 fijo en T4

- **Motivo de consideración:** mayor precisión/rendimiento en GPUs nuevas.
- **Descarte:** T4 no tiene BF16 nativo.
- **Reconsideración:** solo en Ampere+.

## Seleccionar por mayor score (`argmax`)

- **Motivo:** automatización simple.
- **Descarte:** la candidata con mejor score puede ser una parte/prenda y no la instancia completa.
- **Reconsideración:** nunca como sustituto de intención; solo ranking diagnóstico.

## Small como prueba definitiva

- **Descarte:** podría producir falso rechazo del método.
- **Reconsideración:** benchmarking de rendimiento después de validar calidad con Large.

## Sigmoid de logits como matting

- **Descarte:** crea banda suave/neblina, no recupera pelo perdido ni alpha calibrada.
- **Reconsideración:** solo preview diagnóstica.

## Pegar literalmente parches Claude

- **Descarte:** placeholders, incompatibilidades ABI, evaluación circular y flujo incompleto.
- **Reconsideración:** ninguna; extraer ideas y reimplementarlas con contratos vigentes.

## Construir FastAPI/Fase B antes de validar

- **Descarte:** infraestructura prematura.
- **Reconsideración:** únicamente tras `PASS_A_E` ratificado.

## Usar prompt “everything” como prueba de exhaustividad

- **Descarte:** no define ontología ni demuestra objetos omitidos.
- **Reconsideración:** nunca como única prueba.

---

# 22. Preguntas Abiertas

1. ¿“Objeto” incluye solo instancias enteras o también partes y regiones `stuff`?
2. ¿Cuál es el tamaño/área mínima?
3. ¿Cuentan texto, reflejos, sombras y objetos casi totalmente ocultos?
4. ¿Basta una región seleccionable sin nombre?
5. ¿Se requiere jerarquía persona/cara/ropa?
6. ¿Inventario/UI en español y prompts internos bilingües?
7. ¿Todo debe correr offline/local o se permiten APIs y modelos gated?
8. ¿Se acepta licencia/acceso de SAM3/3.1?
9. ¿Presupuesto máximo de GPU, RAM, tiempo y cantidad de máscaras?
10. ¿Exportar todos los objetos o solo el seleccionado?
11. ¿Qué imágenes adicionales formarán el conjunto de validación?
12. ¿Se ratifican los umbrales provisionales de PASS_A_E?
13. ¿Puede recuperarse la carpeta/ZIP histórico v4?

---

# 23. Supuestos Actuales

- `SUPUESTO — REQUIERE VALIDACIÓN`: la foto sigue siendo el caso bloqueante principal.
- `SUPUESTO — REQUIERE VALIDACIÓN`: L4 o A100 estará disponible en Colab.
- `SUPUESTO — REQUIERE VALIDACIÓN`: las coordenadas A‑E(−1) siguen correctamente posicionadas.
- `SUPUESTO — REQUIERE VALIDACIÓN`: SAM2 HEAD mantiene compatibilidad con el cuaderno.
- `SUPUESTO — REQUIERE VALIDACIÓN`: Tier A serán objetos completos y salientes.
- `SUPUESTO — REQUIERE VALIDACIÓN`: las tres personas requieren GT manual obligatorio.
- `SUPUESTO — REQUIERE VALIDACIÓN`: una sola candidata exitosa basta para demostrar separación bajo un protocolo, pero no para generalizar.

---

# 24. Información Obsoleta o Reemplazada

- `OBSOLETO — NO USAR COMO ESTADO ACTUAL`: `PRAGMA_Fase_A_SAM2.ipynb`.
- `OBSOLETO — NO USAR COMO ESTADO ACTUAL`: estado v3 como autoridad.
- `OBSOLETO — NO USAR COMO ESTADO ACTUAL`: PASS histórico v4.
- `OBSOLETO — NO USAR COMO ESTADO ACTUAL`: `phase_b_blocked=false` del reporte histórico.
- `OBSOLETO — NO USAR COMO ESTADO ACTUAL`: nombre A‑E1 aplicado al diagnóstico de chica; ahora es A‑E(−1).
- `OBSOLETO — NO USAR COMO ESTADO ACTUAL`: afirmación “un punto valida SAM 2”.
- `OBSOLETO — NO USAR COMO ESTADO ACTUAL`: tratar alpha intermedia como prueba de borde correcto.

Contradicciones resueltas:

| Información A | Información B | Vigente |
|---|---|---|
| carpeta/reporte `_PASS` | evidencia visual falla | `INCONCLUSIVE` |
| alcance: dos personas | alcance: cada objeto | A‑E es objetivo de producto; A‑E(−1) solo diagnóstico |
| A‑E1 = cierre chica | A‑E1 = AMG | diagnóstico renombrado A‑E(−1) |
| v4 ligero como notebook del run | copia incluye cambios posteriores | equivalencia byte a byte `NO VERIFICADA` |
| carpeta histórica documentada | carpeta ausente hoy | hecho histórico, no adjunto disponible |

---

# 25. Invariantes y Reglas que No Deben Romperse

1. No modificar `pragma-extension.zip` durante Fase A‑E.
2. No avanzar a FastAPI, localhost, extensión ni Fase B sin `PASS_A_E` ratificado.
3. No reemplazar la foto por un ejemplo genérico.
4. No usar `argmax` como selector semántico.
5. No degradar Large→Small silenciosamente.
6. No forzar BF16 en T4.
7. No llamar matting a logits suavizados.
8. No presentar verificación estática como corrida GPU.
9. No presentar el antiguo `_PASS` como válido.
10. Separar proponer, reconocer, seleccionar, refinar y componer.
11. Conservar propuestas originales, `unlabeled` y relaciones parte/entero.
12. Un PASS debe estar ligado a imagen, inventario, propuesta, máscara y evidencias por hash.
13. Un FAIL de componente requiere agotar el protocolo prefijado de ese componente.
14. Si la ontología/GT está incompleta, el resultado es `INCONCLUSIVE`.
15. Cada modelo debe documentar peso, licencia/acceso, backend, tiempo, memoria y fallback.
16. Si se toca la extensión en el futuro, probarla cargada como extensión real mediante `--load-extension`.

---

# 26. Definition of Done

## Componente A‑E(−1) terminado

- notebook ejecutado en GPU;
- cuatro protocolos registrados;
- revisión ligada y notas honestas;
- ZIP/manifiesto íntegros;
- auditoría visual externa;
- estado actualizado sin extrapolar a inventario total.

## A‑E0 terminado

- definición de objeto ratificada;
- inventario numerado completo;
- tiers, bboxes, oclusión/truncamiento y relaciones;
- GT de las tres personas y demás bloqueantes;
- archivos congelados por hash.

## A‑E1 terminado

- sweep SAM2 AMG prefijado;
- propuestas crudas conservadas;
- métricas vs inventario/GT;
- tiempos/RAM/VRAM;
- veredicto `PASS_PROPOSALS`, `INCONCLUSIVE` o `FAIL_COMPONENT`.

## Fase A‑E terminada

- `PASS_PROPOSALS`;
- `PASS_LABELS` si nombres son requisito;
- `PASS_SELECTION`;
- evidencias y hashes completos;
- pruebas en más de una imagen según dataset ratificado.

## Proyecto completo

- pipeline A‑E validado;
- refinamiento de bordes validado aparte;
- servicio local aprobado;
- extensión integrada sin regresiones en Color/ISNet;
- UX, permisos, rendimiento y fallbacks probados;
- documentación y distribución final.

---

# 27. Punto Exacto de Reanudación

## Estamos exactamente aquí

El proyecto dispone de un cuaderno A‑E(−1) completo en cuanto a código y controles estáticos. Todavía no se ha ejecutado con SAM 2/CUDA. Su propósito es diagnosticar la separación de la chica respecto de la tercera persona usando punto, caja y correcciones. El objetivo mayor, inventariar todos los objetos, sigue esperando A‑E0.

La transferencia a ChatGPT 6 Sol está preparada. ChatGPT debe primero verificar los archivos y sus hashes; no debe modificar nada durante esa lectura inicial.

## Próxima acción

En ChatGPT desktop, si aparece **Work locally**, seleccionarlo; elegir **6 Sol** y el nivel de razonamiento más alto disponible si el selector los ofrece. Adjuntar el paquete y su `.zip.sha256`, y pegar el prompt de la sección 28. Si alguna opción no aparece, registrar la opción real en vez de asumirla.

## Resultado esperado

ChatGPT devuelve únicamente:

1. archivos/hashes recibidos;
2. faltantes o contradicciones;
3. estado del proyecto en cinco líneas;
4. una sola próxima acción: ejecutar A‑E(−1) en Colab.

## Si funciona

Confirmar la lectura y pedirle que guíe la ejecución secuencial de A‑E(−1). Conservar el `.ipynb` ejecutado y el ZIP.

## Si falla

Capturar:

- nombre real del modelo mostrado;
- lista de archivos que ChatGPT pudo abrir;
- hashes que no coincidieron;
- mensaje completo de error;
- captura de la interfaz;
- si el problema es Colab: celda, traceback, GPU, dtype y último output.

No improvisar cambios de arquitectura antes de resolver la transferencia.

---

# 28. Prompt de Reanudación para Otra IA

```text
Estoy transfiriendo el proyecto PRAGMA desde Codex a ChatGPT 6 Sol.

Lee completamente PROJECT_STATE.md antes de proponer cambios. Después verifica HANDOFF_MANIFEST_SHA256.txt y todos los archivos adjuntos. Trata PROJECT_STATE.md como la fuente de verdad operativa, pero prioriza cualquier evidencia nueva y actualiza posteriormente el state file si existe una contradicción.

No confundas: diseño, código escrito, verificación estática, ejecución GPU y aceptación visual. Estado obligatorio de partida: v4 histórico = INCONCLUSIVE; A-E(−1) = 68/68 verificación estática y NOT_RUN; Fase B = BLOQUEADA; SAM 2 todavía no es rechazable. No modifiques pragma-extension.zip. No integres FastAPI, localhost, YOLO-seg ni BiRefNet.

En tu primera respuesta no escribas ni ejecutes cambios. Responde solo con:
1) archivos recibidos y hashes que pudiste verificar;
2) faltantes o contradicciones;
3) estado actual en cinco líneas;
4) la única próxima acción tomada de “Punto Exacto de Reanudación”.

Espera mi confirmación antes de continuar. Después guía la ejecución de PRAGMA_A-E-menos-1_diagnostico_caso_chica_Codex.ipynb en Colab. No reinicies el diseño ni reviertas decisiones cerradas sin evidencia técnica nueva.
```

---

# 29. Protocolo de Actualización del State File

Después de cada cambio significativo:

1. actualizar fecha, versión y estado general;
2. registrar el artefacto y SHA‑256 nuevos;
3. distinguir escrito, ejecutado y aceptado;
4. actualizar Estado Actual, Logros, Inventario, Tree y Arquitectura;
5. añadir o cerrar decisiones/bugs;
6. actualizar matriz de pruebas;
7. actualizar riesgos y backlog;
8. mover información reemplazada a Obsoleto, sin borrar historia útil;
9. reescribir Punto Exacto de Reanudación con una sola próxima acción;
10. volver a generar el manifiesto del handoff.

No cambiar retroactivamente un resultado histórico. Añadir una corrección explícita y conservar ambos hechos.

---

# 30. Changelog del State File

| Versión | Fecha | Cambios principales |
|---|---|---|
| v1.0 | 2026‑09‑22 | creación inicial consolidada para transferencia a ChatGPT 6 Sol; incorpora estado v3/v4, corrección del falso PASS, objetivo A‑E, port A‑E(−1), hashes, backlog y punto de reanudación |

---

# 31. Auditoría Final de Integridad

## Cobertura

- [x] objetivos incluidos;
- [x] arquitectura incluida;
- [x] avances incluidos;
- [x] archivos activos, históricos decisivos y artefactos de transferencia incluidos; auxiliares temporales no relevantes quedan identificados solo como tales en el tree;
- [x] estructura de directorios incluida como árbol parcial;
- [x] decisiones incluidas;
- [x] errores incluidos;
- [x] pruebas incluidas;
- [x] pendientes incluidos;
- [x] restricciones incluidas;
- [x] ideas no implementadas separadas;
- [x] alternativas descartadas registradas;
- [x] próximo paso identificado.

## Fidelidad

- [x] hipótesis marcadas como tales;
- [x] no se inventaron archivos;
- [x] no se inventaron pruebas ni resultados;
- [x] versiones desconocidas permanecen desconocidas;
- [x] lo no ejecutado no se declara funcional;
- [x] código vigente y obsoleto diferenciados.

## Coherencia

- [x] contradicciones señaladas;
- [x] decisiones recientes prevalecen;
- [x] backlog corresponde al estado;
- [x] punto de reanudación corresponde al último estado comprobado.

## Portabilidad

Una IA nueva puede conocer el objetivo, estado, artefacto vigente, hashes, invariantes, errores y siguiente acción usando este archivo y el paquete. Para reauditar visualmente la corrida histórica v4 necesita recuperar las evidencias ausentes. Para continuar técnicamente necesita acceso a Colab/red/GPU.

---

# 32. Resultado de la Auditoría

## STATE FILE AUDIT

**Cobertura:** 10/10  
**Fidelidad:** 9/10  
**Coherencia:** 10/10  
**Capacidad de reanudación:** 9/10

### Elementos que no pudieron verificarse

- ejecución GPU del cuaderno A‑E(−1);
- contenido raw de la carpeta histórica v4 ausente;
- hash del notebook exacto que produjo la antigua ejecución;
- versiones exactas futuras de Python/PyTorch/Colab;
- funcionamiento runtime actual de la extensión;
- definición final de objeto y umbrales PASS_A_E.

### Posibles lagunas de información

- ubicación de cualquier respaldo del ZIP v4 histórico;
- comando exacto usado para cargar la extensión en la prueba original;
- dataset adicional de validación;
- decisiones del usuario sobre ontología y presupuesto.

### Contradicciones detectadas

- nombre/reporte `_PASS` frente a evidencia visual: resuelta a `INCONCLUSIVE`;
- alcance antiguo de dos personas frente a inventario de toda la escena: separados en A‑E(−1) y A‑E;
- A‑E1 histórico frente a denominación vigente: diagnóstico renombrado A‑E(−1);
- copia v4 ligera posterior frente al notebook exacto del run: equivalencia no demostrada;
- evidencia histórica documentada frente a archivos actualmente ausentes: señalada.

### Confianza global

`ALTA` para continuidad, decisiones, hashes actuales y próxima acción. `MEDIA` para reconstruir la ejecución v4 histórica sin sus archivos raw. La transferencia es operativa, pero la ciencia permanece inconclusa hasta ejecutar A‑E(−1), crear A‑E0 y medir A‑E1.
