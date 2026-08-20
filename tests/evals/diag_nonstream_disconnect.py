"""Verify the ~360s zai gateway timeout hypothesis.

Hypothesis: zai's gateway kills NON-STREAMING chat requests whose response
takes longer than ~360s to produce a first byte (glm-5.2 is a thinking model;
long generations exceed this). The smoke runs died at a stable 363.69s /
363.76s with APIConnectionError (not APITimeoutError) => gateway-side
disconnect, not client timeout.

Arm A: same ChatOpenAI construction as the agent (zai-code / glm-5.2),
       streaming=False, ask for a very long generation. Expect: hang ~360s
       then APIConnectionError.
Arm B: identical, but streaming=True (aggregated by ainvoke). Expect:
       completes normally in a few minutes.

Run: uv run python tests/evals/diag_nonstream_disconnect.py
"""

import asyncio
import os
import time
from pathlib import Path

# Bare python (not under pytest) never loads .env — deepeval's autoload only
# hooks pytest processes. Load it manually so ZAI_API_KEY is present.
for _line in Path(".env").read_text().splitlines():
    _line = _line.strip()
    if _line and not _line.startswith("#") and "=" in _line:
        _k, _, _v = _line.partition("=")
        os.environ.setdefault(_k.strip(), _v.strip())

PROMPT = (
    "Write an extremely detailed 8000-word survey of turnover-based alpha "
    "factors in A-share markets. Do not summarize; produce the full text."
)


async def run_arm(label: str, streaming: bool) -> None:
    # Bypass get_chat_model entirely — a raw ChatOpenAI isolates gateway
    # behaviour from all deepagents/middleware wrapping.
    from langchain_openai import ChatOpenAI

    model = ChatOpenAI(
        model="glm-5.2",
        base_url="https://api.z.ai/api/coding/paas/v4",
        api_key=os.environ["ZAI_API_KEY"],
        max_tokens=16384,
        streaming=streaming,
    )
    t0 = time.time()
    print(f"[{label}] streaming={streaming} start", flush=True)
    try:
        resp = await model.ainvoke(PROMPT)
        text = resp.content if hasattr(resp, "content") else str(resp)
        print(
            f"[{label}] OK {time.time() - t0:.1f}s, "
            f"content={len(str(text))} chars",
            flush=True,
        )
    except Exception as exc:  # noqa: BLE001
        print(
            f"[{label}] FAIL {time.time() - t0:.1f}s: "
            f"{type(exc).__name__}: {str(exc)[:200]}",
            flush=True,
        )


async def main() -> None:
    # Arm B first: if streaming works, we already have the fix validated.
    await run_arm("B-stream", streaming=True)
    await run_arm("A-nonstream", streaming=False)


if __name__ == "__main__":
    asyncio.run(main())
