"""Middleware capping tool-result size before it enters the message history.

The traced eval baseline (``baseline-round-0``, 2026-08-21) exposed the
unbounded path: a papers/document tool returned ~165KB of content, the
message history ballooned past 420KB / 80 messages, and the provider
rejected the next request with 400 — killing the agent mid-task. The code
interpreter already caps its own results
(``code_interpreter_max_result_chars``); this extends the same guard to
every tool result (file reads, paper search, sub-agent returns, ...).

The cap keeps the head of the result (usually the useful part: headings,
first rows, summary) and tells the agent the exact omitted size so it can
re-query with narrower bounds instead of assuming it saw everything.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from langchain.agents.middleware.types import AgentMiddleware
from langchain_core.messages import ToolMessage

if TYPE_CHECKING:
    from langchain.agents.middleware.types import ToolCallRequest

_SUFFIX = (
    "\n[TOOL RESULT TRUNCATED: {omitted} characters omitted. The full "
    "output was NOT delivered — narrow your request (offsets, specific "
    "sections, filtered queries) if you need more of it.]"
)
_DEFAULT_MAX_CHARS = 24000
_BLOCK_MAX_CHARS = 8000  # per content block when content is a block list


class ToolResultGuardMiddleware(AgentMiddleware):
    """Cap every ToolMessage payload at ``max_chars`` characters."""

    name = "tool_result_guard"

    def __init__(self, max_chars: int = _DEFAULT_MAX_CHARS) -> None:
        super().__init__()
        self.max_chars = max_chars

    # -- sync ---------------------------------------------------------------
    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage],
    ) -> ToolMessage:
        return _cap(handler(request), self.max_chars)

    # -- async --------------------------------------------------------------
    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage]],
    ) -> ToolMessage:
        return _cap(await handler(request), self.max_chars)


def _cap(result: Any, max_chars: int) -> Any:
    """Return a capped copy of a ToolMessage (or pass non-messages through).

    Never raises: the guard must not turn a successful tool call into a
    failure. Content shapes: ``str`` (the common case) or a block list
    (multi-part / hoisted-media results).
    """
    if not isinstance(result, ToolMessage):
        return result  # Command[Any] and custom payloads pass through
    content = result.content
    if isinstance(content, str):
        if len(content) <= max_chars:
            return result
        capped = content[:max_chars] + _SUFFIX.format(omitted=len(content) - max_chars)
        return ToolMessage(
            content=capped,
            tool_call_id=result.tool_call_id,
            name=result.name,
            status=result.status,
        )
    if isinstance(content, list):
        total = sum(len(str(b)) for b in content)
        if total <= max_chars:
            return result
        capped_blocks: list[Any] = []
        used = 0
        for b in content:
            text = b.get("text") if isinstance(b, dict) else b
            block_text = text if isinstance(text, str) else str(b)
            room = min(_BLOCK_MAX_CHARS, max_chars - used - len(_SUFFIX))
            if room <= 0:
                break
            if len(block_text) > room:
                block_text = block_text[:room]
            capped_blocks.append(
                {"type": "text", "text": block_text}
                if isinstance(b, dict)
                else block_text
            )
            used += len(block_text)
        capped_blocks.append(
            {
                "type": "text",
                "text": _SUFFIX.format(omitted=total - used),
            }
        )
        return ToolMessage(
            content=capped_blocks,
            tool_call_id=result.tool_call_id,
            name=result.name,
            status=result.status,
        )
    return result
