"""Единый конфиг РГР. Версия контракта 2.1.

ВАЖНО: этот файл редактирует только лидер команды.
Все участники импортируют данные отсюда и не дублируют параметры вручную.
"""

from copy import deepcopy

CONTRACT_VERSION: str = "2.1"
SEED: int = 42
N_SIM: int = 10_000

# Целевые ограничения проекта.
MAX_DAYS: float = 60.0        # дни
MAX_BUDGET: float = 1200.0    # тыс. руб.

# Единый порядок сущностей проекта.
STAGES: tuple[str, ...] = ("design", "dev", "qa", "mkt")
METRICS: tuple[str, ...] = ("T", "C")

# Порядок вызовов RNG зафиксирован для воспроизводимости между машинами.
# Каждый сценарий запускается с НОВЫМ np.random.default_rng(SEED).
RNG_ORDER: tuple[str, ...] = (
    "T_design", "C_design",
    "T_dev", "C_dev",
    "T_qa", "C_qa",
    "T_mkt", "C_mkt",
)

# Канонический порядок выходных массивов.
SIM_KEYS: tuple[str, ...] = (
    "T_design", "T_dev", "T_qa", "T_mkt", "T_total",
    "C_design", "C_dev", "C_qa", "C_mkt", "C_total",
)

ANALYSIS_KEYS: tuple[str, ...] = (
    "mean_T", "std_T", "median_T", "p95_T", "P_over_days",
    "mean_C", "std_C", "median_C", "p95_C", "P_over_budget",
    "P_success",
)

THEORY_COLUMNS: tuple[str, ...] = ("mean", "var", "std", "p95", "p95_kind")

PLOT_FILENAMES: tuple[str, ...] = (
    "plot_1_base_hist.png",
    "plot_2_comparison.png",
    "plot_3_stages_boxplot.png",
    "plot_4_convergence.png",
)

# Базовый сценарий: 4 последовательных этапа разработки MVP.
# Для uniform: {'dist': 'uniform', 'a': min, 'b': max}
# Для triang:  {'dist': 'triang',  'a': min, 'c': mode, 'b': max}
BASE_PARAMS: dict = {
    "design": {
        "T": {"dist": "uniform", "a": 5.0, "b": 12.0},
        "C": {"dist": "triang", "a": 80.0, "c": 110.0, "b": 160.0},
    },
    "dev": {
        "T": {"dist": "triang", "a": 18.0, "c": 25.0, "b": 40.0},
        "C": {"dist": "triang", "a": 400.0, "c": 550.0, "b": 850.0},
    },
    "qa": {
        "T": {"dist": "uniform", "a": 6.0, "b": 14.0},
        "C": {"dist": "uniform", "a": 100.0, "b": 180.0},
    },
    "mkt": {
        "T": {"dist": "triang", "a": 7.0, "c": 10.0, "b": 18.0},
        "C": {"dist": "triang", "a": 150.0, "c": 200.0, "b": 320.0},
    },
}

# What-if сценарий: ускорение этапа разработки за счёт дополнительного ресурса.
# Слово OPT/optimal намеренно не используется: оптимальность заранее не доказана.
ACCEL_PARAMS: dict = deepcopy(BASE_PARAMS)
ACCEL_PARAMS["dev"] = {
    "T": {"dist": "triang", "a": 14.0, "c": 18.0, "b": 26.0},
    "C": {"dist": "triang", "a": 500.0, "c": 680.0, "b": 950.0},
}

SCENARIO_ORDER: tuple[str, ...] = ("BASE", "ACCEL")
SCENARIOS: dict = {
    "BASE": {
        "params": BASE_PARAMS,
        "max_days": MAX_DAYS,
        "max_budget": MAX_BUDGET,
        "label_ru": "Базовый сценарий",
    },
    "ACCEL": {
        "params": ACCEL_PARAMS,
        "max_days": MAX_DAYS,
        "max_budget": MAX_BUDGET,
        "label_ru": "Ускорение разработки (what-if)",
    },
}

# Модельные допущения, которые должны совпадать в отчёте и коде.
MODEL_ASSUMPTIONS_RU: tuple[str, ...] = (
    "Четыре этапа проекта выполняются последовательно.",
    "Восемь исходных случайных величин считаются независимыми.",
    "Продолжительность проекта равна сумме длительностей четырёх этапов.",
    "Стоимость проекта равна сумме затрат четырёх этапов.",
    "T измеряется в днях, C — в тыс. руб.",
)
