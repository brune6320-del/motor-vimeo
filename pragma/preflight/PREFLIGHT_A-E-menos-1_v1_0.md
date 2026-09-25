# Preflight A‑E(−1) v1.0: coordenadas contra la foto real

> **Modo GENESIS:** diagnóstico técnico. **Fecha:** 2026‑09‑25. **Sin GPU**: aquí no se ejecutó SAM 2.
> Foto verificada por SHA‑256 `8f6e3b…529d`. Cuaderno auditado: `5941be…b706` (Codex v1.0).

## Por qué

La verificación Codex (68/68) comprueba que las 18 coordenadas sean únicas, estén dentro de la
imagen y separen prompts de holdouts. **No comprueba que cada punto caiga sobre la región que
dice su descripción.** Esa comprobación quedaba para una persona mirando un overlay de 22×12
pulgadas de la foto entera, a una escala en la que un punto 20 px por encima de un moño parece
estar sobre él.

## Método

1. Hoja de contactos: cada sentinela recortado a ±90 px, ampliado ×2, con el parche real que se
   evalúa (radio 6) dibujado (`python3 -m pragma_ae preflight <cuaderno>`).
2. Luminancia del parche (media y desviación) comparada con dos referencias de pared lisa.
3. Perfiles de luminancia a lo largo de los bordes afectados.

## Hallazgos

| ID | Rol | v1.0 | Luma media / sd | Pared de referencia | Veredicto |
|---|---|---|---:|---:|---|
| **P‑3** | prompt − persona posterior, "hombro posterior" | (2450, 700) | **205.1 / 20.8** | 209.0 / 19.8 | ❌ **pared**. El perfil vertical en x=2450 muestra el borde del hombro en y≈745. |
| **O2** | holdout otra persona, "cabello posterior superior" | (2680, 300) | **219.7 / 9.3** | 215.3 / 12.3 | ❌ **pared**, ~20–30 px por encima del moño (el cabello empieza en y≈320). |
| **P‑2** | prompt − persona posterior, "cabello/cabeza posterior" | (2600, 400) | 146.7 / 68.7 | — | ⚠️ **borde** pared/moño: la mitad del parche es pared (perfil horizontal: borde en x≈2600). |
| O3 | holdout otra persona, "cabello posterior central" | (2680, 520) | 42.0 / 34.2 | — | ❓ pelo oscuro en la **unión** moño↔coronilla de la chica: propietario no decidible por luminancia. |
| O4 | holdout otra persona, "manga/torso posterior" | (2335, 1035) | 140.9 / 70.5 | — | ❓ **borde** entre blusa floral posterior y hombro de la chica. |
| B2 | holdout fondo, "mesa/mantel" | (1735, 1635) | 182.9 / 35.6 | — | ✅ correcto, pero **fuera de la caja**: bajo `box` casi no puede fallar (poca potencia falsadora). |
| resto (12) | — | — | — | — | ✅ caen donde dicen (hoja de contactos). |

### Consecuencia científica

El fallo auditado en v4 fue que la máscara de la chica **se llevó el cabello y la cabeza de la
persona posterior**. En v1.0, justo en esa zona:

- de los tres prompts negativos, uno está en la pared (P‑3) y otro medio en la pared (P‑2): el
  protocolo `*+corrections` empuja contra la pared, no contra la otra persona;
- el holdout que debía vigilar el cabello superior (O2) mide la pared: una máscara que se lleve
  el moño entero **pasaría ese sentinela**.

Ejecutar v1.0 tal cual habría gastado una corrida de GPU con el diagnóstico debilitado
exactamente donde el caso falla.

## Corrección propuesta → cuaderno v1.1

| ID | v1.0 | v1.1 | Luma v1.1 | Distancia mínima a un holdout |
|---|---|---|---:|---:|
| P‑2 | (2600, 400) | **(2640, 430)** interior del cabello recogido | 56.8 / 44.9 | 78 px (O2) |
| P‑3 | (2450, 700) | **(2400, 810)** tela oscura del hombro posterior | 90.9 / 53.0 | 78 px (O1) |
| O2 | (2680, 300) | **(2700, 380)** interior del cabello recogido | 78.7 / 52.6 | 78 px (P‑2) |
| O3, O4 | sin mover | descripción: **CONFIRMAR PROPIETARIO** | — | — |

- La caja `(2100, 300, 3500, 2247)` y los otros 15 sentinelas no cambian.
- Distancia mínima prompt↔holdout en v1.1: 78 px (umbral de la verificación: 60 px = 10 parches).
- `AEM1_CONFIG_CONFIRMADA` sigue en `False`. **La confirmación es humana**: la luminancia solo
  descarta "pared lisa", no dice de quién es un píxel de pelo.

## Evidencia

- Cuaderno v1.1: `outputs/PRAGMA_A-E-menos-1_diagnostico_caso_chica_v1_1.ipynb` (generado por
  `work/build_pragma_ae1_v1_1.py` desde el v1.0 con hash fijado; el v1.0 no se toca).
- Verificación: `outputs/PRAGMA_A-E-menos-1_v1_1_verificacion.json`: las 68 comprobaciones Codex
  sobre v1.1 + 19 propias + comprobación en píxeles + arnés CPU que ejecutó las celdas 04, 06 y 07
  del propio cuaderno con la foto real (`config_digest` en el JSON).
- Las hojas de contactos y overlays **no se versionan** (derivan de la foto; el repo es público).
  Se regeneran con `python3 -m pragma_ae preflight …` y `python3 work/verify_pragma_ae1_v1_1.py`.
