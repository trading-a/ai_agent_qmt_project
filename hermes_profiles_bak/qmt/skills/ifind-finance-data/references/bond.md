## 债券服务工具 (server_type="bond")

| 工具名称 | 功能说明 | 典型参数 |
|---------|---------|---------|
| `bond_basic_info` | 债券基本信息与发债主体资料 | `{"query": "债券简称/代码+查询内容"}` 如 `"23广东11的发行期限与发行总额"` |
| `bond_market_data` | 债券行情数据与估值分析 | `{"query": "债券简称/代码+指标+时间"}` 如 `"26国债01近五日收盘价、涨跌幅与最新久期、凸性"` |
| `bond_financial_data` | 债券发债主体财务数据与指标 | `{"query": "债券简称/代码+时间+指标"}` 如 `"24辽港01、24皮城01在20251231的资产负债率和ROE"` |
| `bond_special_data` | 债券特殊指标（信用债评级、回购、可转债条款等） | `{"query": "债券简称/代码+指标"}` 如 `"华海转债、南航转债的最新转股价格及转换比例"` |
| `bond_highfreq_quotes` | 债券行情数据的实时快照与高频序列 | `{"symbols": "240025.IB,199222,大连2521", "indicators": "开盘价,最高价,最低价,收盘价,成交量", "data_mode": "highfreq", "interval": 1}` |

### 脚本调用示例

```javascript
const { call, listTools } = require('./call-node.js');

async function main() {
    const result = await call("bond", "bond_basic_info", {
        query: "23广东11的发行期限与发行总额"
    });
    console.log(JSON.stringify(result, null, 2));

    // 工具缺失或名称疑似变更时，再查看当前可用工具列表
    const tools = await listTools("bond");
    console.log(JSON.stringify(tools, null, 2));
}

main().catch(console.error);
```

```python
from call import call, list_tools

result = call("bond", "bond_basic_info", {"query": "23广东11的发行期限与发行总额"})
print(result)

# 工具缺失或名称疑似变更时，再查看当前可用工具列表
tools = list_tools("bond")
print(tools)
```

### 债券查询示例

```python
# 债券基本信息
call("bond", "bond_basic_info", {"query": "23广东11、19黑龙江债01的发行期限与发行总额"})

# 债券行情与估值
call("bond", "bond_market_data", {"query": "26国债01近五日收盘价、涨跌幅与最新久期、凸性"})

# 发债主体财务数据
call("bond", "bond_financial_data", {"query": "24辽港01、24皮城01在20251231的资产负债率和ROE"})

# 可转债特殊指标
call("bond", "bond_special_data", {"query": "华海转债、南航转债的最新转股价格及转换比例"})

# 债券1分钟高频行情
call("bond", "bond_highfreq_quotes", {
    "symbols": "240025.IB,199222,大连2521",
    "indicators": "开盘价,最高价,最低价,收盘价,成交量",
    "data_mode": "highfreq",
    "interval": 1
})

# 债券最新实时快照
call("bond", "bond_highfreq_quotes", {
    "symbols": "24附息国债25",
    "indicators": "最新价,现手,振幅,最新成交价",
    "data_mode": "real_time"
})
```
