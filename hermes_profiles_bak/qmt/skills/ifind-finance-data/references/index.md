## 指数板块服务工具 (server_type="index")

| 工具名称 | 功能说明 | 典型参数 |
|---------|---------|---------|
| `index_data` | 指数行情、技术指标与估值指标 | `{"query": "指数名称+时间+指标"}` 如 `"沪深300、中证2000过去10个交易日的涨跌幅和收盘点数"` |
| `sector_data` | 板块行情、财务分析与成分股指标 | `{"query": "板块名称+时间+指标"}` 如 `"医疗设备板块(中证行业)的成分股个数及过去5个交易日的成分股平均涨跌幅"` |
| `index_highfreq_quotes` | 指数行情数据的实时快照与高频序列 | `{"symbols": "000001.SH,000941,创业板指", "indicators": "最高价,最新价,涨跌幅,上涨家数", "data_mode": "real_time"}` |

### 脚本调用示例

```javascript
const { call, listTools } = require('./call-node.js');

async function main() {
    const result = await call("index", "index_data", {
        query: "沪深300过去10个交易日的涨跌幅和收盘点数"
    });
    console.log(JSON.stringify(result, null, 2));

    // 工具缺失或名称疑似变更时，再查看当前可用工具列表
    const tools = await listTools("index");
    console.log(JSON.stringify(tools, null, 2));
}

main().catch(console.error);
```

```python
from call import call, list_tools

result = call("index", "index_data", {"query": "沪深300过去10个交易日的涨跌幅和收盘点数"})
print(result)

# 工具缺失或名称疑似变更时，再查看当前可用工具列表
tools = list_tools("index")
print(tools)
```

### 指数板块查询示例

```python
# 指数数据查询
call("index", "index_data", {"query": "沪深300、中证2000过去10个交易日的涨跌幅和收盘点数"})

# 板块数据查询
call("index", "sector_data", {"query": "医疗设备板块(中证行业)的成分股个数及过去5个交易日的成分股平均涨跌幅"})

# 指数最新实时快照
call("index", "index_highfreq_quotes", {
    "symbols": "000001.SH,000941,创业板指",
    "indicators": "最高价,最新价,涨跌幅,上涨家数",
    "data_mode": "real_time"
})

# 指数1分钟高频行情
call("index", "index_highfreq_quotes", {
    "symbols": "创业板指",
    "indicators": "开盘价,最高价,最低价,收盘价,日内累积涨跌幅",
    "data_mode": "highfreq",
    "interval": 1
})
```
