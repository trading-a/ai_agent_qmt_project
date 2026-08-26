---
name: tradingagents-reports
description: 查询用户分析历史与按日期获取完整报告（list_analysis_history / list_reports_by_date / get_analysis_result）
---

# 分析历史与报告查询（MCP）

查询当前用户的历史分析任务与按日期获取完整分析报告。

## 前置条件
- MCP 服务器已连接（url + Bearer Token）。

## 工具用法

### list_analysis_history
列出当前用户的历史分析任务。
- `status`（可选）：`pending` / `processing` / `completed` / `failed` / `cancelled`。
- `symbol`（可选）：按股票代码过滤。
- `page` / `page_size`（可选，默认 1 / 20）。
- 返回任务列表（含 task_id、symbol、status、时间）。

### list_reports_by_date
按日期查询某一天生成的所有分析报告（**含完整全文**）。
- `date`（必填）：`YYYY-MM-DD` 格式。
- `page` / `page_size`（可选，默认 1 / 10）。报告正文可能很大，如需精简请调小 page_size。
- 返回该日报告列表，每份含完整报告全文。

### get_analysis_result
用 `task_id` 获取指定任务的完整报告（在历史/日期查询中拿到 task_id 后使用）。

## 示例
用户："我昨天有哪些分析报告？"
1. 计算"昨天"的日期（如 `2026-08-09`）。
2. `list_reports_by_date(date="2026-08-09")` → 该日报告列表。
3. 向用户摘要每份报告的股票与结论；如需某份全文，用其 task_id 调 `get_analysis_result`。

## 注意
- 报告正文可能很大，注意控制返回大小（可调小 page_size 或用 get_analysis_result 单份获取）。
