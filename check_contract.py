"""Автоматическая проверка контрактов проекта РГР.

Использование:
    python check_contract.py
        Проверяет config + stub и все командные модули, которые уже существуют.
        Отсутствующие generator/analyzer/visualizer считаются SKIP.

    python check_contract.py --strict
        Финальный режим: generator.py, analyzer.py и visualizer.py обязательны.

Скрипт не исправляет код автоматически. Он только сообщает, какой контракт нарушен.
"""

from __future__ import annotations

import argparse
import importlib
import json
import math
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

import config
from generator_stub import make_stub_data

ROOT = Path(__file__).resolve().parent


class ContractError(AssertionError):
    pass


def _ok(message: str) -> None:
    print(f"[OK]   {message}")


def _skip(message: str) -> None:
    print(f"[SKIP] {message}")


def _fail(message: str) -> None:
    raise ContractError(message)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        _fail(message)


def _assert_sim_data(data: dict, n_sim: int) -> None:
    _assert(tuple(data.keys()) == config.SIM_KEYS,
            f"Ключи sim_data должны быть строго {config.SIM_KEYS}, получено {tuple(data.keys())}")
    for key in config.SIM_KEYS:
        arr = data[key]
        _assert(isinstance(arr, np.ndarray), f"{key}: ожидается np.ndarray")
        _assert(arr.dtype == np.float64, f"{key}: dtype должен быть np.float64, получено {arr.dtype}")
        _assert(arr.shape == (n_sim,), f"{key}: shape должен быть {(n_sim,)}, получено {arr.shape}")

    expected_t = np.add.reduce([data[f"T_{stage}"] for stage in config.STAGES])
    expected_c = np.add.reduce([data[f"C_{stage}"] for stage in config.STAGES])
    _assert(np.array_equal(data["T_total"], expected_t), "T_total не равен поэлементной сумме этапов")
    _assert(np.array_equal(data["C_total"], expected_c), "C_total не равен поэлементной сумме этапов")


def check_config() -> None:
    _assert(config.STAGES == ("design", "dev", "qa", "mkt"), "Неверный порядок STAGES")
    _assert(config.METRICS == ("T", "C"), "Неверный порядок METRICS")
    _assert(config.RNG_ORDER == (
        "T_design", "C_design", "T_dev", "C_dev",
        "T_qa", "C_qa", "T_mkt", "C_mkt",
    ), "Неверный RNG_ORDER")
    _assert(config.SCENARIO_ORDER == ("BASE", "ACCEL"), "Должны быть сценарии BASE и ACCEL")

    for scenario in config.SCENARIO_ORDER:
        params = config.SCENARIOS[scenario]["params"]
        _assert(tuple(params.keys()) == config.STAGES, f"{scenario}: неверный порядок этапов")
        for stage in config.STAGES:
            _assert(tuple(params[stage].keys()) == config.METRICS,
                    f"{scenario}/{stage}: должны быть только T и C в этом порядке")
            for metric in config.METRICS:
                p = params[stage][metric]
                _assert(p["dist"] in {"uniform", "triang"}, f"{scenario}/{stage}/{metric}: неизвестный dist")
                _assert(float(p["a"]) < float(p["b"]), f"{scenario}/{stage}/{metric}: требуется a < b")
                if p["dist"] == "triang":
                    _assert(float(p["a"]) <= float(p["c"]) <= float(p["b"]),
                            f"{scenario}/{stage}/{metric}: требуется a <= c <= b")
    _ok("config.py: структура, сценарии и параметры")


def check_stub() -> None:
    data = make_stub_data(config.BASE_PARAMS, n_sim=257)
    _assert_sim_data(data, 257)
    _ok("generator_stub.py: ключи, dtype, shape и суммы")


def _import_optional(module_name: str, strict: bool):
    path = ROOT / f"{module_name}.py"
    if not path.exists():
        if strict:
            _fail(f"В strict-режиме отсутствует обязательный файл {path.name}")
        _skip(f"{path.name} пока отсутствует")
        return None
    importlib.invalidate_caches()
    return importlib.import_module(module_name)


def check_generator(strict: bool) -> None:
    module = _import_optional("generator", strict)
    if module is None:
        return

    _assert(hasattr(module, "run_scalar_demo"), "generator.py: нет run_scalar_demo")
    _assert(hasattr(module, "run_monte_carlo"), "generator.py: нет run_monte_carlo")

    scalar = module.run_scalar_demo(config.BASE_PARAMS, seed=config.SEED)
    _assert(tuple(scalar.keys()) == config.SIM_KEYS, "run_scalar_demo: неверные ключи")
    _assert(all(type(scalar[key]) is float for key in config.SIM_KEYS),
            "run_scalar_demo: все значения должны быть Python float")
    _assert(math.isclose(scalar["T_total"], sum(scalar[f"T_{s}"] for s in config.STAGES), rel_tol=0, abs_tol=1e-12),
            "run_scalar_demo: неверный T_total")
    _assert(math.isclose(scalar["C_total"], sum(scalar[f"C_{s}"] for s in config.STAGES), rel_tol=0, abs_tol=1e-12),
            "run_scalar_demo: неверный C_total")

    n = 257
    first = module.run_monte_carlo(config.BASE_PARAMS, n_sim=n, seed=config.SEED)
    second = module.run_monte_carlo(config.BASE_PARAMS, n_sim=n, seed=config.SEED)
    _assert_sim_data(first, n)
    _assert_sim_data(second, n)
    for key in config.SIM_KEYS:
        _assert(np.array_equal(first[key], second[key]), f"run_monte_carlo: {key} не воспроизводится бит-в-бит")

    # Regression check фиксирует не только seed, но и порядок вызовов RNG.
    reference_path = ROOT / "metrics_reference.json"
    if reference_path.exists():
        with reference_path.open("r", encoding="utf-8") as f:
            reference = json.load(f)
        default_data = module.run_monte_carlo(config.BASE_PARAMS, n_sim=config.N_SIM, seed=config.SEED)
        T = default_data["T_total"]
        C = default_data["C_total"]
        got = {
            "mean_T": float(np.mean(T)),
            "std_T": float(np.std(T)),
            "median_T": float(np.median(T)),
            "p95_T": float(np.percentile(T, 95)),
            "P_over_days": float(np.mean(T > config.MAX_DAYS)),
            "mean_C": float(np.mean(C)),
            "std_C": float(np.std(C)),
            "median_C": float(np.median(C)),
            "p95_C": float(np.percentile(C, 95)),
            "P_over_budget": float(np.mean(C > config.MAX_BUDGET)),
            "P_success": float(np.mean((T <= config.MAX_DAYS) & (C <= config.MAX_BUDGET))),
        }
        expected = reference["scenarios"]["BASE"]
        for key, value in got.items():
            _assert(math.isclose(value, float(expected[key]), rel_tol=0.0, abs_tol=1e-12),
                    f"generator regression: {key}={value}, ожидалось {expected[key]}. Проверьте RNG_ORDER.")

    _ok("generator.py: scalar demo, Monte Carlo, воспроизводимость и RNG regression")


def _load_reference_scenario(scenario: str) -> pd.DataFrame:
    ref = pd.read_csv(ROOT / "theory_reference.csv")
    part = ref[ref["scenario"] == scenario].copy()
    part = part.set_index("variable").loc[list(config.SIM_KEYS)]
    return part


def check_analyzer(strict: bool) -> None:
    module = _import_optional("analyzer", strict)
    if module is None:
        return

    _assert(hasattr(module, "get_theoretical_stats"), "analyzer.py: нет get_theoretical_stats")
    _assert(hasattr(module, "analyze_simulation"), "analyzer.py: нет analyze_simulation")

    theory = module.get_theoretical_stats(config.BASE_PARAMS)
    _assert(isinstance(theory, pd.DataFrame), "get_theoretical_stats должен вернуть pd.DataFrame")
    _assert(tuple(theory.index) == config.SIM_KEYS,
            f"theory index должен быть {config.SIM_KEYS}, получено {tuple(theory.index)}")
    _assert(tuple(theory.columns) == config.THEORY_COLUMNS,
            f"theory columns должны быть {config.THEORY_COLUMNS}, получено {tuple(theory.columns)}")

    reference = _load_reference_scenario("BASE")
    for key in config.SIM_KEYS:
        for col in ("mean", "var", "std", "p95"):
            got = float(theory.loc[key, col])
            exp = float(reference.loc[key, col])
            _assert(math.isclose(got, exp, rel_tol=0.0, abs_tol=1e-9),
                    f"theory {key}/{col}: {got} != reference {exp}")
        _assert(str(theory.loc[key, "p95_kind"]) == str(reference.loc[key, "p95_kind"]),
                f"theory {key}/p95_kind не совпадает")

    stub = make_stub_data(config.BASE_PARAMS, n_sim=1000)
    metrics = module.analyze_simulation(stub, config.MAX_DAYS, config.MAX_BUDGET)
    _assert(tuple(metrics.keys()) == config.ANALYSIS_KEYS,
            f"analyze_simulation: ключи должны быть {config.ANALYSIS_KEYS}")
    for prob_key in ("P_over_days", "P_over_budget", "P_success"):
        _assert(0.0 <= float(metrics[prob_key]) <= 1.0, f"{prob_key} должен лежать в [0,1]")

    _ok("analyzer.py: DataFrame theory и контракт метрик риска")


def check_visualizer(strict: bool) -> None:
    module = _import_optional("visualizer", strict)
    if module is None:
        return

    _assert(hasattr(module, "build_all_plots"), "visualizer.py: нет build_all_plots")
    base = make_stub_data(config.BASE_PARAMS, n_sim=1000)
    accel = make_stub_data(config.ACCEL_PARAMS, n_sim=1000)

    # Для stub визуализатору достаточно канонической таблицы BASE.
    theory_ref = _load_reference_scenario("BASE")[list(config.THEORY_COLUMNS)]

    with tempfile.TemporaryDirectory() as tmp:
        returned = module.build_all_plots(
            base,
            accel,
            theory_ref,
            config.MAX_DAYS,
            config.MAX_BUDGET,
            output_dir=tmp,
        )
        _assert(isinstance(returned, list), "build_all_plots должен вернуть list[str]")
        _assert(len(returned) == 4, "build_all_plots должен вернуть ровно 4 пути")
        actual_names = tuple(Path(p).name for p in returned)
        _assert(actual_names == config.PLOT_FILENAMES,
                f"Имена графиков должны быть {config.PLOT_FILENAMES}, получено {actual_names}")
        for p in returned:
            path = Path(p)
            _assert(path.exists() and path.stat().st_size > 0, f"График не создан или пуст: {path}")

    _ok("visualizer.py: создано ровно 4 графика по контракту")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true", help="требовать все командные модули")
    args = parser.parse_args()

    try:
        check_config()
        check_stub()
        check_generator(args.strict)
        check_analyzer(args.strict)
        check_visualizer(args.strict)
    except (ContractError, Exception) as exc:
        print(f"[FAIL] {exc}")
        return 1

    print("\nCONTRACT CHECK PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
