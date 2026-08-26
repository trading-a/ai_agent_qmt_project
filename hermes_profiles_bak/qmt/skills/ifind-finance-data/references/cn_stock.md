## 股票服务工具 (server_type="stock")

| 工具名称 | 功能说明 | 典型参数 |
|---------|---------|---------|
| `search_stocks` | 智能选股 | `{"query": "自然语言选股条件"}` 如 `"电子行业市值大于100亿"` |
| `get_stock_summary` | 股票信息摘要 | `{"query": "股票简称+查询内容"}` 如 `"茅台财务状况"` |
| `get_stock_info` | 股票基本资料 | `{"query": "股票简称+指标名称+时间"}` 如 `"格力电器上市时间"` |
| `get_stock_performance` | 股票日频行情与技术指标 | `{"query": "股票简称+指标名称+时间"}` 如 `"三花智控近5日涨跌幅"` |
| `get_stock_shareholders` | 股本结构与股东数据 | `{"query": "股票简称+指标"}` 如 `"光明乳业流通股占比"` |
| `get_stock_financials` | 财务数据与指标 | `{"query": "股票简称+财务指标+财报日期"}` 如 `"科大讯飞2025年三季度的ROE"` |
| `get_risk_indicators` | 风险定量指标 | `{"query": "股票+时间+指标"}` 如 `"航天电子在2026-03-19的夏普比率"` |
| `get_stock_events` | 上市公司重大事件类指标 | `{"query": "股票+事件相关指标"}` 如 `"摩尔线程IPO首发股本数量"` |
| `get_esg_data` | ESG评级数据 | `{"query": "股票+ESG评级指标"}` 如 `"诚意药业中诚信ESG评级"` |
| `stock_highfreq_quotes` | A股股票行情数据的实时快照与高频序列 | `{"symbols": "300033.SZ,300059,贵州茅台", "indicators": "开盘价,最高价,最低价,收盘价,涨跌幅,成交量", "data_mode": "highfreq", "interval": 1}` |

### 特别提示
- `get_stock_events` 工具是 `公告事件相关结构化指标` 查询工具，而非事件描述文本甚至公告原文查询工具，例如该工具支持上市公司在配股和并购事件中涉及的 `配股价格` 和 `并购标的` 等指标搜索，但不支持 `配股事件介绍` 和 `并购事件公告` 的文本内容搜索，如需获取文本请采用资讯/公告搜索工具。

### 脚本调用示例

```javascript
const { call } = require('./call-node.js');

async function main() {
    const result = await call("stock", "search_stocks", {
        query: "电子行业市值排名前20的股票"
    });
    console.log(JSON.stringify(result, null, 2));
}

main().catch(console.error);
```

```python
from call import call

result = call("stock", "search_stocks", {"query": "电子行业市值排名前20的股票"})
print(result)
```

### 选股查询示例

```python
# 智能选股
call("stock", "search_stocks", {"query": "汽车零部件行业市值大于1000亿的股票"})

# 多主体、多指标合并查询
call("stock", "get_stock_financials", {
    "query": "同花顺、东方财富、大智慧、恒生电子的2025-09-30的净利润增速、ROE、ROA"
})

# 以行业板块作为股票主体查询
call("stock", "get_stock_performance", {"query": "锂电池行业股票的今日涨跌幅"})

# A股股票1分钟高频行情
call("stock", "stock_highfreq_quotes", {
    "symbols": "300033.SZ,300059,贵州茅台",
    "indicators": "开盘价,最高价,最低价,收盘价,涨跌幅,成交量",
    "data_mode": "highfreq",
    "interval": 1
})

# A股股票最新实时快照
call("stock", "stock_highfreq_quotes", {
    "symbols": "贵州茅台",
    "indicators": "最新价,涨跌幅,成交量,成交额",
    "data_mode": "real_time"
})
```
