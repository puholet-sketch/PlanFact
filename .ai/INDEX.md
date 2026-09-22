# PlanFact — карта артефактов

## Публичный сайт
- `index.html`, `docs/index.html` — единый deck по командам
- `assets/chart.umd.min.js` — локальный Chart.js (без CDN)
- `site_data.json` — KPI-сводка
- `.nojekyll` — GitHub Pages

## Скрипты
- `build_all_teams.py` — все команды + unified HTML
- `build_exceed_report.py` — аналитика / payload / per-team
- `report_theme.py` — Jira-light UI + фильтр/Δ/movers
- `team_mapping.py`, `jira_audit_rules.py`, `apply_jira_audit.py`, `fetch_jira_audit_cache.py`

## Источники (локально, не в git)
- `Модель План-Факт *.xlsx` (20 шт., последний 2026.09.14)
- `Распределение по командам.xlsx`

## Контекст
- `.ai/CONTEXT.md`, `.ai/INDEX.md`, `.ai/state.json`
