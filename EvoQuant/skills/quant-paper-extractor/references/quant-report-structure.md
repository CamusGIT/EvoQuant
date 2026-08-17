# Quant Research Report Structure Guide

Typical structure of Chinese quantitative research reports (量化研究研报). Use this reference to locate relevant sections during two-pass extraction.

## Typical Report Structure

| Section | Chinese Heading | Content | Extraction Target |
|---------|----------------|---------|-------------------|
| Cover page | 封面 | Title, source name, date, analyst names | title, year, source |
| Executive summary | 摘要 / 核心观点 / 投资要点 | Key findings and recommendations | tldr, abstract, keywords |
| Research background | 研究背景 / 逻辑 | Why this topic matters | abstract |
| Strategy description | 策略构建 / 投资策略 / 交易策略 | The proposed trading strategy | strategy |
| Methodology | 因子构建 / 模型方法 / 方法论 | Quantitative methods and models | method |
| Backtesting | 回测设计 / 实证分析 | Data, setup, and validation | experiment |
| Results | 实证结果 / 策略表现 / 收益分析 | Performance metrics | result |
| Robustness | 稳健性检验 / 敏感性分析 | Checks on different conditions | (supplementary) |
| Risk disclosure | 风险提示 / 免责声明 | Disclaimers | (skip) |

## Section-Heading Heuristics

Use these patterns to locate relevant sections in the markdown. The `extract.py prepare` command auto-tags matching headings with section categories.

### Strategy headings
- 策略, 投资策略, 组合构建, 交易策略, 信号构建
- portfolio construction, signal construction, trading strategy

### Method headings
- 方法, 模型, 因子, 因子构建, 方法论, 回归, 机器学习
- methodology, model, factor construction, regression, machine learning

### Experiment headings
- 回测, 实证, 数据, 样本, 样本区间, 回测设计, 数据处理
- backtest, empirical, data, sample, dataset

### Result headings
- 结果, 表现, 收益, 超额, 绩效, 夏普, 回撤, 信息比率
- result, performance, return, alpha, sharpe, drawdown, information ratio

## Common Quantitative Finance Terminology

| Chinese | English |
|---------|---------|
| 年化收益率 | Annualized return |
| 夏普比率 | Sharpe ratio |
| 最大回撤 | Maximum drawdown |
| 信息比率 | Information ratio |
| 胜率 | Win rate |
| 换手率 | Turnover rate |
| 多空组合 | Long-short portfolio |
| 因子暴露 | Factor exposure |
| 因子衰减 | Factor decay / Alpha decay |
| 横截面 | Cross-sectional |
| 时序 | Time-series |
| 调仓 | Rebalancing |
| 形成期 | Formation period |
| 持有期 | Holding period |
| 基准 | Benchmark |
| 超额收益 | Excess return / Alpha |
| 多因子模型 | Multi-factor model |
| 排序法 | Sorted portfolio approach |
| Fama-French 三因子 | Fama-French 3-factor |
| 交易成本 | Transaction cost |
| 双边成本 | Round-trip cost |
| 市值中性 | Market-cap neutral |
| 行业中性 | Industry neutral |
| 分组回测 | Group-based backtest |
| IC / IR | Information Coefficient / Information Ratio |
| 因子值 | Factor score / Factor value |
