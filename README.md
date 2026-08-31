# 何价值 · 全自动交易系统

A股价值投资全自动交易机器人。以 SOUL.md 为宪法、STRATEGY.md 为策略手册、AGENTS.md 为操作协议，
通过 Hermes cron 定时任务 + 同花顺 iFinD 数据 MCP + QMT 交易 MCP 实现"数据采集 → 五层分析 → 信号生成 → 风控校验 → 自动下单 → 复盘改进"的完整闭环。

**目标**：账户年化稳定盈利 8%~12%。**底线**：严守 SOUL.md 全部纪律，宁可错过，不可做错。

## 目录结构
```
ai_agent_qmt_project/
├── AGENTS.md          # 操作协议（cron 会话自动注入）
├── STRATEGY.md        # 策略手册（行业专项估值规则、买卖区间判定、数据附录）
├── CONFIG.json        # 运行时配置（auto_execute 开关、仓位上限等）
├── watchlist.json     # 自选池 24 只
├── STOP               # （手动创建）紧急停止开关：存在即全系统禁止下单
├── scripts/
│   ├── journal.py     # 交易流水 / 每日账户快照记账
│   ├── preflight.py   # 下单前代码级预检闸门（白名单/整手/单笔5%/单日10%累计/STOP）
│   └── plans/         # 当日预算台账（预检自动生成，晨间/午后班共享）
├── logs/              # trades.csv（交易流水）、pnl_daily.csv（每日快照）
├── report/            # 复盘报告：decision/ daily/ weekly/ monthly/ quarterly/ annual/ + improvements_log.md
└── robot/             # 遗留脚手架（已废弃，仅 plan.py/mcp_client.py 作工具参考）
```

## 自动化任务（Hermes cron）
| 任务 | 调度 | 职责 |
|------|------|------|
| trading-morning-decision | 工作日 09:40 | 宏观定仓位带 → 自选池信号 → 风控 → 预检 → 按 auto_execute 下单 → report/decision/*_morning.md |
| trading-afternoon-decision | 工作日 13:10 | 午后复查班：识别午后异动、与晨间共享单日预算 → report/decision/*_afternoon.md |
| trading-daily-review | 工作日 15:15 | 收盘复盘：执行偏差、委托核对、结果归因、改进项 → report/daily/ |
| trading-agents-analysis | 每月1、15日 01:00 | 双周多智能体分析（标准深度）：24只自选股分析报告+summary摘要 → report/trading-agents/（供各决策班参考；击球区/警戒区个股由晨间/午后班按需定向补充） |
| trading-weekly-review | 每周六 10:00 | 周复盘：信号命中率、宏观回测、参数建议 → report/weekly/ |
| trading-monthly-review | 每月1日 10:30 | 月复盘：收益 vs 年化目标拆解、纪律审计 → report/monthly/ |
| trading-quarterly-review | 1/4/7/10月1日 11:00 | 季复盘：业绩归因、策略有效性 → report/quarterly/ |
| trading-annual-review | 每年1月1日 11:30 | 年复盘：全年收益/回撤/教训/策略升级 → report/annual/ |

## 上线流程
1. **dry-run 验证**（当前状态）：`CONFIG.json` 中 `auto_execute: false`，任务只生成拟交易清单与报告，不下单。
2. **人工验收**：检查日报、复盘报告质量与信号合理性。
3. **实盘启用**：用户确认后将 `auto_execute` 置 `true`，系统开始真实下单。

## 风控红线（代码即纪律，cron 会话必须逐条校验）
- 仅限自选池24只；医疗医药/食品/种植养殖永不触碰
- 银行≤60%、其他行业≤20%、单票≤10%、现金≥10%（占总资产）
- 单日买入≤总资产10%（由 preflight.py 代码级强制，晨间+午后共享台账）、单次≤5%；强周期股（中远海控/中信证券）严禁 DCF
- 下单必经三段式：写计划 JSON → preflight 预检 PASS → place_order（跳过预检=违规）
- STOP 文件存在 = 全系统只读，禁止一切下单（用户手动创建即刹车）
- 数据不足或 QMT 未连接 → 跳过交易，如实报告，绝不臆造
