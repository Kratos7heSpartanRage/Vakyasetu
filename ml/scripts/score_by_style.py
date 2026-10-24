"""
Score base vs tuned on the SAME sentences, split by whether the REFERENCE English is Bible-style.

Why: about 7% of Samayik's test references are King-James-style English. A model that learns to write
Bible English for Bible sentences earns BLEU there that says nothing about textbook Sanskrit. The
"modern" rows (references without archaic words) are the closer stand-in for school-textbook English.

Input files are the per-sentence CSVs written by evaluate_models.py
(columns: reference, base_output, tuned_output).

    python ml/scripts/score_by_style.py ml/outputs/eval_test_full_run2.csv ml/outputs/eval_test_full_run3.csv
"""

import argparse
import sys
from pathlib import Path

import pandas as pd
from sacrebleu.metrics import BLEU, CHRF

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bible_style_check import is_archaic  # same word list as the training-data check

MIN_ROWS = 5


def scores(hyps, refs):
    return BLEU().corpus_score(hyps, [refs]).score, CHRF().corpus_score(hyps, [refs]).score


def show(name, df):
    archaic = df.reference.map(is_archaic)
    groups = [("all", df), ("modern references", df[~archaic]), ("Bible-style references", df[archaic])]
    print(f"\n{name}")
    print(f"  {'subset':<24}{'n':>6}   {'base BLEU/chrF':>16}   {'tuned BLEU/chrF':>16}")
    for label, g in groups:
        if len(g) < MIN_ROWS:
            print(f"  {label:<24}{len(g):>6}   (too few rows to score)")
            continue
        b_bleu, b_chrf = scores(g.base_output.tolist(), g.reference.tolist())
        t_bleu, t_chrf = scores(g.tuned_output.tolist(), g.reference.tolist())
        print(f"  {label:<24}{len(g):>6}   {b_bleu:>7.1f} /{b_chrf:>6.1f}   {t_bleu:>7.1f} /{t_chrf:>6.1f}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", help="eval_*.csv files from evaluate_models.py")
    args = ap.parse_args()
    for f in args.files:
        p = Path(f)
        if not p.exists():
            print(f"\n{f}: not found")
            continue
        df = pd.read_csv(p, dtype=str, keep_default_na=False, na_filter=False, encoding="utf-8-sig")
        missing = {"reference", "base_output", "tuned_output"} - set(df.columns)
        if missing:
            print(f"\n{f}: missing columns {sorted(missing)}")
            continue
        show(p.name, df)


if __name__ == "__main__":
    main()