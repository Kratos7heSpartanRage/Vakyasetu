"""
Bootstrap confidence intervals and statistical significance for IndicTrans2 LoRA.

Computes 95% paired bootstrap confidence intervals (B=1,000 resamples) and empirical
p-values for BLEU and chrF gains (tuned vs base) on the test split.

Partitions evaluated:
  1. All test sentences (n=2,417)
  2. Modern English references (n=2,224, textbook proxy)
  3. Bible-style references (n=193, archaic style)

Usage:
    python ml/scripts/bootstrap_eval.py
    python ml/scripts/bootstrap_eval.py --input ml/outputs/eval_test_full_run2.csv --resamples 1000
"""

import argparse
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from sacrebleu.metrics import BLEU, CHRF

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bible_style_check import is_archaic


def compute_metrics(hyps, refs):
    b = BLEU().corpus_score(hyps, [refs]).score
    c = CHRF().corpus_score(hyps, [refs]).score
    return b, c


def paired_bootstrap(df, n_resamples=1000, seed=42):
    rng = np.random.RandomState(seed)
    n = len(df)
    base_hyps = df["base_output"].tolist()
    tuned_hyps = df["tuned_output"].tolist()
    refs = df["reference"].tolist()

    # Point estimates
    base_bleu, base_chrf = compute_metrics(base_hyps, refs)
    tuned_bleu, tuned_chrf = compute_metrics(tuned_hyps, refs)
    delta_bleu = tuned_bleu - base_bleu
    delta_chrf = tuned_chrf - base_chrf

    # Bootstrap resampling
    boot_delta_bleu = []
    boot_delta_chrf = []
    boot_base_bleu = []
    boot_tuned_bleu = []
    boot_base_chrf = []
    boot_tuned_chrf = []

    print(f"    Running {n_resamples} paired bootstrap resamples on n={n} sentences...")
    for i in range(n_resamples):
        idx = rng.randint(0, n, size=n)
        s_base = [base_hyps[j] for j in idx]
        s_tuned = [tuned_hyps[j] for j in idx]
        s_ref = [refs[j] for j in idx]

        bb, bc = compute_metrics(s_base, s_ref)
        tb, tc = compute_metrics(s_tuned, s_ref)

        boot_base_bleu.append(bb)
        boot_tuned_bleu.append(tb)
        boot_base_chrf.append(bc)
        boot_tuned_chrf.append(tc)
        boot_delta_bleu.append(tb - bb)
        boot_delta_chrf.append(tc - bc)

    # 95% Percentile Confidence Intervals
    ci_base_bleu = np.percentile(boot_base_bleu, [2.5, 97.5])
    ci_tuned_bleu = np.percentile(boot_tuned_bleu, [2.5, 97.5])
    ci_delta_bleu = np.percentile(boot_delta_bleu, [2.5, 97.5])

    ci_base_chrf = np.percentile(boot_base_chrf, [2.5, 97.5])
    ci_tuned_chrf = np.percentile(boot_tuned_chrf, [2.5, 97.5])
    ci_delta_chrf = np.percentile(boot_delta_chrf, [2.5, 97.5])

    # Empirical one-sided p-value for H0: delta <= 0
    p_bleu = np.mean([d <= 0 for d in boot_delta_bleu])
    p_chrf = np.mean([d <= 0 for d in boot_delta_chrf])

    return {
        "n": n,
        "base_bleu": base_bleu,
        "base_bleu_ci": ci_base_bleu,
        "tuned_bleu": tuned_bleu,
        "tuned_bleu_ci": ci_tuned_bleu,
        "delta_bleu": delta_bleu,
        "delta_bleu_ci": ci_delta_bleu,
        "p_bleu": p_bleu,
        "base_chrf": base_chrf,
        "base_chrf_ci": ci_base_chrf,
        "tuned_chrf": tuned_chrf,
        "tuned_chrf_ci": ci_tuned_chrf,
        "delta_chrf": delta_chrf,
        "delta_chrf_ci": ci_delta_chrf,
        "p_chrf": p_chrf,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="ml/outputs/eval_test_full_run2.csv",
                        help="Path to per-sentence evaluation CSV")
    parser.add_argument("--resamples", type=int, default=1000,
                        help="Number of bootstrap iterations (default 1000)")
    parser.add_argument("--out-csv", default="ml/outputs/bootstrap_evaluation.csv",
                        help="Path to save bootstrap summary CSV")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {input_path} not found.")
        sys.exit(1)

    print(f"Loading {input_path}...")
    df = pd.read_csv(input_path, dtype=str, keep_default_na=False, na_filter=False, encoding="utf-8-sig")

    archaic_mask = df["reference"].map(is_archaic)
    subsets = [
        ("Full Test Split (All)", df),
        ("Modern English References (Textbook Proxy)", df[~archaic_mask]),
        ("Bible-style References (Archaic)", df[archaic_mask]),
    ]

    records = []
    print("\n" + "=" * 80)
    print("VAKYASETU: STATISTICAL EVALUATION WITH 95% BOOTSTRAP CONFIDENCE INTERVALS")
    print("=" * 80)

    for name, sub_df in subsets:
        print(f"\nEvaluating: {name} (n={len(sub_df)})...")
        res = paired_bootstrap(sub_df, n_resamples=args.resamples)
        res["subset"] = name
        records.append(res)

        p_str_b = "< 0.001" if res["p_bleu"] == 0 else f"{res['p_bleu']:.4f}"
        p_str_c = "< 0.001" if res["p_chrf"] == 0 else f"{res['p_chrf']:.4f}"

        print(f"  BLEU: Base {res['base_bleu']:.2f} [{res['base_bleu_ci'][0]:.2f}, {res['base_bleu_ci'][1]:.2f}] "
              f"-> Tuned {res['tuned_bleu']:.2f} [{res['tuned_bleu_ci'][0]:.2f}, {res['tuned_bleu_ci'][1]:.2f}]")
        print(f"        Delta: +{res['delta_bleu']:.2f} [{res['delta_bleu_ci'][0]:.2f}, {res['delta_bleu_ci'][1]:.2f}] (p {p_str_b})")
        print(f"  chrF: Base {res['base_chrf']:.2f} [{res['base_chrf_ci'][0]:.2f}, {res['base_chrf_ci'][1]:.2f}] "
              f"-> Tuned {res['tuned_chrf']:.2f} [{res['tuned_chrf_ci'][0]:.2f}, {res['tuned_chrf_ci'][1]:.2f}]")
        print(f"        Delta: +{res['delta_chrf']:.2f} [{res['delta_chrf_ci'][0]:.2f}, {res['delta_chrf_ci'][1]:.2f}] (p {p_str_c})")

    # Save summary table
    summary_rows = []
    for r in records:
        summary_rows.append({
            "Subset": r["subset"],
            "N": r["n"],
            "Base BLEU (95% CI)": f"{r['base_bleu']:.2f} [{r['base_bleu_ci'][0]:.2f}, {r['base_bleu_ci'][1]:.2f}]",
            "Tuned BLEU (95% CI)": f"{r['tuned_bleu']:.2f} [{r['tuned_bleu_ci'][0]:.2f}, {r['tuned_bleu_ci'][1]:.2f}]",
            "Delta BLEU (95% CI)": f"+{r['delta_bleu']:.2f} [{r['delta_bleu_ci'][0]:.2f}, {r['delta_bleu_ci'][1]:.2f}]",
            "p-value (BLEU)": "< 0.001" if r["p_bleu"] == 0 else f"{r['p_bleu']:.4f}",
            "Base chrF (95% CI)": f"{r['base_chrf']:.2f} [{r['base_chrf_ci'][0]:.2f}, {r['base_chrf_ci'][1]:.2f}]",
            "Tuned chrF (95% CI)": f"{r['tuned_chrf']:.2f} [{r['tuned_chrf_ci'][0]:.2f}, {r['tuned_chrf_ci'][1]:.2f}]",
            "Delta chrF (95% CI)": f"+{r['delta_chrf']:.2f} [{r['delta_chrf_ci'][0]:.2f}, {r['delta_chrf_ci'][1]:.2f}]",
            "p-value (chrF)": "< 0.001" if r["p_chrf"] == 0 else f"{r['p_chrf']:.4f}",
        })
    out_df = pd.DataFrame(summary_rows)
    out_path = Path(args.out_csv)
    out_df.to_csv(out_path, index=False)
    print(f"\nSaved statistical summary to {out_path}")


if __name__ == "__main__":
    main()
