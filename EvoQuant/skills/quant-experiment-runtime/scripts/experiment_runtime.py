"""Quant Research Experiment Executor (core runtime).

This module is intentionally thin. The Experiment Executor only:

  1. prepares the experiment environment (data load + train/val/test split -> RuntimeContext)
  2. calls the research code's unified *experiment entry point*
  3. collects ``results`` WITHOUT interpreting them
  4. calls registered Metrics (Metrics interpret ``results``; they only evaluate, never align)
  5. exposes an Artifact directory the research code writes and Reflection reads
  6. emits a unified ``ExperimentResult``

It deliberately knows nothing about:
  - DSL / expression form
  - research object type (factor / generation method / portfolio) -- that is Workflow's concern
  - the concrete structure of ``results`` -- the Metric interprets it

The unified experiment entry point is a *Convention*, not architecture. The default
function name is ``experiment``; the Executor loads whatever entry point ``compute_ref``
points to. Replacing the engine / object type later requires no change here.
"""

from __future__ import annotations

import importlib.util
import math
import sys
import traceback
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import pandas as pd

# ---------------------------------------------------------------------------
# Split policy (rules / ratios, not hard-coded years)
# ---------------------------------------------------------------------------

DEFAULT_SPLIT_RATIOS = {"train": 0.56, "val": 0.22, "test": 0.22}
"""Default chronological split ratios over the available date coverage.

Ratios, not fixed years: the dataset coverage changes over time (2026-06 today,
2028 / 2032 later). The Executor derives concrete dates from the panel coverage
unless the caller overrides via ``split_config``.
"""


@dataclass
class SplitConfig:
    """How the available date coverage is partitioned into train / val / test.

    Either explicit ``dates`` (per-split [start, end]) **or** ``ratios`` may be
    provided. When neither is given, ``DEFAULT_SPLIT_RATIOS`` is applied over the
    panel coverage. ``test`` is opt-in: by default only train+val are evaluated.
    """

    dates: dict[str, tuple[str, str]] = field(default_factory=dict)
    ratios: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_SPLIT_RATIOS))
    include_test: bool = False

    def resolve(
        self, coverage_start: str, coverage_end: str
    ) -> dict[str, tuple[str, str]]:
        """Return ``{split: (start, end)}`` resolved against the coverage window."""
        if self.dates:
            # caller-supplied explicit dates win; fill missing splits from ratios
            resolved = dict(self.dates)
            if not {"train", "val"} <= resolved.keys():
                resolved.update(self._from_ratios(coverage_start, coverage_end))
            return resolved
        return self._from_ratios(coverage_start, coverage_end)

    def _from_ratios(self, start: str, end: str) -> dict[str, tuple[str, str]]:
        ratios = self.ratios or DEFAULT_SPLIT_RATIOS
        s = pd.Timestamp(start)
        e = pd.Timestamp(end)
        total_days = max((e - s).days, 1)
        cursor = s
        out: dict[str, tuple[str, str]] = {}
        for split, r in ratios.items():
            span = round(total_days * r)
            seg_end = cursor + pd.Timedelta(days=span)
            if split == list(ratios)[-1]:
                seg_end = e  # last split absorbs rounding so the window is contiguous
            out[split] = (cursor.strftime("%Y-%m-%d"), seg_end.strftime("%Y-%m-%d"))
            cursor = seg_end + pd.Timedelta(days=1)
        return out


# ---------------------------------------------------------------------------
# Candidate / ExperimentResult (description + unified output)
# ---------------------------------------------------------------------------


@dataclass
class Candidate:
    """An experiment input description. Not a routing object.

    ``compute_ref`` is a Research Artifact entry point (current default:
    ``"path/to/code.py::experiment"``). The Executor does not assume it is a
    single Python file; that is today's convention. ``object_type`` belongs to
    the Workflow, so it lives in ``metadata`` rather than as a runtime field.
    """

    id: str
    compute_ref: str
    params: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Candidate:
        return cls(
            id=d["id"],
            compute_ref=d["compute_ref"],
            params=dict(d.get("params", {})),
            metadata=dict(d.get("metadata", {})),
        )


@dataclass
class ExperimentResult:
    """Unified output. Reflection and downstream Workflow depend only on this."""

    candidate_id: str
    status: str  # "ok" | "error"
    per_split: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    runtime_meta: dict[str, Any] = field(default_factory=dict)
    artifacts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "status": self.status,
            "per_split": self.per_split,
            "metrics": self.metrics,
            "error": self.error,
            "runtime_meta": self.runtime_meta,
            "artifacts": self.artifacts,
        }


# ---------------------------------------------------------------------------
# RuntimeContext (executor -> research code; forward-extensible)
# ---------------------------------------------------------------------------


class RuntimeContext:
    """What the Executor hands to the research code's entry point.

    Designed so future additions (logger, cache, ...) do not change the call
    signature. Research code reads data via :meth:`get_split`, writes outputs
    under :attr:`artifacts`, and reads config via :attr:`config`.
    """

    def __init__(
        self,
        panel: pd.DataFrame,
        splits: dict[str, tuple[str, str]],
        label_col: str,
        artifacts_dir: Path,
        workspace: Path,
        meta: dict[str, Any] | None = None,
    ) -> None:
        self._panel = panel.sort_index()
        self._splits = splits
        self._label_col = label_col
        self._artifacts_dir = Path(artifacts_dir)
        self._workspace = Path(workspace)
        self._meta = dict(meta or {})
        self._split_cache: dict[str, pd.DataFrame] = {}

    # -- data --------------------------------------------------------------
    def get_split(self, split: str, *, lookback: int = 0) -> pd.DataFrame:
        """Return the panel rows for ``split`` (closed date interval). Cached.

        ``lookback`` extends the slice backwards by that many trading days beyond
        ``split``'s start, so rolling-window factors get warmup data at the
        train boundary. The cache is keyed by ``(split, lookback)``.
        """
        if split not in self._splits:
            raise KeyError(f"unknown split {split!r}; known: {list(self._splits)}")
        cache_key = f"{split}@{lookback}"
        cached = self._split_cache.get(cache_key)
        if cached is not None:
            return cached
        start, end = self._splits[split]
        dt = self._panel.index.get_level_values("datetime")
        mask = (dt >= pd.Timestamp(start)) & (dt <= pd.Timestamp(end))
        sliced = self._panel.loc[mask]
        if lookback and lookback > 0:
            pre_mask = dt < pd.Timestamp(start)
            pre = self._panel.loc[pre_mask].tail(lookback)
            sliced = pd.concat([pre, sliced])
        self._split_cache[cache_key] = sliced
        return sliced

    # -- accessors ---------------------------------------------------------
    @property
    def label_col(self) -> str:
        return self._label_col

    @property
    def config(self) -> dict[str, Any]:
        return {
            "splits": {k: list(v) for k, v in self._splits.items()},
            "label_col": self._label_col,
            **self._meta,
        }

    @property
    def artifacts(self) -> Path:
        self._artifacts_dir.mkdir(parents=True, exist_ok=True)
        return self._artifacts_dir

    @property
    def workspace(self) -> Path:
        return self._workspace

    @property
    def meta(self) -> dict[str, Any]:
        return dict(self._meta)


# ---------------------------------------------------------------------------
# Metrics registry (the one extension point we keep; Metrics only evaluate)
# ---------------------------------------------------------------------------


@runtime_checkable
class Metric(Protocol):
    name: str

    def __call__(
        self, results: Any, split_panel: pd.DataFrame, label_col: str
    ) -> dict[str, Any]: ...


# A Metric consumes research-code ``results`` and the split panel. It must NOT
# realign / transform the data into an evaluation target -- alignment is the
# research code's job. The Metric only evaluates.


def _ic_panel_metric(
    results: Any, split_panel: pd.DataFrame, label_col: str, *, split: str | None = None
) -> dict[str, Any]:
    """Default IC-style metric.

    Default ``results`` contract: ``dict[split_name, pd.Series]`` where each
    Series is factor exposure already aligned to that split's panel index
    (research-code responsibility). If ``results`` is a bare ``pd.Series`` it is
    used directly. Evaluation is delegated to the skill's own cross-sectional IC
    implementation (``_metrics.evaluate_on_panel``). The Metric only evaluates;
    it does NOT realign.
    """
    import _metrics  # local import: keeps core import graph minimal

    series = results
    if isinstance(results, dict):
        if split is None:
            raise ValueError(
                "ic_panel: results is a dict but no split context provided"
            )
        if split not in results:
            raise KeyError(
                f"ic_panel: results missing split {split!r}; got {list(results)}"
            )
        series = results[split]
    if not isinstance(series, pd.Series):
        raise TypeError(
            "ic_panel metric expects an already-aligned pd.Series of exposure; "
            f"got {type(series)!r}. Alignment is the research code's job."
        )
    values = series.reindex(split_panel.index).to_numpy(dtype="float64")
    return _metrics.evaluate_on_panel(
        values, split_panel, label_col=label_col, min_ic_pairs=5
    )


class MetricsRegistry:
    def __init__(self) -> None:
        self._metrics: dict[str, Callable[..., dict[str, Any]]] = {}
        self.register("ic_panel", _ic_panel_metric)

    def register(self, name: str, fn: Callable[..., dict[str, Any]]) -> None:
        self._metrics[name] = fn

    def get(self, name: str) -> Callable[..., dict[str, Any]]:
        if name not in self._metrics:
            raise KeyError(
                f"unknown metric {name!r}; registered: {list(self._metrics)}"
            )
        return self._metrics[name]

    def names(self) -> list[str]:
        return list(self._metrics)


# ---------------------------------------------------------------------------
# Entry-point loading (Convention, not architecture)
# ---------------------------------------------------------------------------


def load_entry_point(compute_ref: str) -> Callable[..., Any]:
    """Load the research-code experiment entry point.

    Python-native Entry Point forms (Convention, not architecture):
      - ``"path/to/code.py::function_name"``  (file path + function; default name ``experiment``)
      - ``"package.module:function_name"``     (importable module + function)

    The function name is convention (default ``experiment``); the Executor does
    not hard-code it. Future: multi-file workspace entry points.
    """
    sep = "::" if "::" in compute_ref else ":"
    ref_part, _, func_name = compute_ref.partition(sep)
    func_name = func_name or "experiment"

    if sep == "::":
        # path::func  -> load file via importlib
        path = Path(ref_part)
        if not path.is_absolute():
            path = Path.cwd() / path
        if not path.exists():
            raise FileNotFoundError(f"research artifact not found: {compute_ref}")
        mod_name = f"_qre_research_{abs(hash(str(path))) % (10**10)}"
        spec = importlib.util.spec_from_file_location(mod_name, str(path))
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load module from {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[mod_name] = module
        spec.loader.exec_module(module)
    else:
        # module:func -> normal import (caller's package must be importable)
        try:
            module = importlib.import_module(ref_part)
        except ImportError as err:
            # fall back: treat ref_part as a path with no leading slash importable as file
            path = Path(ref_part)
            if not path.is_absolute():
                path = Path.cwd() / path
            if not path.exists():
                raise FileNotFoundError(
                    f"research artifact not found: {compute_ref}"
                ) from err
            mod_name = f"_qre_research_{abs(hash(str(path))) % (10**10)}"
            spec = importlib.util.spec_from_file_location(mod_name, str(path))
            if spec is None or spec.loader is None:
                raise ImportError(f"cannot load module from {path}") from err
            module = importlib.util.module_from_spec(spec)
            sys.modules[mod_name] = module
            spec.loader.exec_module(module)
    if not hasattr(module, func_name):
        raise AttributeError(f"{compute_ref}: entry point {func_name!r} not found")
    return getattr(module, func_name)


# ---------------------------------------------------------------------------
# Experiment Executor
# ---------------------------------------------------------------------------


def _jsonable(v: Any) -> Any:
    """Best-effort coercion to JSON-serialisable scalars for ExperimentResult."""
    if v is None or isinstance(v, (bool, int)):
        return v
    if isinstance(v, float):
        return v if math.isfinite(v) else None
    if isinstance(v, (list, tuple)):
        return [_jsonable(x) for x in v]
    if isinstance(v, dict):
        return {str(k): _jsonable(x) for k, x in v.items()}
    # numpy scalars etc.
    try:
        return _jsonable(float(v))
    except (TypeError, ValueError):
        return str(v)


class ExperimentRuntime:
    """The Experiment Executor. Thin by design."""

    def __init__(
        self,
        panel: pd.DataFrame,
        split_config: SplitConfig,
        label_col: str,
        metrics_registry: MetricsRegistry,
        artifacts_dir: Path,
        workspace: Path | None = None,
    ) -> None:
        self._panel = panel
        self._split_config = split_config
        self._label_col = label_col
        self._metrics = metrics_registry
        self._artifacts_dir = Path(artifacts_dir)
        self._workspace = Path(workspace) if workspace else self._artifacts_dir.parent
        self._splits = self._resolve_splits()

    def _coverage(self) -> tuple[str, str]:
        dt = self._panel.index.get_level_values("datetime")
        return str(dt.min().date()), str(dt.max().date())

    def _resolve_splits(self) -> dict[str, tuple[str, str]]:
        start, end = self._coverage()
        splits = self._split_config.resolve(start, end)
        if not self._split_config.include_test:
            splits.pop("test", None)
        return splits

    def _make_context(self, candidate_id: str) -> RuntimeContext:
        cand_artifacts = self._artifacts_dir / candidate_id
        return RuntimeContext(
            panel=self._panel,
            splits=self._splits,
            label_col=self._label_col,
            artifacts_dir=cand_artifacts,
            workspace=self._workspace,
            meta={
                "coverage_start": self._splits["train"][0],
                "coverage_end": self._splits["val"][-1],
            },
        )

    def _list_artifacts(self, candidate_id: str) -> list[str]:
        d = self._artifacts_dir / candidate_id
        if not d.exists():
            return []
        return sorted(
            str(p.relative_to(self._artifacts_dir)) for p in d.rglob("*") if p.is_file()
        )

    def run(
        self, candidate: Candidate, *, splits: tuple[str, ...] | None = None
    ) -> ExperimentResult:
        target_splits = (
            list(splits)
            if splits
            else [s for s in ("train", "val", "test") if s in self._splits]
        )
        context = self._make_context(candidate.id)
        entry = load_entry_point(candidate.compute_ref)
        try:
            results = entry(context, candidate.params)
        except Exception as e:
            return ExperimentResult(
                candidate_id=candidate.id,
                status="error",
                error=f"{type(e).__name__}: {e}",
                runtime_meta={"traceback": traceback.format_exc(limit=6)},
            )

        metric_name = candidate.params.get("metric", "ic_panel")
        try:
            metric_fn = self._metrics.get(metric_name)
        except KeyError as e:
            return ExperimentResult(candidate.id, status="error", error=str(e))

        per_split: dict[str, Any] = {}
        flat: dict[str, Any] = {}
        for split in target_splits:
            split_panel = context.get_split(split)
            if split_panel.empty:
                per_split[split] = {
                    "date_range": list(self._splits[split]),
                    "error": "empty split",
                }
                continue
            try:
                m = metric_fn(results, split_panel, self._label_col, split=split)
            except TypeError:
                # metric does not accept ``split`` kw (older signature) -- fall back
                m = metric_fn(results, split_panel, self._label_col)
            except Exception as e:
                per_split[split] = {
                    "date_range": list(self._splits[split]),
                    "error": f"{type(e).__name__}: {e}",
                }
                continue
            per_split[split] = {
                "date_range": list(self._splits[split]),
                "metrics": _jsonable(m),
                "timing": {},
            }
        # flatten val metrics as the headline metrics
        if "val" in per_split and "metrics" in per_split["val"]:
            flat = dict(per_split["val"]["metrics"])
        return ExperimentResult(
            candidate_id=candidate.id,
            status="ok",
            per_split=per_split,
            metrics=flat,
            runtime_meta={
                "metric": metric_name,
                "splits": target_splits,
                "label_col": self._label_col,
                "object_type": candidate.metadata.get("object_type"),
            },
            artifacts=self._list_artifacts(candidate.id),
        )

    def run_batch(
        self, candidates: list[Candidate], *, splits: tuple[str, ...] | None = None
    ) -> list[ExperimentResult]:
        return [self.run(c, splits=splits) for c in candidates]
