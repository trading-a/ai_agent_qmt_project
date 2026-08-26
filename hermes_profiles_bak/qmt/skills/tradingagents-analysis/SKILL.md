---
name: tradingagents-analysis
description: 使用 MCP 提交并跟进股票多智能体分析（analyze_stock → get_analysis_status → get_analysis_result）
---

# 股票多智能体分析（MCP）

通过已配置的 MCP 服务（tradingagents）对 A 股/港股/美股执行多智能体分析。

## 前置条件
- MCP 服务器已连接（url + Bearer Token），凭据由连接携带。

## 三步异步流程
分析是**异步**的，请严格按以下三步执行：

### 第 1 步：提交分析
调用工具 `analyze_stock`：
- `symbol`（必填）：股票代码。A股 6 位数字（如 `601398`）；港股加 `.HK`（如 `00700.HK`）；美股字母代码（如 `AAPL`）。
- `market_type`：`A股` / `港股` / `美股`（默认 `A股`）。
- `research_depth`：`快速` / `基础` / `标准` / `深度` / `全面`（默认 `标准`）。
- 可选：`quick_analysis_model`、`deep_analysis_model`、`language`、`custom_prompt`。
- **返回**：立即返回 `{"task_id": "...", "status": "submitted", "symbol": "...", "message": "..."}`，**不会阻塞等待**。

### 第 2 步：轮询状态
用返回的 `task_id` 调用 `get_analysis_status(task_id)`：
- `status` 为 `pending` / `processing` 时继续轮询（建议间隔 5-10 秒，并向用户说明需等待数分钟）。
- `status` 为 `completed` / `failed` / `cancelled` 时停止。

### 第 3 步：获取报告
当状态为 `completed` 后，调用 `get_analysis_result(task_id)` 获取完整报告（含摘要、投资建议、决策、各分析师报告全文）。

## 完整示例
用户："分析一下工商银行"
1. `analyze_stock(symbol="601398", market_type="A股", research_depth="标准")` → `{"task_id": "abc...", "status": "submitted", ...}`
2. 轮询 `get_analysis_status(task_id="abc...")` 数次，直至 `completed`。
3. `get_analysis_result(task_id="abc...")` → 完整报告，向用户呈现摘要与决策。

## 排障
- 返回 `401` / `Invalid token`：MCP 连接中的 Token 无效或已吊销，请更换。
- `status` 长期 `processing`：向用户说明分析耗时数分钟，可稍后再查。
- 返回"提交分析失败"：检查参数是否符合约定（如 symbol 格式）。
