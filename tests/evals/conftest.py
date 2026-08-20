"""Eval-suite conftest: isolate global state before any EvoQuant import.

Runs in every pytest/xdist worker before the eval test module is imported.
``MEMORIES_DIR`` is global (~/.evoquant/memories) — without this override,
eval runs would read and WRITE the real user memory store
(see EvoQuant/paths.py: ``_env_path("EVOSCIENTIST_MEMORIES_DIR")``).
Each test re-points this env var at its own tmp workspace; this default only
covers the window before that happens.
"""

import os

_EVAL_STATE_ROOT = os.environ.get(
    "EVOSCIENTIST_EVAL_STATE_ROOT", "/tmp/evoquant-evals"
)
os.environ.setdefault(
    "EVOSCIENTIST_MEMORIES_DIR", os.path.join(_EVAL_STATE_ROOT, "memories")
)
