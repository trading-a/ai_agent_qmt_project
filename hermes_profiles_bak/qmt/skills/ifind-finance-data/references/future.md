## 期货期权服务工具 (server_type="future")

| 工具名称 | 功能说明 | 典型参数 |
|---------|---------|---------|
| `future_profile` | 期货期权合约基本资料查询，含期货合约基本信息、期货合约标的基本信息 | `{"query": "合约名称+查询内容"}` 如 `"螺纹钢主力连续的涨跌幅限制和保证金率"` |
| `future_quotes` | 期货期权行情数据查询，含日频行情指标（涨跌幅、基差率、升贴水率、波动率等）、行情衍生技术指标与技术形态、期货持仓指标（多空持仓量、持仓占比等） | `{"query": "合约名称+指标名称+时间"}` 如 `"橡胶连续、20号胶连续在2026-04-15的基差率、升贴水率"` |

### 脚本调用示例

```javascript
const { call } = require('./call-node.js');

async function main() {
    const result = await call("future", "future_profile", {
        query: "螺纹钢主力连续的涨跌幅限制和保证金率"
    });
    console.log(JSON.stringify(result, null, 2));
}

main().catch(console.error);
```

```python
from call import call

result = call("future", "future_profile", {"query": "螺纹钢2605的涨跌幅限制和保证金率"})
print(result)
```

### 期货期权查询示例

```python
# 期货合约基本资料查询
call("future", "future_profile", {"query": "螺纹钢2605的涨跌幅限制和保证金率"})

# 多主体、多指标合并查询日频行情
call("future", "future_quotes", {
    "query": "橡胶连续、20号胶连续在2026-04-15的基差率、升贴水率"
})

# 期货持仓指标查询
call("future", "future_quotes", {"query": "沪铜主力合约近5日的多空持仓量、持仓占比"})

# 行情衍生技术指标查询
call("future", "future_quotes", {"query": "原油主力合约近20日的MACD、RSI"})
```
