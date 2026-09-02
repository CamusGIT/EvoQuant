"""Diagnose EvoQuant agent context growth (why eval runs die at ~6min).

Runs the same agent-construction path as the eval harness against the fixed
workspace snapshot, with a callback that logs message-count/size at every
LLM call. Reproduces the APIConnectionError seen in smoke tests and shows
whether the message history grows without bound.

Run: uv run python tests/evals/diag_context_growth.py
"""

import asyncio
import faulthandler
import logging
import os
import shutil
import time
import uuid

# Dump all thread stacks after 15 minutes so a hang shows WHERE it hangs.
# (Raised from 240s: with streaming enabled, a full light task legitimately
# runs minutes; the old 240s kill fired mid-run.)
faulthandler.dump_traceback_later(900, exit=True)
logging.basicConfig(level=logging.WARNING)
logging.getLogger("httpx").setLevel(logging.INFO)

WS = "/tmp/evoquant-diag/ws"
os.environ["EVOSCIENTIST_MEMORIES_DIR"] = WS + "/memories"

# Fresh snapshot every run — a previous run's agent outputs pollute it.
if os.path.exists(WS):
    shutil.rmtree(WS)
shutil.copytree("tests/evals/fixtures/workspace", WS)

from langchain_core.callbacks import AsyncCallbackHandler  # noqa: E402

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
    "modes. This task does not require the local papers library — reason from "
    "first principles and standard A-share market microstructure. Write "
    "the document as a markdown file in the workspace and summarize it "
    "in your reply."
)


class SizeProbe(AsyncCallbackHandler):
    call_no = 0

    async def on_chat_model_start(self, serialized, messages, *, run_id, **kw):
        SizeProbe.call_no += 1
        batch = messages[0] if messages else []
        chars = sum(len(str(getattr(m, "content", ""))) for m in batch)
        reasons = sum(
            len(str(getattr(m, "additional_kwargs", {}).get("reasoning_content", "") or ""))
            for m in batch
        )
        tool_calls = sum(len(getattr(m, "tool_calls", None) or []) for m in batch)
        print(
            f"[{time.strftime('%H:%M:%S')}] LLM#{SizeProbe.call_no:3d} "
            f"msgs={len(batch):3d} chars={chars // 1000:6d}KB "
            f"reasoning={reasons // 1000:5d}KB tool_calls={tool_calls}",
            flush=True,
        )


async def main() -> None:
    cfg = get_effective_config(
        cli_overrides={
            "provider": "zai-code",
            "model": "glm-5.2",
            "auto_approve": True,
            "auto_mode": True,
            "enable_async_subagents": False,
            "recursion_limit": 2000,
            "default_workdir": "",
            "model_fallbacks": "glm-5.2:zai-code",
        }
    )
    model = get_chat_model(model=cfg.model, provider=cfg.provider)
    set_workspace_root(WS)
    agent = create_cli_agent(
        workspace_dir=WS, config=cfg, chat_model=model
    )
    t0 = time.time()
    try:
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": GOLDEN_INPUT}]},
            config={
                "callbacks": [SizeProbe()],
                "configurable": {"thread_id": str(uuid.uuid4())},
            },
        )
        msgs = result.get("messages", [])
        print(
            f"\n完成 {time.time() - t0:.0f}s: {len(msgs)} 条消息, "
            f"LLM 调用 {SizeProbe.call_no} 次"
        )
    except Exception as exc:  # noqa: BLE001
        print(
            f"\n失败 {time.time() - t0:.0f}s @ LLM#{SizeProbe.call_no}: "
            f"{type(exc).__name__}: {str(exc)[:300]}",
            flush=True,
        )


if __name__ == "__main__":
    asyncio.run(main())
