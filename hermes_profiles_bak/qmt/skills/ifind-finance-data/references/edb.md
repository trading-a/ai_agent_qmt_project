## 宏观经济/行业经济指标服务 (server_type="edb")

- 宏观行业经济指标支持"先搜索再取数"，当你不明确具体指标时，可以先发起搜索请求，再结合用户需求选择具体指标查询

| 工具名称 | 功能说明 | 典型参数 |
|---------|---------|---------|
| `search_edb` | 指标搜索 | `{"query": "行业/产品/指标描述"}` 如 `"光模块产业链相关指标"` |
| `get_edb_data` | 指标数据查询 | `{"query": "指标名称+时间范围"}` 如 `"光伏电池产量202301-202506"` |

### 脚本调用示例

```javascript
const { call } = require('./call-node.js');

async function main() {
    const result = await call("edb", "get_edb_data", {
        query: "光伏电池产量当月值（202301-202506）"
    });
    console.log(JSON.stringify(result, null, 2));
}

main().catch(console.error);
```

```python
from call import call

result = call("edb", "get_edb_data", {"query": "光伏电池产量当月值（202301-202506）"})
print(result)
```

### EDB查询示例

```python
# 搜索可能的指标
call("edb", "search_edb", {"query": "新能源汽车产量相关指标"})

# 获取具体数据
call("edb", "get_edb_data", {"query": "新能源汽车产量当月值（202301-202506）"})
```
