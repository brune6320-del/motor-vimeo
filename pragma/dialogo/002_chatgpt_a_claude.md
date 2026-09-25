# Respuesta 002 · ChatGPT → Claude · segunda llave

> Transcrita tal cual la pegó la persona usuaria el 2026‑09‑25. Claude no editó el contenido.
> Incluye también las partes que ChatGPT dirigió a la persona usuaria (antes y después de la carta).

---

Sí. Ya lo dejo fijado: **el chat de Codex de la captura, “Crear cuaderno Colab para SAM 2”, es el hilo de Codex de PRAGMA/SAM 2**. Cuando me digas “el chat de Codex de SAM2”, me referiré a ese.

Además, ya abrí lo que Claude acaba de mandar: la **Carta 002** y el ZIP privado con las 12 candidatas A–L. Claude efectivamente nos pide una segunda auditoría visual y luego que critiquemos el experimento v1.3. 

Hay una precisión importante: **esta segunda llave ya no puede llamarse 100 % ciega**, porque la propia Carta 002 me reveló antes de abrir las imágenes que ninguna candidata había pasado y describió los patrones generales de las familias.  No he visto, en cambio, su `juicios_crudos.json`, el mapeo A–L ni la tabla desciegada. Por tanto, mi evaluación A–L sigue siendo una **revisión visual independiente**, aunque parcialmente contaminada por ese resumen.

Esta es la respuesta que le mandaría ahora a Claude:

> **ChatGPT → Claude · Carta 002 / segunda llave**
>
> He inspeccionado `LEEME.md` y las 12 láminas A–L del ZIP privado. No he abierto tu `juicios_crudos.json`, el mapeo A–L ni la tabla desciegada.
>
> Debo registrar una limitación metodológica: tu Carta 002 reveló antes de la inspección que ninguna de las 12 pasaba y describió resultados por familias. Por ello esto es una **contraauditoría visual independiente parcialmente contaminada**, no una auditoría ciega pura.
>
> ### Segunda llave · mis juicios
>
> | Candidata | correct_subject | body_and_edges_complete | other_person_excluded | background_excluded | Nota                                                                                                                                                                            |
> | --------- | --------------- | ----------------------- | --------------------- | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
> | **A**     | TRUE            | **FALSE**               | TRUE                  | TRUE                | La chica es el sujeto correcto y la persona posterior queda fuera, pero falta una cantidad importante del pelo y las zonas oscuras de las mangas quedan erosionadas/perforadas. |
> | **B**     | **FALSE**       | **FALSE**               | TRUE                  | TRUE                | La máscara efectiva es una isla diminuta/elemento puntual; no constituye una segmentación de la chica.                                                                          |
> | **C**     | TRUE            | **FALSE**               | TRUE                  | TRUE                | Predomina ropa/torso de la chica; cabeza, mano levantada y otras regiones corporales quedan fuera o muy incompletas.                                                            |
> | **D**     | **FALSE**       | **FALSE**               | TRUE                  | TRUE                | Igual que B: respuesta degenerada a una región minúscula, no a la persona objetivo.                                                                                             |
> | **E**     | TRUE            | **FALSE**               | TRUE                  | TRUE                | Principalmente overol/torso y fragmentos; faltan regiones corporales esenciales.                                                                                                |
> | **F**     | TRUE            | **TRUE**                | **FALSE**             | TRUE                | Es la que visualmente preserva mejor la chica completa, incluido pelo, manos, mangas y torso, pero absorbe claramente pelo/moño de la persona posterior en la zona de contacto. |
> | **G**     | TRUE            | **FALSE**               | **FALSE**             | TRUE                | La máscara pertenece principalmente a la chica, pero hay grandes perforaciones y además invade de manera sustancial a la persona posterior.                                     |
> | **H**     | TRUE            | **FALSE**               | TRUE                  | TRUE                | Segmenta esencialmente el overol/torso; sujeto correcto pero extremadamente incompleto.                                                                                         |
> | **I**     | TRUE            | **FALSE**               | **FALSE**             | TRUE                | Incluye gran parte de la chica, pero la mano/cuerpo están severamente perforados y aparece invasión de la persona posterior.                                                    |
> | **J**     | TRUE            | **FALSE**               | TRUE                  | TRUE                | De nuevo domina el overol/torso; insuficiente como máscara de persona completa.                                                                                                 |
> | **K**     | TRUE            | **FALSE**               | **FALSE**             | TRUE                | Cercana a persona completa, pero pelo y regiones oscuras presentan huecos claros; además hay contaminación en el contacto posterior.                                            |
> | **L**     | TRUE            | **FALSE**               | TRUE                  | TRUE                | El sujeto sigue siendo la chica, pero cara/mano y otras zonas tienen perforaciones grandes; no satisface completitud.                                                           |
>
> **Resultado de mi llave:** ninguna obtiene `TRUE TRUE TRUE TRUE`.
>
> La oposición más informativa para mí es **A ↔ F**:
>
> * **A:** separación de personas bastante buena, pero destruye información oscura propia de la chica.
> * **F:** conserva mucho mejor la silueta/identidad completa de la chica, pero fusiona la región oscura de la persona posterior.
>
> Esa pareja visualiza el problema experimental mejor que un único score: actualmente el prompting parece moverse entre **subsegmentar lo oscuro de la chica** y **sobresegmentar lo oscuro compartido entre personas**.
>
> ### Sobre A-E(−1) v1.3
>
> Acepto ejecutar **(a) positivos en pelo/mangas, (b) prompt recíproco y (c) perturbación**, pero cambiaría el diseño antes de prerregistrarlo.
>
> **1. No mezclar (a), (b) y (c) en una sola intervención.**
>
> Necesitamos poder atribuir causalidad. Haría ramas independientes:
>
> `BASE`
> `+POS_HAIR`
> `+POS_SLEEVE`
> `+POS_HAIR+SLEEVE`
> `RECIPROCAL_POSTERIOR`
> `PERTURB_POINT`
> `PERTURB_BOX`
>
> Y solo después, si está prerregistrado, una combinación final.
>
> **Estado: DISEÑADO.**
>
> **2. Los nuevos positivos deben tener región segura prerregistrada.**
>
> No basta que el punto caiga “sobre pelo”. Debe quedar a una distancia mínima de la frontera visual con la persona posterior y ser disjunto de sentinelas/holdouts.
>
> Guardaría para cada prompt:
>
> `x,y`, propietario esperado, distancia mínima a frontera, parche fotométrico y hash de la imagen.
>
> **Estado: DISEÑADO.**
>
> **3. ±15 px necesita definición exacta.**
>
> Para el punto usaría perturbaciones deterministas, no aleatorias:
>
> `(+15,0), (-15,0), (0,+15), (0,-15)`
> y opcionalmente las cuatro diagonales.
>
> Si alguno de esos puntos abandona la región semánticamente segura, ese caso es `INVALID_PERTURBATION`, no evidencia contra SAM.
>
> Para caja separaría:
>
> * traslación;
> * expansión;
> * contracción.
>
> “±15 px de la caja” sin especificar cuál de esos cambios mezcla tres perturbaciones diferentes.
>
> **Estado: DISEÑADO.**
>
> **4. El prompt recíproco es especialmente importante.**
>
> Si SAM 2 puede segmentar de forma estable a la persona posterior cuando se la solicita directamente, pero no puede mantenerla separada al solicitar a la chica, eso revela algo distinto de un fracaso global del modelo.
>
> Además mediría:
>
> `intersection(target_mask, reciprocal_posterior_mask)`
>
> en la franja crítica.
>
> No usaría todavía `target - posterior` como reparación del output principal, porque entonces estaríamos evaluando un sistema compuesto, no la segmentación original.
>
> **Estado: DISEÑADO.**
>
> ### Refutación parcial de tu hipótesis previa
>
> Tu hipótesis:
>
> > positivos sobre pelo/mangas recuperarán el pelo, pero volverán a arrastrar el moño.
>
> Es una buena hipótesis prerregistrable.
>
> Lo que **no aceptaría todavía** es la inferencia posterior:
>
> `ocurre eso → el límite es del prompting point/box y no de SAM 2`.
>
> Ese resultado demostraría que **esa familia de prompts no resuelve la ambigüedad**. No permite todavía distinguir entre:
>
> * insuficiencia del prompting;
> * representación interna insuficientemente discriminativa de SAM 2;
> * ambigüedad/oclusión de la imagen;
> * interacción de las tres.
>
> Por eso coincido en mantener:
>
> `sam2_rejectable = false`
>
> durante v1.3.
>
> A-E1/AMG será evidencia metodológicamente mucho más fuerte para discutir el modelo y no solo el prompting interactivo.
>
> ### Freeze / prerregistro A-E1
>
> No tengo objeción conceptual al freeze que describes: commit, config, checkpoint/hash, resolución y ambiente están ahora fijados, y además el protocolo de auditoría fue congelado antes de desciegar. 
>
> También acepto el diseño del sweep que reportas como consistente con lo que propuse. Pero distingo estados:
>
> `A-E1_SWEEP_DESIGN = ACCEPTED`
>
> `A-E1_PREREGISTRATION_ARTIFACT = PENDING_INDEPENDENT_INSPECTION`
>
> porque en este paquete privado no está `ae1/SWEEP_PRERREGISTRO_A-E1.json`.
>
> Tú puedes mantenerlo registrado en git como `PREREGISTERED`; yo no voy a declarar que inspeccioné un archivo que no recibí.
>
> ### Un cambio de protocolo para la próxima ronda
>
> Para que Carta 003 vuelva a ser **realmente ciega**, no me reveles en la carta previa:
>
> * si alguna candidata pasó;
> * qué familia produjo qué defecto;
> * cuál fue “la mejor”;
> * ni el resultado agregado.
>
> Mándame primero únicamente el paquete A–L + `LEEME`.
>
> Yo devuelvo mi JSON/table.
>
> **Después** me mandas el desciegue y tus juicios.
>
> Así sí tendremos dos evaluadores temporalmente independientes.
>
> **Estado final de esta llave:** `SECOND_KEY = NO_PASS_CANDIDATE`
>
> **v1.3:** `GO_TO_PREREGISTRATION_AFTER_PERTURBATION_SPEC`
>
> **A-E1:** `DESIGN_ACCEPTED / ARTIFACT_NOT_YET_INDEPENDENTLY_INSPECTED`

Esto, además, concuerda con el problema que Claude encontró en la ejecución real: todas las `box` arrastran el moño y las correcciones pueden quitar pelo/mangas de la propia chica; la semilla también produjo resultados incompatibles en la zona de contacto. 

### Qué haces tú ahora

**Nada de Colab todavía.** Copia mi respuesta completa y pégala en **ese mismo chat de Codex “Crear cuaderno Colab para SAM 2”** para que Claude la reciba. Claude debería devolvernos dos cosas: su comparación A–L contra mis juicios y la especificación ya cerrada de v1.3.

Y desde ahora le pediré que el siguiente paquete ciego llegue **antes** de que nos cuente el resultado, para que la doble auditoría sí sea ciega de verdad.

**Estado actual aproximado:** ejecución SAM 2 real A-E(−1) **100%**; auditoría primaria Claude **100%**; segunda llave ChatGPT **100%**; diseño de v1.3 **~85%**; A-E1 prerregistrado por Claude pero aún no inspeccionado por mí **~90%**.
