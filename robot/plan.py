# -*- coding: utf-8 -*-
"""
robot/plan.py ? ??????? AI ?????????
????? JSON?schema ? validate_plan() ? AGENTS.md?
"""
import json
import os
import re
import sys

CODE_RE = re.compile(r"^\d{6}\.(SH|SZ)$")
ACTIONS = ("buy", "sell", "hold")


def load_plan(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_plan(plan, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)


def validate_plan(plan):
    """??????? (ok: bool, errors: list[str])?"""
    errors = []
    if not isinstance(plan, dict):
        return False, ["????? JSON ??"]
    if not plan.get("date"):
        errors.append("?? date ???YYYY-MM-DD?")
    if not isinstance(plan.get("intents"), list) or not plan["intents"]:
        errors.append("intents ???????")
        return False, errors
    seen = set()
    for i, it in enumerate(plan["intents"]):
        tag = "intents[%d]" % i
        if not isinstance(it, dict):
            errors.append(tag + " ?????")
            continue
        code = it.get("code", "")
        if not CODE_RE.match(code):
            errors.append(tag + " code ???? 6?.SH/SZ?? 600036.SH")
            continue
        if code in seen:
            errors.append(tag + " ???? " + code)
        seen.add(code)
        action = it.get("action")
        if action not in ACTIONS:
            errors.append(tag + " action ??? buy/sell/hold")
            continue
        if action == "hold":
            continue
        vol = it.get("volume")
        ratio = it.get("target_ratio")
        if action == "buy" and not ratio and not vol:
            errors.append(tag + " buy ?? target_ratio ? volume")
        if action == "sell" and not vol and not ratio:
            errors.append(tag + " sell ?? volume ? target_ratio")
        if vol is not None and (not isinstance(vol, (int, float)) or vol <= 0):
            errors.append(tag + " volume ?? > 0")
        if ratio is not None and (not isinstance(ratio, (int, float)) or not (0 < ratio <= 0.5)):
            errors.append(tag + " target_ratio ??? (0, 0.5]")
        if it.get("price") is not None and (not isinstance(it["price"], (int, float)) or it["price"] <= 0):
            errors.append(tag + " price ?? > 0")
        if not it.get("reason"):
            errors.append(tag + " ?? reason?????????")
    return len(errors) == 0, errors


def main():
    if len(sys.argv) < 2:
        print("??: python plan.py <plan.json>")
        return 1
    try:
        plan = load_plan(sys.argv[1])
    except Exception as e:
        print("????:", e)
        return 1
    ok, errors = validate_plan(plan)
    print("OK" if ok else "INVALID")
    for e in errors:
        print(" -", e)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
