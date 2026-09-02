"""Generate the eval golden dataset via deepeval's Python API.

Replaces ``deepeval generate --method contexts`` for this repo, working around
two CLI fragilities we hit with the thinking judge model (deepseek-v4-flash):

1. ``DeepSeekModel`` sends no ``max_tokens`` -> the API default (4096) can be
   entirely consumed by reasoning tokens on long contexts, leaving
   ``content=""`` which crashes ``trim_and_load_json`` ("Expecting value:
   line 1 column 1"). We pass ``max_tokens=16384`` explicitly.
2. The CLI's single ``asyncio.gather`` fails the WHOLE run when one context
   misbehaves; here each context is generated independently with try/except,
   so one bad context is logged and skipped instead of losing everything.

Run (from repo root):
    uv run python tests/evals/generate_dataset.py
Output: tests/evals/.dataset.json (same format the test harness loads).
"""

import json
import sys
from pathlib import Path

from deepeval.cli.generate.utils import single_turn_styling_config
from deepeval.models import DeepSeekModel
from deepeval.synthesizer import Synthesizer

EVAL_DIR = Path(__file__).parent
CONTEXTS_PATH = EVAL_DIR / "contexts.json"

SCENARIO = (
    "A quantitative researcher delegates a bounded, single-session research "
    "task to an autonomous agent (EvoQuant) that has a local workspace with "
    "broker research reports (rawpaper PDFs + wiki extracts + parsed "
    "markdown), a code interpreter, and domain skills. Input in English."
)
TASK = (
    "End-to-end completion of one self-contained quant research instruction: "
    "retrieve evidence from the local papers library, or design a factor/experiment, "
    "or run analysis code on local data, and report concrete metrics or "
    "findings, without asking the user questions mid-run."
)
INPUT_FORMAT = (
    "A single imperative research instruction stating the topic, local-data "
    "constraints (which papers or files to use), and the expected deliverable; "
    "completable unattended in one session."
)
EXPECTED_OUTPUT_FORMAT = (
    "A short structured research note: method, key numbers (IC/ICIR/coverage "
    "etc. if computed), artifact paths, and limitations."
)


def main() -> int:
    contexts = json.loads(CONTEXTS_PATH.read_text())
    print(f"载入 {len(contexts)} 个 context")

    model = DeepSeekModel(
        model="deepseek-v4-flash",
        generation_kwargs={"max_tokens": 16384},
    )
    styling = single_turn_styling_config(
        scenario=SCENARIO,
        task=TASK,
        input_format=INPUT_FORMAT,
        expected_output_format=EXPECTED_OUTPUT_FORMAT,
    )
    synth = Synthesizer(model=model, async_mode=False, styling_config=styling)

    all_goldens = []
    failed = []
    for i, context in enumerate(contexts):
        try:
            goldens = synth.generate_goldens_from_contexts(
                contexts=[context],
                include_expected_output=True,
                max_goldens_per_context=1,
                # Keep results from previous iterations (True would wipe
                # synthetic_goldens and restart cost accounting each call).
                _reset_cost=(i == 0),
            )
            all_goldens.extend(goldens)
            preview = (goldens[0].input or "")[:90].replace("\n", " ")
            print(f"[{i + 1}/{len(contexts)}] ✓ {preview}...")
        except Exception as exc:  # noqa: BLE001 — one bad context must not cascade
            failed.append(i)
            print(f"[{i + 1}/{len(contexts)}] ✗ context #{i} 失败: {exc}", file=sys.stderr)

    if not all_goldens:
        print("没有任何 golden 生成成功", file=sys.stderr)
        return 1

    # Same schema save_as writes for file_type="json", inlined because
    # save_as rejects file names containing periods (".dataset" does).
    payload = [
        {
            "input": golden.input,
            "actual_output": golden.actual_output,
            "expected_output": golden.expected_output,
            "context": golden.context,
            "source_file": golden.source_file,
        }
        for golden in all_goldens
    ]
    out_path = EVAL_DIR / ".dataset.json"
    out_path.write_text(
        json.dumps(payload, indent=4, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\n成功 {len(all_goldens)} 条，失败 context: {failed or '无'}")
    print(f"已保存: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
