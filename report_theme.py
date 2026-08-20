# -*- coding: utf-8 -*-
"""Jira-like light theme for PlanFact unified site (Virtu portal look)."""

from __future__ import annotations

import json
from datetime import datetime
from html import escape as esc


def _num(value, digits: int = 1) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def _period_span(periods: list) -> str:
    if not periods:
        return "—"
    if len(periods) == 1:
        return str(periods[0])
    return f"{periods[0]} — {periods[-1]}"


def render_unified_site(meta: dict, teams: list[dict]) -> str:
    """Single-page deck: overview + one slide per team."""
    periods = meta.get("periods") or []
    generated = meta.get("generated") or datetime.now().strftime("%d.%m.%Y %H:%M")
    source_count = meta.get("source_count", len(periods))
    rules = meta.get("rules") or []
    reestimate_steps = meta.get("reestimate_steps") or []
    rules_title = meta.get("rules_title") or "Базовые правила"
    reestimate_title = meta.get("reestimate_title") or "Переоценка"
    reestimate_example = meta.get("reestimate_example") or ""

    total_hours = round(sum(t["kpi"]["hours"] for t in teams), 1)
    total_tasks = sum(t["kpi"]["tasks"] for t in teams)
    total_cases = sum(t["kpi"]["cases"] for t in teams)
    teams_with_excess = sum(1 for t in teams if t["kpi"]["hours"] > 0)

    overview_rows = []
    for i, team in enumerate(teams, start=1):
        kpi = team["kpi"]
        overview_rows.append(
            "<tr>"
            f"<td><a href='#team-{esc(team['slug'])}'>{esc(team['name'])}</a></td>"
            f"<td>{kpi['people']}</td>"
            f"<td>{kpi['cases']}</td>"
            f"<td>{kpi['tasks']}</td>"
            f"<td class='bad'>+{_num(kpi['hours'])}</td>"
            f"<td>{esc(kpi.get('top_fio') or '—')}</td>"
            "</tr>"
        )

    team_nav = "".join(
        f"<a class='nav-chip' href='#team-{esc(t['slug'])}'>{esc(t['name'])}</a>"
        for t in teams
    )

    rules_li = "".join(f"<li>{esc(x)}</li>" for x in rules)
    reest_li = "".join(f"<li>{esc(x)}</li>" for x in reestimate_steps)

    team_slides = "".join(_render_team_slide(i + 2, team) for i, team in enumerate(teams))

    chart_teams = [t["name"] for t in teams]
    chart_hours = [round(t["kpi"]["hours"], 1) for t in teams]
    chart_tasks = [t["kpi"]["tasks"] for t in teams]
    team_charts = {t["slug"]: t["chart"] for t in teams}

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>PlanFact — превышения по командам</title>
  <script src="assets/chart.umd.min.js"></script>
  <style>
    :root {{
      --jira-navy: #205081;
      --jira-blue: #0052cc;
      --jira-blue-soft: #deebff;
      --bg: #f4f5f7;
      --surface: #ffffff;
      --surface2: #fafbfc;
      --text: #172b4d;
      --muted: #6b778c;
      --border: #dfe1e6;
      --danger: #de350b;
      --ok: #00875a;
      --amber: #ff8b00;
      --active: #14892c;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      background: var(--bg); color: var(--text); line-height: 1.5;
    }}
    a {{ color: var(--jira-blue); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .topbar {{
      background: var(--jira-navy); color: #fff; padding: 0.7rem 1.25rem;
      display: flex; align-items: center; gap: 1rem; position: sticky; top: 0; z-index: 50;
    }}
    .topbar .brand {{ font-weight: 700; letter-spacing: 0.04em; color: #fff; text-decoration: none; }}
    .topbar .meta {{ color: rgba(255,255,255,0.78); font-size: 0.85rem; }}
    .deck {{ max-width: 1180px; margin: 0 auto; padding: 1.25rem 1.25rem 3rem; }}
    .slide {{
      background: var(--surface); border: 1px solid var(--border); border-radius: 3px;
      padding: 1.35rem 1.5rem 1.5rem; margin-bottom: 1rem;
      box-shadow: 0 1px 1px rgba(9, 30, 66, 0.08);
    }}
    .slide-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem; gap: 1rem; }}
    .slide-num {{ font-size: 0.72rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: var(--muted); }}
    h1, h2 {{ font-weight: 600; color: var(--text); }}
    h2 {{ font-size: 1.35rem; margin-bottom: 0.25rem; }}
    .subtitle {{ color: var(--muted); font-size: 0.92rem; }}
    .cover {{ padding: 1.75rem 1.5rem; }}
    .cover h1 {{ font-size: clamp(1.45rem, 3vw, 1.85rem); margin: 0.35rem 0 0.5rem; }}
    .lozenge {{
      display: inline-block; padding: 0.1rem 0.55rem; border-radius: 3px;
      font-size: 0.7rem; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase;
      background: #e3fcef; color: var(--active);
    }}
    .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 0.75rem; margin: 1rem 0; }}
    .kpi {{
      background: var(--surface2); border: 1px solid var(--border); border-radius: 3px;
      padding: 0.9rem 1rem; border-left: 4px solid var(--jira-blue);
    }}
    .kpi.green {{ border-left-color: var(--ok); }}
    .kpi.amber {{ border-left-color: var(--amber); }}
    .kpi.red {{ border-left-color: var(--danger); }}
    .kpi-value {{ font-size: 1.45rem; font-weight: 700; color: var(--text); }}
    .kpi-label {{ font-size: 0.78rem; color: var(--muted); margin-top: 0.2rem; }}
    .chart-box {{ background: var(--surface2); border: 1px solid var(--border); border-radius: 3px; padding: 1rem; margin-top: 0.85rem; }}
    .chart-title {{ font-size: 0.85rem; font-weight: 600; margin-bottom: 0.65rem; color: var(--text); }}
    .chart-wrap {{ position: relative; height: 280px; }}
    .chart-wrap.sm {{ height: 220px; }}
    .section-label {{
      font-size: 0.72rem; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;
      color: var(--muted); margin: 1.15rem 0 0.5rem;
    }}
    .section-label.blue {{ color: var(--jira-blue); }}
    .section-label.amber {{ color: var(--amber); }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.84rem; margin-top: 0.35rem; }}
    th, td {{ padding: 0.5rem 0.65rem; text-align: left; border-bottom: 1px solid var(--border); vertical-align: top; }}
    th {{ color: var(--muted); font-weight: 600; font-size: 0.72rem; background: #f4f5f7; }}
    tbody tr:hover {{ background: #f8f9fb; }}
    td.bad, .bad {{ color: var(--danger); font-weight: 700; }}
    td.ok {{ color: var(--ok); }}
    td.empty {{ color: var(--muted); text-align: center; }}
    .name {{ font-weight: 600; white-space: nowrap; }}
    .muted {{ color: var(--muted); font-size: 0.8rem; }}
    .ratio {{ font-weight: 700; }}
    .delta {{ font-size: 0.75rem; }}
    .issue-key {{ font-weight: 600; color: var(--jira-blue); }}
    .nav-bar {{ display: flex; flex-wrap: wrap; gap: 0.4rem; margin: 0.75rem 0 0; }}
    .nav-chip {{
      display: inline-block; padding: 0.28rem 0.65rem; border-radius: 3px;
      background: var(--jira-blue-soft); color: var(--jira-blue); font-size: 0.76rem; font-weight: 600;
      border: 1px solid #b3d4ff; text-decoration: none;
    }}
    .nav-chip:hover {{ background: #b3d4ff; text-decoration: none; }}
    .sticky-nav {{
      position: sticky; top: 48px; z-index: 40; background: rgba(244,245,247,0.96);
      backdrop-filter: blur(8px); border: 1px solid var(--border); border-radius: 3px;
      padding: 0.55rem 0.75rem; margin: 0 0 0.85rem;
    }}
    .sticky-nav .nav-bar {{ margin: 0; }}
    details.tasks {{
      margin-top: 0.85rem; background: var(--surface2); border: 1px solid var(--border);
      border-radius: 3px; padding: 0.75rem 0.9rem;
    }}
    details.tasks summary {{ cursor: pointer; font-weight: 600; color: var(--jira-blue); }}
    .fio-block {{ margin-top: 0.85rem; padding-top: 0.75rem; border-top: 1px solid var(--border); }}
    .badge {{
      display: inline-block; margin-left: 0.35rem; padding: 0.08rem 0.45rem; border-radius: 3px;
      background: #ffebe6; color: var(--danger); font-size: 0.7rem; font-weight: 700;
    }}
    .reasons {{ margin: 0.35rem 0 0.55rem; padding-left: 1.1rem; color: var(--muted); font-size: 0.8rem; }}
    .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 0.85rem; }}
    @media (max-width: 860px) {{
      .two-col {{ grid-template-columns: 1fr; }}
      .slide {{ padding: 1rem; }}
      .chart-wrap {{ height: 240px; }}
    }}
    .table-scroll {{ overflow-x: auto; border: 1px solid var(--border); border-radius: 3px; }}
    .table-scroll table {{ margin: 0; }}
    footer {{ text-align: center; color: var(--muted); font-size: 0.78rem; padding: 1rem 0 2rem; }}
    .insight {{ font-size: 0.88rem; color: var(--muted); margin-top: 0.65rem; }}
    .insight strong {{ color: var(--text); }}
  </style>
</head>
<body>
<header class="topbar">
  <a class="brand" href="#top">VIRTU · PlanFact</a>
  <span class="meta">Превышения План/Факт · Производство · {esc(_period_span(periods))}</span>
</header>
<div class="deck" id="top">

  <section class="slide cover">
    <p class="slide-num">Backlog analytics</p>
    <h1>Превышения План / Факт по командам</h1>
    <p class="subtitle">Категория «Производство» · {source_count} срезов · сформировано {esc(generated)}
      <span class="lozenge">Active</span>
    </p>
    <div class="kpi-grid" style="text-align:left;max-width:960px;margin:1.25rem 0 0">
      <div class="kpi red"><div class="kpi-value">+{_num(total_hours)}</div><div class="kpi-label">суммарное превышение, ч</div></div>
      <div class="kpi amber"><div class="kpi-value">{total_tasks}</div><div class="kpi-label">строк задач с превышением</div></div>
      <div class="kpi"><div class="kpi-value">{total_cases}</div><div class="kpi-label">случаев (ФИО × период)</div></div>
      <div class="kpi green"><div class="kpi-value">{teams_with_excess}/{len(teams)}</div><div class="kpi-label">команд с превышением</div></div>
    </div>
  </section>

  <section class="slide" id="overview">
    <div class="slide-header">
      <div>
        <p class="slide-num">Слайд 1</p>
        <h2>Сводка по командам</h2>
        <p class="subtitle">Клик по названию — переход к слайду команды</p>
      </div>
    </div>
    <div class="sticky-nav"><div class="nav-bar">{team_nav}</div></div>
    <div class="table-scroll">
      <table>
        <thead>
          <tr><th>Команда</th><th>Людей</th><th>Случаев</th><th>Строк задач</th><th>+ч</th><th>Лидер по +ч</th></tr>
        </thead>
        <tbody>
          {''.join(overview_rows) if overview_rows else "<tr><td colspan='6'>Нет данных</td></tr>"}
        </tbody>
      </table>
    </div>
    <div class="chart-box">
      <div class="chart-title">Сравнение команд: часы превышения</div>
      <div class="chart-wrap"><canvas id="teamsCompareChart"></canvas></div>
    </div>
  </section>

  <section class="slide" id="rules">
    <div class="slide-header">
      <div>
        <p class="slide-num">Слайд 2</p>
        <h2>{esc(rules_title)}</h2>
        <p class="subtitle">Единые правила для всех команд</p>
      </div>
    </div>
    <div class="two-col">
      <div>
        <p class="section-label">Декомпозиция и заведение</p>
        <ul class="reasons" style="list-style:disc">{rules_li}</ul>
      </div>
      <div>
        <p class="section-label amber">{esc(reestimate_title)}</p>
        <ol class="reasons" style="list-style:decimal;padding-left:1.2rem">{reest_li}</ol>
        <p class="muted" style="margin-top:0.75rem">{esc(reestimate_example)}</p>
      </div>
    </div>
  </section>

  {team_slides}

  <footer>Стиль: Jira backlog (Virtu portal) · PlanFact · https://puholet-sketch.github.io/PlanFact/</footer>
</div>

<script>
  if (typeof Chart === 'undefined') {
    document.querySelectorAll('.chart-wrap').forEach((el) => {
      el.innerHTML = '<p class="muted" style="padding:1rem 0">График не загрузился (Chart.js). Обновите страницу или проверьте, что открыт сайт с папкой <code>assets/</code>.</p>';
    });
  } else {
  Chart.defaults.color = '#6b778c';
  Chart.defaults.borderColor = '#dfe1e6';
  const teamNames = {json.dumps(chart_teams, ensure_ascii=False)};
  const teamHours = {json.dumps(chart_hours)};
  const teamTasks = {json.dumps(chart_tasks)};
  const teamCharts = {json.dumps(team_charts, ensure_ascii=False)};

  new Chart(document.getElementById('teamsCompareChart'), {{
    type: 'bar',
    data: {{
      labels: teamNames,
      datasets: [
        {{
          label: 'Часы превышения',
          data: teamHours,
          backgroundColor: 'rgba(222, 53, 11, 0.72)',
          borderColor: '#de350b',
          borderWidth: 1,
          yAxisID: 'yH'
        }},
        {{
          label: 'Строк задач',
          data: teamTasks,
          backgroundColor: 'rgba(0, 82, 204, 0.55)',
          borderColor: '#0052cc',
          borderWidth: 1,
          yAxisID: 'yT'
        }}
      ]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      interaction: {{ mode: 'index', intersect: false }},
      plugins: {{ legend: {{ position: 'top' }} }},
      scales: {{
        x: {{ ticks: {{ maxRotation: 45, minRotation: 30 }} }},
        yH: {{ type: 'linear', position: 'left', beginAtZero: true, title: {{ display: true, text: 'Часы' }} }},
        yT: {{ type: 'linear', position: 'right', beginAtZero: true, grid: {{ drawOnChartArea: false }}, title: {{ display: true, text: 'Задачи' }} }}
      }}
    }}
  }});

  Object.keys(teamCharts).forEach((slug) => {{
    const c = teamCharts[slug];
    const el = document.getElementById('chart-' + slug);
    if (!el || !c || !c.labels || !c.labels.length) return;
    new Chart(el, {{
      type: 'bar',
      data: {{
        labels: c.labels,
        datasets: [
          {{
            label: 'Задач',
            data: c.tasks,
            backgroundColor: 'rgba(0, 82, 204, 0.65)',
            borderColor: '#0052cc',
            borderWidth: 1,
            yAxisID: 'yTasks'
          }},
          {{
            label: 'Часы',
            data: c.hours,
            backgroundColor: 'rgba(255, 139, 0, 0.7)',
            borderColor: '#ff8b00',
            borderWidth: 1,
            yAxisID: 'yHours'
          }}
        ]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        interaction: {{ mode: 'index', intersect: false }},
        plugins: {{
          legend: {{ position: 'top' }},
          tooltip: {{
            callbacks: {{
              afterBody: (items) => {{
                const i = items[0]?.dataIndex ?? 0;
                return 'Сотрудников: ' + ((c.people && c.people[i]) || 0);
              }}
            }}
          }}
        }},
        scales: {{
          x: {{ ticks: {{ maxRotation: 45, minRotation: 45 }} }},
          yTasks: {{ type: 'linear', position: 'left', beginAtZero: true, ticks: {{ stepSize: 1 }} }},
          yHours: {{ type: 'linear', position: 'right', beginAtZero: true, grid: {{ drawOnChartArea: false }} }}
        }}
      }}
    }});
  }});
  }}
</script>
</body>
</html>
"""


def _render_team_slide(slide_num: int, team: dict) -> str:
    kpi = team["kpi"]
    slug = esc(team["slug"])
    name = esc(team["name"])
    periods = team.get("periods") or []
    period_th = "".join(f"<th>{esc(p)}</th>" for p in periods)

    fio_rows = []
    for row in team.get("fio_totals") or []:
        fio_rows.append(
            "<tr>"
            f"<td class='name'>{esc(row['fio'])}</td>"
            f"<td>{row['periods']}</td>"
            f"<td>{row['task_rows']}</td>"
            f"<td>{row['unique_keys']}</td>"
            f"<td class='bad'>+{_num(row['hours'])}</td>"
            "</tr>"
        )
    grand = team.get("fio_grand") or {}
    if fio_rows:
        fio_rows.append(
            "<tr>"
            f"<td class='name'><strong>Итого</strong></td>"
            f"<td><strong>{grand.get('periods', 0)}</strong></td>"
            f"<td><strong>{grand.get('task_rows', 0)}</strong></td>"
            f"<td><strong>{grand.get('unique_keys', 0)}</strong></td>"
            f"<td class='bad'><strong>+{_num(grand.get('hours', 0))}</strong></td>"
            "</tr>"
        )

    people_rows = []
    for person in team.get("people_trend") or []:
        cells = [f"<td class='name'>{esc(person['name'])}</td>"]
        for cell in person.get("cells") or []:
            if cell is None:
                cells.append("<td class='empty'>—</td>")
                continue
            cls = "bad" if cell["has_exceed"] else "ok"
            cells.append(
                f"<td class='{cls}'><div class='ratio'>{cell['ratio']:.2f}</div>"
                f"<div class='muted'>{_num(cell['plan'])} → {_num(cell['fact'])}</div>"
                f"<div class='delta'>+{_num(cell['excess'])} ч</div></td>"
            )
        people_rows.append("<tr>" + "".join(cells) + "</tr>")

    viol_rows = []
    for row in team.get("violations") or []:
        viol_rows.append(
            "<tr>"
            f"<td><strong>{esc(row['category'])}</strong></td>"
            f"<td>{row['tasks_count']}</td>"
            f"<td class='bad'>+{_num(row['hours'])}</td>"
            f"<td>{row['stories_count']}</td>"
            f"<td class='muted'>{esc(row['action'])}</td>"
            "</tr>"
        )

    task_blocks = []
    for block in team.get("tasks_by_fio") or []:
        reason_items = "".join(
            f"<li><strong>{esc(r['reason'])}</strong> — {r['count']} · +{_num(r['hours'])} ч</li>"
            for r in block.get("reasons") or []
        )
        reasons_html = f"<ul class='reasons'>{reason_items}</ul>" if reason_items else ""
        rows_html = []
        for row in block.get("rows") or []:
            key = row["key"]
            link = esc(row.get("url") or "#")
            rows_html.append(
                "<tr>"
                f"<td>{esc(row['period'])}</td>"
                f"<td><a class='issue-key' href='{link}' target='_blank' rel='noopener'>{esc(key)}</a></td>"
                f"<td>{esc(row['work_type'])}</td>"
                f"<td>{_num(row['plan'])}</td><td>{_num(row['fact'])}</td>"
                f"<td class='bad'>+{_num(row['excess'])}</td>"
                f"<td class='muted'>{esc(row['reasons'])}</td>"
                "</tr>"
            )
        task_blocks.append(
            f"""
            <div class="fio-block">
              <p><strong>{esc(block['fio'])}</strong>
                <span class="badge">{block['count']} · +{_num(block['hours'])} ч</span></p>
              {reasons_html}
              <div class="table-scroll">
              <table>
                <thead><tr><th>Период</th><th>Ключ</th><th>Тип</th><th>План</th><th>Факт</th><th>+ч</th><th>Причины</th></tr></thead>
                <tbody>{''.join(rows_html)}</tbody>
              </table>
              </div>
            </div>
            """
        )

    insight = team.get("insights") or {}
    insight_html = ""
    if insight:
        delta = insight.get("hours_delta")
        delta_txt = "н/д" if delta is None else f"{delta:+.1f} ч"
        insight_html = (
            f"<p class='insight'>Последний срез <strong>{esc(insight.get('last_period') or '—')}</strong>: "
            f"+{_num(insight.get('last_hours', 0))} ч · к прошлому: <strong>{esc(delta_txt)}</strong>. "
            f"Лидер: <strong>{esc(insight.get('top_fio') or '—')}</strong> "
            f"(+{_num(insight.get('top_hours', 0))} ч). "
            f"Концентрация топ-2: <strong>{_num(insight.get('concentration', 0), 0)}%</strong>.</p>"
        )

    viol_section = ""
    if viol_rows:
        viol_section = f"""
        <p class="section-label amber">Нарушения по типам</p>
        <div class="table-scroll">
          <table>
            <thead><tr><th>Тип</th><th>Задач</th><th>+ч</th><th>Story</th><th>Действие</th></tr></thead>
            <tbody>{''.join(viol_rows)}</tbody>
          </table>
        </div>
        """

    return f"""
  <section class="slide" id="team-{slug}">
    <div class="slide-header">
      <div>
        <p class="slide-num">Слайд {slide_num}</p>
        <h2>{name}</h2>
        <p class="subtitle">{kpi['people']} чел. в roster · категория «Производство»</p>
      </div>
    </div>
    <div class="kpi-grid">
      <div class="kpi red"><div class="kpi-value">+{_num(kpi['hours'])}</div><div class="kpi-label">сумма превышения, ч</div></div>
      <div class="kpi amber"><div class="kpi-value">{kpi['tasks']}</div><div class="kpi-label">строк задач</div></div>
      <div class="kpi"><div class="kpi-value">{kpi['cases']}</div><div class="kpi-label">случаев ФИО×период</div></div>
      <div class="kpi green"><div class="kpi-value">{kpi['unique_keys']}</div><div class="kpi-label">уник. задач Jira</div></div>
    </div>
    {insight_html}
    <div class="chart-box">
      <div class="chart-title">Динамика по периодам</div>
      <div class="chart-wrap sm"><canvas id="chart-{slug}"></canvas></div>
    </div>
    <p class="section-label">Итого по ФИО</p>
    <div class="table-scroll">
      <table>
        <thead><tr><th>ФИО</th><th>Периодов</th><th>Строк</th><th>Уник.</th><th>+ч</th></tr></thead>
        <tbody>{''.join(fio_rows) if fio_rows else "<tr><td colspan='5'>Нет превышений</td></tr>"}</tbody>
      </table>
    </div>
    <p class="section-label blue">План → факт по сотрудникам</p>
    <div class="table-scroll">
      <table>
        <thead><tr><th>ФИО</th>{period_th}</tr></thead>
        <tbody>{''.join(people_rows) if people_rows else "<tr><td colspan='99'>Нет данных</td></tr>"}</tbody>
      </table>
    </div>
    {viol_section}
    <details class="tasks">
      <summary>Детализация задач с превышением ({kpi['tasks']})</summary>
      {''.join(task_blocks) if task_blocks else "<p class='muted'>Нет задач</p>"}
    </details>
  </section>
"""


def render_planfact_html(ctx: dict) -> str:
    """Backward-compatible single-team page via unified renderer."""
    team = {
        "slug": "team",
        "name": ctx.get("team_name") or "Команда",
        "periods": ctx.get("periods") or [],
        "kpi": {
            "people": len(ctx.get("trend_rows") or []),
            "cases": ctx.get("total_cases", 0),
            "tasks": ctx.get("total_tasks", 0),
            "hours": ctx.get("total_excess", 0),
            "unique_keys": 0,
            "top_fio": "",
        },
        "chart": {
            "labels": ctx.get("chart_labels") or [],
            "tasks": ctx.get("chart_tasks") or [],
            "hours": ctx.get("chart_hours") or [],
            "people": ctx.get("chart_people") or [],
        },
        "fio_totals": [],
        "fio_grand": {},
        "people_trend": [],
        "violations": [],
        "tasks_by_fio": [],
        "insights": {},
    }
    meta = {
        "periods": ctx.get("periods") or [],
        "generated": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "source_count": len(ctx.get("periods") or []),
        "rules": [],
        "reestimate_steps": [],
        "rules_title": ctx.get("rules_title") or "",
        "reestimate_title": ctx.get("reestimate_title") or "",
        "reestimate_example": ctx.get("reestimate_example") or "",
    }
    # Prefer full unified payload if provided
    if ctx.get("team_payload"):
        return render_unified_site(meta, [ctx["team_payload"]])
    return render_unified_site(meta, [team])
