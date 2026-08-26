#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/retry_failed_tasks.py — 串行重试服务端标死的分析任务

背景：tradingagents 服务端并发/排队能力有限，一次性提交 23 只时部分任务
会被服务端快速标记为 failed（progress=0，message 仍为"任务已创建，等待执行..."）。
本脚本对清单中 status=failed 的任务**逐只串行**重新提交：
提交 1 只 → 轮询至 completed/failed → 拉取保存 → 再提交下一只，避开并发排队。

用法（在项目根）:
  ./.venv-runner/Scripts/python.exe scripts/retry_failed_tasks.py --date 2026-08-19 --max-minutes-per 10

复用 tradingagents_runner 的函数与清单/报告路径。
"""
import argparse
import asyncio
import json
import os
import sys
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "scripts"))

from tradingagents_runner import (  # noqa: E402
    REPORT_DIR,
    _call_tool,
    _parse_json,
    load_mcp_conn,
    load_manifest,
    load_watchlist,
    save_manifest,
)

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


async def retry_one(session, w, depth, max_seconds):
    """提交一只并轮询至结束，返回 (status, note, task_id)。"""
    code, name = w["code"], w["name"]
    text = await _call_tool(session, "analyze_stock",
                            {"symbol": code, "market_type": "A股", "research_depth": depth})
    r = _parse_json(text)
    task_id = r.get("task_id", "")
    if not task_id:
        return "failed", f"no task_id: {text[:120]}", ""
    print(f"[提交] {code} {name} -> {task_id} ({r.get('status', 'submitted')})")

    deadline = asyncio.get_event_loop().time() + max_seconds
    while True:
        await asyncio.sleep(15)
        stext = await _call_tool(session, "get_analysis_status", {"task_id": task_id}, attempts=2)
        sr = _parse_json(stext)
        st = sr.get("status", "")
        print(f"[状态] {code} {name}: {st} | {str(sr.get('message', ''))[:60]}")
        if st == "completed":
            return "completed", str(sr.get("message", ""))[:200], task_id
        if st == "failed":
            return "failed", str(sr.get("message", ""))[:200], task_id
        if asyncio.get_event_loop().time() >= deadline:
            return "timeout", f"超过{max_seconds//60}分钟未完成", task_id


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    ap.add_argument("--depth", default="标准")
    ap.add_argument("--max-minutes-per", type=int, default=10)
    args = ap.parse_args()

    today = args.date
    manifest = load_manifest(today)
    targets = [t for t in manifest["tasks"] if t.get("status") == "failed" and t.get("task_id")]
    if not targets:
        print("无 failed 任务需要重试")
        return
    print(f"待重试 {len(targets)} 只（串行逐只）: {[t['name'] for t in targets]}")

    url, headers = load_mcp_conn()
    out_dir = os.path.join(REPORT_DIR, today)
    os.makedirs(out_dir, exist_ok=True)
    symbol_map = {w["code"]: w.get("symbol", w["code"]) for w in load_watchlist()}

    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client

    async with streamablehttp_client(url, headers=headers) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("连接成功，开始串行重试 ...")
            for t in targets:
                code = t["code"]
                w = next((x for x in load_watchlist() if x["code"] == code), {"code": code, "name": t["name"]})
                try:
                    st, note, task_id = await retry_one(session, w, args.depth, args.max_minutes_per * 60)
                    if st == "completed":
                        rtext = await _call_tool(session, "get_analysis_result", {"task_id": task_id}, attempts=2)
                        symbol = t.get("symbol") or symbol_map.get(code, code)
                        fname = f"{symbol}_{today}.md"
                        with open(os.path.join(out_dir, fname), "w", encoding="utf-8") as f:
                            f.write(f"# {code} {t['name']} · 多智能体分析报告\n\n")
                            f.write(f"> 生成日期 {today} | task_id {task_id} | 来源 tradingagents-mcp\n\n")
                            f.write(rtext)
                        t["status"] = "completed"
                        t["task_id"] = task_id
                        t["note"] = note
                        t["saved"] = fname
                        t["updated"] = datetime.now().strftime("%H:%M:%S")
                        print(f"[报告] {fname} 已保存 ({len(rtext)} 字)")
                    else:
                        t["status"] = st
                        t["task_id"] = task_id
                        t["note"] = note
                        t["updated"] = datetime.now().strftime("%H:%M:%S")
                        print(f"[失败] {code} {t['name']}: {note}")
                except Exception as e:  # noqa: BLE001
                    t["status"] = "failed"
                    t["note"] = str(e)[:200]
                    t["updated"] = datetime.now().strftime("%H:%M:%S")
                    print(f"[ERR] {code} {t['name']}: {e}")
                save_manifest(manifest)

    ok = sum(1 for t in manifest["tasks"] if t.get("status") == "completed")
    fail = sum(1 for t in manifest["tasks"] if t.get("status") == "failed")
    print(f"== 汇总: 共{len(manifest['tasks'])}只 | 报告已保存{ok} | 失败{fail} ==")


if __name__ == "__main__":
    asyncio.run(main())
