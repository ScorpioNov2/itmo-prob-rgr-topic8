"""Точка интеграции РГР.

Файл принадлежит лидеру команды. После появления generator.py, analyzer.py и
visualizer.py запуск `python main.py` должен полностью собрать результаты проекта.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from config import (
    ACCEL_PARAMS,
    BASE_PARAMS,
    MAX_BUDGET,
    MAX_DAYS,
    N_SIM,
    PLOT_FILENAMES,
    SEED,
)
from generator import run_monte_carlo, run_scalar_demo
from analyzer import analyze_simulation, get_theoretical_stats
from visualizer import build_all_plots

ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results"
PLOTS_DIR = ROOT / "plots"


def _save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _save_theory(path: Path, theory: pd.DataFrame) -> None:
    out = theory.copy()
    out.index.name = "variable"
    out.to_csv(path, encoding="utf-8", float_format="%.10f")


def _build_comparison(base_metrics: dict, accel_metrics: dict) -> pd.DataFrame:
    ordered = (
        "mean_T", "std_T", "median_T", "p95_T", "P_over_days",
        "mean_C", "std_C", "median_C", "p95_C", "P_over_budget",
        "P_success",
    )
    rows = []
    for metric in ordered:
        base = float(base_metrics[metric])
        accel = float(accel_metrics[metric])
        absolute_change = accel - base
        relative_change_pct = (absolute_change / base * 100.0) if base != 0.0 else float("nan")
        rows.append({
            "metric": metric,
            "BASE": base,
            "ACCEL": accel,
            "absolute_change": absolute_change,
            "relative_change_pct": relative_change_pct,
        })
    return pd.DataFrame(rows)


def run_project() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Демонстрация встроенного модуля random.
    scalar_demo = {
        "BASE": run_scalar_demo(BASE_PARAMS, seed=SEED),
        "ACCEL": run_scalar_demo(ACCEL_PARAMS, seed=SEED),
    }
    _save_json(RESULTS_DIR / "scalar_demo.json", scalar_demo)

    # 2. Основное моделирование. Каждый сценарий получает новый RNG с тем же seed.
    base_data = run_monte_carlo(BASE_PARAMS, n_sim=N_SIM, seed=SEED)
    accel_data = run_monte_carlo(ACCEL_PARAMS, n_sim=N_SIM, seed=SEED)

    # 3. Теоретические характеристики.
    theory_base = get_theoretical_stats(BASE_PARAMS)
    theory_accel = get_theoretical_stats(ACCEL_PARAMS)
    _save_theory(RESULTS_DIR / "theory_BASE.csv", theory_base)
    _save_theory(RESULTS_DIR / "theory_ACCEL.csv", theory_accel)

    # 4. Характеристики результатов моделирования и риски.
    metrics_base = analyze_simulation(base_data, MAX_DAYS, MAX_BUDGET)
    metrics_accel = analyze_simulation(accel_data, MAX_DAYS, MAX_BUDGET)
    _save_json(RESULTS_DIR / "metrics_BASE.json", metrics_base)
    _save_json(RESULTS_DIR / "metrics_ACCEL.json", metrics_accel)

    comparison = _build_comparison(metrics_base, metrics_accel)
    comparison.to_csv(RESULTS_DIR / "comparison.csv", index=False, encoding="utf-8", float_format="%.10f")

    # 5. Визуализация.
    plot_paths = build_all_plots(
        base_data,
        accel_data,
        theory_base,
        MAX_DAYS,
        MAX_BUDGET,
        output_dir=str(PLOTS_DIR),
    )
    returned_names = tuple(Path(p).name for p in plot_paths)
    if returned_names != PLOT_FILENAMES:
        raise RuntimeError(
            f"visualizer.py вернул неверный набор файлов: {returned_names}; "
            f"ожидалось {PLOT_FILENAMES}"
        )

    # 6. Краткий итог в консоли.
    print("\n=== BASE: теоретические характеристики ===")
    print(theory_base.round(4).to_string())
    print("\n=== ACCEL: теоретические характеристики ===")
    print(theory_accel.round(4).to_string())
    print("\n=== Сравнение результатов моделирования ===")
    print(comparison.round(4).to_string(index=False))
    print(f"\nРезультаты сохранены в: {RESULTS_DIR}")
    print(f"Графики сохранены в:   {PLOTS_DIR}")


if __name__ == "__main__":
    run_project()
