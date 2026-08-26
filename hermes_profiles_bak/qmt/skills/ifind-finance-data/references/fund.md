## 基金服务工具 (server_type="fund")

| 工具名称 | 功能说明 | 典型参数 |
|---------|---------|---------|
| `search_funds` | 基金搜索 | `{"query": "模糊基金名称或选基需求"}` 如 `"南方基金新能源ETF"` |
| `get_fund_profile` | 基金基本资料 | `{"query": "基金名称+指标"}` 如 `"工银双盈债券A(010068)的发行日期与发行费率"` |
| `get_fund_market_performance` | 基金行情与业绩 | `{"query": "基金名称+时间范围+指标"}` 如 `"方正富邦策略精选A(010072)在近一月收益率"` |
| `get_fund_ownership` | 基金份额与持有人 | `{"query": "基金名称+日期+指标"}` 如 `"湘财长弘灵活配置混合A(010076)在2025-06-30的申购总份额和赎回总份额"` |
| `get_fund_portfolio` | 基金持仓明细 | `{"query": "基金名称+日期+指标"}` 如 `"工银优质成长混合A(010088)在2025-06-30披露报告中的股票投资占比"` |
| `get_fund_financials` | 基金财务指标 | `{"query": "基金名称+日期+指标"}` 如 `"泰康浩泽混合A(010081)在2025-06-30的利润"` |
| `get_fund_company_info` | 基金公司信息 | `{"query": "基金名称+所属基金公司维度指标"}` 如 `"蜂巢丰瑞债券A的所属基金公司基金经理数量"` |
| `fund_highfreq_quotes` | 中国公募基金行情数据的实时快照与高频序列 | `{"symbols": "000307.OF,516850,易方达蓝筹精选混合", "indicators": "最新价,IOPV净值估值,振幅,折价", "data_mode": "real_time"}` |

### 使用技巧

- 1.关于基金公司数据指标的查询: 基金数据查询工具实际上接受的是以"具体基金产品"为主语的数据指标查询，暂不兼容以"基金公司"为主语的查询，故此类问句主语需做转换，将`基金公司指标`转变为`某基金所属基金管理人的指标`，例如: {"原问句":"易方达的基金经理数量" , "转换后":"易方达蓝筹精选基金的基金管理人旗下基金经理数量"}

### 脚本调用示例

```javascript
const { call } = require('./call-node.js');

async function main() {
    const result = await call("fund", "search_funds", {
        query: "易方达蓝筹精选混合的基金净值和近一月收益率"
    });
    console.log(JSON.stringify(result, null, 2));
}

main().catch(console.error);
```

```python
from call import call

result = call("fund", "search_funds", {"query": "南方基金的新能源ETF"})
print(result)
```

### 基金高频实时行情示例

```python
# 基金最新实时快照
call("fund", "fund_highfreq_quotes", {
    "symbols": "000307.OF,516850,易方达蓝筹精选混合",
    "indicators": "最新价,IOPV净值估值,振幅,折价",
    "data_mode": "real_time"
})

# 基金1分钟高频行情
call("fund", "fund_highfreq_quotes", {
    "symbols": "516850",
    "indicators": "开盘价,最高价,最低价,收盘价,成交量",
    "data_mode": "highfreq",
    "interval": 1
})
```

