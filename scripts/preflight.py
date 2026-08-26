#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/preflight.py — 下单前预检闸门（代码级风控）

用途：交易会话在 place_order 之前，必须先写出交易计划 JSON，再运行本脚本校验。
通过（PASS）才允许执行下单；任何一项不过（FAIL）则禁止执行。
本脚本是确定性代码闸门，不依赖 LLM 自觉。

用法:
  python scripts/preflight.py <plan.json> --assets <总资产> --account_time "<query_account的data_time_text>"

--account_time 必填：传入 query_account 返回的 data_time_text（如 "2026-08-17 09:41:00"）。
  校验其日期 == 今天；否则（QMT 账户数据停留在昨日/更早）全部意图 FAIL，禁止下单。
  这是 2026-08-14 账户数据滞后事件的代码级闸门（此前仅靠 LLM 流程层拦截）。

计划 JSON 格式:
{
  "date": "2026-08-14",
  "intents": [
    {"code": "600036", "name": "招商银行", "action": "buy",  "volume": 100, "price": 38.75, "reason": "击球区第一批"},
    {"code": "601169", "name": "北京银行", "action": "sell", "volume": 300, "price": 5.01,  "reason": "警戒区减仓"}
  ]
}

校验规则:
  0. STOP 紧急开关：项目根存在 STOP 文件 -> 拒绝一切下单
  0.1 账户数据时效：--account_time 的日期必须 == 今天（QMT 账户数据未刷新 -> 拒绝一切下单）
  1. 计划结构：date 必填、intents 非空
  2. 白名单：code 必须在 watchlist.json 内（名称不符仅警告）
  3. 单只去重：同一计划内 code 不得重复
  4. volume：正整数且 100 整数倍（A股整手）
  5. buy 必须提供 price>0（用实时最新价估算金额）
  6. 单笔上限：买入金额 <= 总资产 x single_order_pct_of_assets (5%)
  7. 单日预算：当日已批准买入合计 + 本次 <= 总资产 x daily_buy_budget_pct_of_assets (10%)
     （当日台账 scripts/plans/YYYYMMDD.json，晨间/午后班共享）
  8. 同一标的同一日最多一次买入批准
  9. reason 必填
  PASS 时把批准记录写入 scripts/plans/YYYYMMDD.json（含金额），作为当日预算台账。
  全部通过才记录；任一错误则整体 FAIL，不记录任何内容。

退出码: 0=PASS 1=FAIL
"""
import argparse
import json
import os
import sys
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WATCHLIST = os.path.join(BASE, "watchlist.json")
CONFIG = os.path.join(BASE, "CONFIG.json")
STOP_FILE = os.path.join(BASE, "STOP")
PLANS_DIR = os.path.join(BASE, "scripts", "plans")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser(description="下单前预检闸门")
    ap.add_argument("plan", help="交易计划 JSON 路径")
    ap.add_argument("--assets", type=float, required=True, help="账户总资产（预算计算基准，必须取买入前总资产）")
    ap.add_argument(
        "--account_time",
        required=True,
        help='query_account 返回的 data_time_text（如 "2026-08-17 09:41:00"）；日期≠今天则全部意图 FAIL',
    )
    ap.add_argument("--no-save", action="store_true", help="仅校验，不写入当日台账")
    args = ap.parse_args()

    errors = []
    warnings = []

    # 0. STOP 紧急开关
    if os.path.exists(STOP_FILE):
        print("FAIL")
        print(" - [STOP] 紧急停止开关已激活（项目根存在 STOP 文件），禁止一切下单。")
        return 1

    # 0.1 账户数据时效（QMT 账户数据必须为今日实时快照，2026-08-14 滞后事件代码级闸门）
    acc_time = args.account_time.strip()
    acc_date = acc_time.split(" ")[0] if acc_time else ""
    today = datetime.now().strftime("%Y-%m-%d")
    if acc_date != today:
        print("FAIL")
        print(
            f" - [账户时效] query_account data_time={acc_time!r}，日期 {acc_date!r} != 今天 {today!r}；"
            "QMT 账户数据未刷新，禁止下单。"
        )
        return 1

    # 1. 配置
    try:
        cfg = load_json(CONFIG)
    except Exception as e:
        print("FAIL")
        print(f" - 无法读取 CONFIG.json: {e}")
        return 1
    daily_budget = args.assets * float(cfg.get("daily_buy_budget_pct_of_assets", 0.10))
    single_cap = args.assets * float(cfg.get("single_order_pct_of_assets", 0.05))

    # 2. 白名单
    try:
        wl = load_json(WATCHLIST)
    except Exception as e:
        print("FAIL")
        print(f" - 无法读取 watchlist.json: {e}")
        return 1
    whitelist = {str(w["code"]): w["name"] for w in wl}

    # 3. 计划结构
    try:
        plan = load_json(args.plan)
    except Exception as e:
        print("FAIL")
        print(f" - 计划 JSON 无法解析: {e}")
        return 1
    if not isinstance(plan, dict) or not plan.get("date"):
        print("FAIL")
        print(" - 缺少 date 字段（YYYY-MM-DD）")
        return 1
    date = str(plan["date"])
    intents = plan.get("intents") or []
    if not isinstance(intents, list) or not intents:
        print("FAIL")
        print(" - intents 为空")
        return 1

    # 4. 当日已批准台账
    day_ledger_path = os.path.join(PLANS_DIR, f"{date}.json")
    day_ledger = {"date": date, "approved": []}
    if os.path.exists(day_ledger_path):
        try:
            day_ledger = load_json(day_ledger_path)
            day_ledger.setdefault("approved", [])
        except Exception:
            warnings.append("当日台账解析失败，按空台账处理（请人工核查）")
    approved_buys = [a for a in day_ledger.get("approved", []) if a.get("action") == "buy"]
    spent = sum(float(a.get("amount", 0)) for a in approved_buys)
    day_codes = {a.get("code") for a in approved_buys}

    # 5. 逐笔校验
    seen = set()
    new_buys = []
    planned_so_far = 0.0  # 本计划内已校验通过的买入金额（滚动累计）
    for i, it in enumerate(intents):
        tag = f"intents[{i}]"
        if not isinstance(it, dict):
            errors.append(f"{tag} 不是对象")
            continue
        code = str(it.get("code", ""))
        name = str(it.get("name", ""))
        action = it.get("action")
        volume = it.get("volume")
        price = it.get("price")
        reason = str(it.get("reason", "")).strip()

        if code not in whitelist:
            errors.append(f"{tag} {code} 不在自选池白名单（watchlist.json）")
            continue
        if name and whitelist[code] and name != whitelist[code]:
            warnings.append(f"{tag} 名称 {name} 与白名单 {whitelist[code]} 不一致（以代码为准）")
        if action not in ("buy", "sell"):
            errors.append(f"{tag} action 必须是 buy/sell，收到 {action!r}")
            continue
        if code in seen:
            errors.append(f"{tag} 计划内重复代码 {code}")
        seen.add(code)
        if not isinstance(volume, int) or volume <= 0:
            errors.append(f"{tag} volume 必须为正整数")
            continue
        if volume % 100 != 0:
            errors.append(f"{tag} volume {volume} 不是100整数倍（A股整手）")
        if not reason:
            errors.append(f"{tag} 缺少 reason（决策依据）")

        if action == "buy":
            if not isinstance(price, (int, float)) or price <= 0:
                errors.append(f"{tag} buy 必须提供 price>0（用实时最新价估算）")
                continue
            amount = round(volume * float(price), 2)
            if amount > single_cap:
                errors.append(
                    f"{tag} 单笔金额 {amount:.2f} 超单笔上限 {single_cap:.2f}（总资产5%）"
                )
            if code in day_codes:
                errors.append(f"{tag} {code} 今日已有买入批准，同一标的单日最多一次")
            if spent + planned_so_far + amount > daily_budget:
                errors.append(
                    f"{tag} 当日累计买入 {spent + planned_so_far + amount:.2f} 将超单日预算 {daily_budget:.2f}"
                    f"（总资产10%，其中今日已批准 {spent:.2f}、本计划前序 {planned_so_far:.2f}）"
                )
            planned_so_far += amount
            new_buys.append(
                {"code": code, "name": name, "action": action, "volume": volume,
                 "price": float(price), "amount": amount, "reason": reason,
                 "approved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            )
        else:
            amount = round(volume * float(price), 2) if isinstance(price, (int, float)) and price > 0 else 0.0
            day_ledger["approved"].append(
                {"code": code, "name": name, "action": action, "volume": volume,
                 "price": price, "amount": amount, "reason": reason,
                 "approved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            )

    for w in warnings:
        print("WARN:", w)

    if errors:
        print("FAIL")
        for e in errors:
            print(" -", e)
        print(f" - 拒绝原因：{len(errors)} 项校验未通过，未写入任何台账。")
        return 1

    # 6. PASS：写入当日台账（买入预算累计）
    if not args.no_save:
        day_ledger["approved"].extend(new_buys)
        os.makedirs(PLANS_DIR, exist_ok=True)
        with open(day_ledger_path, "w", encoding="utf-8") as f:
            json.dump(day_ledger, f, ensure_ascii=False, indent=2)
        print(f"台账已更新: {day_ledger_path}")

    total_planned_buy = sum(a["amount"] for a in new_buys)
    print("PASS")
    print(f" - 账户数据时效：{acc_time}（日期==今天，校验通过）")
    print(f" - 预算基准总资产：{args.assets:.2f}（须为买入前总资产）")
    print(f" - 本次计划 {len(intents)} 笔（买入 {len(new_buys)} 笔 / 卖出 {len(intents) - len(new_buys)} 笔）")
    if new_buys:
        print(f" - 本次买入合计 {total_planned_buy:.2f} 元；当日已批准合计 {spent + total_planned_buy:.2f} / 预算 {daily_budget:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
