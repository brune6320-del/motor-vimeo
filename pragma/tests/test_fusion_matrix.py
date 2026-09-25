"""Matriz sintética que decide entre DEC-013-P y DEC-013-Q (ChatGPT 001, R1) ANTES de ver A-E1 real.

Escena a la resolución canónica 4000×2248. La víctima es la persona posterior (caja amodal de
ae0_003: x 2230–2600, y 310–1180), tapada por la chica desde la derecha. Su parte visible es una
franja cuyo ancho fija la visibilidad (5, 10, 25 o 50 % del ancho amodal). δ = 5 px (tolerancia de
borde del protocolo), τ = 0,10.

Etiquetas PRERREGISTRADAS (escritas antes de ejecutar esta prueba):
- absorción profunda (atraviesa la víctima) del 5 %               → NO_FUSION  (bajo τ)
- absorción profunda del 10, 20 y 50 %                             → FUSION
- banda de borde de 3 px pegada a la chica (≤ δ)                   → NO_FUSION  (frontera ambigua)
- víctima más delgada que 2δ+1 con cualquier solape                → NOT_EVALUABLE
- caso crítico, 200 px en banda frente a 200 px en bloque profundo → NO_FUSION / FUSION
- propuesta en contacto sin solape, o separada                     → NO_FUSION

Regla de decisión prerregistrada: gana la regla que acierte TODAS las etiquetas; si aciertan
ambas, P (la más simple); si no acierta ninguna, no se adopta ninguna.
"""

import unittest

import numpy as np

from pragma_ae.metrics import fusion_status

H, W = 2248, 4000
AMODAL = (2230, 310, 2600, 1180)       # x1, y1, x2, y2
TAU, DELTA = 0.10, 5


def scene(visible_width):
    """Chica (tapa desde la derecha) y víctima visible (franja izquierda de la caja amodal)."""
    x1, y1, x2, y2 = AMODAL
    girl = np.zeros((H, W), bool)
    girl[430:H, x1 + visible_width:3430] = True
    victim = np.zeros((H, W), bool)
    victim[y1:y2, x1:x1 + visible_width] = True
    victim &= ~girl
    return girl, victim


def deep(girl, victim, fraction):
    """La propuesta atraviesa la víctima entera en una banda horizontal que suma `fraction` de su área."""
    rows = np.flatnonzero(victim.any(axis=1))
    height = int(round(fraction * len(rows)))
    start = rows[0] + (len(rows) - height) // 2
    proposal = girl.copy()
    proposal[start:start + height] |= victim[start:start + height]
    return proposal


def band(girl, victim, width=3):
    """Banda de `width` px de la víctima pegada a la frontera con la chica (el borde ambiguo)."""
    cols = np.flatnonzero(victim.any(axis=0))
    proposal = girl.copy()
    edge = cols[-1] + 1
    proposal[:, edge - width:edge] |= victim[:, edge - width:edge]
    return proposal


def cases():
    out = []
    amodal_width = AMODAL[2] - AMODAL[0]
    for visibility in (0.05, 0.10, 0.25, 0.50):
        girl, victim = scene(int(round(visibility * amodal_width)))
        for fraction in (0.05, 0.10, 0.20, 0.50):
            out.append((f"profunda v={visibility:.0%} a={fraction:.0%}", deep(girl, victim, fraction), victim,
                        "NO_FUSION" if fraction < TAU else "FUSION"))
        out.append((f"banda 3px v={visibility:.0%}", band(girl, victim), victim, "NO_FUSION"))
    girl, victim = scene(8)                                   # 8 px < 2δ+1: la erosión la borra
    out.append(("víctima delgada 8px + profunda 50%", deep(girl, victim, 0.50), victim, "NOT_EVALUABLE"))
    out.append(("víctima delgada 8px + banda 3px", band(girl, victim), victim, "NOT_EVALUABLE"))
    # Caso crítico: mismo solape (~200 px) sobre un fragmento visible pequeño (~1 500 px).
    small = np.zeros((H, W), bool)
    small[600:683, 2382:2400] = True                          # 83 × 18 = 1 494 px, pegado a la chica
    girl = np.zeros((H, W), bool)
    girl[430:H, 2400:3430] = True
    band200 = girl.copy()
    band200[600:667, 2397:2400] = True                        # 67 × 3 = 201 px en el borde
    block200 = girl.copy()
    block200[634:648, 2384:2398] = True                       # 14 × 14 = 196 px en el interior
    out.append(("crítico 200px banda", band200, small, "NO_FUSION"))
    out.append(("crítico 200px profunda", block200, small, "FUSION"))
    girl, victim = scene(185)
    out.append(("contacto sin solape", girl, victim, "NO_FUSION"))
    separated = np.zeros((H, W), bool)
    separated[430:H, 2465:3430] = True
    out.append(("separada", separated, victim, "NO_FUSION"))
    return out


class FusionMatrix(unittest.TestCase):
    def test_rule_q_wins_the_preregistered_matrix(self):
        results = {"P": [], "Q": []}
        for name, proposal, victim, expected in cases():
            for rule in results:
                got = fusion_status(proposal, victim, rule=rule, tau=TAU, erosion_px=DELTA)["status"]
                results[rule].append((name, expected, got))
        misses = {rule: [(n, e, g) for n, e, g in rows if e != g] for rule, rows in results.items()}
        # Resultado: Q acierta toda la matriz; P falla justo donde R1 decía (bandas y víctimas delgadas).
        self.assertEqual(misses["Q"], [], misses["Q"])
        self.assertTrue(misses["P"], "si P también acertara todo, la regla prerregistrada elegiría P")
        names_p = {n for n, _, _ in misses["P"]}
        self.assertIn("crítico 200px banda", names_p)
        self.assertIn("víctima delgada 8px + profunda 50%", names_p)

    def test_equal_area_different_depth(self):
        by_name = {name: (proposal, victim) for name, proposal, victim, _ in cases()}
        band200, small = by_name["crítico 200px banda"]
        block200, _ = by_name["crítico 200px profunda"]
        p_band = fusion_status(band200, small, rule="P")
        p_block = fusion_status(block200, small, rule="P")
        self.assertEqual(p_band["status"], p_block["status"])          # P no distingue la geometría
        self.assertEqual(fusion_status(band200, small, rule="Q")["status"], "NO_FUSION")
        self.assertEqual(fusion_status(block200, small, rule="Q")["status"], "FUSION")


if __name__ == "__main__":
    unittest.main()
