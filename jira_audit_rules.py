"""Правила аудита превышений: базовые правила декомпозиции и заведения задач + Jira."""

from __future__ import annotations

import re
from typing import Any

RULES_TITLE = "Базовые правила декомпозиции и заведения задач"

DECOMP_RULES = [
    "Аналитикам — не забывать проставлять оценки.",
    "External-дефекты с прода — оценка 16 ч; в рамках разработки оценку не проставляем.",
    "Дробить подзадачи BA/DEV/QA на части не более 24 ч (тимлид + тестировщик по ФТ/ОП).",
    "Создавать задачу на аналитическое сопровождение разработки и тестирования.",
    "За дроблением следит аналитик; при новых требованиях — правим план или новая задача.",
    "Для оценок использовать тип «Планирование»: малая 4 ч, средняя 12 ч, большая 20 ч.",
    "При превышении или невозможности дробления — обратная связь аналитику / ПМ / тимлиду.",
]

REESTIMATE_TITLE = "Новые требования: как переоценить"

REESTIMATE_STEPS = [
    "Аналитик фиксирует, что изменилось (новый scope, какие подзадачи затронуты).",
    "Обновить соседнюю подзадачу «Оценка» / «Планирование» (тип Planning) — общая переоценка Story.",
    "Скорректировать оценки на затронутых подзадачах (фронт / бэк / QA); каждая ≤ 24 ч.",
    "При существенном росте объёма — новая подзадача или Story, а не «дотягивание» фактом.",
    "Согласовать с аналитиком / ПМ / тимлидом.",
]

REESTIMATE_EXAMPLE = (
    "Пример: появилась валидация в ЕКИС — сначала переоценка в Planning, "
    "затем правка плана на затронутых подзадачах."
)

MISSING_ESTIMATE_MSG = "Не проставлена оценка — аналитикам не забывать проставлять оценки"

# Подзадачи одной Story на одном уровне (в коде Jira — siblings)
NEIGHBOR_PLANNING_HINT = (
    "оценка может быть на соседней подзадаче «Оценка» / «Планирование» у той же Story — "
    "проверить точность оценки там"
)
CHECK_NEIGHBOR_PLANNING = (
    "сверить с соседней подзадачей «Планирование» / «Оценка» у родительской Story"
)
JIRA_STRUCTURE_HINT = (
    "в Jira: родительская Story и её подзадачи "
    "(соседние «Оценка»/«Планирование», аналитика, разработка, тестирование — BA/DEV/QA)"
)

def norm(value: str) -> str:
    text = (value or "").strip().lower().replace("ё", "е")
    return re.sub(r"\s+", " ", text)


def find_planning_siblings(siblings: list[dict]) -> list[dict]:
    result = []
    for s in siblings or []:
        stype = norm(str(s.get("type") or ""))
        summary = norm(str(s.get("summary") or ""))
        if stype == "planning" or summary.startswith("оценка") or " оценка " in f" {summary} ":
            result.append(s)
    return result


def audit_task(
    task_key: str,
    fio: str,
    work_type: str,
    plan_h: float,
    fact_h: float,
    jira: dict | None,
) -> dict[str, Any]:
    """Возвращает нарушения, статус проверки и текст причин для отчёта."""
    violations: list[str] = []
    notes: list[str] = []
    delta = fact_h - plan_h

    jira = jira or {}
    siblings = jira.get("siblings") or []
    parent = jira.get("parent")
    jtype = jira.get("type") or ""
    summary = jira.get("summary") or ""
    orig_est = float(jira.get("origEstH") or 0)
    spent = float(jira.get("spentH") or 0)
    planning_tasks = find_planning_siblings(siblings)

    # --- 1. Структура Story / подзадачи ---
    if not parent and not siblings:
        violations.append("Нет родительской Story / структуры подзадач BA-DEV-QA")

    if parent and not planning_tasks:
        violations.append("Нет задачи «Планирование» / «Оценка» у Story (нарушение дробления)")

    # --- 2. Тип «Оценка» не Planning ---
    for pt in planning_tasks:
        ptype = str(pt.get("type") or "")
        if ptype and ptype != "Planning" and "planning" not in norm(ptype):
            violations.append(
                f"Задача оценки {pt.get('key')} имеет тип «{ptype}», ожидается Planning"
            )

    # --- 3. Оценка+аналитика в одной задаче ---
    if "оценка" in norm(summary) and any(
        x in norm(summary) for x in ("анализ", "сопровожд", "документ")
    ):
        violations.append(
            "Оценка совмещена с аналитикой/сопровождением в одной задаче — нужно разделить"
        )

    # --- 4. Гранулярность >24 ч ---
    size = max(plan_h, fact_h, orig_est, spent)
    if size > 24:
        violations.append(f"Задача/оценка >24 ч ({size:.1f} ч) — нарушена гранулярность BA/DEV/QA")

    # --- 5. План=0 на подзадаче ---
    if plan_h == 0 and fact_h > 0:
        if planning_tasks:
            notes.append(
                "План=0 в выгрузке при наличии соседней подзадачи «Планирование» у Story — "
                "превышение относительно нуля; проверить оценку в ней"
            )
        else:
            violations.append(
                f"План=0, факт>0 и нет задачи «Планирование» у Story — {MISSING_ESTIMATE_MSG.lower()}"
            )

    # --- 6. Промах в оценке (есть Planning) ---
    if plan_h > 0 and fact_h > plan_h:
        if planning_tasks:
            pt = planning_tasks[0]
            violations.append(
                f"Промах в оценке: план {plan_h:g} ч → факт {fact_h:g} ч (+{delta:g} ч); "
                f"сверить с {pt.get('key')} «{pt.get('summary', '')[:50]}»"
            )
        else:
            violations.append(
                f"Превышение при наличии оценки: план {plan_h:g} ч → факт {fact_h:g} ч (+{delta:g} ч)"
            )

    # --- 7. Существенный перерасход (новые требования) ---
    if plan_h > 0 and fact_h >= plan_h * 1.35:
        violations.append(
            f"Существенный перерасход (+{delta:g} ч, x{fact_h/plan_h:.2f}) — "
            "вероятны новые требования / расширение объёма работ (обратная связь аналитику/ПМ)"
        )

    # --- 8. External / дефект 16 ч ---
    if plan_h == 16 or "external" in norm(task_key) or "дефект" in norm(summary):
        notes.append(f"Проверить: external-дефект (стандарт 16 ч по {RULES_TITLE.lower()})")

    # --- 9. Нестандартная оценка Planning 4/12/20 ---
    if jtype == "Planning" or (planning_tasks and task_key in [p.get("key") for p in planning_tasks]):
        if orig_est > 0 and orig_est not in (4, 12, 20) and orig_est <= 24:
            notes.append(
                f"Оценка Planning {orig_est:g} ч не из шкалы 4/12/20 ч ({RULES_TITLE})"
            )

    # --- 10. План=0 на подзадаче аналитики ---
    if plan_h == 0 and fact_h > 0 and any(
        x in norm(work_type) for x in ("анализ", "сопровожд", "документ", "исследован")
    ):
        if planning_tasks:
            notes.append(
                "План=0 на подзадаче аналитики при наличии соседней «Планирование» — "
                "аналитикам проверить оценку"
            )
        elif MISSING_ESTIMATE_MSG not in violations:
            violations.append(MISSING_ESTIMATE_MSG)

    if not violations and not notes:
        if plan_h > 0 and fact_h > plan_h:
            violations.append(f"Превышение +{delta:g} ч — требуется разбор с аналитиком/ПМ/тимлидом")
        else:
            notes.append("Превышение зафиксировано — явных нарушений регламента не найдено")

    # Уникальные формулировки
    violations = list(dict.fromkeys(violations))
    notes = list(dict.fromkeys(notes))

    return {
        "violations": violations,
        "notes": notes,
        "planning_keys": [p.get("key") for p in planning_tasks],
        "parent": parent,
        "jira_type": jtype,
        "checked": bool(jira),
    }


def format_reasons(audit: dict[str, Any]) -> str:
    parts = audit.get("violations", []) + audit.get("notes", [])
    if not audit.get("checked"):
        parts.insert(0, "[Jira не проверен — эвристика по выгрузке]")
    return "; ".join(parts)


def categorize_violation(violation: str) -> str:
    text = norm(violation)
    if "нет родительской story" in text:
        return "Нет структуры Story / подзадач"
    if "нет задачи" in text and "планирование" in text:
        return "Нет Planning / «Оценка» у Story"
    if "тип" in text and "planning" in text:
        return "Неверный тип задачи «Оценка»"
    if "совмещена" in text and "аналитик" in text:
        return "Оценка + аналитика в одной задаче"
    if ">24" in text or "гранулярность" in text:
        return "Гранулярность >24 ч"
    if "соседн" in text and "планирован" in text:
        return "План=0 без Planning / оценка"
    if "sibling" in text:
        return "План=0 без Planning / оценка"
    if "не проставлена оценка" in text or "аналитикам не забывать" in text or "аналитикам — не забывать" in text:
        return "Не проставлена оценка — аналитикам"
    if "план = 0" in text or "план=0" in text:
        return "План=0 без Planning / оценка"
    if "задача >24" in text or "крупная задача" in text:
        return "Гранулярность >24 ч"
    if "неточная оценка" in text or ("сверить с" in text and "планирован" in text):
        return "Промах в оценке"
    if "external" in text or "дефект" in text:
        return "External / дефект (16 ч)"
    if "update 21/04" in text and "не проставлена" in text:
        return "Не проставлена оценка — аналитикам"
    if "промах в оценке" in text:
        return "Промах в оценке"
    if "перерасход" in text or "расширение объема" in text or "расширение объёма" in text:
        return "Существенный перерасход / новые требования"
    if "external" in text or "дефект" in text:
        return "External / дефект (16 ч)"
    if "превышение +" in text:
        return "Превышение — разбор с аналитиком/ПМ"
    return "Прочее"


ACTION_BY_CATEGORY = {
    "Нет Planning / «Оценка» у Story": "Создать задачу «Планирование» с оценкой 4/12/20 ч; дробить Story на BA/DEV/QA.",
    "Неверный тип задачи «Оценка»": "Сменить тип задачи «Оценка» на Planning.",
    "Оценка + аналитика в одной задаче": "Разделить оценку и аналитическое сопровождение на отдельные подзадачи.",
    "Гранулярность >24 ч": "Дробить подзадачи на части ≤24 ч (тимлид + QA по ФТ/ОП).",
    "План=0 без Planning": "Проставить оценку; при отсутствии Planning — создать задачу «Планирование».",
    "План=0 без Planning / оценка": (
        "Проставить оценку; проверить соседнюю подзадачу «Планирование» / «Оценка» у Story."
    ),
    "Не проставлена оценка — аналитикам": "Аналитикам — не забывать проставлять оценки на подзадачах.",
    "Промах в оценке": (
        "Сверить факт с соседней подзадачей «Планирование»; скорректировать оценку или завести новую задачу."
    ),
    "Существенный перерасход / новые требования": "Обратная связь аналитику/ПМ: новые требования → правка плана или новая задача.",
    "Нет структуры Story / подзадач": f"Оформить Story и подзадачи BA/DEV/QA по {RULES_TITLE.lower()}.",
    "External / дефект (16 ч)": "Проверить соответствие стандарту 16 ч для external-дефектов.",
    "Превышение — разбор с аналитиком/ПМ": "Разбор причин превышения с аналитиком, ПМ и тимлидом.",
    "Прочее": "Разбор с аналитиком / ПМ / тимлидом.",
}


def action_for_category(category: str) -> str:
    return ACTION_BY_CATEGORY.get(category, ACTION_BY_CATEGORY["Прочее"])
