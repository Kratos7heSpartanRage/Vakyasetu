"""
Print the evaluation curve of one or more training runs.

Pass log files (best: they contain every evaluation) and/or run folders:
    python ml/scripts/training_curve.py ml/outputs/run2_full.log ml/outputs/run3_filtered.log
    python ml/scripts/training_curve.py ml/checkpoints/run3_filtered

A run folder only gives the evaluations saved up to its best checkpoint; a log file gives all of them.
Log files do not record the step number, so it is worked out as (evaluation number x --eval-steps).
"""

import argparse
import ast
import json
import re
from pathlib import Path

EVAL_DICT = re.compile(r"\{[^{}]*'eval_BLEU'[^{}]*\}")


def rows_from_log(path, eval_steps):
    text = Path(path).read_text(encoding="utf-8", errors="replace").replace("\r", "\n")
    rows = []
    for i, chunk in enumerate(EVAL_DICT.findall(text), start=1):
        d = ast.literal_eval(chunk)
        rows.append((i * eval_steps, d["eval_loss"], d["eval_BLEU"], d["eval_chrF"]))
    return rows


def rows_from_run_dir(path):
    states = sorted(Path(path).glob("checkpoint-*/trainer_state.json"),
                    key=lambda p: int(p.parent.name.split("-")[1]))
    if not states:
        raise SystemExit(f"No checkpoint-*/trainer_state.json under {path}")
    state = json.loads(states[-1].read_text(encoding="utf-8"))
    return [(e["step"], e["eval_loss"], e["eval_BLEU"], e["eval_chrF"])
            for e in state["log_history"] if "eval_BLEU" in e]


def show(label, rows):
    print(f"\n{label}")
    if not rows:
        print("  no evaluation lines found (has the first evaluation happened yet?)")
        return
    best_bleu = max(r[2] for r in rows)
    best_loss = min(r[1] for r in rows)
    print(f"  {'step':>6} {'loss':>7} {'BLEU':>7} {'chrF':>7}")
    for step, loss, bleu, chrf in rows:
        marks = ("  <- best BLEU" if bleu == best_bleu else "") + ("  <- lowest loss" if loss == best_loss else "")
        print(f"  {step:>6} {loss:>7.3f} {bleu:>7.1f} {chrf:>7.1f}{marks}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+", help="log files and/or run folders")
    ap.add_argument("--eval-steps", type=int, default=500, help="the --eval_steps used in training")
    args = ap.parse_args()
    for p in args.paths:
        path = Path(p)
        if not path.exists():
            print(f"\n{p}: not found")
            continue
        rows = rows_from_run_dir(path) if path.is_dir() else rows_from_log(path, args.eval_steps)
        show(p, rows)


if __name__ == "__main__":
    main()