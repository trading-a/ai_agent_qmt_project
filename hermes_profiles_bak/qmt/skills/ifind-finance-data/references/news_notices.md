## 新闻公告服务 (server_type="news")

- 新闻公告服务内置语义检索能力，支持输入需要查询的内容，返回相关段落，而非公告全文
- 热点事件查询工具注重时效性，参数限制不宜过多，否则容易无结果，没有结果时可尝试放宽限制，或选择资讯搜索
- query 字段支持同时输入报告元数据要求及查询内容，如{"query":"有研新材2024年年度报告 固态电池技术相关"}

| 工具名称 | 功能说明 | 典型参数 |
|---------|---------|---------|
| `search_news` | 新闻资讯语义检索 | `{"query": "内容", "time_start": "开始日期", "time_end": "结束日期", "size": 数量}` |
| `search_notice` | 公告语义检索 | `{"query": "内容", "time_start": "开始日期", "time_end": "结束日期", "size": 数量}` |
| `search_trending_news` | 热点事件资讯查询 | `{"keyword": "关键词", "industry_name": "行业", "time_scope": "时效范围", "size": 数量}` |

### 脚本调用示例

```javascript
const { call } = require('./call-node.js');

async function main() {
    const result = await call("news", "search_news", {
        query: "人工智能行业动态",
        time_start: "2025-01-01",
        time_end: "2026-01-01",
        size: 5
    });
    console.log(JSON.stringify(result, null, 2));
}

main().catch(console.error);
```

```python
from call import call

result = call("news", "search_news", {
    "query": "人工智能行业动态",
    "time_start": "2025-01-01",
    "time_end": "2026-01-01",
    "size": 5
})
print(result)
```

### 新闻查询示例

```python
# 财经新闻
call("news", "search_news", {
    "query": "脑机接口技术最新进展",
    "time_start": "2025-01-01",
    "time_end": "2026-01-01",
    "size": 5
})

# 上市公司公告
call("news", "search_notice", {
    "query": "光迅科技2024年度报告 光模块技术",
    "time_start": "2025-01-01",
    "time_end": "2026-01-01",
    "size": 5
})

# 热点事件
call("news", "search_trending_news", {
    "keyword": "智能体",
    "industry_name": "计算机",
    "time_scope": "24小时",
    "size": 5
})
```
