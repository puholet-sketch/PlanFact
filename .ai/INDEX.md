# PlanFact — карта артефактов

## Публичный сайт
- `index.html`, `docs/index.html` — единый deck по командам (стиль Jira)
- `site_data.json` — KPI-сводка
- `.nojekyll` — GitHub Pages
- Live: https://puholet-sketch.github.io/PlanFact/

## Скрипты
- `build_all_teams.py` — все команды + unified HTML
- `build_exceed_report.py` — аналитика / payload / per-team HTML+XLSX
- `report_theme.py` — Jira-like light theme (Virtu portal)
- `team_mapping.py`, `jira_audit_rules.py`, `apply_jira_audit.py`

## Источники (локально, не в git)
- `Модель План-Факт *.xlsx` (18 срезов, последний 2026.08.17)
- `Распределение по командам.xlsx`
