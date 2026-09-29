# Preflight A‑E(−1) v1.2: confirmación de la configuración por el auditor IA

> **Fecha:** 2026‑09‑25 · **Auditor:** Claude Code (IA) · **Sin GPU**.
> Foto verificada por SHA‑256 `8f6e3b…529d`. Cuaderno auditado: v1.2 (`06315e…f0da`), generado
> desde v1.1 (`ddf784…00dc`) por `work/build_pragma_ae1_v1_2.py`.
> Antecedente: [`PREFLIGHT_A-E-menos-1_v1_0.md`](PREFLIGHT_A-E-menos-1_v1_0.md) (P‑2, P‑3 y O2 corregidos en v1.1).

## Por qué cambia el papel de la persona usuaria

La persona usuaria pidió no fiscalizar en Colab lo que puede verificar una IA. Desde v1.2
(DEC‑018‑P), la confirmación de coordenadas la hace el auditor IA **con evidencia registrada**, y
esa confirmación queda **ligada a los píxeles**: el cuaderno recalcula la luminancia de los 18
parches y solo continúa si coincide con la tabla de abajo (tolerancia 3,0). Si la foto o su
decodificación fueran otras, el cuaderno se detiene en `PENDING_CONFIG`.

## Lo que quedaba abierto en v1.1: O3 y O4

En v1.1, `O3` (2680, 520) y `O4` (2335, 1035) caían en zonas de contacto donde **no se podía
decidir a quién pertenece el píxel**:

- `O3` estaba en la unión del pelo recogido de la persona posterior con la coronilla de la chica.
  La luminancia (42) solo dice "pelo oscuro", no de quién.
- `O4` estaba en el borde entre la blusa floral posterior y una zona oscura que, mirada a
  resolución completa, parece la manga oscura del brazo izquierdo de la chica.

Un holdout de propietario dudoso no falsa nada: si falla, no se sabe si falló el modelo o el
punto. La franja de contacto se audita mejor con la máscara completa (primeros planos a
resolución nativa en `pragma_ae.aem1_audit`) que con dos puntos ambiguos.

| ID | v1.1 | **v1.2** | Por qué es inequívoco | Luma media | Prompt más cercano |
|---|---|---|---|---:|---|
| O3 | (2680, 520) | **(2735, 360)** | interior del pelo recogido, por encima de la coronilla de la chica (que empieza en y≈440) y a ≥25 px de sus bordes | 57,1 | P‑2 a 118 px |
| O4 | (2335, 1035) | **(2325, 965)** | interior del estampado floral de la blusa posterior, a >50 px de sus bordes | 185,1 | P‑1 a 70 px |

Extensión del pelo recogido medida por perfiles de luminancia (píxeles con media 7×7 < 110):
x ∈ [2645, 2760] en y=350 y x ∈ [2630, 2770] en y=380. La coronilla de la chica se une a partir de y≈430.

## Confirmación 18/18

| ID | Rol | Coordenada | Región | Luma esperada |
|---|---|---|---|---:|
| P+1 | prompt + | (2588, 1785) | overol de la chica | 249,3 |
| P‑1 | prompt − | (2350, 900) | blusa floral posterior | 125,6 |
| P‑2 | prompt − | (2640, 430) | pelo recogido posterior | 56,8 |
| P‑3 | prompt − | (2400, 810) | hombro posterior, tela oscura | 90,9 |
| K1 | dentro | (2835, 635) | frente/cara | 245,8 |
| K2 | dentro | (2730, 650) | nacimiento del pelo de la chica | 135,3 |
| K3 | dentro | (2435, 1135) | hombro con rayas | 101,4 |
| K4 | dentro | (3185, 985) | dedo de la mano en V (sobreexpuesta) | 254,3 |
| K5 | dentro | (3285, 1335) | manga del brazo levantado | 101,7 |
| K6 | dentro | (2235, 1935) | mano que cuelga | 220,3 |
| K7 | dentro | (2785, 2035) | overol inferior | 252,9 |
| O1 | fuera (otra persona) | (2460, 860) | blusa floral posterior | 179,8 |
| O2 | fuera (otra persona) | (2700, 380) | pelo recogido posterior | 78,7 |
| **O3** | fuera (otra persona) | **(2735, 360)** | pelo recogido posterior, arriba | 57,1 |
| **O4** | fuera (otra persona) | **(2325, 965)** | blusa floral posterior, interior | 185,1 |
| B1 | fuera (fondo) | (2185, 435) | cuadro | 203,4 |
| B2 | fuera (fondo) | (1735, 1635) | mesa/mantel (fuera de la caja: poca potencia falsadora) | 182,9 |
| B3 | fuera (fondo) | (3485, 1485) | silla oscura | 49,6 |

Distancia mínima prompt↔holdout: **70 px** (P‑1↔O4; umbral 60 px). La caja `(2100, 300, 3500, 2247)` no cambia.

## Límites honestos

- La luminancia descarta "pared lisa" y liga la confirmación a los píxeles; **la pertenencia** de
  cada punto la juzgó el auditor IA mirando recortes a resolución completa. Puede equivocarse:
  por eso ChatGPT contraaudita (DEC‑019‑P) y la persona usuaria puede vetar.
- Ninguna comprobación de esta página ejecutó SAM 2.

## Evidencia

- Verificación: `outputs/PRAGMA_A-E-menos-1_v1_2_verificacion.json`: 68 comprobaciones Codex, 39 de
  v1.2, comprobación en píxeles y arnés de punta a punta con SAM simulado. El arnés cubre tres
  escenarios (navegador, sin navegador y sin foto) y la auditoría IA lee el ZIP resultante.
- Recortes y hojas de contactos: locales (`local/`), no versionados (el repositorio es público).
