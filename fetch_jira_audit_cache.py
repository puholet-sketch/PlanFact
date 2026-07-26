"""Сбор кэша Jira для аудита превышений.

Запуск (нужна открытая сессия portal.virtusystems.ru в Chrome/Edge):
  python fetch_jira_audit_cache.py

Скрипт читает audit_tasks.json, формирует JS для консоли браузера
и сохраняет шаблон jira_audit_cache.json при ручной вставке результата.

Автоматически: если задан JIRA_USER + JIRA_TOKEN — тянет REST API.
"""
import json
import os
import sys

import requests

from team_mapping import vfos_report_dir

SOURCE_ROOT = os.path.dirname(os.path.abspath(__file__))
VFOS_DIR = vfos_report_dir(SOURCE_ROOT)
TASKS_FILE = os.path.join(VFOS_DIR, "audit_tasks.json")
CACHE_FILE = os.path.join(VFOS_DIR, "jira_audit_cache.json")
PORTAL = "https://portal.virtusystems.ru"


def fetch_issue(session: requests.Session, key: str) -> dict:
    fields = "summary,issuetype,parent,timeoriginalestimate,timespent"
    r = session.get(f"{PORTAL}/rest/api/2/issue/{key}", params={"fields": fields}, timeout=30)
    r.raise_for_status()
    j = r.json()
    siblings = []
    parent_key = j.get("fields", {}).get("parent", {}).get("key")
    if parent_key:
        pr = session.get(
            f"{PORTAL}/rest/api/2/issue/{parent_key}",
            params={"fields": "subtasks"},
            timeout=30,
        )
        pr.raise_for_status()
        pj = pr.json()
        for s in pj.get("fields", {}).get("subtasks") or []:
            siblings.append(
                {
                    "key": s.get("key"),
                    "summary": s.get("fields", {}).get("summary"),
                    "type": s.get("fields", {}).get("issuetype", {}).get("name"),
                }
            )
    f = j.get("fields", {})
    return {
        "key": key,
        "summary": f.get("summary"),
        "type": f.get("issuetype", {}).get("name"),
        "parent": parent_key,
        "origEstH": (f.get("timeoriginalestimate") or 0) / 3600,
        "spentH": (f.get("timespent") or 0) / 3600,
        "siblings": siblings,
    }


def main() -> None:
    tasks = json.load(open(TASKS_FILE, encoding="utf-8"))
    keys = sorted(tasks.keys())
    user = os.environ.get("JIRA_USER") or os.environ.get("JIRA_EMAIL")
    token = os.environ.get("JIRA_TOKEN") or os.environ.get("JIRA_API_TOKEN")

    if user and token:
        session = requests.Session()
        session.auth = (user, token)
        session.headers["Accept"] = "application/json"
        cache = {}
        for i, key in enumerate(keys, 1):
            try:
                cache[key] = fetch_issue(session, key)
                print(f"[{i}/{len(keys)}] OK {key}")
            except Exception as exc:
                print(f"[{i}/{len(keys)}] FAIL {key}: {exc}", file=sys.stderr)
        json.dump(cache, open(CACHE_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"Saved {CACHE_FILE} ({len(cache)} issues)")
        return

    js_keys = json.dumps(keys, ensure_ascii=False)
    js = f"""
// Вставьте в консоль на https://portal.virtusystems.ru (авторизованы)
(async () => {{
  const keys = {js_keys};
  const out = {{}};
  for (const key of keys) {{
    const r = await fetch('/rest/api/2/issue/' + key + '?fields=summary,issuetype,parent,timeoriginalestimate,timespent');
    const j = await r.json();
    let siblings = [];
    const parent = j.fields && j.fields.parent && j.fields.parent.key;
    if (parent) {{
      const pr = await fetch('/rest/api/2/issue/' + parent + '?fields=subtasks');
      const pj = await pr.json();
      siblings = (pj.fields.subtasks || []).map(s => ({{
        key: s.key, summary: s.fields.summary, type: s.fields.issuetype.name
      }}));
    }}
    out[key] = {{
      key, summary: j.fields.summary, type: j.fields.issuetype.name, parent,
      origEstH: (j.fields.timeoriginalestimate || 0) / 3600,
      spentH: (j.fields.timespent || 0) / 3600,
      siblings
    }};
    console.log('done', key);
  }}
  copy(JSON.stringify(out, null, 2));
  console.log('JSON скопирован в буфер — сохраните в jira_audit_cache.json');
  return out;
}})();
"""
    console_path = os.path.join(FOLDER, "jira_fetch_console.js")
    open(console_path, "w", encoding="utf-8").write(js)
    print("JIRA credentials not set.")
    print(f"Open portal, paste script from: {console_path}")
    print(f"Save result to: {CACHE_FILE}")


if __name__ == "__main__":
    main()
