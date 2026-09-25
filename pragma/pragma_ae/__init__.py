"""PRAGMA · kit A-E (inventario de escena, métricas y preflight).

Solo depende de NumPy y Pillow. No carga modelos, no toca la extensión y no
implementa nada de Fase B: define la verdad humana (A-E0) y la regla con la que
se medirán los proponentes (A-E1) antes de ejecutar ninguno.
"""

EXPECTED_IMAGE_SHA256 = "8f6e3b6f5013265a45c7e89121e3f0a18e3386951e2e75378b28da6d02ec529d"
EXPECTED_IMAGE_SIZE = (4000, 2248)  # (ancho, alto)

__all__ = ["EXPECTED_IMAGE_SHA256", "EXPECTED_IMAGE_SIZE"]
