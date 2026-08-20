# EvoQuant × DeepEval 迭代日志

> 每轮五段固定格式：① 本轮运行 ② 分数快照 ③ 失败诊断 ④ 改动内容 ⑤ 复跑结果与下轮焦点。
> 防回归红线：不调指标阈值、不删 golden（除非论证无效并经用户同意）、不换应用模型供应商。

---

## 前置修复（Round 0 之前，非迭代轮，不涉指标）

**问题**：安装 deepeval 后 `tests/test_llm.py` 两个 minimax 路由测试失败，且报错形态随 `.env` 清洗而变（脏注释值断言失败 → 清洗后 `KeyError: 'base_url'`），裸 python 进程查环境变量却干净——"幽灵污染"。

**根因（两层叠加）**：
1. deepeval 在被 import 瞬间执行 `autoload_dotenv()`（`deepeval/__init__.py:12`），而 pytest 启动会自动加载其插件 → **每次 pytest 都把仓库根 `.env` 灌进环境变量**。Phase 1 全绿只是因为当时 `.env` 尚不存在。
2. `EvoQuant/llm/models.py` minimax 分支用 `os.environ.get("MINIMAX_BASE_URL", default)`：键"存在但为空串"（`.env` 里 `MINIMAX_BASE_URL=` 空值行的 dotenv 语义）不会走默认值，返回 `""` → `if base_url:` 跳过 → `base_url` 未传。

**改动**：`models.py:514` 改为 `(os.environ.get("MINIMAX_BASE_URL") or base_url_default).rstrip("/")`——空串视同未设置，回落默认常量。这是应用真 bug（`.env.example` 自带空值行，用户照抄后 minimax 请求会静默打到 Anthropic 官方端点导致 401），非为过测试的改动。

**验证**：`tests/test_llm.py` 152 passed；全套旧套件复跑见下。`test_minimax_base_url_env_override`（显式设真 URL）不受影响。

---

## 数据集定稿（Round 0 之前）

**生成方式**：`tests/evals/generate_dataset.py`（deepeval Python API，绕开 CLI 两个脆弱点：① CLI 的 `asyncio.gather` 一崩全崩且无部分保存；② `DeepSeekModel` 不传 `max_tokens`，思考型评审模型在长 context 下把 API 默认 4096 输出额度耗尽于推理，`content=""` 使 `trim_and_load_json` 崩溃——脚本显式传 16384）。生成模型 = 评审模型 = `deepseek-v4-flash`（单价经 `DEEPSEEK_COST_PER_INPUT/OUTPUT_TOKEN` 环境变量补入，deepeval 4.1.8 价目表尚无此新模型）。19 个 context 产 18 条（context #18 稳定失败，放弃）。

**修剪 18 → 12**（夜间自动模式，用户授权自主决策）：
- 淘汰 7 条：GFlowNet 挖因子（单会话不可行+编数风险）、多策略比较（题面预埋答案数字 18.32%/2.273，评分会失真）、4 条 EvoQuant 自身功能调查（语料前提错误：快照工作区只有研报没有应用文档）、全市场收益排名（需全量行情数据）
- 改写 2 条：策略 IR 比较（"compute"→"从研报汇编并引用出处"，防无数据自行计算）；动量崩溃检索（加"没有就明说"诚实条款——语料中确实无此主题，构成 honesty 测试）
- 新增 1 条：无语料构思类（换手率因子设计文档）——原 18 条全为语料类，`--method contexts` 的固有偏差，手工补齐覆盖

**12 条构成**：语料检索/汇编 7 + 情景策略推理 1 + 技能执行（rawpaper 端到端）1 + 写作整理（LaTeX 综述）1 + 诚实性测试 1 + 无语料构思 1。

---

## 冒烟期发现（Round 0 之前，均已实锤）

1. **上下文无限堆积**：Gold 任务（读研报）跑到 4,532,896 tokens（glm-5.2 上限 1,048,576）→ zai 返回 400。中间件栈只有**事后错误映射**（`ContextOverflowMapperMiddleware` 把 400 映射成 ContextOverflowError）与 fallback，**没有主动裁剪/摘要**——上下文只涨不缩。
2. **连接错误穿透**：轻任务（无语料）在 `deepeval test run` 下两次稳定死于 `APIConnectionError`（363.69s/363.76s，确定性死法）；zai 对超大请求可能掐线而非返回 400，不匹配 `_is_context_limit_error` 的任何 pattern → 直接穿透无 fallback。
3. **zai 端点本身健康**（分级直测全通过）：10/100/300KB prompt、±tools、±streaming、OpenAI SDK 同步、langchain ChatOpenAI 异步——全部秒级返回。挂起只发生在完整 agent 环境（deepagents 中间件栈）内，第一调（msgs=2, 67KB）发出后无响应。
4. deepeval 4.x traced 断言要求：`assert_test(golden=...)` 必须在 `deepeval test run` 下 + 测试体内有 `@observe` 函数（harness 已改为 `@observe(name="evoquant-agent-run")` 包住 ainvoke，返回最终 AI 文本作为 actual_output）。
5. harness 增加 `EVOQUANT_SMOKE=<substring>` 单 golden 过滤器（`deepeval test run` 无 -k 透传）。
6. **zai 传输层三层修复（冒烟阻塞的根因，已修）**：
   - **第一层：非流式请求被网关 ~360s 掐线**。faulthandler 栈转储显示主线程空闲等 I/O（非死锁），httpx 无 zai 响应日志；两次冒烟稳定死于 363.69s/363.76s 且异常是 `APIConnectionError`（非 `APITimeoutError`）→ 网关侧主动断开，OpenAI SDK 重试与 `_is_context_limit_error` pattern 均不匹配 → 直接穿透。机理（对照实验双向实锤）：同样的长生成，流式 613.6s 完成 57326 字符，非流式 361.9s 死于 `APIConnectionError`——非流式首字节要等整个生成完成，glm-5.2 是思考模型（实测单次 reasoning 达 42-52KB），生成轻松超 360s。修复：`models.py` 对 `zai`/`zai-code` 强制 `streaming=True`（修复后 LLM#1 立即 200 OK）。
   - **第二层：`stream_chunk_timeout` 默认 120s 太短**。流式修复后推进到 LLM#2，收 3071 个 chunk 后 120s 无新 chunk 被 langchain 判死（`StreamChunkTimeoutError`）——思考模型深思考阶段可长时间不吐 chunk。修复：同分支 `stream_chunk_timeout=300`。
7. **"应用上下文堆积 4.5M tokens"系误判，已撤销（2026-08-21 实锤推翻）**：冒烟期记录的 Gold 任务 4,532,896 tokens 与轻任务 4,553,747/4,856,489/5,434,910 全部同源——**不是应用 agent 的请求，是 deepeval 评分阶段发给评审模型（api.deepseek.com）的 judge prompt**。决定性证据：httpx 层双 patch（同步+异步）记录到的全部应用请求最大仅 143KB，而 400 请求实测 body=11,384,655 字节、URL=`https://api.deepseek.com/chat/completions`、内容开头为 deepeval 的 trace 分析模板（"Given a nested workflow trace whose spans…"）。机理：deepeval trace 级指标（TaskCompletion/StepEfficiency）把整棵 trace 序列化进 judge prompt，每个 LLM span 的 input 是该次调用的全量消息历史（含 40-100KB reasoning）——7 次调用即 11MB ≈ 4.8M tokens，远超评审模型上限。裸环境（无 deepeval test run）同任务两次完整跑通（903s/545s）也旁证应用本身无此问题。修复：harness 增 `_slim_trace_for_judge()`——agent 跑完后、trace 关闭前把每个 span 的 input/output 截断到 2000 字符（树结构/根 trace 的 actual_output 保持完整）。原"context_editing 裁不动"分析（ClearToolUsesEdit 只清旧工具对）作为背景知识保留，但不再是本轮缺陷。
8. **trace 生命周期零成本探针（2026-08-21，`test_diag_trace_probe.py`，无任何模型调用）**：为定位 slim 连续三次 no-op，读 deepeval 源码 + 写探针实证了完整链路：pytest plugin 在每个测试外包 `__deepeval_internal_pytest_test_wrapper__` Observer span（plugins/plugin.py `pytest_runtest_call`）→ `assert_test(golden=)` 走 `_assert_test_from_current_trace`：从 `current_trace_context.get()` 拿 trace，跳过 wrapper 提升 `children[0]` 为 root，`create_nested_spans_dict()` **从 span 对象现算** dict（非缓存）赋给 `test_case._trace_dict`，指标再 `serialize_to_json(_trace_dict)` 进 judge prompt。探针实证：① 测试体内 contextvar 拿到的 Trace 树 mid-flight 实时可读（wrapper→children 已挂载）；② `trace_manager.traces` 里就是同一条 trace（此前"不是同一条"的假设错误）；③ 测试体内原地截断 `span.input/output` 后，assert_test 收到的 `_trace_dict` 从 ~200KB 降到 **4089 chars**——截断确定生效。据此把 harness slim 改为 contextvar 优先来源。
9. **slim 第 10 轮：找到树但仍不缩（对象透传 bug）**：contextvar 版 slim 日志 `ctx=Trace roots=1 chars=7364906`（树找到了，截断前 7.36MB），但 judge 请求仍 11,724,316B、400（`4,605,592 tokens`）。解剖 400 body：`"role"×151 + reasoning×89 + "Tool Input"×110`。根因：CallbackHandler 的 `on_chain_start` 把 agent span 的 input 设为 langchain `{"messages": [BaseMessage 对象...]}`（pydantic 模型），`_slim` 只认 str/list/dict，**非容器对象原样透传**（`return v`）——7MB 全在对象里；judge 的 `serialize_to_json` 再把对象 model_dump 全量展开 → 11MB。探针当时有效恰因喂的是纯 str。修复：`_slim` 增加对象分支——repr 超 limit 的对象替换为截断 str；`_walk` 扩展到 `expected_output/context/retrieval_context/tools_called/error` 全部可膨胀字段。
10. **冒烟通过（smoke11，2026-08-21，轻任务 golden 全链路）**：agent 4 个 zai 请求（103-124KB）→ slim `chars=7125811→251097`、judge trace JSON `nested_json=2051746`（中文 ASCII 转义 ~6-8 倍膨胀，span_chars 由此收紧 2000→1000）→ 4/4 指标出分、无 400：**TaskCompletion 0.85 / StepEfficiency 0.50（压线）/ Rigor 1.0 / Deliverable 1.0**。Phase 4 冒烟完成。

---

## Round 0 — 基线

**① 本轮运行**：`EVOSCIENTIST_EVALS=1 deepeval test run tests/evals/test_evoquant_agent.py --identifier "baseline-round-0" --num-processes 3 --ignore-errors`（2026-08-21，Confident AI: test-runs/cmt24q9…，约 55 分钟，12/12 golden 全部走完 agent + 评分阶段）

**② 分数快照**（rich 表折行致逐条解析不全，逐条明细见 Confident AI；下为可靠观测值）：

| 指标 | 阈值 | 结果 |
|---|---|---|
| TaskCompletion | 0.5 | 有分条均值 ~0.91（1.0×6、0.9、0.85、0.45；其余评分 error） |
| StepEfficiency | 0.5 | **重灾区**：9 条有分 = 0.0×4、0.25×3、0.5×2（仅 2 条压线过） |
| Quant Research Rigor | 0.5 | 12/12 有分：1.0×8、0.9×2、0.8×2，全部通过 |
| Actionable Deliverable | 0.5 | 多条 1.0/0.9 通过（折行致统计不全） |

**per-case 分布**：2 条 4/4 全过；5 条挂 1 指标；5 条挂 2 指标。

**③ 失败诊断**（两类硬失败 + 一个软失败面）：
- **应用侧：工具输出无上限 → provider 400 → agent 中途崩溃**（9 起）。实锤链：某文档/语料工具返回 ~165KB 内容（经 `llm/patches.py::_sanitize_messages` 的 media 提升机制变成 164KB 的 `role=user, content=list` 消息）→ 消息历史滚到 420KB/81 条 → zai 400 → 循环重试至崩。`code_interpreter` 早有 `max_result_chars=10000`，但文件读取/语料检索/子代理返回全无护栏（其源码注释自认了这点）。
- **评分侧：judge prompt 超 deepseek 1M 窗**（3 起 400，body 5.9-6.6MB）。机理：slim 后 nested_json 仍达 2.3-2.5MB（重任务 span 多），HTTP 层 JSON-in-JSON 转义再膨胀 ~2.6×（6.6MB ≈ 1.8M tokens）。这些条目的 trace 指标记 error 无分数。
- **软失败面：StepEfficiency 全线低**——与 400 重试循环、消息堆积（79-81 条消息、42 tool_calls 的 trace）直接相关：judge 看到的就是"反复调用、无进展"的轨迹。

**④ 改动内容**（两处，均为最小改动）：
- 应用（Round 1 主改动）：新增 `EvoQuant/middleware/tool_result_guard.py::ToolResultGuardMiddleware`——`wrap_tool_call`/`awrap_tool_call` 拦截所有 ToolMessage，str 超 24000 字符截断（块列表逐块 8000/总量 24000 上限），尾部注入 `[TOOL RESULT TRUNCATED: N chars omitted …]` 明示被截断并引导收窄请求。配置项 `tool_result_max_chars=24000`（settings.py + env 映射）。挂载主 agent 与 subagents 两处中间件栈（EvoQuant.py）。离线验证 _cap 四用例通过；全套单测 2567 passed 无回归。
- 评测基建：harness `_slim_trace_for_judge` 加预算循环——walk 后实测 `create_nested_spans_dict` 序列化大小，>800KB 则 span_chars 减半重截（幂等）直至达标，杜绝 judge 侧 1.8M-token 400。

**⑤ 复跑结果与下轮焦点**：待 Round 1（identifier `iterating-on-tool-result-guard-round-1`）。焦点：① zai 400 归零（应用消息历史不超 ~150KB）；② judge 400 归零（nested_json ≤800KB）；③ StepEfficiency 是否随消息膨胀/重试消失而回升；④ TaskCompletion 低分条（0.45）与评分 error 条恢复出分。
