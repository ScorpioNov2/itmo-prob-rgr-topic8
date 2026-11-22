"""Модуль для построения графиков по результатам симуляции (Тема 8).

Используем объектный подход Matplotlib (Figure -> Axes -> Artist).
Функции вроде plt.plot() или plt.title() не применяем.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Режим сохранения в файл без открытия окна

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import config
from generator_stub import make_stub_data


def _normal_pdf(x: np.ndarray, mean: float, std: float) -> np.ndarray:
    """Считаем плотность нормального распределения для кривой на графике."""
    coeff = 1.0 / (std * np.sqrt(2.0 * np.pi))
    exponent = -0.5 * ((x - mean) / std) ** 2
    return coeff * np.exp(exponent)


def _plot_base_hist(
    base_data: dict,
    base_theory: pd.DataFrame,
    max_days: float,
    max_budget: float,
    out_path: Path,
) -> None:
    """График 1: Гистограммы сроков и бюджета для базового плана (BASE)."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5), dpi=300)

    specs = [
        (
            axes[0],
            base_data["T_total"],
            float(base_theory.loc["T_total", "mean"]),
            float(base_theory.loc["T_total", "std"]),
            max_days,
            f"Лимит: {max_days:.0f} дн.",
            "Общий срок T_total, дни",
            "Срок проекта (BASE)",
            "#2b6cb0",
        ),
        (
            axes[1],
            base_data["C_total"],
            float(base_theory.loc["C_total", "mean"]),
            float(base_theory.loc["C_total", "std"]),
            max_budget,
            f"Лимит: {max_budget:.0f} тыс. руб.",
            "Общая стоимость C_total, тыс. руб.",
            "Стоимость проекта (BASE)",
            "#2f855a",
        ),
    ]

    for ax, sample, mu, sigma, limit, limit_label, xlabel, title, color in specs:
        ax.hist(
            sample,
            bins=40,
            density=True,
            color=color,
            alpha=0.55,
            edgecolor="white",
            linewidth=0.6,
            label="Симуляция (Монте-Карло)",
        )

        x_min = min(float(np.min(sample)), mu - 3.5 * sigma)
        x_max = max(float(np.max(sample)), mu + 3.5 * sigma, limit * 1.03)
        x_grid = np.linspace(x_min, x_max, 300)
        y_norm = _normal_pdf(x_grid, mu, sigma)

        ax.plot(
            x_grid,
            y_norm,
            color="#1a202c",
            linewidth=2.0,
            label=f"Норм. кривая (μ={mu:.1f}, σ={sigma:.1f})",
        )
        ax.axvline(
            limit,
            color="#c53030",
            linestyle="--",
            linewidth=2.0,
            label=limit_label,
        )

        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.set_xlabel(xlabel, fontsize=10)
        ax.set_ylabel("Плотность вероятности", fontsize=10)
        ax.grid(True, linestyle=":", alpha=0.5)
        ax.legend(loc="upper right", fontsize=8.5)

    fig.suptitle(
        "Базовый сценарий (BASE): итоги симуляции и лимиты",
        fontsize=13,
        fontweight="bold",
    )
    fig.tight_layout()
    fig.savefig(out_path, dpi=300)
    plt.close(fig)


def _plot_comparison(
    base_data: dict,
    accel_data: dict,
    max_days: float,
    max_budget: float,
    out_path: Path,
) -> None:
    """График 2: Сравнение планов BASE и ACCEL на одном графике."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5), dpi=300)

    specs = [
        (
            axes[0],
            base_data["T_total"],
            accel_data["T_total"],
            max_days,
            f"Лимит: {max_days:.0f} дн.",
            "Общий срок T_total, дни",
            "Сроки: BASE и ACCEL",
        ),
        (
            axes[1],
            base_data["C_total"],
            accel_data["C_total"],
            max_budget,
            f"Лимит: {max_budget:.0f} тыс. руб.",
            "Общая стоимость C_total, тыс. руб.",
            "Затраты: BASE и ACCEL",
        ),
    ]

    for ax, base_arr, accel_arr, limit, limit_label, xlabel, title in specs:
        low = min(float(np.min(base_arr)), float(np.min(accel_arr)))
        high = max(float(np.max(base_arr)), float(np.max(accel_arr)))
        bins = np.linspace(low, high, 42)

        ax.hist(
            base_arr,
            bins=bins,
            density=True,
            alpha=0.5,
            color="#3182ce",
            edgecolor="white",
            linewidth=0.5,
            label="BASE (обычный план)",
        )
        ax.hist(
            accel_arr,
            bins=bins,
            density=True,
            alpha=0.5,
            color="#dd6b20",
            edgecolor="white",
            linewidth=0.5,
            label="ACCEL (ускорение dev)",
        )
        ax.axvline(
            limit,
            color="#c53030",
            linestyle="--",
            linewidth=2.0,
            label=limit_label,
        )

        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.set_xlabel(xlabel, fontsize=10)
        ax.set_ylabel("Плотность вероятности", fontsize=10)
        ax.grid(True, linestyle=":", alpha=0.5)
        ax.legend(loc="upper right", fontsize=8.5)

    fig.suptitle(
        "Сравнение BASE и ACCEL: выигрыш по времени против роста затрат",
        fontsize=13,
        fontweight="bold",
    )
    fig.tight_layout()
    fig.savefig(out_path, dpi=300)
    plt.close(fig)


def _plot_stages_boxplot(base_data: dict, out_path: Path) -> None:
    """График 3: Разброс сроков и затрат по каждому из 4 этапов."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5), dpi=300)

    stage_labels = [
        "design\n(Дизайн)",
        "dev\n(Разработка)",
        "qa\n(Тесты)",
        "mkt\n(Маркетинг)",
    ]

    t_series = [base_data[f"T_{stage}"] for stage in config.STAGES]
    c_series = [base_data[f"C_{stage}"] for stage in config.STAGES]

    configs = [
        (
            axes[0],
            t_series,
            "Срок этапа, дни",
            "Разброс сроков по этапам (BASE)",
            "#63b3ed",
        ),
        (
            axes[1],
            c_series,
            "Стоимость этапа, тыс. руб.",
            "Разброс затрат по этапам (BASE)",
            "#68d391",
        ),
    ]

    for ax, series, ylabel, title, box_color in configs:
        bp = ax.boxplot(
            series,
            tick_labels=stage_labels,
            patch_artist=True,
            showmeans=True,
            meanprops={
                "marker": "D",
                "markerfacecolor": "#c53030",
                "markeredgecolor": "#c53030",
                "markersize": 5,
            },
            medianprops={"color": "#1a202c", "linewidth": 1.8},
        )
        for patch in bp["boxes"]:
            patch.set_facecolor(box_color)
            patch.set_alpha(0.65)

        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.set_ylabel(ylabel, fontsize=10)
        ax.grid(True, axis="y", linestyle=":", alpha=0.5)

    fig.suptitle(
        "Сколько времени и денег занимает каждый этап (BASE)",
        fontsize=13,
        fontweight="bold",
    )
    fig.tight_layout()
    fig.savefig(out_path, dpi=300)
    plt.close(fig)


def _plot_convergence(
    base_data: dict,
    base_theory: pd.DataFrame,
    out_path: Path,
) -> None:
    """График 4: Как среднее время сходится к теоретическому с ростом числа опытов."""
    t_total = base_data["T_total"]
    n_total = len(t_total)
    start_n = min(100, n_total)

    n_values = np.arange(start_n, n_total + 1)
    cumulative_sum = np.cumsum(t_total)
    running_mean = cumulative_sum[start_n - 1 :] / n_values

    theoretical_mean = float(base_theory.loc["T_total", "mean"])

    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=300)

    ax.plot(
        n_values,
        running_mean,
        color="#2b6cb0",
        linewidth=1.6,
        label="Среднее по симуляции",
    )
    ax.axhline(
        theoretical_mean,
        color="#c53030",
        linestyle="--",
        linewidth=2.0,
        label=f"Теория E[T_total] = {theoretical_mean:.2f} дн.",
    )

    ax.set_title(
        "Сходимость среднего срока T_total (BASE) при увеличении числа прогонов N",
        fontsize=11.5,
        fontweight="bold",
    )
    ax.set_xlabel("Количество прогонов N", fontsize=10)
    ax.set_ylabel("Средний срок, дни", fontsize=10)
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.legend(loc="best", fontsize=9.5)

    fig.tight_layout()
    fig.savefig(out_path, dpi=300)
    plt.close(fig)


def build_all_plots(
    base_data: dict,
    accel_data: dict,
    base_theory: pd.DataFrame,
    max_days: float,
    max_budget: float,
    output_dir: str = "plots",
) -> list[str]:
    """Строит 4 графика и возвращает список путей к файлам."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    paths = [out_dir / fname for fname in config.PLOT_FILENAMES]

    _plot_base_hist(base_data, base_theory, max_days, max_budget, paths[0])
    _plot_comparison(base_data, accel_data, max_days, max_budget, paths[1])
    _plot_stages_boxplot(base_data, paths[2])
    _plot_convergence(base_data, base_theory, paths[3])

    return [str(p) for p in paths]


if __name__ == "__main__":
    stub_base = make_stub_data(config.BASE_PARAMS, n_sim=config.N_SIM)
    stub_accel = make_stub_data(config.ACCEL_PARAMS, n_sim=config.N_SIM)
    ref_df = pd.read_csv("theory_reference.csv")
    base_ref = (
        ref_df[ref_df["scenario"] == "BASE"]
        .set_index("variable")
        .loc[list(config.SIM_KEYS), list(config.THEORY_COLUMNS)]
    )
    created = build_all_plots(
        stub_base,
        stub_accel,
        base_ref,
        config.MAX_DAYS,
        config.MAX_BUDGET,
        output_dir="plots",
    )
    print("Готово, созданы файлы:", created)
