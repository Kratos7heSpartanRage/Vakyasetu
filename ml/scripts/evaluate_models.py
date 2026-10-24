"""
Compare the UNMODIFIED IndicTrans2 model with a LoRA-fine-tuned adapter on the same sentences.

The base model is loaded once. The tuned result uses the adapter; the baseline result is
produced by switching the adapter off (PEFT's disable_adapter), so only one model is in memory.

Run from the repo root with the .venv active, and NOT while a training run is using the GPU.

Examples:
  # your NCERT sentences (CSV needs columns: sanskrit, reference_english)
  python ml/scripts/evaluate_models.py --adapter ml/checkpoints/run1 \
      --data ml/outputs/baseline_outputs_annotated.csv --name ncert

  # 500 random sentences from the official Samayik test split (TSV columns: sanskrit, english)
  python ml/scripts/evaluate_models.py --adapter ml/checkpoints/run1 \
      --data data/processed/test.tsv --name test500 --limit 500

  # same, with repeated-phrase loops blocked (use a different --name so results are kept apart)
  python ml/scripts/evaluate_models.py --adapter ml/checkpoints/run2_full \
      --data ml/outputs/baseline_outputs_annotated.csv --name ncert_run2_nr3 --no-repeat-ngram 3

Writes:
  ml/outputs/eval_<name>.csv   per-sentence outputs from both models + sentence chrF
  ml/outputs/eval_scores.csv   one summary row appended per run (for your report)
"""

import argparse
import csv
import time
from pathlib import Path

import pandas as pd
from sacrebleu.metrics import BLEU, CHRF

CKPT = "ai4bharat/indictrans2-indic-en-dist-200M"
SRC_LANG, TGT_LANG = "san_Deva", "eng_Latn"
MAX_LEN = 256


# ---------- data ----------

def load_pairs(path, limit=0, seed=0):
    """Return (sanskrit list, reference list). Rows with an empty side are skipped and reported."""
    path = Path(path)
    sep = "\t" if path.suffix == ".tsv" else ","
    df = pd.read_csv(path, sep=sep, dtype=str, keep_default_na=False, na_filter=False,
                     encoding="utf-8-sig")
    if "sanskrit" not in df.columns:
        raise SystemExit(f"{path} has no 'sanskrit' column; found {list(df.columns)}")
    ref_col = next((c for c in ("reference_english", "english") if c in df.columns), None)
    if ref_col is None:
        raise SystemExit(f"{path} needs a 'reference_english' or 'english' column; found {list(df.columns)}")

    df = df[["sanskrit", ref_col]].rename(columns={ref_col: "reference"})
    df["sanskrit"] = df["sanskrit"].str.strip()
    df["reference"] = df["reference"].str.strip()
    keep = (df.sanskrit != "") & (df.reference != "")
    if (~keep).sum():
        print(f"  skipped {int((~keep).sum())} row(s) with an empty Sanskrit or reference cell")
    df = df[keep]
    if df.empty:
        raise SystemExit("No usable rows. If this is your NCERT CSV, fill in the reference_english column first.")
    if limit and len(df) > limit:
        df = df.sample(n=limit, random_state=seed)
    df = df.reset_index(drop=True)
    return df.sanskrit.tolist(), df.reference.tolist()


# ---------- translation ----------

def run_batches(sentences, generate_batch, batch_size):
    """Translate in length-sorted batches (less padding, faster), returning results in the ORIGINAL order."""
    order = sorted(range(len(sentences)), key=lambda i: len(sentences[i]))
    results = [None] * len(sentences)
    for start in range(0, len(order), batch_size):
        idx = order[start:start + batch_size]
        outs = generate_batch([sentences[i] for i in idx])
        if len(outs) != len(idx):
            raise RuntimeError(f"generate_batch returned {len(outs)} outputs for {len(idx)} inputs")
        for i, out in zip(idx, outs):
            results[i] = out
        done = min(start + batch_size, len(order))
        if done % (batch_size * 10) == 0 or done == len(order):
            print(f"    {done}/{len(order)}")
    return results


def make_generator(model, tokenizer, ip, device, beams, no_repeat=0):
    import torch

    def generate_batch(batch):
        prepared = ip.preprocess_batch(batch, src_lang=SRC_LANG, tgt_lang=TGT_LANG)
        inputs = tokenizer(prepared, padding="longest", truncation=True,
                           max_length=MAX_LEN, return_tensors="pt").to(device)
        gen_kwargs = dict(max_length=MAX_LEN, num_beams=beams, num_return_sequences=1)
        if no_repeat:  # forbids repeating any n-gram of this size, which stops "and a scribe, and a scribe, ..." loops
            gen_kwargs["no_repeat_ngram_size"] = no_repeat
        with torch.inference_mode():
            generated = model.generate(**inputs, **gen_kwargs)
        decoded = tokenizer.batch_decode(generated, skip_special_tokens=True,
                                         clean_up_tokenization_spaces=True)
        return ip.postprocess_batch(decoded, lang=TGT_LANG)

    return generate_batch


# ---------- scoring and output ----------

def score(hyps, refs):
    return BLEU().corpus_score(hyps, [refs]).score, CHRF().corpus_score(hyps, [refs]).score


def write_outputs(out_dir, name, adapter, sanskrit, refs, base, tuned):
    out_dir.mkdir(parents=True, exist_ok=True)
    chrf = CHRF()
    detail = out_dir / f"eval_{name}.csv"
    with open(detail, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["sanskrit", "reference", "base_output", "tuned_output", "chrf_base", "chrf_tuned"])
        for s, r, b, t in zip(sanskrit, refs, base, tuned):
            w.writerow([s, r, b, t, round(chrf.sentence_score(b, [r]).score, 1),
                        round(chrf.sentence_score(t, [r]).score, 1)])

    b_bleu, b_chrf = score(base, refs)
    t_bleu, t_chrf = score(tuned, refs)
    summary = out_dir / "eval_scores.csv"
    new = not summary.exists()
    with open(summary, "a", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["name", "adapter", "n_sentences", "bleu_base", "chrf_base", "bleu_tuned", "chrf_tuned"])
        w.writerow([name, adapter, len(refs), round(b_bleu, 1), round(b_chrf, 1),
                    round(t_bleu, 1), round(t_chrf, 1)])
    return detail, (b_bleu, b_chrf), (t_bleu, t_chrf)


# ---------- main ----------

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--adapter", required=True, help="folder containing adapter_config.json")
    ap.add_argument("--data", required=True, help="CSV/TSV with a sanskrit column and a reference column")
    ap.add_argument("--name", required=True, help="label used in the output file names")
    ap.add_argument("--limit", type=int, default=0, help="score only N random rows (0 = all)")
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--beams", type=int, default=5)
    ap.add_argument("--no-repeat-ngram", type=int, default=0,
                    help="forbid repeated n-grams of this size (try 3); 0 = off. Put it in --name, e.g. ncert_run2_nr3")
    ap.add_argument("--device", default=None, help="cuda or cpu (default: cuda if available)")
    ap.add_argument("--out-dir", default="ml/outputs")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    adapter = Path(args.adapter)
    if not (adapter / "adapter_config.json").exists():
        raise SystemExit(f"No adapter_config.json in {adapter}")

    sanskrit, refs = load_pairs(args.data, args.limit, args.seed)
    print(f"Loaded {len(sanskrit)} sentence pairs from {args.data}")

    import torch
    from peft import PeftModel
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    from IndicTransToolkit import IndicProcessor

    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}. Loading base model and adapter...")
    ip = IndicProcessor(inference=True)
    tokenizer = AutoTokenizer.from_pretrained(CKPT, trust_remote_code=True)
    base_model = AutoModelForSeq2SeqLM.from_pretrained(CKPT, trust_remote_code=True)
    model = PeftModel.from_pretrained(base_model, str(adapter)).to(device)
    model.eval()
    generate = make_generator(model, tokenizer, ip, device, args.beams, args.no_repeat_ngram)

    t0 = time.time()
    print("  tuned model (adapter on):")
    tuned = run_batches(sanskrit, generate, args.batch_size)
    print("  base model (adapter off):")
    with model.disable_adapter():
        base = run_batches(sanskrit, generate, args.batch_size)
    print(f"  translation took {time.time() - t0:.0f}s")

    detail, (b_bleu, b_chrf), (t_bleu, t_chrf) = write_outputs(
        Path(args.out_dir), args.name, str(adapter), sanskrit, refs, base, tuned)

    print(f"\nResults on {len(refs)} sentences ({args.name}):")
    print(f"  {'model':<22}{'BLEU':>8}{'chrF':>8}")
    print(f"  {'base (unmodified)':<22}{b_bleu:>8.1f}{b_chrf:>8.1f}")
    print(f"  {'tuned (' + adapter.name + ')':<22}{t_bleu:>8.1f}{t_chrf:>8.1f}")
    print(f"\nPer-sentence outputs: {detail}")
    if len(refs) < 100:
        print("Note: with fewer than ~100 sentences, treat BLEU as noisy and look at chrF and the outputs themselves.")


if __name__ == "__main__":
    main()