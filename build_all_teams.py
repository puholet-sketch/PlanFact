"""Пересборка отчётов по всем командам + единый HTML-сайт."""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime

from build_exceed_report import ReportConfig, build_report, list_source_files, set_config
from jira_audit_rules import (
    DECOMP_RULES,
    REESTIMATE_EXAMPLE,
    REESTIMATE_STEPS,
    REESTIMATE_TITLE,
    RULES_TITLE,
)
from report_theme import render_unified_site
from team_mapping import (
    DEFAULT_MAPPING_FILE,
    SKIP_TEAMS,
    VFOS_TEAM,
    load_team_rosters,
    output_team_dir,
    output_team_name,
)

SOURCE_ROOT = os.path.dirname(os.path.abspath(__file__))
TEAMS_ROOT = os.path.join(SOURCE_ROOT, "teams")
SITE_ROOT = SOURCE_ROOT


def write_site(teams: list[dict], periods: list[str], source_count: int) -> str:
    html = render_unified_site(
        {
            "periods": periods,
            "generated": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "source_count": source_count,
            "rules": DECOMP_RULES,
            "reestimate_steps": REESTIMATE_STEPS,
            "rules_title": RULES_TITLE,
            "reestimate_title": REESTIMATE_TITLE,
            "reestimate_example": REESTIMATE_EXAMPLE,
        },
        teams,
    )
    index_path = os.path.join(SITE_ROOT, "index.html")
    docs_dir = os.path.join(SITE_ROOT, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    with open(index_path, "w", encoding="utf-8") as handle:
        handle.write(html)
    shutil.copyfile(index_path, os.path.join(docs_dir, "index.html"))
    assets_src = os.path.join(SITE_ROOT, "assets")
    assets_dst = os.path.join(docs_dir, "assets")
    if os.path.isdir(assets_src):
        os.makedirs(assets_dst, exist_ok=True)
        for name in os.listdir(assets_src):
            src = os.path.join(assets_src, name)
            if os.path.isfile(src):
                shutil.copy2(src, os.path.join(assets_dst, name))
    nojekyll = os.path.join(SITE_ROOT, ".nojekyll")
    if not os.path.exists(nojekyll):
        open(nojekyll, "w", encoding="utf-8").close()
    with open(os.path.join(SITE_ROOT, "site_data.json"), "w", encoding="utf-8") as handle:
        json.dump(
            {
                "generated": datetime.now().isoformat(timespec="seconds"),
                "periods": periods,
                "teams": [{"name": t["name"], "slug": t["slug"], "kpi": t["kpi"]} for t in teams],
            },
            handle,
            ensure_ascii=False,
            indent=2,
        )
    return index_path


def main() -> None:
    rosters = load_team_rosters(DEFAULT_MAPPING_FILE)
    print(f"Mapping: {DEFAULT_MAPPING_FILE}")
    print(f"Teams in roster: {len(rosters)}")
    print(f"Skip teams: {', '.join(sorted(SKIP_TEAMS))}")

    os.makedirs(TEAMS_ROOT, exist_ok=True)
    teams_to_build = sorted(t for t in rosters if t not in SKIP_TEAMS)
    set_config(
        ReportConfig(
            source_folder=SOURCE_ROOT,
            output_folder=TEAMS_ROOT,
            team_name="ALL",
            target_fios=[],
            use_jira_audit=False,
        )
    )
    source_files = list_source_files()

    payloads: list[dict] = []
    for team_name in teams_to_build:
        display_name = output_team_name(team_name)
        out_dir = os.path.join(TEAMS_ROOT, output_team_dir(team_name))
        os.makedirs(out_dir, exist_ok=True)
        cfg = ReportConfig(
            source_folder=SOURCE_ROOT,
            output_folder=out_dir,
            team_name=display_name,
            target_fios=rosters[team_name],
            use_jira_audit=(team_name == VFOS_TEAM),
        )
        print(f"\n=== {display_name} -> {out_dir} ===")
        payload = build_report(cfg)
        if payload:
            payloads.append(payload)

    payloads.sort(key=lambda t: (-float(t["kpi"]["hours"]), t["name"]))
    periods = payloads[0]["periods"] if payloads else []
    index_path = write_site(payloads, periods, len(source_files))
    print(f"\nDone. Teams root: {TEAMS_ROOT}")
    print(f"UNIFIED_HTML: {index_path}")
    print(f"TEAMS_IN_SITE: {len(payloads)}")


if __name__ == "__main__":
    main()
