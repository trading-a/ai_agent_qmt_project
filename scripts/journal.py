#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
何价值 · 全自动交易系统 — 交易与盈亏记账脚本
用法（由 cron 会话通过 terminal 调用）：
  python scripts/journal.py add-trade --date 2026-08-13 --code 600036 --name 招商银行 --side buy --price 38.75 --volume 100 --status filled --remark "击球区建仓第一批"
  python scripts/journal.py add-pnl --date 2026-08-13 --total_assets 996054.84 --cash 831942.84 --market_value 164196.00 --pnl -998.81 --position_pct 16.48
  python scripts/journal.py summary --limit 10
输出：logs/trades.csv（交易流水）、logs/pnl_daily.csv（每日账户快照）
"""
import argparse
import csv
import os
import sys
from datetime import date, datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS = os.path.join(BASE, "logs")
TRADES_CSV = os.path.join(LOGS, "trades.csv")
PNL_CSV = os.path.join(LOGS, "pnl_daily.csv")

TRADES_HEADER = ["date", "time", "code", "name", "side", "price", "volume", "amount", "status", "remark"]
PNL_HEADER = ["date", "time", "total_assets", "cash", "market_value", "pnl", "position_pct", "remark"]


def ensure_dir():
    os.makedirs(LOGS, exist_ok=True)


def append_row(path, header, row):
    ensure_dir()
    new_file = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(header)
        w.writerow(row)
    print(f"[journal] 已写入: {path}  ->  {row}")


def add_trade(args):
    row = [
        args.date,
        args.time or datetime.now().strftime("%H:%M:%S"),
        args.code,
        args.name,
        args.side,
        args.price,
        args.volume,
        args.amount or (round(float(args.price) * int(args.volume), 2) if args.price and args.volume else ""),
        args.status,
        args.remark or "",
    ]
    append_row(TRADES_CSV, TRADES_HEADER, row)


def add_pnl(args):
    row = [
        args.date,
        args.time or datetime.now().strftime("%H:%M:%S"),
        args.total_assets,
        args.cash,
        args.market_value,
        args.pnl,
        args.position_pct,
        args.remark or "",
    ]
    append_row(PNL_CSV, PNL_HEADER, row)


def summary(args):
    def read(path, header):
        if not os.path.exists(path):
            print(f"（无记录）{path}")
            return []
        with open(path, "r", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        return rows

    trades = read(TRADES_CSV, TRADES_HEADER)
    pnls = read(PNL_CSV, PNL_HEADER)
    print(f"== 交易流水: {len(trades)} 条 ==")
    for r in trades[- (args.limit or 10):]:
        print(r)
    print(f"== 每日账户快照: {len(pnls)} 条 ==")
    for r in pnls[- (args.limit or 10):]:
        print(r)
    if pnls:
        try:
            first = pnls[0]
            last = pnls[-1]
            fa = float(first.get("total_assets") or 0)
            la = float(last.get("total_assets") or 0)
            if fa:
                print(f"== 区间总资产变动: {fa} -> {la} ({(la/fa - 1)*100:.2f}%) ==")
        except (ValueError, TypeError):
            pass


def main():
    p = argparse.ArgumentParser(description="何价值交易系统记账脚本")
    sub = p.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("add-trade", help="记录一笔交易")
    t.add_argument("--date", required=True)
    t.add_argument("--time", default="")
    t.add_argument("--code", required=True)
    t.add_argument("--name", required=True)
    t.add_argument("--side", required=True, choices=["buy", "sell"])
    t.add_argument("--price", required=True)
    t.add_argument("--volume", required=True)
    t.add_argument("--amount", default="")
    t.add_argument("--status", default="filled", choices=["filled", "pending", "rejected", "cancelled"])
    t.add_argument("--remark", default="")
    t.set_defaults(func=add_trade)

    pnl = sub.add_parser("add-pnl", help="记录当日账户快照")
    pnl.add_argument("--date", required=True)
    pnl.add_argument("--time", default="")
    pnl.add_argument("--total_assets", required=True)
    pnl.add_argument("--cash", required=True)
    pnl.add_argument("--market_value", required=True)
    pnl.add_argument("--pnl", required=True)
    pnl.add_argument("--position_pct", required=True)
    pnl.add_argument("--remark", default="")
    pnl.set_defaults(func=add_pnl)

    s = sub.add_parser("summary", help="查看最近记录")
    s.add_argument("--limit", type=int, default=10)
    s.set_defaults(func=summary)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
