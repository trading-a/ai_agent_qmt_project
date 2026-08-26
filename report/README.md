# report/ — 复盘报告目录

系统自动生成的复盘报告统一存放于此，按周期分子目录：

| 类别 | 路径 | 触发 |
|------|------|------|
| 决策执行（晨间班） | `decision/YYYYMMDD_morning.md` | 每个工作日 09:40 |
| 决策执行（午后班） | `decision/YYYYMMDD_afternoon.md` | 每个工作日 13:10 |
| 日复盘 | `daily/YYYYMMDD.md` | 每个交易日 15:15（收盘后） |
| 多智能体分析 | `trading-agents/YYYYMMDD/<代码>.SH_YYYYMMDD.md` + `index.md` | 每个交易日 19:00（供次日决策参考） |
| 周复盘 | `weekly/YYYY-Www.md` | 每周六 10:00 |
| 月复盘 | `monthly/YYYYMM.md` | 每月1日 10:30 |
| 季复盘 | `quarterly/YYYY-Qn.md` | 每季首月1日 11:00 |
| 年复盘 | `annual/YYYY.md` | 每年1月1日 11:30 |
| 改进台账 | `improvements_log.md` | 任何复盘产生改进项时追加 |

每份报告必须包含：**复盘（事实）→ 反思（归因）→ 改进（可执行）→ 闭环（入台账）**。
决策执行报告（decision/）以执行记录为主：信号清单、成交明细、风控校验、账户快照。
