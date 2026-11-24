"""Модуль генерации случайных величин для РГР (Тема № 8, Contract v2.1).

Реализует скалярную демонстрацию на базе встроенного модуля ``random``
и векторное имитационное моделирование методом Монте-Карло с использованием
генератора ``numpy.random.default_rng`` (алгоритм PCG64).
"""

import random

import numpy as np

from config import N_SIM, RNG_ORDER, SEED, SIM_KEYS, STAGES


def _extract_dist_params(key: str, spec: dict) -> tuple[str, float, float, float | None]:
    """Извлечь и проверить параметры закона распределения из config."""
    dist = spec["dist"]
    if dist not in {"uniform", "triang"}:
        raise ValueError(f"{key}: неподдерживаемый закон распределения '{dist}'")

    a = float(spec["a"])
    b = float(spec["b"])
    if not a < b:
        raise ValueError(f"{key}: требуется условие a < b, получено a={a}, b={b}")

    if dist == "uniform":
        return dist, a, b, None

    c = float(spec["c"])
    if not a <= c <= b:
        raise ValueError(f"{key}: требуется условие a <= c <= b, получено a={a}, c={c}, b={b}")
    return dist, a, b, c


def run_scalar_demo(params: dict, seed: int = SEED) -> dict:
    """Сгенерировать единичную реализацию проекта встроенным модулем random."""
    random.seed(seed)
    out: dict[str, float] = {}

    for key in RNG_ORDER:
        metric, stage = key.split("_", 1)
        dist, a, b, c = _extract_dist_params(key, params[stage][metric])
        if dist == "uniform":
            out[key] = float(random.uniform(a, b))
        else:
            # В random.triangular аргументы передаются в порядке (low, high, mode).
            out[key] = float(random.triangular(a, b, c))

    out["T_total"] = float(sum(out[f"T_{stage}"] for stage in STAGES))
    out["C_total"] = float(sum(out[f"C_{stage}"] for stage in STAGES))
    return {key: out[key] for key in SIM_KEYS}


def run_monte_carlo(
    params: dict,
    n_sim: int = N_SIM,
    seed: int = SEED,
) -> dict:
    """Провести векторную симуляцию Монте-Карло на базе np.random.default_rng."""
    if isinstance(n_sim, bool) or not isinstance(n_sim, (int, np.integer)) or n_sim <= 0:
        raise ValueError("n_sim должен быть положительным целым числом")

    n_runs = int(n_sim)
    rng = np.random.default_rng(seed)
    out: dict[str, np.ndarray] = {}

    # Порядок вызовов RNG строго фиксирован (RNG_ORDER) для полной воспроизводимости.
    for key in RNG_ORDER:
        metric, stage = key.split("_", 1)
        dist, a, b, c = _extract_dist_params(key, params[stage][metric])
        if dist == "uniform":
            arr = rng.uniform(a, b, size=n_runs)
        else:
            # В rng.triangular аргументы передаются в порядке (left, mode, right).
            arr = rng.triangular(a, c, b, size=n_runs)
        out[key] = np.asarray(arr, dtype=np.float64)

    out["T_total"] = np.add.reduce([out[f"T_{stage}"] for stage in STAGES]).astype(np.float64)
    out["C_total"] = np.add.reduce([out[f"C_{stage}"] for stage in STAGES]).astype(np.float64)
    return {key: out[key] for key in SIM_KEYS}
