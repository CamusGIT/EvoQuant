# AGENTS.md — EvoQuant 语料库契约

本文件是 agent 与仓库之间的硬约定：语料库长什么样、怎么读、什么不能碰。
硬规则的优先级高于任何 skill 的建议。

## 语料库布局（仓库根 `papers/`，只读）

| 路径 | 内容 | agent 访问方式 |
|---|---|---|
| `papers/cards/{paperId}.jsonl` | 论文卡片（tldr/摘要/分节总结） | `paper_read` / 直接读 `/papers/cards/` |
| `papers/markdown/{paperId}.md` | 全文 markdown | **仅** `paper_section` 按节读 |
| `papers/raw/{paperId}.pdf` | 原始 PDF | **禁止**（卡片已承载内容） |
| `papers/context_brief.md` | 全库概览（≤4000 字符） | 直接读 `/papers/context_brief.md` |
| `papers/index.jsonl` | 派生索引 | 直接读 `/papers/index.jsonl` |

关联键统一为 `paperId`（PDF、全文、卡片三层同名）。PDF 不再以中文文件名寻址。

## 工具链（唯一受支持的读取路径）

```
paper_search(query)               # L3：一行/篇，先找 paperId
paper_read(paper_id)              # L2：卡片全文 + 章节大纲，一次即够
paper_section(paper_id, heading)  # L1：单节原文（引用时的逃生舱）
```

## 硬规则

1. **检索先于阅读**：从 `paper_search` 开始，禁止无目标 `ls /papers/`。
2. **同一 paperId 不二次 `paper_read`**：卡片已在上下文里就是有了。
3. **直读被拒是设计而非故障**：`/papers/markdown/**`、`/papers/raw/**`
   的读取被机制拦截并附带引导，改用 `paper_section`。
4. **引用必须可溯源**：带 paperId 前 8 位以上（加标题），主张才能被核对。

## 历史遗留

workspace 下的 `rawpaper/`、`markdown/`、`wiki/`、`manifest.jsonl` 已废弃
（迁移至 `papers/`，旧位置移入 `_papers_migrated_backup_*/`）。不要读、
不要写、不要再通过环境变量定位它们。
