# 0. Identidad del State File

- **Proyecto:** PRAGMA · Motor de Transparencia / Inventario exhaustivo de escena
- **Archivo:** `PROJECT_STATE.md`
- **Fecha de generación:** 22 de septiembre de 2026 (America/Lima)
- **Última actualización:** 25 de septiembre de 2026 (v1.5, misma sesión) · continuación en **Claude Code** (claude.ai/code, contenedor remoto **sin GPU**), actuando como GENESIS. La transferencia prevista a ChatGPT 6 Sol (§27 v1.0) no se usó para esta continuación.
- **Versión:** `v1.5`
- **Estado general:** `INCONCLUSIVE_A_E0_REQUIRED`
- **Fase B:** `BLOQUEADA`
- **Último hito documentado (v1.5):** ChatGPT contraauditó el paquete 003 (integridad PASS, diseño PASS, decisiones a–d aceptadas) y pidió dos cambios de contrato, aplicados **antes de cualquier corrida**: `BASE_V2_REFERENCE` (una máscara idéntica no hereda un juicio emitido con otro protocolo) y adjudicación técnica de discrepancias (la persona usuaria no arbitra píxeles). Con eso `AEM1_v1.3 = GO_TO_BUILD`: prerregistro `PREREGISTERED` con plan de 178 llamadas y el código de análisis congelado por hash; cuaderno v1.3 generado desde el prerregistro y verificado 26/26 con SAM simulado; contrato de análisis A‑E1 en borrador. GPU v1.3 `NOT_RUN`
- **Hito v1.4:** la corrida 1 queda **aceptada por doble llave** (`INCONCLUSIVE_SELECTED_OUTPUT_FAILED`; veredicto concordante 12/12 con ChatGPT, 42/48 celdas, 5 concesiones de Claude y 1 refutación por medición; segunda llave parcialmente contaminada, contaminación acotada). **A‑E(−1) v1.3 cerrado y prerregistrado**: ramas independientes, prompts nuevos por regla reproducible en región segura, perturbaciones deterministas con `INVALID_PERTURBATION`, recíproco sin reparación. **Protocolo ciego v2**: paquete antes que resultados, compromiso por hash, `correct_subject` = identidad, agujeros medidos. Sin cuaderno v1.3 ni corrida nueva
- **Hito v1.3:** **primera corrida GPU real** de A‑E(−1) v1.2 (L4, bf16, SAM 2 `2b90b9f5`, checkpoint `2647878d…`), auditada a ciegas con protocolo congelado antes de mirar: `INCONCLUSIVE_SELECTED_OUTPUT_FAILED` (0/12 candidatas pasan; mejor intento `box+corrections:s1`), pendiente de segunda llave de ChatGPT; reproduce la corrida v4; DEC‑013‑Q adoptada por matriz prerregistrada; sweep A‑E1 prerregistrado y verificado contra el commit exacto; ontología v0.2 con los cambios R4 de ChatGPT
- **Hito v1.2:** la persona usuaria deja de fiscalizar (DEC‑018‑P): cuaderno A‑E(−1) **v1.2 «un clic»** (O3/O4 inequívocos, confirmación del auditor IA ligada a la luminancia de los 18 parches, semillas exhaustivas, `PENDING_EXTERNAL_AUDIT`, modo sin navegador) verificado con 68 + 39 comprobaciones, píxeles y arnés de punta a punta con SAM simulado; herramienta de auditoría IA de ZIPs; protocolo de diálogo Claude↔ChatGPT con doble llave (DEC‑019‑P) y carta 001; evaluación de Colab MCP/CLI
- **Hito v1.1:** preflight de coordenadas de A‑E(−1) con la foto real (3 de 18 puntos mal ubicados) → cuaderno **v1.1** verificado (68 Codex + 19 propias + píxeles + arnés CPU; GPU `NOT_RUN`); kit A‑E0/A‑E1 (`pragma_ae`) con 22 tests; borrador de inventario de 52 objetos; ontología propuesta sin ratificar; proyecto versionado en `brune6320-del/motor-vimeo` bajo `pragma/`
- **Hito anterior (v1.0):** port a un cuaderno independiente A‑E(−1), con 68/68 verificaciones estáticas y experimento GPU todavía `NOT_RUN`
- **Propósito:** fuente de verdad operativa para continuar PRAGMA en ChatGPT 6 Sol, otra IA o una nueva sesión sin depender de la conversación original.
- **Confianza general:** alta para archivos, hashes, decisiones y estado lógico; media para la antigua ejecución v4 porque sus evidencias ya no están presentes en el disco.
- **Ubicación versionada:** repositorio público `brune6320-del/motor-vimeo`, rama `claude/genesis-emerge-proyecto-6mdcs0`, carpeta `pragma/`. La foto y la extensión **no** están en git (DEC‑017).

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

**Actualización v1.1.** Antes de gastar la corrida GPU se auditaron las 18 coordenadas de A‑E(−1) contra la foto real: `P‑3` y `O2` caían sobre la pared y `P‑2` en el borde pared/moño, justo en la zona donde v4 falló. Se generó el cuaderno **v1.1** (v1.0 intacto) y se verificó sin GPU. Además se construyó el kit A‑E (`pragma_ae`): contrato y validador de `scene_inventory.json` con congelado por hash, lámina numerada, hoja de contactos y métricas A‑E1. Las métricas demostraron un hueco del contrato §9: una máscara con el defecto de v4 obtiene IoU 0,94 y pasaría el umbral de 0,70; se propone medir la fusión normalizada por el área invadida (DEC‑013‑P). Nada de esto cambia los veredictos: v4 `INCONCLUSIVE`, Fase B `BLOQUEADA`, SAM 2 no rechazable.

**Actualización v1.5.** ChatGPT inspeccionó el paquete 003 completo y verificó:

- el SHA‑256 del ZIP;
- 10/10 archivos;
- el `content_sha256` del prerregistro;
- la transcripción de su llave;
- el propietario de H1, S1 y sus 24 perturbaciones.

Aceptó (a)–(d) y objetó dos cosas, que se corrigieron antes de correr:

- **BASE bit a bit** ya no «hereda la doble llave»: usa una referencia normalizada. B y D pasan a
  `correct_subject = TRUE`, medido: el 100 % de su área está dentro de A.
- **Discrepancias entre llaves:** van a adjudicación técnica (medición → tercera revisión ciega →
  adjudicación conjunta conservadora), no a la persona usuaria.

Se registraron sus hipótesis H‑G1–G4. El cuaderno v1.3 ejecuta exactamente el plan prerregistrado,
no muestra resultados y deja la auditoría ciega fuera de Colab. Falta la corrida en GPU.

**Actualización v1.4.** ChatGPT devolvió la segunda llave sobre las mismas 12 láminas.

- **Veredicto concordante:** ninguna candidata pasa en ninguna llave.
- **Diferencias:** 6 de 48 celdas. Claude concede 5 porque aplicó una condición no escrita en
  `correct_subject`: 4 por el texto congelado y 1 medida (el 61,9 % de G cae sobre la chica). La
  sexta se decide por medición contra ChatGPT: F tiene 2 agujeros de ≥ 1000 px.
- **Contaminación:** la carta 002 reveló recuentos, no etiquetas. Las dos llaves reproducen la
  misma partición de A–L, que por azar tendría probabilidad 1/207 900.
- **v1.3 cerrado y prerregistrado** con el diseño de ChatGPT, sin cuaderno todavía:
  - ramas independientes;
  - dos prompts nuevos, H1 (pelo) y S1 (manga), elegidos por regla reproducible;
  - 24/24 perturbaciones de punto válidas y 5/6 de caja;
  - propiedad frente al recíproco sin reparar nada.
- **Protocolo ciego v2**, a pedido de ChatGPT: el paquete ciego va antes que cualquier resultado,
  los juicios de Claude se comprometen por hash, `correct_subject` pasa a ser identidad y los
  agujeros se miden.

**Actualización v1.3.** La persona usuaria ejecutó v1.2 en Colab (L4) y adjuntó el ZIP. Se verificó el freeze (mismo commit y checkpoint que v4) y se publicó el protocolo de auditoría antes de mirar ninguna máscara. Después se juzgaron a ciegas las 12 candidatas, con etiquetas A–L y el mapeo sellado, y se publicaron los juicios crudos antes de desciegar. **Ninguna candidata separa a la chica completa sin la persona posterior.** Las correcciones negativas sacan el pelo y las mangas oscuras de la chica junto con la persona posterior; sin ellas, lo oscuro entra con el moño. `point#1` reproduce exactamente la candidata aceptada en v4 (scores 0,906/0,002/0,006; área 15,56 %). La respuesta 001 de ChatGPT aportó DEC‑013‑Q, que ganó una matriz sintética prerregistrada (Q 26/26, P 22/26), el sweep A‑E1 (prerregistrado; parámetros verificados en el commit exacto) y tres cambios de ontología aceptados.

**Actualización v1.2.** La persona usuaria pidió no fiscalizar en Colab lo que una IA puede verificar, y trabajar en ping‑pong con ChatGPT: Claude audita y guía, ChatGPT desafía y contraaudita. Se construyó el cuaderno **v1.2**: basta arrastrar la foto, pulsar «Ejecutar todas» y adjuntar el ZIP. La configuración llega confirmada por el auditor IA y el propio cuaderno comprueba que los píxeles son los auditados. Las seis correcciones se ejecutan sin elegir semillas, y la selección y la revisión visual las hace la auditoría IA externa (`pragma_ae.aem1_audit`) con evidencia y hashes, sin poder confundir nunca una corrida simulada con evidencia. El Colab MCP solo funciona en local; el Colab CLI funcionaría desde la sesión en la nube si se abre la red a `colab.research.google.com` y se autoriza una vez.

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

- `🟡` ejecutar A‑E(−1) **v1.1** sobre la chica y la persona posterior (escrito y verificado; GPU pendiente);
- `🟡` definir A‑E0: ontología **propuesta** (sin ratificar), kit y borrador de inventario listos; revisión humana, GT y congelado pendientes;
- `❌` ejecutar A‑E1 con `SAM2AutomaticMaskGenerator` y comparar contra el inventario (métricas ya implementadas).

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

## Hito 9 — Emergencia en repositorio, preflight y kit A‑E (Claude Code · GENESIS)

- **Contexto:** la continuación se hizo en Claude Code, no en ChatGPT 6 Sol. Contenedor sin GPU; `dl.fbaipublicfiles.com` y `huggingface.co` bloqueados por la política de red → SAM 2 no ejecutable aquí.
- **Verificación de llegada:** hash del ZIP (`648b62…f75c`) y 15/15 entradas del manifiesto v1.0 coinciden; `verify_pragma_ae1_codex.py` reproduce 68/68 con JSON byte‑idéntico.
- **Hallazgo:** la verificación estática nunca comprobó que los puntos cayeran en su región. Preflight con la foto: `P‑3` y `O2` sobre pared (luma 205/220, igual que la pared de referencia), `P‑2` en el borde; `O3`/`O4` en zonas de contacto de propietario dudoso.
- **Cambio:** cuaderno `v1.1` con 3 coordenadas reubicadas, O3/O4 marcados y hoja de contactos embebida; el v1.0 se conserva.
- **Nuevo:** kit `pragma_ae` (contrato A‑E0, validador, congelado, lámina, preflight, métricas A‑E1), borrador de inventario de 52 objetos, ontología propuesta con recomendación para las 13 preguntas.
- **Hallazgo de contrato:** con IoU como único criterio, el defecto de v4 pasa (IoU 0,94). Propuesta DEC‑013‑P.
- **Certeza:** `✅` estático, píxeles y arnés CPU; `❌` GPU; `❌` ratificación humana.

## Hito 11 — Primera corrida GPU real de A‑E(−1) y auditoría ciega (v1.3)

- **Corrida:** `20260925T062504Z_256dba9f` · ZIP `e6bb7a46…1976` · `REAL_GPU` (NVIDIA L4, bf16) · 12 candidatas.
- **Orden probado en git:** protocolo congelado (`2a9e264`) → juicios ciegos crudos (`84530ff`) → desciegue y veredicto.
- **Veredicto (primera llave):** `INCONCLUSIVE_SELECTED_OUTPUT_FAILED`; mejor intento `box+corrections:s1#0` (persona posterior y fondo fuera; sin el pelo de la chica y con las mangas perforadas); las `box` sin corrección arrastran el moño.
- **Sonda de contacto:** semillas `box` = `CONFLICT` (IoU mínimo 0,135); semillas `point` = `NOT_EVALUABLE`; point↔box = `CONFLICT`.
- **ChatGPT 001:** DEC‑013‑Q adoptada (matriz prerregistrada; Q 26/26, P 22/26); sweep A‑E1 prerregistrado (`ae1/SWEEP_PRERREGISTRO_A-E1.json`), verificado contra `2b90b9f5`; ontología v0.2 (R4).
- **Certeza:** `✅` corrida GPU, integridad y auditoría ciega de primera llave; `❌` segunda llave (carta 002 enviada); `❌` A‑E0.

## Hito 12 — Doble llave de la corrida 1 y v1.3 prerregistrado (v1.4)

- **ChatGPT 002** (archivada tal cual, `b6d51d…046c`):
  - segunda llave `NO_PASS_CANDIDATE`, declarada «parcialmente contaminada» por la carta 002;
  - crítica de v1.3: ramas separadas, región segura, ±15 px exacto y recíproco sin `T − R`;
  - refutación de la inferencia «el límite es del prompting, no de SAM 2»;
  - cambio de protocolo: el paquete ciego antes que los resultados.
- **Comparación** (`work/double_key_aem1.py` → `doble_llave.json`):
  - veredicto concordante; 42/48 celdas; κ(O) = 1,00 y κ(S) = 0,25;
  - adjudicación tras el desciegue: 5 celdas para ChatGPT (C, E, H, J y G · S) y 1 contra
    ChatGPT por medición (F · B);
  - B y D: hueco compartido del protocolo v1.
- **v1.3:**
  - `aem1/PRERREGISTRO_A-E-menos-1_v1_3.json` (`918ffd…efd2`, `content_sha256` `20d1f9f5…bf1d`),
    reproducible byte a byte con `work/design_aem1_v1_3.py --check`;
  - especificación legible en `aem1/ESPECIFICACION_A-E-menos-1_v1_3.md`;
  - métricas en `pragma_ae/aem1_v13.py` (18 tests).
- **Protocolo ciego v2:** `auditoria/PROTOCOLO_AUDITORIA_AEM1_v2.md` (`bc7e58…2591`).
- **Nomenclatura:** «Crear cuaderno Colab para SAM 2» es el hilo de Codex de PRAGMA/SAM 2; las
  cartas para Claude se pegan en su sesión de Claude Code.
- **Certeza:**
  - `✅` doble llave de la corrida 1 (con límites escritos);
  - `✅ VERIFICADO ESTÁTICO` diseño y métricas v1.3;
  - `❌` cuaderno v1.3, corrida v1.3 e inspección del prerregistro por ChatGPT.

## Hito 13 — Contraauditoría previa y cuaderno v1.3 (v1.5)

- **ChatGPT 003** (tal cual, `dcc637…484e`):
  - `ZIP_INTEGRITY = PASS` (`0453d7d2…e8ff`, 10/10) y `DESIGN_PROMPTS_SECOND_KEY = PASS`;
  - (a) `ACCEPT`, (b) `ACCEPT_WITH_NAMING_CLARIFICATION`, (c) `ACCEPT_WITH_CONTINUOUS_DIAGNOSTICS`
    y (d) `ACCEPT_AS_DIAGNOSTIC`;
  - (e) `CHANGE_REQUIRED` y protocolo v2 `ACCEPT_AFTER_TECHNICAL_ADJUDICATION_CHANGE`;
  - A‑E1: sweep `PREREGISTERED` y análisis completo `CONDITIONAL`.
- **Aplicado antes de correr:**
  - `auditoria/aem1_20260925T062504Z_256dba9f/BASE_V2_REFERENCE.json` (`c1f01d…0b66`);
  - protocolo v2 rev. 1 (`b5b11c…7a71`);
  - L∞ y euclídea; cobertura O* continua; razones de propiedad direccionales;
  - nueva descripción de P+1; H‑G1–G4;
  - `ae1/CONTRATO_ANALISIS_A-E1.json` (`498ee9…e156`, `DRAFT_FREEZES_WITH_A_E0`).
- **Prerregistro v1.3** (`9953ed…9fb8`, `content_sha256` `5800f2bf…2a8c`):
  - `call_plan` con las 178 llamadas;
  - `analysis_implementation_sha256` de `aem1_v13.py`, `aem1_v13_audit.py` y `masks.py`.
- **Cuaderno v1.3:** `outputs/PRAGMA_A-E-menos-1_diagnostico_caso_chica_v1_3.ipynb` (`b477f3…e62e`),
  generado por `work/build_pragma_aem1_v1_3.py`.
- **Verificación:** `work/verify_pragma_aem1_v1_3.py`, 26/26.
- **Guía:** `GUIA_COLAB_A-E-menos-1_v1_3.md`. **Carta:** 004, sin resultados.
- **Certeza:**
  - `✅ VERIFICADO ESTÁTICO + SIMULADO` cuaderno y análisis;
  - `❌` GPU v1.3;
  - `❌` confirmación de ChatGPT sobre las interpretaciones de H‑G1 y H‑G3 (no bloquea).

## Hito 10 — La persona usuaria deja de fiscalizar; ping‑pong con ChatGPT (v1.2)

- **Solicitud:** "no me delegues fiscalizar lo que la IA puede hacer"; mandar los avances a ChatGPT en retroalimentación constante; traspasar no es delegar; usar Colab MCP/CLI si es posible.
- **Decisiones:** DEC‑018‑P (auditoría IA con evidencia en lugar de casillas humanas; veto de la persona usuaria) y DEC‑019‑P (doble llave Claude + ChatGPT y cartas numeradas en `dialogo/`).
- **Artefactos:** cuaderno v1.2 (`06315e…f0da`), verificador v1.2 y arnés `harness_aem1.py`, `pragma_ae/aem1_audit.py`, `preflight/PREFLIGHT_A-E-menos-1_v1_2.md`, `GUIA_COLAB_A-E-menos-1_v1_2.md`, `dialogo/README.md` y carta 001.
- **Colab:** el **MCP** (`googlecolab/colab-mcp`) exige que el agente corra en el equipo local con una pestaña de Colab abierta: **no** sirve desde esta sesión en la nube. El **CLI** (`google-colab-cli` 0.7.2, Python ≥ 3.12, OAuth por código pegado; permisos `colaboratory`, `drive.file`, `cloud-platform`…) sí serviría si se permite `colab.research.google.com` (hoy bloqueado por la política de red) y la persona usuaria autoriza una vez.
- **Certeza:** `✅` estático + píxeles + E2E simulado + auditoría sobre el ZIP del arnés; `❌` GPU; `❌` contraauditoría de ChatGPT (carta 001 enviada para pegar).

---

# 4. Estado Actual del Proyecto

- **Último componente trabajado (v1.5):** correcciones de ChatGPT 003, cuaderno v1.3, verificador E2E, análisis v1.3 y contrato A‑E1.
- **Componente anterior (v1.4):** doble llave de la corrida 1, diseño y prerregistro A‑E(−1) v1.3, protocolo ciego v2 y carta 003.
- **Último artefacto de implementación vigente:** `outputs/PRAGMA_A-E-menos-1_diagnostico_caso_chica_v1_2.ipynb` (`06315e…f0da`). v1.1 (`ddf784…00dc`) y v1.0 (`5941be…b706`) quedan como antecedentes inmutables.
- **Último documento modificado:** `PROJECT_STATE.md` v1.5.
- **Últimos comandos de verificación ejecutados (v1.5):** `python3 work/verify_pragma_aem1_v1_3.py` (26/26), `python3 work/design_aem1_v1_3.py --check`, `python3 work/ae1_analysis_contract.py --check` y `python3 -m unittest discover -s tests` (67/67).
- **Comandos v1.4:** `python3 work/double_key_aem1.py --zip <ZIP real>`, `python3 work/design_aem1_v1_3.py --check` (byte a byte: True) y `python3 -m unittest discover -s tests` (47/47).
- **Último resultado observado:** v1.2 = 68/68 Codex + 39/39 propias, píxeles `PASS`; el arnés E2E con SAM simulado ejecutó las celdas 03–11 con la foto real en tres escenarios. Con navegador: 8 propuestas, 12 candidatas, `PENDING_EXTERNAL_AUDIT`, ZIP de 4,7 MB y una descarga. Sin navegador: igual, sin descarga. Sin foto: error claro, sin selector. La auditoría IA leyó ese ZIP, detectó `SIMULATED` y devolvió `SIMULATED_RUN_NOT_EVIDENCE`. 27/27 tests; experimento `NOT_RUN`.
- **Último error material de ejecución:** ninguno nuevo en GPU (no hubo corrida). En el arnés CPU, la celda 06 requiere `pipeline` de la celda 05: se sustituyó por un objeto mínimo documentado.
- **Última decisión (v1.5):** aplicar los dos cambios de contrato de ChatGPT antes de correr; construir el cuaderno v1.3 (`GO_TO_BUILD`); tras la corrida, ChatGPT recibe solo el paquete ciego.
- **Decisión v1.4:** adoptar el cambio de protocolo de ChatGPT (doble ciego temporal y compromiso por hash); cerrar v1.3 con su diseño; no construir el cuaderno v1.3 hasta que ChatGPT inspeccione el prerregistro («nada de Colab todavía»); Fase B bloqueada.
- **Último elemento confirmado como funcional:** celda de configuración v1.1 con la foto real (overlay, hoja de contactos, `config_digest`), kit `pragma_ae`.
- **Escrito pero no probado en GPU:** los cuatro protocolos y el flujo de exportación A‑E(−1) (idénticos en v1.0 y v1.1 salvo configuración y lista blanca).
- **Evidencia histórica faltante:** la carpeta `/Users/usuario/Desktop/PRAGMA_Fase_A_v4_20260811T001154Z_6e6a9ae1_PASS/` ya no existe en el filesystem actual. Sus resultados sobreviven solo en documentos de estado.
- **Foto disponible:** `/Users/usuario/Desktop/P1070614.JPG` y, localmente, `pragma/inputs/` (no versionada); hash confirmado.
- **Extensión:** `/Users/usuario/Desktop/pragma-extension.zip`; copia local en `pragma/inputs/` verificada por hash; no versionada ni modificada.

Estado resumido:

```text
Fase A dirigida por clic       INCONCLUSIVE
A‑E(−1) diagnóstico chica     CORRIDA 1 (v1.2, GPU): INCONCLUSIVE_SELECTED_OUTPUT_FAILED (0/12) · ACEPTADO POR DOBLE LLAVE
A‑E(−1) v1.3                  PRERREGISTRADO Y CONTRAAUDITADO · CUADERNO LISTO (26/26 SIMULADO) · GPU NOT_RUN
A‑E0 inventario humano        KIT LISTO · BORRADOR 52 OBJETOS · ONTOLOGÍA SIN RATIFICAR
A‑E1 SAM2 AMG                 SWEEP PREREGISTERED (ChatGPT 003) · ANÁLISIS CONDICIONADO A A‑E0 · SIN CORRIDA
Revisión                      AUDITOR IA + CONTRAAUDITORÍA CHATGPT · VETO DE LA PERSONA USUARIA
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

## 5.8 Preflight de coordenadas y A‑E(−1) v1.1

**Estado:** `✅ VERIFICADO SIN GPU` (estático + píxeles + celdas 04/06/07 en CPU con la foto real)
**Cambios:** `P‑2` (2600,400)→(2640,430), `P‑3` (2450,700)→(2400,810), `O2` (2680,300)→(2700,380); `O3`/`O4` exigen confirmar propietario; hoja de contactos en la celda 06 y en el ZIP; `config_revision=1.1`.
**Informe:** `preflight/PREFLIGHT_A-E-menos-1_v1_0.md`.

## 5.9 Kit A‑E (`pragma_ae`)

**Estado:** `✅ 22 TESTS` (datos sintéticos + borrador real)
**Incluye:** contrato `scene_inventory` 0.1.0 con validador y congelado por hash canónico; lámina numerada; hoja de contactos; métricas A‑E1 (IoU, recall, duplicación, fraccionamiento, fusión normalizada por área invadida, fuga en franja de contacto, cribado por cajas) y gates `section9_operational` / `proposed_v1_1`.
**Límite:** nunca se ha evaluado una propuesta real de SAM 2.

## 5.10 Borrador de inventario A‑E0

**Estado:** `🟡 DRAFT_UNVERIFIED` · 52 objetos (A 24 · B 19 · C 9) · `content_sha256 e4adc6…b940`
**Método:** estimación visual sobre vistas reducidas y recortes, sin modelo; cajas aproximadas. No es GT.

## 5.11 A‑E(−1) v1.2 «un clic»

**Estado:** `✅ VERIFICADO SIN GPU` (68 Codex + 39 propias + píxeles + E2E simulado en 3 escenarios)
**Cambios sobre v1.1:** O3 (2680,520)→(2735,360) y O4 (2335,1035)→(2325,965), ambos de propietario inequívoco; confirmación del auditor IA con `AEM1_CONFIG_READY = CONFIRMADA and AEM1_PREFLIGHT_MATCH`, que recalcula la luma de los 18 parches con tolerancia 3,0; correcciones para las 3 semillas de cada baseline (claves `point+corrections:sN`, `box+corrections:sN`); estado `PENDING_EXTERNAL_AUDIT` y descarga siempre; búsqueda de la foto por hash con cualquier nombre en `/content`; `PRAGMA_HEADLESS=1` para Colab CLI; galerías y overlay a menor dpi.

## 5.12 Auditoría IA de ZIPs (`pragma_ae.aem1_audit`)

**Estado:** `✅ 5 TESTS + VALIDADA SOBRE EL ZIP DEL ARNÉS`
**Hace:** manifiesto, bytes, SHA‑256, digest e invariantes; detecta `SIMULATED` / `REAL_CPU` / `REAL_GPU`; recalcula sentinelas y los compara con el informe; mide componentes, agujeros y cobertura de regiones de apoyo (aproximadas); genera primeros planos a resolución completa. **No elige**: el veredicto (`write_verdict`) registra auditor, candidata, criterios, razonamiento y token, y nunca puede declarar demostración sobre una corrida simulada.

## 5.13 Diálogo Claude ↔ ChatGPT

**Estado:** `✅` cartas 001 (ida y vuelta) y 002 enviada; segunda llave pendiente.

## 5.14 Corrida GPU real A‑E(−1) y auditoría ciega

**Estado:** `✅ EJECUTADO GPU` + `✅ AUDITORÍA CIEGA (1ª llave)` · `❌ 2ª llave`
**Resultado:** 0/12 candidatas pasan los cuatro criterios. Informe: `auditoria/aem1_20260925T062504Z_256dba9f/INFORME.md`. Veredicto: `aem1_audit_verdict.json` (token `6efc1850…a935`).

## 5.16 Doble llave de la corrida 1

**Estado:** `✅ ACEPTADO (doble llave; segunda llave parcialmente contaminada)`.

- **Registro:** `auditoria/aem1_20260925T062504Z_256dba9f/doble_llave.json` (`1c50da…add8`), con la
  llave de ChatGPT transcrita en `segunda_llave_chatgpt.json` (`9881d8…9746`).
- **Veredicto concordante;** 42/48 celdas.
- **Adjudicación medida:** G tiene ≥ 61,9 % de su área sobre la chica; F tiene 2 agujeros cerrados
  ≥ 1000 px sobre su material.
- **Contaminación acotada:** 1/207 900.

## 5.17 A‑E(−1) v1.3 prerregistrado

**Estado:** `✅ VERIFICADO ESTÁTICO` (diseño y métricas) · `❌` cuaderno y corrida.

- **Prompts nuevos**, elegidos por `select_safe_point`:
  - H1 = (3072, 592), pelo, cuadrado seguro de 61 px, margen de 173 px;
  - S1 = (2230, 1686), manga, 171 px y 387 px.
- **Perturbaciones:** 24/24 de punto válidas; 5/6 de caja (`T+0+15` sale de la imagen).
- **Máscaras previstas:** 210.
- **Hipótesis:** H‑C1 (pelo sí, moño también), H‑C2 (P+1 junto a un botón → `point` inestable) y
  H‑G* (pendientes de ChatGPT).

## 5.18 A‑E(−1) v1.3 listo para correr

**Estado:** `✅ VERIFICADO ESTÁTICO + SIMULADO` · `❌ GPU`.

- El cuaderno embebe el prerregistro byte a byte y bloquea si no coinciden el commit `2b90b9f5`,
  el checkpoint `2647878d…`, la foto o la luma de los 44 puntos (tolerancia 3,0).
- Con SAM simulado:
  - hace las 178 llamadas exactas del plan (puntos, etiquetas, cajas, multimask y semillas);
  - produce 210 máscaras y no muestra ninguna.
- Sobre su ZIP:
  - la integridad da `SIMULATED_RUN_NOT_EVIDENCE`;
  - manipular una máscara o el plan da `INVALID_BUNDLE`;
  - el paquete ciego (láminas `C01…`, agujeros numerados, plantilla) y el análisis funcionan.

## 5.19 Contrato de análisis A‑E1

**Estado:** `🟡 DRAFT_FREEZES_WITH_A_E0`.

- Liga el sweep inspeccionado (`25a61a…5a38`, sin tocar) al SHA‑256 de `metrics.py`, `masks.py` e
  `inventory.py` y a todos los umbrales de `GateParams`.
- `A_E0_FROZEN = REQUIRED`.

## 5.15 DEC‑013‑Q y matriz prerregistrada

**Estado:** `✅ VERIFICADO ESTÁTICO` · `tests/test_fusion_matrix.py` a 4000×2248: Q acierta las 26 etiquetas prerregistradas y P falla 4 (bandas y víctimas delgadas) → `GateParams.fusion_rule = "Q"`, δ = 5 px.

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

`TREE DEL REPOSITORIO v1.5` (`brune6320-del/motor-vimeo`, carpeta `pragma/`; la raíz contiene además un backend Node no relacionado que no se toca)

```text
pragma/
├── README.md
├── PROJECT_STATE.md                 # este archivo, v1.5
├── MANIFEST_SHA256.txt              # hashes del árbol versionado
├── requirements.txt                 # numpy, pillow (+ matplotlib para el arnés)
├── .gitignore                       # inputs/*, local/, runs/, ae0/gt/
├── inputs/                          # NO versionado salvo README e INPUTS_SHA256.txt
│   ├── README.md
│   ├── INPUTS_SHA256.txt
│   ├── P1070614.JPG                 # local
│   └── pragma-extension.zip         # local
├── outputs/
│   ├── PRAGMA_A-E-menos-1_diagnostico_caso_chica_Codex.ipynb   # v1.0, inmutable
│   ├── PRAGMA_A-E-menos-1_Codex_verificacion.json
│   ├── PRAGMA_A-E-menos-1_diagnostico_caso_chica_v1_1.ipynb    # antecedente
│   ├── PRAGMA_A-E-menos-1_v1_1_verificacion.json
│   ├── PRAGMA_A-E-menos-1_diagnostico_caso_chica_v1_2.ipynb    # vigente («un clic»)
│   ├── PRAGMA_A-E-menos-1_v1_2_verificacion.json
│   ├── PRAGMA_A-E-menos-1_diagnostico_caso_chica_v1_3.ipynb    # vigente (prerregistrado, a ciegas)
│   ├── PRAGMA_A-E-menos-1_v1_3_verificacion.json
│   ├── PRAGMA-ESTADO-FASE-A-E-INVENTARIO-ESCENA.md
│   ├── PRAGMA-ESTADO-TRASPASO-CLAUDE-A-CODEX.md
│   ├── PRAGMA_Fase_A_SAM2_v4_ligero.ipynb
│   ├── PRAGMA_Fase_A_v4_auditoria.md
│   ├── PRAGMA_Fase_A_v4_verificacion.json
│   └── claude_originals/
├── work/
│   ├── build_pragma_ae1_codex.py
│   ├── verify_pragma_ae1_codex.py
│   ├── build_pragma_ae1_v1_1.py
│   ├── verify_pragma_ae1_v1_1.py
│   ├── build_pragma_ae1_v1_2.py
│   ├── verify_pragma_ae1_v1_2.py
│   ├── harness_aem1.py              # arnés E2E con SAM simulado
│   ├── blind_audit_aem1.py          # láminas ciegas, mapeo sellado, desciegue
│   ├── double_key_aem1.py           # comparación de las dos llaves (corrida 1)
│   ├── design_aem1_v1_3.py          # diseño v1.3 → prerregistro determinista
│   ├── build_pragma_aem1_v1_3.py    # prerregistro → cuaderno v1.3
│   ├── verify_pragma_aem1_v1_3.py   # estático + E2E simulado + auditoría
│   └── ae1_analysis_contract.py     # contrato de análisis A‑E1
├── pragma_ae/                       # kit A‑E (python3 -m pragma_ae …)
│   ├── inventory.py  metrics.py  masks.py  preflight.py  sheet.py  imageio.py  aem1_audit.py  aem1_v13.py  aem1_v13_audit.py  __main__.py
├── ae0/
│   ├── ONTOLOGIA_PROPUESTA.md
│   ├── PROTOCOLO_A-E0.md
│   └── scene_inventory.draft.json
├── ae1/SWEEP_PRERREGISTRO_A-E1.json, CONTRATO_ANALISIS_A-E1.json
├── aem1/                            # A‑E(−1) v1.3: ESPECIFICACION_… .md + PRERREGISTRO_… .json
├── auditoria/                       # PROTOCOLO_AUDITORIA_AEM1_v1.md (congelado), v2 (para v1.3), corrida 1 con doble llave
├── preflight/PREFLIGHT_A-E-menos-1_v1_0.md, PREFLIGHT_A-E-menos-1_v1_2.md
├── dialogo/                         # ping‑pong Claude ↔ ChatGPT (README + cartas)
├── GUIA_COLAB_A-E-menos-1_v1_3.md   # guía vigente (un clic, a ciegas); v1_2 = modo delegado
├── CLAUDE.md                        # reglas para agentes
├── tests/                           # 67 tests
├── history/handoff_v1.0/            # PROJECT_STATE v1.0, START_HERE, manifiesto original (+ enlaces)
└── local/                           # NO versionado: overlays, hojas de contactos, láminas, arnés
```

Artefactos históricos del workspace Codex no incluidos en el paquete (v3, v4 autocontenidos, primer cuaderno, auditoría v3) siguen existiendo solo en la máquina de origen, como indica §8.

---

# 8. Inventario de Archivos

| Archivo | Ruta | Función | Estado | Última información conocida |
|---|---|---|---|---|
| `PROJECT_STATE.md` | `pragma/` | Fuente de verdad portable | ✅ | **v1.5, 2026‑09‑25**; v1.0 en `history/handoff_v1.0/` |
| `PRAGMA_A-E-menos-1_diagnostico_caso_chica_v1_3.ipynb` | `pragma/outputs/` | Experimento A‑E(−1) **vigente** | 🟡 GPU NOT_RUN | `b477f3…e62e`; 26/26 simulado |
| `aem1_v13_audit.py` · `BASE_V2_REFERENCE.json` · `CONTRATO_ANALISIS_A-E1.json` | `pragma_ae/` · `auditoria/…256dba9f/` · `ae1/` | análisis v1.3 · referencia BASE · contrato A‑E1 | ✅ · ✅ · 🟡 borrador | `820af0…c13a` · `c1f01d…0b66` · `498ee9…e156` |
| `PRERREGISTRO_A-E-menos-1_v1_3.json` · `ESPECIFICACION_A-E-menos-1_v1_3.md` | `pragma/aem1/` | v1.3 cerrado | ✅ `PREREGISTERED` (contraauditado, ChatGPT 003) | `9953ed…9fb8` (content `5800f2bf…2a8c`; v1.4 era `918ffd…efd2`) · `5c5ddf…bafa` |
| `PROTOCOLO_AUDITORIA_AEM1_v2.md` | `pragma/auditoria/` | auditoría ciega v2 (DEC‑021), rev. 1 (DEC‑022/023) | ✅ escrito antes de la corrida v1.3 | `b5b11c…7a71` (v2 original `bc7e58…2591`) |
| `segunda_llave_chatgpt.json` · `doble_llave.json` | `pragma/auditoria/aem1_20260925T062504Z_256dba9f/` | segunda llave y comparación | ✅ | `9881d8…9746` · `1c50da…add8` |
| `aem1_v13.py` · `design_aem1_v1_3.py` · `double_key_aem1.py` · `test_aem1_v13.py` | `pragma_ae/`, `work/`, `tests/` | métricas v1.3, diseño, doble llave, tests | ✅ | `88a73f…be75` · `368502…b119` · `030645…92f7` · `05c4a6…9279` |
| `002_chatgpt_a_claude.md` · `003_claude_a_chatgpt.md` | `pragma/dialogo/` | segunda llave de ChatGPT; carta 003 | ✅ archivada · 🟡 para pegar | `b6d51d…046c` · ver manifiesto |
| `PRAGMA_A-E-menos-1_diagnostico_caso_chica_v1_2.ipynb` | `pragma/outputs/` | Experimento A‑E(−1) **vigente**, un clic | 🟡 GPU NOT_RUN | 23 celdas, 0 outputs, 81 581 bytes, hash `06315e…f0da` |
| `PRAGMA_A-E-menos-1_v1_2_verificacion.json` | `pragma/outputs/` | 68 + 39 + píxeles + E2E simulado + auditoría | ✅ estático/simulado | hash `08f50b…0e83` (los bytes varían entre corridas: incluye el tamaño del ZIP simulado) |
| `build_pragma_ae1_v1_2.py` / `verify_pragma_ae1_v1_2.py` / `harness_aem1.py` | `pragma/work/` | construir, verificar y probar v1.2 de punta a punta | ✅ ejecutados | `bae166…568e` / `f54b46…c63a` / `fa8923…b7bd` |
| `aem1_audit.py` | `pragma/pragma_ae/` | auditoría IA de ZIPs | ✅ tests + ZIP del arnés + corrida real | ver manifiesto |
| `PROTOCOLO_AUDITORIA_AEM1_v1.md` | `pragma/auditoria/` | protocolo congelado antes de mirar | ✅ | `436937…0810` (commit `2a9e264`) |
| `juicios_crudos.json` · `aem1_tabla_desciegada.json` · `aem1_audit_verdict.json` · `INFORME.md` | `pragma/auditoria/aem1_20260925T062504Z_256dba9f/` | auditoría ciega de la corrida real | ✅ 1ª llave | `e8286d…2673` · `e767de…01f0` · `dae172…3fc3` · `ce8671…5be4` |
| `blind_audit_aem1.py` | `pragma/work/` | preparar láminas ciegas y desciegar | ✅ ejecutado | `88d3d3…2521` |
| `SWEEP_PRERREGISTRO_A-E1.json` | `pragma/ae1/` | sweep A‑E1 prerregistrado | 🟡 pendiente de ChatGPT | `25a61a…5a38` |
| `test_fusion_matrix.py` | `pragma/tests/` | matriz que decidió DEC‑013‑Q | ✅ | `2626b7…c2ae` |
| ZIP de la corrida `…062504Z_256dba9f` | local (no versionado: recortes de la foto) | evidencia GPU | ✅ | `e6bb7a46…1976` |
| `PREFLIGHT_A-E-menos-1_v1_2.md` | `pragma/preflight/` | confirmación 18/18 del auditor IA | ✅ | `0df931…f800` |
| `GUIA_COLAB_A-E-menos-1_v1_2.md` | `pragma/` | pasos vigentes | ✅ | `e67c0e…7e69` |
| `dialogo/001_claude_a_chatgpt.md` | `pragma/dialogo/` | carta 001 | 🟡 enviada para pegar | `b1313f…b901` |
| `PRAGMA_A-E-menos-1_diagnostico_caso_chica_v1_1.ipynb` | `pragma/outputs/` | A‑E(−1) v1.1 | ⛔ supersedido por v1.2 para ejecutar; inmutable | 76 764 bytes, hash `ddf784…00dc` |
| `PRAGMA_A-E-menos-1_v1_1_verificacion.json` | `pragma/outputs/` | 68 + 19 + píxeles + arnés CPU | ✅ estático/CPU | hash `5c9868…dd54` |
| `build_pragma_ae1_v1_1.py` / `verify_pragma_ae1_v1_1.py` | `pragma/work/` | construir y verificar v1.1 | ✅ ejecutados | hashes `fcf62d…365c` / `23c4b2…714c` |
| `pragma_ae/` | `pragma/` | kit A‑E0/A‑E1 | ✅ 22 tests | ver `MANIFEST_SHA256.txt` |
| `scene_inventory.draft.json` | `pragma/ae0/` | borrador de inventario | 🟡 DRAFT | 52 objetos, archivo `aa011f…7741`, contenido `e4adc6…b940` |
| `ONTOLOGIA_PROPUESTA.md` / `PROTOCOLO_A-E0.md` | `pragma/ae0/` | propuesta y protocolo A‑E0 | 🔵 propuesta | hashes `0dae04…dcdd` / `c93cdb…8152` |
| `PREFLIGHT_A-E-menos-1_v1_0.md` | `pragma/preflight/` | informe del preflight | ✅ | hash `0870ed…44fa` |
| `START_HERE_CHATGPT_6_SOL.md` | `outputs/` | instrucciones y prompt inicial | ✅ | entregar con el bundle |
| `PRAGMA_ChatGPT_6_Sol_Handoff/` | `outputs/` | árbol portable con layout ejecutable | ✅ | manifiesto interno verifica payloads |
| `HANDOFF_MANIFEST_SHA256.txt` | dentro del handoff | hashes internos | ✅ | validado con `shasum -c` |
| `PRAGMA_ChatGPT_6_Sol_Handoff.zip` | `outputs/` | archivo único de transferencia | ✅ | integridad comprobada con `unzip -tq`; hash en sidecar externo |
| `PRAGMA_ChatGPT_6_Sol_Handoff.zip.sha256` | `outputs/` | hash de transporte no autorreferencial | ✅ | adjuntar junto al ZIP |
| `P1070614.JPG` | Desktop / paquete de transferencia | Foto de aceptación | ✅ | hash `8f6e3b…529d` |
| `PRAGMA_A-E-menos-1_diagnostico_caso_chica_Codex.ipynb` | `outputs/` | Experimento A‑E(−1) v1.0 | ⛔ supersedido por v1.1 para ejecutar; inmutable | 23 celdas, 10 de código, 0 outputs, hash `5941be…b706`; 3 coordenadas mal ubicadas |
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

- `SceneInventory`: contrato, validador y congelado — `✅` (`pragma_ae.inventory`); GT humano — `❌` (borrador DRAFT).
- `ClassAgnosticProposer`: SAM2 AMG — `🔵`.
- `ConceptSegmenter`: SAM3 o Grounding DINO→SAM2 — `🟣`.
- `ProposalRegistry`: inmutable y addressable — `🔵`.
- `OverlapContainmentGraph`: relaciones/duplicados — `🔵`; el inventario ya registra `parent_id` y `occluded_by`.
- `ProposalEvaluator`: métricas y gates A‑E1 — `✅ sintético` (`pragma_ae.metrics`).
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

### DEC-013-P — Fusión medible normalizada por el área invadida

**Propuesta:** "ninguna máscara Tier A fusiona dos instancias" = `|P*ᵢ ∩ Gⱼ| / |Gⱼ| ≥ 0,10` → fallo, excluyendo parte/entero.  
**Motivación:** con IoU solo, una máscara con el defecto de v4 obtiene 0,94 y pasa (test `FusionLoophole`).  
**Estado:** `🔵 PROPUESTA`, implementada en `metrics.py`; requiere ratificación.

### DEC-014-P — Fuga en franja de contacto por oclusión

**Propuesta:** fuga ≥ 0,20 en `dilatar(Gᵢ, 24 px) ∩ Gⱼ` para pares en `occluded_by`.  
**Recomendación:** reportar sin bloquear en la primera corrida A‑E1 y calibrar.  
**Estado:** `🔵 PROPUESTA`.

### DEC-015-P — Pasada humana ciega antes del borrador

**Propuesta:** la lista humana se escribe antes de leer el borrador asistido, para no heredar sus omisiones.  
**Estado:** `🔵 PROPUESTA`.

### DEC-016-P — Confirmación de coordenadas por hoja de contactos

**Propuesta:** ninguna configuración de puntos se confirma sin hoja de contactos a resolución nativa.  
**Motivación:** BUG‑008.  
**Estado:** `🟡` implementada en v1.1; requiere ratificación como regla general.

### DEC-013-Q — Fusión = fracción de la víctima + invasión interior

**Decisión:** FUSION si `|P ∩ G|/|G| ≥ 0,10` **y** `|P ∩ erode(G, 5)|/|erode(G, 5)| ≥ 0,10`; NOT_EVALUABLE si hay solape y la erosión borra la víctima; G es modal (visible).
**Origen:** ChatGPT 001 R1. **Cómo se decidió:** matriz sintética prerregistrada con una regla de decisión previa (Q 26/26, P 22/26).
**Estado:** `🟡` adoptada en el código; ratificación de la persona usuaria pendiente. Reemplaza a DEC‑013‑P como regla por defecto (P se sigue reportando).

### DEC-020 — Auditoría ciega con protocolo congelado antes de mirar

**Decisión:** toda corrida real se audita con un protocolo publicado antes de ver resultados, etiquetas anónimas, mapeo sellado y juicios crudos publicados antes de desciegar.
**Estado:** vigente (primera aplicación en la corrida `20260925T062504Z_256dba9f`).

### DEC-021 — Doble ciego temporal y compromiso por hash (auditoría v2)

**Decisión:**

- el paquete ciego de una corrida viaja solo, antes de cualquier resultado;
- ninguna carta previa revela si algo pasó, cuántas fallan, patrones por familia ni «la mejor»;
- los juicios de Claude se comprometen en git solo por SHA‑256 y se publican después de archivar
  la segunda llave;
- la segunda llave devuelve el SHA‑256 del paquete;
- `correct_subject` = identidad por mayoría del área;
- los agujeros cerrados ≥ 1000 px se miden y se clasifican;
- una candidata pasa solo con las dos llaves en TRUE.

**Origen:** ChatGPT 002 (cambio de protocolo) y comparación A–L (κ = 0,25 en `correct_subject`; F).
**Estado:** vigente desde v1.4 para corridas nuevas (`auditoria/PROTOCOLO_AUDITORIA_AEM1_v2.md`); la
corrida 1 queda juzgada con v1.

### DEC-022 — Adjudicación técnica de discrepancias (protocolo v2 rev. 1 §5.2)

**Decisión:**

- si las dos llaves discrepan, se resuelve primero por evidencia objetiva (agujeros, sentinelas,
  área dentro de una referencia, borde de ≤ 5 px);
- si no hay medición que decida, por una tercera revisión ciega: otra IA con solo la lámina y su
  `LEEME`, y decide la mayoría de tres;
- si tampoco, por adjudicación conjunta documentada, con regla conservadora (`UNRESOLVED` = no pasa).

**Origen:** ChatGPT 003, coherente con DEC‑018‑P. Sustituye la cláusula «decide la persona usuaria»
de DEC‑019‑P para cuestiones técnicas. La persona usuaria conserva el veto y decide lo semántico
irreducible.
**Estado:** vigente desde v1.5.

### DEC-023 — Referencia normalizada para BASE (`BASE_V2_REFERENCE`)

**Decisión:** una candidata BASE que reproduce bit a bit la corrida 1 no hereda una doble llave v2.
Su referencia es la adjudicación archivada, normalizada a las definiciones v2 con medición (B y D →
`correct_subject = TRUE`, 100 % dentro de A).
**Origen:** ChatGPT 003 (e): `BIT_EXACT_MASK ≠ BIT_EXACT_JUDGMENT_UNDER_NEW_PROTOCOL`.
**Estado:** vigente.

### DEC-018-P — La persona usuaria no fiscaliza: auditoría IA con evidencia

**Decisión (pedida por la persona usuaria, 2026‑09‑25):** las verificaciones que una IA puede hacer las hace la IA: confirmar coordenadas, revisar máscaras, verificar ZIPs. Queda registrado quién audita, sobre qué evidencia y con qué token.
**Salvaguardas:** la confirmación de configuración queda ligada a los píxeles (luma de los 18 parches); la auditoría detecta corridas simuladas o no GPU; toda aceptación exige doble llave (DEC‑019‑P); la persona usuaria puede vetar.
**Riesgo aceptado:** un error visual de la IA; se mitiga con primeros planos a resolución completa, métricas independientes y contraauditoría.
**Estado:** `🟡` implementada en v1.2 y `aem1_audit`; pendiente de ratificar como regla general.

### DEC-019-P — Ping‑pong Claude ↔ ChatGPT con doble llave

**Decisión:** Claude audita y guía; ChatGPT desafía y contraaudita sobre los mismos hashes; las cartas se numeran en `dialogo/` y se pegan entre aplicaciones mientras no haya canal directo (`api.openai.com` bloqueado en este entorno). Traspasar no es delegar.
**Estado:** `🟡` protocolo y carta 001 escritos.

### DEC-017 — Entradas y derivados de la foto fuera del repositorio público

**Decisión:** la foto, la extensión y todo derivado de la foto (overlays, recortes, láminas, GT) no se versionan; se localizan por hash.  
**Motivación:** repositorio público; la foto muestra personas reales con etiquetas de nombre.  
**Estado:** vigente desde v1.1 (reversible solo por decisión explícita si el repo pasa a privado).

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
| GPT‑6 Sol | `gpt-6-sol` en API; UI según selector | agente deseado en v1.0 | no usado en la continuación v1.1 |
| Claude Code (remoto) | claude.ai/code | continuación v1.1 | ✅ sin GPU; red sin acceso a `dl.fbaipublicfiles.com` ni `huggingface.co` |
| NumPy / Pillow / Matplotlib | 2.4.6 / 12.3.0 / 3.11.2 | kit, verificación v1.1 y arnés | ✅ versiones de la verificación v1.1 |
| Python (contenedor) | 3.11.15 (hay 3.12/3.13 disponibles) | verificación v1.1/v1.2 | ✅ |
| Colab CLI | `google-colab-cli` 0.7.2 (PyPI; Python ≥ 3.12) | ejecución delegada desde la sesión | 🔵 viable si se permite `colab.research.google.com` + OAuth por código; no probado |
| Colab MCP | `googlecolab/colab-mcp` | agente local + pestaña de Colab | ⛔ no aplicable a la sesión en la nube (solo local) |

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

**v1.1:** `P‑2` → (2640, 430) y `O2` → (2700, 380), ambos en el interior del cabello recogido posterior; `P‑3` → (2400, 810), tela oscura del hombro posterior; `O3` y `O4` sin mover, con “CONFIRMAR PROPIETARIO”. La caja no cambia. Distancia mínima prompt↔holdout: 78 px. `AEM1_CONFIG_CONFIRMADA` sigue en `False` y se confirma **en la hoja de contactos**.

**v1.2:** `O3` → (2735, 360) (pelo recogido posterior, arriba) y `O4` → (2325, 965) (blusa floral, interior). La confirmación la hace el auditor IA y queda ligada a la luma esperada de los 18 parches (`preflight/PREFLIGHT_A-E-menos-1_v1_2.md`, tolerancia 3,0). Distancia mínima prompt↔holdout: 70 px.

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

Estado: `✅ IMPLEMENTADO` como schema `pragma.scene_inventory` 0.1.0 con extensiones propuestas (`concept_en`, `kind`, `occluded_by`, `gt_required`, `review`, `notes`, `bbox_source`); ver `ae0/ONTOLOGIA_PROPUESTA.md` §3.

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

## 15.3 Verificación y herramientas v1.1

```bash
cd pragma
python3 work/verify_pragma_ae1_v1_1.py          # 68 Codex + 19 propias + píxeles + arnés CPU
python3 -m unittest discover -s tests           # 22 tests del kit
python3 -m pragma_ae validate ae0/scene_inventory.draft.json
python3 -m pragma_ae sheet ae0/scene_inventory.draft.json --out local/lamina_A-E0.png
python3 -m pragma_ae preflight outputs/PRAGMA_A-E-menos-1_diagnostico_caso_chica_v1_1.ipynb
python3 -m pragma_ae freeze ae0/scene_inventory.json --out ae0/scene_inventory.frozen.json --frozen-by "<firma>"
```

`build_pragma_ae1_v1_1.py` solo construye desde el v1.0 con hash fijado; si se cambia `pragma_ae/preflight.py`, hay que reconstruir y reverificar (la función se embebe en el cuaderno y el verificador exige que sea idéntica).

## 15.4 v1.2 y auditoría

```bash
python3 work/verify_pragma_ae1_v1_2.py                      # 68 + 39 + píxeles + E2E simulado + auditoría
python3 -m pragma_ae audit-aem1 PRAGMA_AEM1_<run>.zip        # auditoría automática de una corrida real
```

El veredicto se registra con `pragma_ae.aem1_audit.write_verdict` tras revisar todas las candidatas.

## 15.5 Carga de extensión futura

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
| Preflight coordenadas v1.0 | configuración A‑E(−1) | 18 puntos en su región | P‑3 y O2 en pared; P‑2 en borde; O3/O4 dudosos | ❌ v1.0 / corregido en v1.1 |
| Codex 68 checks sobre v1.1 | notebook v1.1 | 68/68 | 68/68 | ✅ estático |
| Checks propios v1.1 | notebook v1.1 | diff acotado, coordenadas, distancias, función embebida, ZIP | 19/19 | ✅ estático |
| Comprobación en píxeles | v1.0 vs v1.1 | viejos = pared; nuevos ≠ pared | PASS | ✅ con foto |
| Arnés CPU celdas 04/06/07 | notebook v1.1 | corren con la foto real | PASS; overlay, config y hoja de contactos generados | ✅ CPU (sin SAM) |
| Kit `pragma_ae` | contrato, métricas, preflight | 22 tests | 22/22 | ✅ sintético + borrador |
| Hueco IoU‑only del §9 | contrato de evaluación | detectar defecto v4 | IoU 0,94 lo aprueba; fusión 0,58 lo rechaza | ✅ sintético |
| Codex 68 checks sobre v1.2 | notebook v1.2 | 68/68 | 68/68 | ✅ estático |
| Checks propios v1.2 | diff, coordenadas, confirmación ligada, AST de correcciones, E2E, auditoría | 39/39 | 39/39 | ✅ estático + simulado |
| E2E con SAM simulado | celdas 03–11 del v1.2 con la foto real | un clic sin decisiones | 8 propuestas, 12 candidatas, `PENDING_EXTERNAL_AUDIT`, ZIP 4,7 MB | ✅ simulado (no mide calidad) |
| Auditoría IA sobre ZIP del arnés | `aem1_audit` | leer formato real, detectar simulado | integridad OK, `SIMULATED`, `SIMULATED_RUN_NOT_EVIDENCE` | ✅ |
| Kit completo | 29 tests | 29/29 | 29/29 | ✅ |
| **Corrida GPU A‑E(−1) v1.2** | SAM 2.1 Large en L4 | 4 protocolos, 12 candidatas | 12 candidatas, integridad 24/24, freeze = v4 | ✅ ejecución |
| Auditoría ciega (1ª llave) | 12 candidatas | alguna separa a la chica completa | 0/12; mejor intento `box+corrections:s1` | ❌ aceptación · ✅ auditoría |
| Reproducción v4 | `point#1` | mismos scores y área | 0,906/0,002/0,006 · 15,56 % | ✅ reproducida |
| Matriz DEC‑013 | 26 casos prerregistrados | la regla que acierte todos | Q 26/26 · P 22/26 | ✅ decide Q |
| Segunda llave (ChatGPT) | 12 láminas A–L | juicios independientes | `NO_PASS_CANDIDATE`; veredicto concordante 12/12; 42/48 celdas | ✅ doble llave (parcialmente contaminada) |
| Adjudicación G | `correct_subject` | mayoría del área sobre la chica | ≥ 61,9 % dentro de A | ✅ medido |
| Adjudicación F | agujeros ≥ 1000 px | ninguno sobre la chica | 2 (2540 y 1885 px), sobre pelo y overol | ✅ medido → FALSE |
| Diseño v1.3 | prerregistro | reproducible byte a byte | `--check` True | ✅ con foto |
| Métricas v1.3 + doble llave | `tests/test_aem1_v13.py` | 18 | 18/18 | ✅ sintético + archivos |
| Kit completo (v1.4) | 47 tests | 47/47 | 47/47 | ✅ |
| Contraauditoría previa (ChatGPT 003) | paquete 003 | integridad, diseño, decisiones | ZIP y 10/10 archivos OK; diseño PASS; (e) y §5.2 corregidos | ✅ |
| Cuaderno v1.3 | estático + E2E con SAM simulado + auditoría | 26 comprobaciones | 26/26 | ✅ simulado (no mide calidad) |
| Plan de llamadas | 178 llamadas registradas frente al plan | idénticas | 178/178 | ✅ simulado |
| Kit completo (v1.5) | 67 tests | 67/67 | 67/67 | ✅ |
| **Corrida GPU v1.3** | SAM 2.1 Large | 210 máscaras y auditoría ciega v2 | no ejecutada | ❌ |

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

### BUG-008 — Coordenadas A‑E(−1) v1.0 fuera de su región

**Síntoma:** `P‑3` y `O2` sobre la pared (luma 205/220, σ 21/9, igual que la pared de referencia); `P‑2` en el borde pared/moño.  
**Causa:** la verificación estática no puede comprobar semántica de ubicación y el overlay completo no tiene resolución para juzgar puntos a 20 px de un borde.  
**Impacto:** `*+corrections` empujaba contra la pared y el holdout del cabello superior medía la pared, justo en la zona del fallo v4.  
**Corrección:** cuaderno v1.1 + hoja de contactos (DEC‑016‑P).  
**Estado:** corregido en artefacto; confirmación humana pendiente; O3/O4 abiertos.

### BUG-009 — El contrato §9 aprobaría el defecto de v4

**Síntoma:** IoU 0,94 con 58 % de la persona posterior absorbida (escena sintética con proporciones reales).  
**Causa:** la cláusula de no fusión no estaba operacionalizada y el IoU se normaliza por la instancia grande.  
**Corrección propuesta:** DEC‑013‑P / DEC‑014‑P.  
**Estado:** abierto hasta ratificación.

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
| Definición de “objeto” no ratificada | segura | crítico | propuesta con recomendaciones en `ae0/ONTOLOGIA_PROPUESTA.md`; falta la decisión |
| Propietario de O3/O4 incierto | alta | medio | decidir en la hoja de contactos; si no se puede, no confirmar y reubicar |

## Riesgos técnicos

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---:|---:|---|
| SAM2 repo usa HEAD no fijado antes del run | media | alta | fijar commit después de primera corrida validada o registrar y repetir con ese commit |
| OOM/entorno Colab | baja-media en L4/A100 | alta | capturar estado, no degradar modelo en silencio, limpiar cache y reportar `INCONCLUSIVE_ENVIRONMENT` |
| errores humanos de inspección | media | alta | closeups, checklist ligado, segunda revisión independiente |
| sentinelas pasan pero hay fuga entre ellos | media | alta | no auto-PASS; inspección completa y luego GT real |
| `files.upload/download` se bloquea en Brave | media | media | detener celda y usar panel Archivos |
| publicar la foto o derivados en el repo público | baja con `.gitignore` | alta (privacidad) | DEC‑017; revisar `git status` antes de cada commit |
| el borrador asistido ancla la revisión humana | media | alta | pasada ciega DEC‑015‑P |
| umbrales DEC‑013/014 mal calibrados | media | media | reportar antes de bloquear; calibrar con la primera corrida A‑E1 |
| error visual del auditor IA | media | alta | primeros planos 1:1, métricas independientes, contraauditoría ChatGPT, veto de la persona usuaria |
| token OAuth del Colab CLI con permiso `cloud-platform` | baja | alta | solo si la persona usuaria lo decide; contenedor efímero; revocable en myaccount.google.com/permissions |
| ZIP real demasiado grande para adjuntar | baja | media | dpi reducido en v1.2 (simulado: 4,7 MB); si pasa, se sube por partes o se usa el modo delegado |

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

### P0-1 — (HECHO) Ejecutar A‑E(−1) v1.2

- **Acción:** ejecutar `PRAGMA_A-E-menos-1_diagnostico_caso_chica_v1_2.ipynb` con GPU: modo un clic (la persona arrastra la foto, pulsa «Ejecutar todas» y adjunta el ZIP) o delegado (Colab CLI desde la sesión de Claude).
- **Motivo:** el artefacto actual solo tiene verificación estática.
- **Dependencia:** Colab con GPU y la foto.
- **Criterio de finalización:** notebook ejecutado + ZIP íntegro + revisión visual independiente.

### P0-2 — (HECHO, 1ª llave) Auditar el resultado A‑E(−1)

- **Acción:** `python3 -m pragma_ae audit-aem1 <ZIP>`; revisar las 12 candidatas a resolución completa; registrar el veredicto con `write_verdict`; carta a ChatGPT para la contraauditoría (doble llave).
- **Motivo:** evitar otro PASS basado solo en checkboxes.
- **Criterio:** estado defendible y state file actualizado.

### P0-3 — Ratificar definición de objeto

- **Acción:** aceptar, cambiar o rechazar las recomendaciones de `ae0/ONTOLOGIA_PROPUESTA.md` (regla de tiers, 13 preguntas, DEC‑013‑P…016‑P).
- **Estado:** propuesta escrita; decisión humana pendiente. Puede hacerse en paralelo a P0‑1 (no requiere GPU).
- **Criterio:** contrato A‑E0 firmado conceptualmente por el usuario.

### P0-4 — Crear A‑E0

- **Acción:** seguir `ae0/PROTOCOLO_A-E0.md`: pasada ciega, revisar el borrador de 52 objetos con la lámina, GT de las tres personas, congelar.
- **Estado:** herramientas y borrador listos; trabajo humano pendiente (estimación: 3–5 h hasta etapa 1).
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

### P0-6 — (HECHO) Segunda llave de ChatGPT sobre la corrida real

- **Acción:** la persona usuaria pega la carta 002 y adjunta `PRAGMA_AEM1_contraauditoria_ciega.zip` (privado); ChatGPT juzga A–L a ciegas; Claude compara y registra.

### P0-7 — (HECHO) Prerregistrar A‑E(−1) v1.3

- **Acción:** prompts positivos sobre el pelo y las mangas de la chica (coordenadas nuevas con preflight), prompt recíproco a la persona posterior y perturbación ±15 px; mismo protocolo ciego. Solo después de la crítica de ChatGPT.

### P0-8 — (HECHO) Contraauditoría del prerregistro v1.3 y del A‑E1

- **Acción:** la persona usuaria pega la carta 003 y adjunta `PRAGMA_carta003_diseno_v1_3.zip`.
  ChatGPT verifica el propietario de H1, S1 y sus perturbaciones en la lámina privada, registra sus
  predicciones H‑G*, objeta o acepta las decisiones (a)–(e) e inspecciona el sweep A‑E1.
- **Criterio:** respuesta archivada tal cual y prerregistro marcado `PREREGISTERED` (o nueva versión
  si cambia algo, antes de cualquier corrida).

### P0-9 — (CONSTRUIDO; falta la GPU) Construir y ejecutar el cuaderno v1.3

- **Dependencia:** P0-8.
- **Acción:** construir el cuaderno según el prerregistro, con gates de congelado y luma de todos los
  prompts, verificarlo con el arnés, y que la persona usuaria lo ejecute con un clic.
- **Después:** auditoría ciega v2, con el paquete a ChatGPT antes que cualquier resultado.

### P0-10 — Auditoría ciega v2 de la corrida v1.3

- **Acción:** ejecutar en orden, sin saltar pasos:
  1. `aem1_v13_audit.integrity`, sin datos de resultado;
  2. `blind_package`: el paquete va solo a ChatGPT;
  3. juicio ciego de Claude, del que a git va solo el hash;
  4. segunda llave archivada tal cual;
  5. `analyze`, adjudicación técnica si hace falta, veredicto e hipótesis.
- **Criterio:** veredicto con doble llave o `UNRESOLVED` documentado; `PROJECT_STATE` actualizado.

### P0-5 — (HECHO) Cerrar la carta 001 con ChatGPT

- **Acción:** la persona usuaria pega `dialogo/001_claude_a_chatgpt.md` en ChatGPT y trae la respuesta; Claude la guarda como `001_chatgpt_a_claude.md`, la audita y responde.

### P1-4 — Calibrar DEC‑014‑P

- **Acción:** en la primera corrida A‑E1, reportar `contact_leak` sin bloquear y fijar el umbral con esos datos.
- **Criterio:** umbral ratificado antes de usarlo como gate.

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

> v1.1: cada pregunta tiene ahora una recomendación explícita en `ae0/ONTOLOGIA_PROPUESTA.md` §5. Siguen abiertas hasta que se ratifiquen.

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
- `OBSOLETO — NO USAR PARA EJECUTAR`: cuaderno A‑E(−1) v1.0 (`5941be…b706`); se conserva como antecedente inmutable.
- `OBSOLETO — HISTÓRICO`: `START_HERE_CHATGPT_6_SOL.md` y el punto de reanudación v1.0 (movidos a `history/handoff_v1.0/`).
- `OBSOLETO — NO USAR`: coordenadas v1.0 de `P‑2`, `P‑3` y `O2`.
- `OBSOLETO — NO USAR PARA EJECUTAR`: cuaderno A‑E(−1) v1.1 y su guía (exigían decisiones humanas); coordenadas v1.1 de `O3` y `O4`.
- `REEMPLAZADO`: "la revisión visual la hace la persona usuaria" → auditoría IA con doble llave y veto (DEC‑018‑P/019‑P).

Contradicciones resueltas:

| Información A | Información B | Vigente |
|---|---|---|
| carpeta/reporte `_PASS` | evidencia visual falla | `INCONCLUSIVE` |
| alcance: dos personas | alcance: cada objeto | A‑E es objetivo de producto; A‑E(−1) solo diagnóstico |
| A‑E1 = cierre chica | A‑E1 = AMG | diagnóstico renombrado A‑E(−1) |
| v4 ligero como notebook del run | copia incluye cambios posteriores | equivalencia byte a byte `NO VERIFICADA` |
| carpeta histórica documentada | carpeta ausente hoy | hecho histórico, no adjunto disponible |
| 68/68 = configuración lista | preflight: 3 puntos mal ubicados | la verificación estática no cubre ubicación; v1.1 |
| §9: IoU ≥ 0,70 basta | defecto v4 obtiene IoU 0,94 | DEC‑013‑P propuesta |

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
17. No versionar la foto, la extensión ni ningún derivado de la foto en el repositorio público (DEC‑017).
18. No confirmar coordenadas sin hoja de contactos a resolución nativa.
19. Un inventario solo sirve como GT si `validate` devuelve `A_E0_FROZEN`.
20. No pedir a la persona usuaria que verifique lo que una IA puede verificar; sí pedirle decisiones y dejarle vetar.
21. Nada es `ACEPTADO` sin doble llave (Claude + ChatGPT sobre los mismos hashes).
22. Una corrida simulada nunca es evidencia de SAM 2.

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

El prerregistro v1.3 está contraauditado por ChatGPT, con sus dos cambios de contrato aplicados
antes de correr. El cuaderno v1.3 está construido desde el prerregistro y verificado con SAM
simulado (26/26). Falta la corrida en GPU.

## Próxima acción

La persona usuaria ejecuta el cuaderno v1.3 en Colab (`GUIA_COLAB_A-E-menos-1_v1_3.md`) y adjunta
el ZIP **solo a Claude**. En paralelo, sin bloquear nada, pega la carta 004 en ChatGPT.

## Resultado esperado

Un ZIP `PRAGMA_AEM1v13_…_PENDING_EXTERNAL_AUDIT.zip`. Claude verifica su integridad sin mirar
resultados, prepara el paquete ciego `C01…` y la persona usuaria se lo manda **solo** a ChatGPT.

## En paralelo

- Respuesta de ChatGPT a la carta 004: interpretaciones de H‑G1 y H‑G3, Codex como tercera revisión.
- Ratificar la ontología v0.2 y hacer la pasada ciega del inventario A‑E0.

---

# 28. Prompt de Reanudación para Otra IA

```text
Continúo el proyecto PRAGMA. Repositorio: brune6320-del/motor-vimeo, carpeta pragma/.

Lee completo pragma/PROJECT_STATE.md (v1.5) y pragma/dialogo/README.md antes de proponer cambios.
Verifica pragma/MANIFEST_SHA256.txt y, si tienes la foto y la extensión, pragma/inputs/INPUTS_SHA256.txt.

No confundas: diseño, código escrito, verificación estática, ejecución simulada, ejecución GPU y
aceptación (doble llave Claude + ChatGPT). Estado de partida: v4 = INCONCLUSIVE; A-E(−1) corrida 1
(v1.2, GPU) = INCONCLUSIVE_SELECTED_OUTPUT_FAILED aceptado por doble llave; v1.3 = prerregistrado,
contraauditado, cuaderno listo (26/26 con SAM simulado), GPU NOT_RUN; auditoría ciega v2 rev. 1
(paquete antes que resultados, adjudicación técnica); A-E0 = borrador
DRAFT_UNVERIFIED y ontología sin ratificar; Fase B = BLOQUEADA; SAM 2 todavía no es rechazable.
La persona usuaria no fiscaliza: la verificación es de la IA; ella decide y veta.
No modifiques pragma-extension.zip. No integres FastAPI, localhost, YOLO-seg ni BiRefNet. No subas la
foto ni sus derivados al repositorio (es público).

En tu primera respuesta no cambies nada. Responde solo con:
1) archivos y hashes verificados;
2) faltantes o contradicciones;
3) estado en cinco líneas;
4) la única próxima acción de §27.
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
| v1.5 | 2026‑09‑25 | contraauditoría previa de ChatGPT 003 archivada; `BASE_V2_REFERENCE` (DEC‑023) y protocolo v2 rev. 1 con adjudicación técnica (DEC‑022); L∞/euclídea, cobertura O* continua y razones direccionales; H‑G1–G4; prerregistro `PREREGISTERED` con `call_plan` (178) y código de análisis congelado; cuaderno v1.3 construido y verificado 26/26 con SAM simulado; `aem1_v13_audit` (integridad, paquete ciego, análisis); contrato A‑E1 en borrador; guía v1.3; carta 004 |
| v1.4 | 2026‑09‑25 | segunda llave de ChatGPT archivada y comparada (`doble_llave.json`: veredicto concordante, 42/48, 5 concesiones y 1 refutación medida, contaminación acotada 1/207 900) → corrida 1 aceptada por doble llave; A‑E(−1) v1.3 cerrado y prerregistrado (ramas, región segura H1/S1, perturbaciones deterministas, recíproco sin reparación; `aem1_v13` + 18 tests); protocolo ciego v2 y DEC‑021; carta 003 |
| v1.3 | 2026‑09‑25 | primera corrida GPU real de A‑E(−1) v1.2 auditada a ciegas con protocolo congelado antes de mirar (`INCONCLUSIVE_SELECTED_OUTPUT_FAILED`, 0/12); reproducción de v4; respuesta 001 de ChatGPT archivada; DEC‑013‑Q adoptada por matriz prerregistrada; sweep A‑E1 prerregistrado y verificado en el commit exacto; ontología v0.2; DEC‑020; carta 002 |
| v1.2 | 2026‑09‑25 | la persona usuaria deja de fiscalizar: cuaderno A‑E(−1) v1.2 «un clic» (O3/O4 inequívocos, confirmación del auditor IA ligada a la luma, semillas exhaustivas, `PENDING_EXTERNAL_AUDIT`, modo sin navegador), verificador con arnés E2E de SAM simulado, auditoría IA de ZIPs, protocolo de diálogo con ChatGPT y carta 001, evaluación de Colab MCP/CLI, DEC‑018‑P/019‑P |
| v1.1 | 2026‑09‑25 | (addendum) guía de Colab paso a paso y `CLAUDE.md` con la regla de cerrar siempre con los pasos del usuario. Continuación en Claude Code: proyecto versionado en `pragma/`; preflight de coordenadas (BUG‑008) → A‑E(−1) v1.1 verificado sin GPU; kit `pragma_ae` con 22 tests; hueco del §9 (BUG‑009) y DEC‑013‑P…017; borrador de inventario de 52 objetos; ontología propuesta; nuevo punto de reanudación |

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

- ejecución GPU del cuaderno A‑E(−1) (v1.0 y v1.1);
- propietario real de los píxeles bajo O3 y O4;
- exactitud de las cajas del borrador de inventario (estimación visual);
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
