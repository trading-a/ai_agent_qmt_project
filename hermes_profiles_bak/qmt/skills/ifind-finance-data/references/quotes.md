# 高频实时行情工具统一说明

- 高频实时行情工具用于查询交易日日内的实时快照或高频时间序列
- 当前支持 `stock`、`fund`、`bond`、`index` 四个服务
- 工具名分别为 `stock_highfreq_quotes`、`fund_highfreq_quotes`、`bond_highfreq_quotes`、`index_highfreq_quotes`
- 高频实时行情工具使用结构化参数，不使用 `query` 字段
- 必填参数为 `symbols`、`indicators`、`data_mode`；`data_mode` 必须显式传入 `real_time` 或 `highfreq`，不可省略；
- 当 `data_mode` 为 `highfreq` 时，可传 `interval` 指定 1/3/5/10/15/30/60 分钟周期
- `symbols` 支持多个主体用英文逗号拼接，单次请求上限 10 个；
- `indicators` 支持多个指标用英文逗号拼接，单次请求上限 10 个

# 工具边界
- 数据边界：仅支持交易日日内数据查询，不支持历史数据查询；债券高频实时行情仅支持交易所债券数据，对于银行间市场债券实时高频行情，仅支持外汇交易中心（CFETS）的相关指标，不支持经纪商报价，鉴于债券高频实时行情数据的权限复杂性，当存在某债券返回数据为空时，建议联系客服咨询数据权限，而非反复试错。
- 适用边界: 当用户询问“最新价、实时行情、盘中走势、1分钟/5分钟K线、日内分时”等需求时，优先选择对应服务的高频实时行情工具；当用户询问历史日频、财报、基本资料、公告事件等需求时，使用各服务内其他取数工具。
- 指标限制: 禁止在单次请求中同时输入同一指标的不同参数，例如: {"indicators" : "KDJ随机指标K值,KDJ随机指标D值"}，如有需要拆分请求

# symbols 参数规范
- 多证券主体以英文逗号拼接，支持证券六位代码、同花顺代码、标准证券简称三种表达方式

# indicators 参数规范
- 多指标名称以英文逗号拼接，具体支持指标范围因"tool_name"和"data_mode"而有所差异，具体支持指标名称范围见下表：

| tool_name | mode | indicator_names |
|---|---|---|
| stock_highfreq_quotes | highfreq | 开盘价, 最高价, 最低价, 涨跌, 涨跌幅, 成交额, 成交量, 换手率, 收盘价, 均价, 内盘, 外盘, MA均线5周期, MA均线10周期, MA均线20周期, MA均线60周期, KDJ随机指标K值, KDJ随机指标D值, KDJ随机指标J值, MACD指标DIFF值, MACD指标DEA值, MACD指标MACD值, RSI相对强弱指标6周期, RSI相对强弱指标12周期 |
| stock_highfreq_quotes | real_time | 开盘价, 最高价, 最低价, 涨跌, 涨跌幅, 成交额, 成交量, 换手率, 最新价, 现额, 现量, 委比, 委差, 量比, 总股本, 总市值, 市净率, 1分钟涨跌幅, 3分钟涨跌幅, 5分钟涨跌幅, 流通市值, 市盈率TTM |
| fund_highfreq_quotes | highfreq | 开盘价, 最高价, 最低价, 涨跌, 涨跌幅, 成交额, 成交量, 收盘价, 均价 |
| fund_highfreq_quotes | real_time | 开盘价, 最高价, 最低价, 涨跌, 涨跌幅, 成交额, 成交量, 最新价, 现手, 内盘, 外盘, IOPV净值估值, 振幅, 折价 |
| index_highfreq_quotes | highfreq | 开盘价, 最高价, 最低价, 均价, 涨跌, 涨跌幅, 成交额, 成交量, 收盘价, 日内累积涨跌幅 |
| index_highfreq_quotes | real_time | 开盘价, 最高价, 最低价, 均价, 涨跌, 涨跌幅, 成交额, 成交量, 最新价, 领先指数, 现额, 现量, 总市值, 上涨家数, 下跌家数, 涨停家数, 跌停家数, 停牌家数, 振幅, 最新成交价 |
| bond_highfreq_quotes | highfreq | 开盘价, 最高价, 最低价, 均价, 成交额, 成交量, 收盘价, 涨跌, 涨跌幅, 内盘, 外盘 |
| bond_highfreq_quotes | real_time | 开盘价, 最高价, 最低价, 均价, 成交额, 成交量, 最新价, 现手, 振幅, 最新成交价 |