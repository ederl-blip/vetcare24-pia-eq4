"""Genera docs/evidencia/*.csv con el resultado de los 120 casos y 20 transiciones."""

import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src.application.evaluacion import evaluar_casos, evaluar_transiciones, guardar  # noqa: E402

casos, trans = evaluar_casos(), evaluar_transiciones()
guardar(casos, RAIZ / "docs/evidencia/resultados_casos.csv")
guardar(trans, RAIZ / "docs/evidencia/resultados_transiciones.csv")
print("Casos:", len(casos), dict(Counter(c["resultado"] for c in casos)))
print("Transiciones:", len(trans), dict(Counter(t["resultado"] for t in trans)))
