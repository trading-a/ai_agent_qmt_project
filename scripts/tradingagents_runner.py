#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/tradingagents_runner.py — 自选股多智能体分析执行器

直连 tradingagents MCP 服务（url 与凭据从 Hermes 配置读取），
对 watchlist.json 全部自选股提交多智能体分析（异步任务），轮询状态，拉取完整报告，
保存到 report/trading-agents/YYYYMMDD/ 目录，供本周决策参考（周频任务，默认周一凌晨运行）。

用法:
  python scripts/tradingagents_runner.py run  [--depth 标准] [--max-minutes 40] [--limit N] [--codes 600036,601398]
  python scripts/tradingagents_runner.py submit [--depth 标准] [--codes 600036,601398]  # 仅提交（写任务清单）
  python scripts/tradingagents_runner.py status [--date YYYY-MM-DD]   # 仅轮询更新状态
  python scripts/tradingagents_runner.py collect [--date YYYY-MM-DD]  # 仅拉取已完成报告
  python scripts/tradingagents_runner.py summary [--date YYYY-MM-DD]  # 仅重新生成批次摘要 summary.md
断点续跑: 任务清单 scripts/tradingagents_tasks/YYYYMMDD.json，已提交的不会重复提交。
成本纪律: 全量批次默认双周（每月1/15日）且深度=标准；--codes 用于晨间/午后决策班按需定向提交单只（标准档）。
"""
import argparse
import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WATCHLIST = os.path.join(BASE, "watchlist.json")
TASKS_DIR = os.path.join(BASE, "scripts", "tradingagents_tasks")
REPORT_DIR = os.path.join(BASE, "report", "trading-agents")
HERMES_CONFIG = r"C:\Users\Administrator\AppData\Local\hermes\profiles\qmt\config.yaml"

POLL_INTERVAL = 25  # 秒
DEFAULT_MAX_MINUTES = 40

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def load_mcp_conn():
    """从 Hermes 配置读取 tradingagents-mcp 的 url 与 Authorization 头。"""
    with open(HERMES_CONFIG, "r", encoding="utf-8") as f:
        text = f.read()
    m = re.search(
        r"tradingagents-mcp:\s*\n\s+url:\s*(\S+)\s*\n\s+headers:\s*\n\s+Authorization:\s*(.+)",
        text,
    )
    if not m:
        raise RuntimeError("未在 Hermes 配置中找到 tradingagents-mcp 条目")
    url = m.group(1).strip()
    auth = m.group(2).strip()
    if auth.startswith("Bearer "):
        auth = auth
    headers = {"Authorization": auth}
    return url, headers


def load_watchlist():
    with open(WATCHLIST, "r", encoding="utf-8") as f:
        return json.load(f)


def manifest_path(today):
    return os.path.join(TASKS_DIR, f"{today}.json")


def load_manifest(today):
    p = manifest_path(today)
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"date": today, "tasks": []}


def save_manifest(m):
    os.makedirs(TASKS_DIR, exist_ok=True)
    with open(manifest_path(m["date"]), "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=2)


async def _call_tool(session, name, args, attempts=3):
    from mcp.types import CallToolResult  # noqa: F401

    last = None
    for i in range(attempts):
        try:
            res = await session.call_tool(name, args)
            text = ""
            if getattr(res, "content", None):
                parts = []
                for c in res.content:
                    parts.append(getattr(c, "text", "") or "")
                text = "".join(parts)
            return text
        except Exception as e:  # noqa: BLE001
            last = e
            await asyncio.sleep(2 * (i + 1))
    raise RuntimeError(f"call_tool {name} 失败: {last}")


def _parse_json(text):
    text = (text or "").strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
        return {"_raw": text[:500]}


async def do_submit(depth, limit=None, codes=None):
    url, headers = load_mcp_conn()
    wl = load_watchlist()
    if codes:
        code_set = set(c.strip() for c in codes.split(",") if c.strip())
        wl = [w for w in wl if w["code"] in code_set]
        if not wl:
            print(f"警告: 指定代码 {codes} 均不在自选池内，无任务可提交")
    today = datetime.now().strftime("%Y-%m-%d")
    manifest = load_manifest(today)
    have = {t["code"] for t in manifest["tasks"]}
    todo = [w for w in wl if w["code"] not in have]
    if limit:
        todo = todo[:limit]
    if not todo:
        print("无可提交的新任务（全部已提交过）")
        return manifest

    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client

    print(f"连接 {url} ...")
    async with streamablehttp_client(url, headers=headers) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("连接成功，开始提交分析任务 ...")
            for w in todo:
                code, name = w["code"], w["name"]
                try:
                    text = await _call_tool(
                        session, "analyze_stock",
                        {"symbol": code, "market_type": "A股", "research_depth": depth},
                    )
                    r = _parse_json(text)
                    task_id = r.get("task_id", "")
                    st = r.get("status", "submitted")
                    if not task_id:
                        print(f"[WARN] {code} {name}: 未返回 task_id: {text[:200]}")
                        manifest["tasks"].append(
                            {"code": code, "name": name, "symbol": w.get("symbol", code), "task_id": "", "status": "failed",
                             "note": "no task_id", "updated": datetime.now().strftime("%H:%M:%S")}
                        )
                    else:
                        print(f"[提交] {code} {name} -> {task_id} ({st})")
                        manifest["tasks"].append(
                            {"code": code, "name": name, "symbol": w.get("symbol", code), "task_id": task_id, "status": st,
                             "note": "", "updated": datetime.now().strftime("%H:%M:%S")}
                        )
                    save_manifest(manifest)
                except Exception as e:  # noqa: BLE001
                    print(f"[ERR] {code} {name}: {e}")
                    manifest["tasks"].append(
                        {"code": code, "name": name, "symbol": w.get("symbol", code), "task_id": "", "status": "failed",
                         "note": str(e)[:200], "updated": datetime.now().strftime("%H:%M:%S")}
                    )
                    save_manifest(manifest)
    return manifest


ACTIVE_STATES = ("submitted", "pending", "processing", "running", "queued", "")


async def do_status(date=None):
    url, headers = load_mcp_conn()
    today = date or datetime.now().strftime("%Y-%m-%d")
    manifest = load_manifest(today)
    active = [t for t in manifest["tasks"] if t.get("task_id") and t.get("status") in ACTIVE_STATES]
    if not active:
        print("无进行中任务")
        return manifest
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client

    print(f"轮询 {len(active)} 个进行中任务 ...")
    async with streamablehttp_client(url, headers=headers) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for t in active:
                try:
                    text = await _call_tool(session, "get_analysis_status", {"task_id": t["task_id"]}, attempts=2)
                    r = _parse_json(text)
                    st = r.get("status", t.get("status"))
                    t["status"] = st
                    t["updated"] = datetime.now().strftime("%H:%M:%S")
                    t["note"] = str(r.get("message", ""))[:200]
                    print(f"[状态] {t['code']} {t['name']}: {st}")
                except Exception as e:  # noqa: BLE001
                    print(f"[ERR] {t['code']} {t['name']}: {e}")
            save_manifest(manifest)
    return manifest


def _report_filename(symbol, date):
    """报告文件名规则：<代码>.SH_YYYYMMDD.md（用户约定格式）"""
    return f"{symbol}_{date}.md"


async def do_collect(date=None):
    url, headers = load_mcp_conn()
    target = date or datetime.now().strftime("%Y-%m-%d")
    manifest = load_manifest(target)
    done = [t for t in manifest["tasks"] if t.get("task_id") and t.get("status") == "completed"]
    if not done:
        print("无已完成任务")
        return manifest
    out_dir = os.path.join(REPORT_DIR, target)
    os.makedirs(out_dir, exist_ok=True)
    symbol_map = {w["code"]: w.get("symbol", w["code"]) for w in load_watchlist()}

    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client

    print(f"拉取 {len(done)} 份报告 ...")
    async with streamablehttp_client(url, headers=headers) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for t in done:
                if t.get("saved"):
                    continue
                try:
                    text = await _call_tool(session, "get_analysis_result", {"task_id": t["task_id"]}, attempts=2)
                    symbol = t.get("symbol") or symbol_map.get(t["code"], t["code"])
                    fname = _report_filename(symbol, target)
                    with open(os.path.join(out_dir, fname), "w", encoding="utf-8") as f:
                        f.write(f"# {t['code']} {t['name']} · 多智能体分析报告\n\n")
                        f.write(f"> 生成日期 {target} | task_id {t['task_id']} | 来源 tradingagents-mcp\n\n")
                        f.write(text)
                    t["saved"] = fname
                    t["updated"] = datetime.now().strftime("%H:%M:%S")
                    print(f"[报告] {fname} 已保存 ({len(text)} 字)")
                    save_manifest(manifest)
                except Exception as e:  # noqa: BLE001
                    print(f"[ERR] {t['code']} {t['name']}: {e}")
            save_manifest(manifest)
    return manifest


def write_index(manifest):
    os.makedirs(REPORT_DIR, exist_ok=True)
    date = manifest["date"]
    tasks = manifest["tasks"]
    lines = [
        "# trading-agents 分析报告索引",
        "",
        f"最新批次: {date}（供下一交易日决策参考）",
        "",
        "| 代码 | 名称 | 状态 | 报告文件 |",
        "|------|------|------|----------|",
    ]
    for t in tasks:
        fname = t.get("saved", "")
        lines.append(
            f"| {t['code']} | {t['name']} | {t.get('status', '')} | "
            f"{f'{date}/{fname}' if fname else '—'} |"
        )
    idx_path = os.path.join(REPORT_DIR, "index.md")
    with open(idx_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"索引已更新: {idx_path}")


def _extract_report_summary(path):
    """从完整报告抽取 决策/风险等级/摘要/投资建议 段（纯脚本，不消耗 LLM tokens）。"""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    out = []
    for ln in text.splitlines()[:12]:
        s = ln.strip()
        if (
            s.startswith("# ")
            or s.startswith("股票:")
            or s.startswith("分析日期:")
            or s.startswith("决策:")
            or s.startswith("风险等级:")
        ):
            out.append(s)

    def _seg(pattern, cap):
        m = re.search(pattern, text, re.S)
        if not m:
            return None
        seg = m.group(1).strip()
        if len(seg) > cap:
            seg = seg[:cap] + "…（截断）"
        return seg

    seg = _seg(r"## 摘要\s*\n(.*?)(?=\n## |\Z)", 600)
    if seg:
        out.append("## 摘要")
        out.append(seg)
    seg2 = _seg(r"## 投资建议\s*\n(.*?)(?=\n## |\Z)", 400)
    if seg2:
        out.append("## 投资建议")
        out.append(seg2)
    if len(out) <= 1:
        return None
    return "\n".join(out)


def write_summary(manifest):
    """从批次已保存报告抽取摘要/结论，生成 <批次>/summary.md（供决策班次快速浏览，勿逐份读全文）。"""
    date = manifest["date"]
    out_dir = os.path.join(REPORT_DIR, date)
    if not os.path.isdir(out_dir):
        print(f"批次目录不存在: {out_dir}")
        return
    files = sorted(f for f in os.listdir(out_dir) if f.endswith(".md") and f != "summary.md")
    if not files:
        print(f"批次 {date} 无已保存报告，跳过 summary 生成")
        return
    lines = [
        "# trading-agents 分析摘要（脚本自动生成，勿手改）",
        "",
        f"> 批次 {date} | 仅含已保存报告的个股 | 完整报告见同目录 .md 文件",
        "",
    ]
    for f in files:
        summ = _extract_report_summary(os.path.join(out_dir, f))
        if not summ:
            continue
        lines.append("---")
        lines.append("")
        lines.append(summ)
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("> 本摘要由 scripts/tradingagents_runner.py 从完整报告自动抽取（决策/风险等级/摘要/投资建议段），"
                 "供决策班次快速浏览；第三方观点仅供参考，决策仍以 SOUL.md 框架与 STRATEGY.md 规则为准。")
    sp = os.path.join(out_dir, "summary.md")
    with open(sp, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"摘要已生成: {sp} ({os.path.getsize(sp)} 字节)")


async def do_run(depth, max_minutes, limit, codes=None):
    deadline = time.time() + max_minutes * 60
    manifest = await do_submit(depth, limit=limit, codes=codes)
    while True:
        await asyncio.sleep(POLL_INTERVAL)
        manifest = await do_status()
        active = [t for t in manifest["tasks"] if t.get("status") in ACTIVE_STATES]
        if not active:
            break
        if time.time() > deadline:
            print(f"[超时] 达到 {max_minutes} 分钟上限，仍有 {len(active)} 个进行中，先收已完成的。")
            break
    manifest = await do_collect()
    write_index(manifest)
    write_summary(manifest)
    total = len(manifest["tasks"])
    ok = sum(1 for t in manifest["tasks"] if t.get("saved"))
    failed = sum(1 for t in manifest["tasks"] if t.get("status") == "failed")
    processing = sum(1 for t in manifest["tasks"] if t.get("status") in ACTIVE_STATES)
    print(f"== 汇总: 共{total}只 | 报告已保存{ok} | 失败{failed} | 进行中{processing} ==")
    return manifest


def main():
    p = argparse.ArgumentParser(description="tradingagents 多智能体分析执行器")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="提交→轮询→拉取 全流程")
    r.add_argument("--depth", default="标准")
    r.add_argument("--max-minutes", type=int, default=DEFAULT_MAX_MINUTES)
    r.add_argument("--limit", type=int, default=None, help="仅处理前N只（测试用）")
    r.add_argument("--codes", default=None, help="逗号分隔代码子集（如 600036,601398）")
    s1 = sub.add_parser("submit", help="仅提交（写任务清单）")
    s1.add_argument("--depth", default="标准")
    s1.add_argument("--codes", default=None, help="逗号分隔代码子集（如 600036,601398）")
    s2 = sub.add_parser("status", help="仅轮询更新状态")
    s2.add_argument("--once", action="store_true")
    s2.add_argument("--date", default=None, help="任务清单日期 YYYY-MM-DD（默认今天）")
    s3 = sub.add_parser("collect", help="仅拉取已完成报告")
    s3.add_argument("--date", default=None, help="任务清单日期 YYYY-MM-DD（默认今天）")
    s4 = sub.add_parser("summary", help="仅为指定批次重新生成 summary.md（需 --date）")
    s4.add_argument("--date", default=None, help="批次日期 YYYY-MM-DD（默认今天）")
    args = p.parse_args()

    if args.cmd == "run":
        asyncio.run(do_run(args.depth, args.max_minutes, args.limit, args.codes))
    elif args.cmd == "submit":
        m = asyncio.run(do_submit(args.depth, codes=args.codes))
        write_index(m)
    elif args.cmd == "status":
        m = asyncio.run(do_status(date=args.date))
        write_index(m)
    elif args.cmd == "collect":
        m = asyncio.run(do_collect(date=args.date))
        write_index(m)
        write_summary(m)
    elif args.cmd == "summary":
        date = args.date or datetime.now().strftime("%Y-%m-%d")
        write_summary(load_manifest(date))


if __name__ == "__main__":
    main()
