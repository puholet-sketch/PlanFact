# PlanFact — превышения План/Факт

Единый HTML-дайджест превышений по категории **Производство** в разбивке по командам.

**Live:** https://puholet-sketch.github.io/PlanFact/

## Что внутри

- `index.html` — единая страница (стиль ежемесячного статус-дайджеста)
- `build_all_teams.py` — пересборка всех команд + сайта
- `build_exceed_report.py` — аналитика Plan-Fact / XLSX / payload
- `report_theme.py` — тёмный deck UI
- `team_mapping.py` — ФИО ↔ команда

## Локальная пересборка

Положите срезы `Модель План-Факт YYYY.MM.DD (все категории).xlsx` и файл распределения в корень, затем:

```bash
python build_all_teams.py
```

## GitHub Pages

Источник: ветка `main`, корень репозитория (`index.html` + `.nojekyll`).
