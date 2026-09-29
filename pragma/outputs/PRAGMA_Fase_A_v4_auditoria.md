# PRAGMA · Auditoría del parche de Claude y v4 integrada

Fecha: 2026-08-10

## Archivos auditados

Parche de Claude:

```text
/Users/usuario/Desktop/PRAGMA_Fase_A_v4_parche.md
SHA-256: d5c05f4c2c02026e8ef34baec11b606c28bc1d6f3ae71d643b028548845fe722
```

Cuaderno base v3:

```text
SHA-256: 3d9b75a1944274a3d107d971c2cd6395dd49b0d835febf8cf5e04ed6870a4157
```

Cuaderno v4 integrado:

```text
PRAGMA_Fase_A_SAM2_v4_autocontenido.ipynb
SHA-256: 148ea1bca428fed7723ec0af7bc8b00f0603f27f8de56cc046e53e532f1270db
```

## Veredicto sobre el parche de Claude

Contiene dos ideas valiosas:

1. conservar logits de alta resolución mediante `return_logits=True`;
2. impedir que un resultado negativo con una sola modalidad se interprete como rechazo general de SAM 2.

Sin embargo, el `.md` es una especificación parcial, no un parche ejecutable:

- cambia `generate()` de cuatro a cinco retornos sin actualizar los consumidores;
- `propose_with_box()` termina en un comentario y no devuelve una propuesta;
- una caja sin puntos deja `prompts=None`, pero el flujo v3 desreferencia `.points`;
- solo registra la modalidad `box`, por lo que FAIL queda inalcanzable;
- el cálculo de estado modifica `notes` y duplica texto al reejecutarse;
- el smoke rechaza CPU/FP32 y puede pasar aunque ninguna máscara contenga el clic;
- `SOFT_BAND` es local y no puede reportarse por sujeto;
- una alpha con valores intermedios no demuestra un borde correcto;
- el checklist no está ligado a la propuesta ni a las evidencias que se inspeccionaron.

Aplicado literalmente, el cambio de retornos produce `ValueError: too many values to unpack` en la primera ruta que siga esperando cuatro valores.

## Matiz conceptual sobre la alpha

Es correcto que la salida SAM 2 de la v3 es binaria cuando `return_logits=False`. Eso no demuestra un fallo del contrato de Fase A: esta fase valida selección por instancia y deja un refinador intercambiable para BiRefNet.

La v4 conserva ambos artefactos:

- **salida de aceptación:** máscara binaria de SAM 2;
- **vista diagnóstica:** alpha suavizada desde logits.

La vista por logits no participa en PASS/FAIL y se etiqueta expresamente como no-matting. Así se puede comparar la banda de transición sin confundir probabilidad de segmentación con cobertura real del pelo.

## Mejoras implementadas en la v4

### API y datos

- `GeneratedMasks` sustituye la tupla frágil de cinco posiciones;
- el umbral binario se aplica sobre logits float32 antes de almacenarlos como fp16;
- `Proposal` guarda puntos opcionales, caja, modalidad, logits high/low y parentesco;
- caja sola y caja+puntos están soportadas;
- el refinamiento conserva la caja y usa `mask_input`;
- selector de caja accesible mediante dos clics, con Cancelar y timeout.

### Smoke test

Comprueba:

- tres candidatas;
- shapes correctos;
- scores y logits finitos;
- al menos una máscara no vacía;
- que alguna máscara contenga el punto;
- al menos un área plausible.

La diversidad entre candidatas se registra como diagnóstico. CPU/FP32 no se rechaza.

### Estados y modalidades

- PASS puede obtenerse con cualquier modalidad;
- un negativo antes de completar el protocolo es `INCONCLUSIVE`;
- FAIL requiere revisiones de `point`, `point+corrections` y `box`;
- cada revisión se liga a un `proposal_id` real;
- deben enumerarse todas las candidatas revisadas;
- cada revisión FAIL exige notas;
- calcular el estado no modifica el checklist.

### Bloqueo de falsos PASS

El checklist positivo debe coincidir con:

```text
proposal_id
candidate_index
inspection_token
```

El `inspection_token` incorpora hashes de las evidencias. Un reintento o una nueva finalización invalida el checklist anterior.

### Evidencias

- `trial_history` append-only;
- nombres únicos por finalización;
- salida binaria y preview por logits separadas;
- hashes verificados otra vez antes de exportar;
- todos los trials permanecen en el ZIP;
- el ZIP se reabre y cada payload se compara contra tamaño y SHA-256 del manifiesto.

## Demostración

Resultado local:

```text
15 / 15 pruebas PASS
```

Incluye:

1. JSON y sintaxis de las 15 celdas;
2. fotografía exacta incorporada;
3. matriz T4/A100/CPU;
4. resultado del generador tipado;
5. API de logits y orden correcto de umbral/cast;
6. JavaScript y selector de caja;
7. smoke sensible al contenido;
8. alpha por logits no bloqueante;
9. camino de caja sin `None` inválido;
10. ausencia de `argmax` automático;
11. modalidades registradas desde propuestas;
12. PASS ligado a evidencia y FAIL auditado;
13. cálculo de estado puro;
14. ledger append-only e integridad del ZIP;
15. comparación entre el memo parcial y la v4 integrada.

Prueba falsable del nuevo smoke:

- tres máscaras plausibles que contienen el punto → PASS;
- tres máscaras no vacías y plausibles, pero alejadas del punto → FAIL.

Prueba falsable contra checklist obsoleto:

- token/propuesta/candidata coincidentes → PASS;
- token de una evidencia anterior → `ValueError` y PASS rechazado.

## Límite honesto

Estas pruebas cubren estructura, JavaScript y lógica ejecutable con datos sintéticos. La calidad final de SAM 2 sobre las dos personas solo queda demostrada al ejecutar el cuaderno en Colab con GPU, conservar el notebook ejecutado y revisar las evidencias reales.

## Fuentes primarias

- https://github.com/facebookresearch/sam2
- https://github.com/facebookresearch/sam2/blob/main/sam2/sam2_image_predictor.py
- https://github.com/facebookresearch/sam2/blob/main/INSTALL.md
- https://raw.githubusercontent.com/googlecolab/colabtools/main/google/colab/output/_js.py
