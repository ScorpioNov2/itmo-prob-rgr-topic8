"""Контрактный stub для параллельной разработки analyzer.py и visualizer.py.

Это НЕ генератор для финальных результатов РГР.
Stub гарантирует только структуру данных: ключи, dtype, shape и корректные суммы.
"""

from __future__ import annotations

import numpy as np

from config import SIM_KEYS, STAGES


def _bounded_line(a: float, b: float, n_sim: int, phase: float = 0.0) -> np.ndarray:
    """Детерминированный массив внутри [a, b] для тестирования интерфейса."""
    x = np.linspace(0.0, 1.0, n_sim, dtype=np.float64)
    if phase:
        x = np.mod(x + phase, 1.0)
    return (a + (b - a) * x).astype(np.float64, copy=False)


def make_stub_data(params: dict, n_sim: int = 1000) -> dict[str, np.ndarray]:
    """Вернуть данные, совместимые с Output Contract generator.py."""
    if n_sim <= 0:
        raise ValueError("n_sim должен быть положительным")

    out: dict[str, np.ndarray] = {}
    phase = 0.0

    for stage in STAGES:
        for metric in ("T", "C"):
            p = params[stage][metric]
            key = f"{metric}_{stage}"
            out[key] = _bounded_line(float(p["a"]), float(p["b"]), n_sim, phase)
            phase += 0.071

    out["T_total"] = np.add.reduce([out[f"T_{stage}"] for stage in STAGES]).astype(np.float64)
    out["C_total"] = np.add.reduce([out[f"C_{stage}"] for stage in STAGES]).astype(np.float64)

    # Возвращаем словарь в каноническом порядке SIM_KEYS.
    return {key: out[key] for key in SIM_KEYS}
