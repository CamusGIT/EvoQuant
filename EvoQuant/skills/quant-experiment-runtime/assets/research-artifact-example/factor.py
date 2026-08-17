"""Research Artifact example: 20-day reversal (momentum) factor.

This is the canonical example a research-code LLM should imitate. It is a
**single-file Research Artifact** that exposes an **Entry Point** callable the
Executor calls. Key points this example demonstrates (copy these patterns):

  1. Entry Point signature:  ``run(context, config) -> results``
     - function name is whatever you name it; ``compute_ref`` points to it
       (e.g. ``"assets/research-artifact-example/factor.py::run"``)
  2. ``results`` default contract: a ``dict[split_name, pd.Series]`` where each
     Series is factor exposure **already aligned** to that split panel's index.
     The Metric (ic_panel) consumes these Series; it does NOT realign.
  3. Alignment is YOUR job: build the factor on ``context.get_split(split)``
     (with ``lookback`` warmup), then ``reindex`` to the *un-lookbacked* panel
     index so only the split's rows are exposed.
  4. Write any byproducts to ``context.artifacts`` (Reflection reads them).

This factor: 20-day mean return (a short-term reversal/momentum proxy), built
from the panel's ``ret`` column, cross-sectionally usable as stock-selection
exposure. Replace the factor logic with your own; keep the Entry Point shape.
"""

from __future__ import annotations

import pandas as pd


def run(context, config):
    """Entry Point. Returns {split: aligned factor Series}.

    ``config`` may carry hyperparameters, e.g. ``{"window": 20}`` and which
    column to use (``"ret"`` by default).
    """
    window = int(config.get("window", 20))
    src_col = config.get("src_col", "ret")
    # compute exposure for whichever splits the Executor is evaluating
    # (from context.config), falling back to params if set.
    splits = config.get("splits") or tuple(
        context.config.get("splits", ("train", "val"))
    )

    results: dict[str, pd.Series] = {}
    for split in splits:
        # lookback = window so the rolling mean is defined on the first split day
        panel = context.get_split(split, lookback=window)
        if panel.empty or src_col not in panel.columns:
            results[split] = pd.Series(
                dtype="float32", name="factor", index=panel.index
            )
            continue

        # --- factor logic (research-code free zone) ---
        ret = panel[src_col]
        factor = (
            ret.groupby(level="instrument", group_keys=False)
            .rolling(window)
            .mean()
            .reset_index(level=0, drop=True)
        )
        # --- alignment (YOUR job): expose only the split's rows, aligned to panel ---
        split_panel = context.get_split(split)  # un-lookbacked, for exact index
        factor = factor.reindex(split_panel.index).astype("float32")
        factor.name = "factor"

        # --- byproduct artifact (Reflection can read this) ---
        factor.to_frame("factor").to_parquet(
            context.artifacts / f"factor_{split}.parquet"
        )

        results[split] = factor
    return results
