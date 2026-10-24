"""
Measure how much Bible-style (archaic, King-James) English there is in the training data
and in the model outputs, and optionally write a training set without it.

Why: Samayik includes an old Bible translation, and the fine-tuned model's outputs on
textbook stories contain phrases like "And behold ... unto the king's gate". This script
MEASURES that instead of assuming it. The marker list is a heuristic, so look at the sample
rows it prints before trusting the percentages.

Run from the repo root with the .venv active:
    python ml/scripts/bible_style_check.py                    # report only
    python ml/scripts/bible_style_check.py --write-filtered   # also writes data/processed_filtered/

Then, to train on the filtered data:
    python ml/scripts/prepare_lora_data.py --in-dir data/processed_filtered \
        --out-dir data/lora_filtered --dev-size 200
"""

import argparse
import re
import shutil
from pathlib import Path

import pandas as pd

# Conservative list of King-James-style words that almost never appear in modern English.
ARCHAIC = re.compile(
    r"\b(thou|thee|thy|thine|ye|unto|hath|hast|doth|dost|saith|shalt|wilt|"
    r"behold|verily|wherefore|whosoever|begat|yea)\b",
    re.IGNORECASE,
)


def is_archaic(text):
    return bool(ARCHAIC.search(str(text)))


def read_tsv(path):
    return pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False, na_filter=False)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in-dir", default="data/processed")
    ap.add_argument("--out-dir", default="data/processed_filtered")
    ap.add_argument("--eval", nargs="*", default=["ml/outputs/eval_test500_run2.csv", "ml/outputs/eval_ncert_run2.csv"],
                    help="evaluate_models.py output CSVs to scan (base_output / tuned_output columns)")
    ap.add_argument("--write-filtered", action="store_true")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    in_dir = Path(args.in_dir)
    train = read_tsv(in_dir / "train_clean.tsv")
    flagged = train.english.map(is_archaic)
    print(f"Training rows with archaic markers: {int(flagged.sum())} / {len(train)} ({flagged.mean():.1%})")

    sample = train[flagged]
    if len(sample):
        print("\nRandom flagged training rows (do these look like Bible text?):")
        for _, row in sample.sample(min(10, len(sample)), random_state=args.seed).iterrows():
            print("  EN:", row.english[:140])

    print("\nModel outputs containing archaic markers:")
    for path in args.eval:
        p = Path(path)
        if not p.exists():
            print(f"  {path}: not found, skipped")
            continue
        df = pd.read_csv(p, dtype=str, keep_default_na=False, na_filter=False, encoding="utf-8-sig")
        n = len(df)
        base = int(df.base_output.map(is_archaic).sum())
        tuned = int(df.tuned_output.map(is_archaic).sum())
        ref = int(df.reference.map(is_archaic).sum()) if "reference" in df.columns else 0
        print(f"  {p.name}: base {base}/{n} ({base / n:.1%})   tuned {tuned}/{n} ({tuned / n:.1%})   references {ref}/{n}")

    if args.write_filtered:
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        kept = train[~flagged]
        kept.to_csv(out_dir / "train_clean.tsv", sep="\t", index=False)
        for name in ("validation.tsv", "test.tsv", "test_ood.tsv"):
            if (in_dir / name).exists():
                shutil.copy(in_dir / name, out_dir / name)  # evaluation splits are copied UNCHANGED
        print(f"\nWrote {out_dir}/train_clean.tsv: {len(train)} -> {len(kept)} rows "
              f"({int(flagged.sum())} removed). Validation/test copied unchanged.")
    else:
        print("\nReport only. Add --write-filtered to save a training set without these rows.")


if __name__ == "__main__":
    main()