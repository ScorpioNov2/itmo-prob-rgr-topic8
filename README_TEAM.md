# RGR Probability — Team Starter Pack v2.1

Этот архив — **единый источник контрактов проекта**. Перед началом работы каждый участник должен получить одну и ту же копию папки.

## Что нельзя менять без лидера

- `config.py`
- `generator_stub.py`
- `check_contract.py`
- `requirements.txt`
- `theory_reference.csv`
- `metrics_reference.json`
- сигнатуры функций из `TEAM_TZ_RU.md`

`main.py` также принадлежит лидеру; участники не исправляют его под свой модуль — свой модуль нужно привести к контракту.

## Быстрый старт

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python check_contract.py
```

В начале проекта отсутствие `generator.py`, `analyzer.py`, `visualizer.py` будет показано как `SKIP` — это нормально.

После появления всех модулей финальная проверка:

```bash
python check_contract.py --strict
python main.py
```

## Главный принцип

**Никаких чисел вручную в итоговый Word.**

Финальные таблицы и выводы берутся только из файлов, созданных `main.py` в папке `results/`.

- `theory_reference.csv` — эталон для проверки теоретических расчётов и `analyzer.py`.
- `metrics_reference.json` — regression reference для проверки seed + порядка RNG.
- Эти два reference-файла не являются заменой финальному запуску `main.py`.

## Git

Один участник — одна ветка — один владелец файла.

Рекомендуемые ветки:

- `irina/system-analysis`
- `victoria/math-theory`
- `islam/generator`
- `sagor/analyzer`
- `rami/visualizer`
- `ali/report`
- `duong/integration`

Merge только через PR после выполнения Definition of Done.
