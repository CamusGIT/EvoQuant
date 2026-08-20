"""Dump per-message sizes of a short agent run to find the 4.5M-token bloat.

The smoke run died with "4553747 tokens in the messages" while the
SizeProbe callback only ever saw ~170KB of history at LLM#7 — a 100x gap.
Something inflates the request far beyond what the main-thread messages
contain. Run with a small recursion_limit, then print every message in the
final state with content / additional_kwargs / tool_calls sizes.

Run: uv run python tests/evals/diag_message_sizes.py
"""

import asyncio
import os
import shutil
import time
import uuid
from pathlib import Path

for _line in Path(".env").read_text().splitlines():
    _line = _line.strip()
    if _line and not _line.startswith("#") and "=" in _line:
        _k, _, _v = _line.partition("=")
        os.environ.setdefault(_k.strip(), _v.strip())

WS = "/tmp/evoquant-diag/ws2"
os.environ["EVOSCIENTIST_MEMORIES_DIR"] = WS + "/memories"
if os.path.exists(WS):
    shutil.rmtree(WS)
shutil.copytree("tests/evals/fixtures/workspace", WS)

from EvoQuant.EvoQuant import create_cli_agent  # noqa: E402
from EvoQuant.config import get_effective_config  # noqa: E402
from EvoQuant.llm.models import get_chat_model  # noqa: E402
from EvoQuant.paths import set_workspace_root  # noqa: E402

GOLDEN_INPUT = (
    "Design a new turnover-based alpha factor for CSI 500 constituents. "
    "Deliver a self-contained factor design document covering: the "
    "economic hypothesis, a precise construction formula, data "
    "requirements, a validation plan (rank IC / ICIR by month, decile "
    "long-short backtest, turnover-cost sensitivity), and known failure "
    "modes. This task does not require the local corpus — reason from "
    "first principles and standard A-share market microstructure. Write "
    "the document as a markdown file in the workspace and summarize it "
    "in your reply."
)


def _size(x) -> int:
    try:
        return len(str(x))
    except Exception:  # noqa: BLE001
        return -1


async def main() -> None:
    cfg = get_effective_config(
        cli_overrides={
            "provider": "zai-code",
            "model": "glm-5.2",
            "auto_approve": True,
            "auto_mode": True,
            "enable_async_subagents": False,
            "recursion_limit": 8,  # STOP EARLY: just enough to see the shape
            "default_workdir": "",
            "model_fallbacks": "glm-5.2:zai-code",
        }
    )
    model = get_chat_model(model=cfg.model, provider=cfg.provider)
    set_workspace_root(WS)
    agent = create_cli_agent(workspace_dir=WS, config=cfg, chat_model=model)
    t0 = time.time()
    # astream + stream_mode="values": the last yielded chunk is the final
    # state even when GraphRecursionError aborts ainvoke.
    result: dict = {}
    try:
        async for chunk in agent.astream(
            {"messages": [{"role": "user", "content": GOLDEN_INPUT}]},
            config={"configurable": {"thread_id": str(uuid.uuid4())}},
            stream_mode="values",
        ):
            result = chunk
    except Exception as exc:  # noqa: BLE001 - still dump what we collected
        print(f"stream aborted: {type(exc).__name__}: {str(exc)[:200]}")
    msgs = result.get("messages", [])
    print(f"\n{time.time() - t0:.0f}s, recursion stopped, {len(msgs)} messages:")
    total = 0
    for i, m in enumerate(msgs):
        content = _size(getattr(m, "content", ""))
        ak = getattr(m, "additional_kwargs", {}) or {}
        reasoning = _size(ak.get("reasoning_content", ""))
        ak_other = _size({k: v for k, v in ak.items() if k != "reasoning_content"})
        tc = _size(getattr(m, "tool_calls", None) or [])
        name = getattr(m, "name", "") or getattr(m, "type", "?")
        line_total = content + reasoning + ak_other + max(tc, 0)
        total += line_total
        print(
            f"  [{i:3d}] {str(name)[:24]:24s} content={content:8d} "
            f"reasoning={reasoning:8d} ak_other={ak_other:8d} "
            f"tool_calls={tc:7d} | line={line_total:8d}"
        )
    print(f"TOTAL: {total} chars (~{total // 4} tokens)")


if __name__ == "__main__":
    asyncio.run(main())
