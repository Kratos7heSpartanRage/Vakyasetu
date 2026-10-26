"""
Comprehensive Evaluation Suite for IndicTrans2 LoRA Models on NCERT / Samayik Data.

Features:
  1. Compares Base (unmodified IndicTrans2), Primary Tuned Adapter (Run 2), and optional Compare Adapter.
  2. Computes Paired Bootstrap Resampling (B=1,000) for 95% Confidence Intervals and p-values.
  3. Reports chrF primarily (character n-grams are robust for morphologically rich Sanskrit), with BLEU secondary.
  4. Automatic Per-Tag Breakdown: splits by has_sandhi, has_compound, sentence_type, tense, class.
  5. Includes a fast --mock mode for testing the scoring/bootstrap pipeline without GPU/heavy weights.

Usage Examples:
  # Standard evaluation on NCERT gold benchmark
  python ml/scripts/evaluate_models.py --adapter models/adapter \
      --data ml/data/ncert_eval_gold.csv --name ncert_gold --no-repeat-ngram 3

  # Head-to-head comparison between Run 2 and Run 3
  python ml/scripts/evaluate_models.py --adapter models/adapter \
      --compare-adapter ml/checkpoints/run3_filtered \
      --data ml/data/ncert_eval_gold.csv --name ncert_compare

  # Fast mock pipeline test (no GPU or model loading needed)
  python ml/scripts/evaluate_models.py --adapter models/adapter \
      --data ml/data/ncert_eval_gold.csv --name test_mock --mock --resamples 200
"""

import argparse
import csv
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sacrebleu.metrics import BLEU, CHRF

CKPT = "ai4bharat/indictrans2-indic-en-dist-200M"
SRC_LANG, TGT_LANG = "san_Deva", "eng_Latn"
MAX_LEN = 256
TAG_COLUMNS = ["has_sandhi", "has_compound", "sentence_type", "tense", "class"]
MIN_TAG_ROWS = 5


# ---------- data loading ----------

def load_evaluation_data(path, limit=0, seed=0):
    """Loads evaluation dataset, preserving all tagging columns for faceted breakdowns."""
    path = Path(path)
    sep = "\t" if path.suffix == ".tsv" else ","
    df = pd.read_csv(path, sep=sep, dtype=str, keep_default_na=False, na_filter=False, encoding="utf-8-sig")

    if "sanskrit" not in df.columns:
        raise SystemExit(f"{path} missing required 'sanskrit' column; found {list(df.columns)}")

    ref_col = next((c for c in ("reference_english", "reference", "english") if c in df.columns), None)
    if ref_col is None:
        raise SystemExit(f"{path} missing reference column ('reference_english', 'reference', or 'english')")

    df["sanskrit"] = df["sanskrit"].str.strip()
    df["reference"] = df[ref_col].str.strip()

    keep = (df["sanskrit"] != "") & (df["reference"] != "")
    if (~keep).sum():
        print(f"  Skipped {int((~keep).sum())} row(s) with empty Sanskrit or reference text.")
    df = df[keep]

    if df.empty:
        raise SystemExit("Error: Evaluation dataset contains no usable rows.")

    if limit and len(df) > limit:
        df = df.sample(n=limit, random_state=seed)

    return df.reset_index(drop=True)


# ---------- metrics & bootstrap ----------

def compute_corpus_scores(hyps, refs):
    """Computes primary chrF and secondary BLEU score."""
    c = CHRF().corpus_score(hyps, [refs]).score
    b = BLEU().corpus_score(hyps, [refs]).score
    return round(c, 2), round(b, 2)


def paired_bootstrap_metrics(hyps_tuned, hyps_base, refs, n_resamples=1000, seed=42):
    """
    Computes 95% paired percentile bootstrap confidence intervals and empirical p-value.
    Returns:
      dict with base_chrf, tuned_chrf, delta_chrf, chrf_ci, p_chrf, and BLEU equivalents.
    """
    n = len(refs)
    if n == 0:
        return None

    tuned_chrf, tuned_bleu = compute_corpus_scores(hyps_tuned, refs)
    base_chrf, base_bleu = compute_corpus_scores(hyps_base, refs)
    delta_chrf = tuned_chrf - base_chrf
    delta_bleu = tuned_bleu - base_bleu

    if n < MIN_TAG_ROWS or n_resamples <= 0:
        return {
            "n": n,
            "base_chrf": base_chrf, "tuned_chrf": tuned_chrf, "delta_chrf": delta_chrf,
            "chrf_ci": (base_chrf, tuned_chrf), "delta_chrf_ci": (0.0, 0.0), "p_chrf": 1.0,
            "base_bleu": base_bleu, "tuned_bleu": tuned_bleu, "delta_bleu": delta_bleu,
            "bleu_ci": (base_bleu, tuned_bleu), "delta_bleu_ci": (0.0, 0.0), "p_bleu": 1.0,
        }

    rng = np.random.RandomState(seed)
    boot_delta_chrf = []
    boot_delta_bleu = []
    boot_tuned_chrf = []
    boot_base_chrf = []

    for _ in range(n_resamples):
        idx = rng.randint(0, n, size=n)
        s_tuned = [hyps_tuned[j] for j in idx]
        s_base = [hyps_base[j] for j in idx]
        s_ref = [refs[j] for j in idx]

        tc, tb = compute_corpus_scores(s_tuned, s_ref)
        bc, bb = compute_corpus_scores(s_base, s_ref)

        boot_tuned_chrf.append(tc)
        boot_base_chrf.append(bc)
        boot_delta_chrf.append(tc - bc)
        boot_delta_bleu.append(tb - bb)

    delta_chrf_ci = np.percentile(boot_delta_chrf, [2.5, 97.5])
    tuned_chrf_ci = np.percentile(boot_tuned_chrf, [2.5, 97.5])
    delta_bleu_ci = np.percentile(boot_delta_bleu, [2.5, 97.5])

    p_chrf = np.mean([d <= 0 for d in boot_delta_chrf])
    p_bleu = np.mean([d <= 0 for d in boot_delta_bleu])

    return {
        "n": n,
        "base_chrf": base_chrf,
        "tuned_chrf": tuned_chrf,
        "tuned_chrf_ci": (round(tuned_chrf_ci[0], 2), round(tuned_chrf_ci[1], 2)),
        "delta_chrf": round(delta_chrf, 2),
        "delta_chrf_ci": (round(delta_chrf_ci[0], 2), round(delta_chrf_ci[1], 2)),
        "p_chrf": round(p_chrf, 4),
        "base_bleu": base_bleu,
        "tuned_bleu": tuned_bleu,
        "delta_bleu": round(delta_bleu, 2),
        "delta_bleu_ci": (round(delta_bleu_ci[0], 2), round(delta_bleu_ci[1], 2)),
        "p_bleu": round(p_bleu, 4),
    }


# ---------- generation ----------

def make_generator(model, tokenizer, ip, device, beams, no_repeat=0):
    import torch

    def generate_batch(batch):
        prepared = ip.preprocess_batch(batch, src_lang=SRC_LANG, tgt_lang=TGT_LANG)
        inputs = tokenizer(prepared, padding="longest", truncation=True,
                           max_length=MAX_LEN, return_tensors="pt").to(device)
        gen_kwargs = dict(max_length=MAX_LEN, num_beams=beams, num_return_sequences=1)
        if no_repeat:
            gen_kwargs["no_repeat_ngram_size"] = no_repeat
        with torch.inference_mode():
            generated = model.generate(**inputs, **gen_kwargs)
        decoded = tokenizer.batch_decode(generated, skip_special_tokens=True,
                                         clean_up_tokenization_spaces=True)
        return ip.postprocess_batch(decoded, lang=TGT_LANG)

    return generate_batch


def run_batches(sentences, generate_batch, batch_size):
    """Sorts by length to minimize padding, preserves original order."""
    order = sorted(range(len(sentences)), key=lambda i: len(sentences[i]))
    results = [None] * len(sentences)
    for start in range(0, len(order), batch_size):
        idx = order[start:start + batch_size]
        outs = generate_batch([sentences[i] for i in idx])
        for i, out in zip(idx, outs):
            results[i] = out
        done = min(start + batch_size, len(order))
        if done % (batch_size * 10) == 0 or done == len(order):
            print(f"    {done}/{len(order)}")
    return results


# ---------- main evaluation routine ----------

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--adapter", required=True, help="Path to primary LoRA adapter (e.g. models/adapter)")
    ap.add_argument("--compare-adapter", default=None, help="Optional secondary adapter to compare head-to-head")
    ap.add_argument("--data", required=True, help="Evaluation dataset CSV or TSV")
    ap.add_argument("--name", required=True, help="Experiment label for output filenames")
    ap.add_argument("--resamples", type=int, default=1000, help="Number of bootstrap resamples (default 1000)")
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--beams", type=int, default=5)
    ap.add_argument("--no-repeat-ngram", type=int, default=3, help="no_repeat_ngram_size (default 3)")
    ap.add_argument("--device", default=None, help="cuda or cpu")
    ap.add_argument("--limit", type=int, default=0, help="Limit number of rows evaluated (0 = all)")
    ap.add_argument("--out-dir", default="ml/outputs")
    ap.add_argument("--mock", action="store_true", help="Run in fast mock mode for testing without GPU/model loading")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = load_evaluation_data(args.data, limit=args.limit, seed=args.seed)
    sanskrit = df["sanskrit"].tolist()
    refs = df["reference"].tolist()
    n = len(df)
    print(f"Loaded {n} sentences from {args.data}")

    # Generate or mock translations
    if args.mock:
        print("  [MOCK MODE] Generating simulated translations for test...")
        base_preds = [f"Base translation for: {s[:25]}" for s in sanskrit]
        tuned_preds = [r if i % 3 == 0 else f"{r} (tuned variation)" for i, r in enumerate(refs)]
        comp_preds = None
        if args.compare_adapter:
            comp_preds = [f"Comp translation for: {s[:25]}" for s in sanskrit]
    else:
        import torch
        from peft import PeftModel
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        from IndicTransToolkit import IndicProcessor

        device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Device: {device}. Loading base model and adapter: {args.adapter}...")

        ip = IndicProcessor(inference=True)
        tokenizer = AutoTokenizer.from_pretrained(CKPT, trust_remote_code=True)
        base_model = AutoModelForSeq2SeqLM.from_pretrained(CKPT, trust_remote_code=True)
        model = PeftModel.from_pretrained(base_model, str(args.adapter)).to(device)
        model.eval()
        generate = make_generator(model, tokenizer, ip, device, args.beams, args.no_repeat_ngram)

        t0 = time.time()
        print("  Evaluating tuned adapter (Run 2)...")
        tuned_preds = run_batches(sanskrit, generate, args.batch_size)

        print("  Evaluating base model (adapter disabled)...")
        with model.disable_adapter():
            base_preds = run_batches(sanskrit, generate, args.batch_size)
        print(f"  Inference finished in {time.time() - t0:.1f}s")

        comp_preds = None
        if args.compare_adapter:
            print(f"  Evaluating compare adapter: {args.compare_adapter}...")
            comp_adapter_path = Path(args.compare_adapter)
            if (comp_adapter_path / "adapter_config.json").exists():
                comp_model = PeftModel.from_pretrained(base_model, str(comp_adapter_path)).to(device)
                comp_model.eval()
                comp_gen = make_generator(comp_model, tokenizer, ip, device, args.beams, args.no_repeat_ngram)
                comp_preds = run_batches(sanskrit, comp_gen, args.batch_size)

    # Compute sentence-level chrF
    chrf_calc = CHRF()
    df["base_output"] = base_preds
    df["tuned_output"] = tuned_preds
    df["chrf_base"] = [round(chrf_calc.sentence_score(b, [r]).score, 1) for b, r in zip(base_preds, refs)]
    df["chrf_tuned"] = [round(chrf_calc.sentence_score(t, [r]).score, 1) for t, r in zip(tuned_preds, refs)]
    if comp_preds:
        df["comp_output"] = comp_preds
        df["chrf_comp"] = [round(chrf_calc.sentence_score(c, [r]).score, 1) for c, r in zip(comp_preds, refs)]

    detail_path = out_dir / f"eval_{args.name}.csv"
    df.to_csv(detail_path, index=False, encoding="utf-8-sig")
    print(f"\nSaved sentence-level outputs to {detail_path}")

    # Bootstrap evaluation overall and per tag
    summary_records = []

    print("\n" + "=" * 90)
    print(f"VAKYASETU EVALUATION REPORT: {args.name} (chrF Primary, BLEU Secondary)")
    print("=" * 90)

    # 1. Overall
    overall_res = paired_bootstrap_metrics(tuned_preds, base_preds, refs, n_resamples=args.resamples, seed=args.seed)
    overall_res["category"] = "Overall"
    overall_res["slice"] = "All Sentences"
    summary_records.append(overall_res)

    p_str = "< 0.001" if overall_res["p_chrf"] == 0 else f"{overall_res['p_chrf']:.4f}"
    print(f"OVERALL (n={overall_res['n']}):")
    print(f"  chrF: Base {overall_res['base_chrf']} -> Tuned {overall_res['tuned_chrf']} "
          f"[95% CI: {overall_res['tuned_chrf_ci'][0]}, {overall_res['tuned_chrf_ci'][1]}] | "
          f"Delta: +{overall_res['delta_chrf']} [{overall_res['delta_chrf_ci'][0]}, {overall_res['delta_chrf_ci'][1]}] (p {p_str})")
    print(f"  BLEU: Base {overall_res['base_bleu']} -> Tuned {overall_res['tuned_bleu']} | "
          f"Delta: +{overall_res['delta_bleu']} [{overall_res['delta_bleu_ci'][0]}, {overall_res['delta_bleu_ci'][1]}]")

    # 2. Per-Tag Breakdown
    for tag in TAG_COLUMNS:
        if tag in df.columns:
            print(f"\nBreakdown by: [{tag}]")
            for val, group in df.groupby(tag):
                if len(group) < MIN_TAG_ROWS:
                    continue
                g_tuned = group["tuned_output"].tolist()
                g_base = group["base_output"].tolist()
                g_refs = group["reference"].tolist()

                g_res = paired_bootstrap_metrics(g_tuned, g_base, g_refs, n_resamples=args.resamples, seed=args.seed)
                g_res["category"] = tag
                g_res["slice"] = str(val)
                summary_records.append(g_res)

                p_s = "< 0.001" if g_res["p_chrf"] == 0 else f"{g_res['p_chrf']:.4f}"
                sign = "+" if g_res["delta_chrf"] >= 0 else ""
                print(f"  {val:<20} (n={len(group):>3}): chrF {g_res['base_chrf']:>5.1f} -> {g_res['tuned_chrf']:>5.1f} "
                      f"| Delta: {sign}{g_res['delta_chrf']:>5.1f} [{g_res['delta_chrf_ci'][0]:>5.1f}, {g_res['delta_chrf_ci'][1]:>5.1f}] (p {p_s}) "
                      f"| BLEU: {g_res['base_bleu']:>4.1f} -> {g_res['tuned_bleu']:>4.1f}")

    # Save summary table
    summary_path = out_dir / f"eval_{args.name}_summary.csv"
    summary_df = pd.DataFrame([{
        "Category": r["category"],
        "Slice": r["slice"],
        "N": r["n"],
        "Base chrF": r["base_chrf"],
        "Tuned chrF": r["tuned_chrf"],
        "Tuned chrF 95% CI": f"[{r['tuned_chrf_ci'][0]}, {r['tuned_chrf_ci'][1]}]",
        "Delta chrF": f"{'+' if r['delta_chrf'] >= 0 else ''}{r['delta_chrf']}",
        "Delta chrF 95% CI": f"[{r['delta_chrf_ci'][0]}, {r['delta_chrf_ci'][1]}]",
        "p-value (chrF)": "< 0.001" if r["p_chrf"] == 0 else f"{r['p_chrf']:.4f}",
        "Base BLEU": r["base_bleu"],
        "Tuned BLEU": r["tuned_bleu"],
        "Delta BLEU": f"{'+' if r['delta_bleu'] >= 0 else ''}{r['delta_bleu']}",
    } for r in summary_records])
    summary_df.to_csv(summary_path, index=False)
    print(f"\nSaved statistical breakdown summary to {summary_path}")


if __name__ == "__main__":
    main()