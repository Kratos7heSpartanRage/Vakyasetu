"""
Inspect (and optionally clean) the Samayik English-Sanskrit dataset.

Run from the repo root, with the .venv active:
    python ml/scripts/inspect_samayik.py            # report only, writes nothing
    python ml/scripts/inspect_samayik.py --examples # also prints samples of each flagged category
    python ml/scripts/inspect_samayik.py --write    # also saves splits to data/processed/

Rules:
  * The official splits (train / validation / test / test_ood) are used as they come.
  * Rows are only ever DROPPED from train. Validation and test are never filtered.
  * The same light text normalisation (Unicode NFC, whitespace, wrapping quotes) is
    applied to every split so they stay comparable.
  * Every rule prints how many rows it touches, so nothing is silent.
"""

import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

DATASET = "acomquest/Saamayik"
NCERT_FILE = Path("ml/data/ncert_sentences.txt")
OUT_DIR = Path("data/processed")

# English words / Sanskrit words. Sanskrit compounds make Sanskrit sides shorter,
# so these bounds are generous: only extreme outliers (likely misalignments) are dropped.
MIN_RATIO, MAX_RATIO = 0.25, 8.0
# Sanskrit side: Samayik has many tutorial lines that mix Sanskrit with English UI terms
# (e.g. 'Database Host नाम localhost इति ददामि'). Those are real Sanskrit and are kept; only
# rows that are almost entirely Latin (English copied into the Sanskrit side) are dropped.
MIN_DEVA_FRAC_SA = 0.15
# English side: must be mostly Latin letters (otherwise Sanskrit was copied into the English side).
MIN_LATIN_FRAC_EN = 0.5

DEVA = re.compile(r"[\u0900-\u097F]")
LATIN = re.compile(r"[A-Za-z]")
QUOTE_WRAP = re.compile(r'^["\u201c\u201d]+\s*(.*?)\s*["\u201c\u201d]+$', re.S)
ANY_QUOTE = re.compile(r'["\u201c\u201d]')


def norm(value):
    text = unicodedata.normalize("NFC", str(value))
    return re.sub(r"\s+", " ", text).strip()


def strip_wrapping_quotes(text):
    """Turn '\"\"\"Hello\"\"\"' into 'Hello', but leave text with quotes inside alone."""
    m = QUOTE_WRAP.match(text)
    if m and not ANY_QUOTE.search(m.group(1)):
        return m.group(1)
    return text


def frac(pattern, text):
    letters = [c for c in text if c.isalpha()]
    return len(pattern.findall(text)) / len(letters) if letters else 0.0


def detect_columns(df, n=200):
    """For flat tables: guess which columns hold Sanskrit and English by their script."""
    sample = df.head(n)
    deva, latin = {}, {}
    for col in df.columns:
        vals = [norm(v) for v in sample[col] if isinstance(v, str) and v.strip()]
        if not vals:
            continue
        deva[col] = sum(frac(DEVA, v) for v in vals) / len(vals)
        avg_len = sum(len(v) for v in vals) / len(vals)
        latin[col] = sum(frac(LATIN, v) for v in vals) / len(vals) * avg_len
    if len(deva) < 2:
        raise SystemExit(f"Could not find two text columns in {list(df.columns)}")
    sa = max(deva, key=deva.get)
    en = max((c for c in latin if c != sa), key=latin.get)
    return sa, en


def prepare(df):
    """Return a frame with columns sanskrit, english (+ source if present)."""
    first = df["translation"].iloc[0] if "translation" in df.columns else None
    if isinstance(first, dict):  # Hugging Face translation format: {'en': ..., 'sa': ...}
        if not {"sa", "en"} <= set(first):
            raise SystemExit(f"Expected keys 'sa' and 'en', found {list(first)}")
        out = pd.DataFrame({
            "sanskrit": df["translation"].map(lambda d: d.get("sa", "")),
            "english": df["translation"].map(lambda d: d.get("en", "")),
        })
    else:
        sa, en = detect_columns(df)
        print(f"  (flat table) Sanskrit column = {sa!r}, English column = {en!r}")
        out = df[[sa, en]].copy()
        out.columns = ["sanskrit", "english"]
    if "source" in df.columns:
        out["source"] = df["source"].astype(str)

    for col in ("sanskrit", "english"):
        out[col] = out[col].map(norm)
    before = out[["sanskrit", "english"]].copy()
    for col in ("sanskrit", "english"):
        out[col] = out[col].map(strip_wrapping_quotes)
    changed = int((before != out[["sanskrit", "english"]]).any(axis=1).sum())
    return out, changed


def word_ratio(df):
    sa_w = df["sanskrit"].str.split().str.len().clip(lower=1)
    en_w = df["english"].str.split().str.len()
    return en_w / sa_w


def report(df, name):
    ratio = word_ratio(df)
    print(f"\n[{name}] rows: {len(df)}")
    if "source" in df.columns:
        print("  by source                      :", {k: int(v) for k, v in df["source"].value_counts().items()})
    print("  empty sanskrit or english      :", int(((df.sanskrit == "") | (df.english == "")).sum()))
    print("  sanskrit almost no Devanagari  :", int((df.sanskrit.map(lambda s: frac(DEVA, s)) < MIN_DEVA_FRAC_SA).sum()))
    print("  english not mostly Latin       :", int((df.english.map(lambda s: frac(LATIN, s)) < MIN_LATIN_FRAC_EN).sum()))
    print(f"  length ratio outside [{MIN_RATIO}, {MAX_RATIO}]:", int(((ratio < MIN_RATIO) | (ratio > MAX_RATIO)).sum()))
    print("  exact duplicate pairs          :", int(df.duplicated(subset=["sanskrit", "english"]).sum()))
    print("  median words (sa / en)         :", int(df.sanskrit.str.split().str.len().median()),
          "/", int(df.english.str.split().str.len().median()))


def clean_train(train, held_out_sanskrit):
    """Drop bad rows from train only. Returns cleaned frame and a log of what each rule removed."""
    log, df = [], train.copy()

    def drop(mask, label):
        nonlocal df
        log.append((label, int(mask.sum())))
        df = df[~mask]

    drop((df.sanskrit == "") | (df.english == ""), "empty side")
    drop(df.sanskrit.map(lambda s: frac(DEVA, s)) < MIN_DEVA_FRAC_SA, "sanskrit almost no Devanagari (English copy)")
    drop(df.english.map(lambda s: frac(LATIN, s)) < MIN_LATIN_FRAC_EN, "english not Latin")
    ratio = word_ratio(df)
    drop((ratio < MIN_RATIO) | (ratio > MAX_RATIO), "extreme length ratio")
    drop(df.duplicated(subset=["sanskrit", "english"]), "exact duplicate pair")
    drop(df.sanskrit.isin(held_out_sanskrit), "sanskrit also in validation/test (leakage)")
    return df.reset_index(drop=True), log


def show_examples(df, n=10, seed=0):
    """Print random examples of each flagged category so the rules can be judged by eye."""
    ratio = word_ratio(df)
    groups = {
        "sanskrit almost no Devanagari": df.sanskrit.map(lambda s: frac(DEVA, s)) < MIN_DEVA_FRAC_SA,
        "english not mostly Latin": df.english.map(lambda s: frac(LATIN, s)) < MIN_LATIN_FRAC_EN,
        "extreme length ratio": (ratio < MIN_RATIO) | (ratio > MAX_RATIO),
    }
    for label, mask in groups.items():
        sub = df[mask]
        k = min(n, len(sub))
        print(f"\n--- {label}: {len(sub)} rows, showing {k} random ---")
        for _, row in sub.sample(k, random_state=seed).iterrows():
            print("  SA:", repr(row.sanskrit))
            print("  EN:", repr(row.english))
            print()


def main():
    from datasets import load_dataset  # imported here so the helpers above stay testable

    write = "--write" in sys.argv
    ds = load_dataset(DATASET)
    print(ds)

    splits = {}
    for name, split in ds.items():
        splits[name], n_quotes = prepare(split.to_pandas())
        print(f"{name}: wrapping quotes stripped from {n_quotes} rows")

    print("\nSample rows after normalisation (train):")
    print(splits["train"].head(5).to_string())

    for name, df in splits.items():
        report(df, name)

    if "--examples" in sys.argv:
        print("\nRaw vs processed (exact characters), train rows 2 and 4:")
        for i in (2, 4):
            print("  raw      :", repr(ds["train"][i]["translation"]))
            print("  processed:", repr(splits["train"].iloc[i].sanskrit), "|", repr(splits["train"].iloc[i].english))
        show_examples(splits["train"])

    if "train" not in splits:
        raise SystemExit("No 'train' split found; check the dataset structure printed above.")

    held_out = set()
    for name, df in splits.items():
        if name != "train":
            held_out |= set(df.sanskrit)

    cleaned, log = clean_train(splits["train"], held_out)
    print("\nCleaning train:")
    for label, n in log:
        print(f"  removed {n:6d}  {label}")
    print(f"  train: {len(splits['train'])} -> {len(cleaned)} rows")
    if "source" in cleaned.columns:
        print("  train by source after cleaning:", {k: int(v) for k, v in cleaned["source"].value_counts().items()})

    if NCERT_FILE.exists():
        ncert = {norm(l) for l in NCERT_FILE.read_text(encoding="utf-8").splitlines() if l.strip()}
        for name, df in {**splits, "train_cleaned": cleaned}.items():
            print(f"  NCERT gold sentences found in {name}: {len(ncert & set(df.sanskrit))} / {len(ncert)}")

    if write:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        cleaned.to_csv(OUT_DIR / "train_clean.tsv", sep="\t", index=False)
        for name, df in splits.items():
            if name != "train":
                df.to_csv(OUT_DIR / f"{name}.tsv", sep="\t", index=False)
        print(f"\nSaved to {OUT_DIR}/ (git-ignored). Validation/test rows were not filtered.")
    else:
        print("\nReport only. Re-run with --write to save the files.")


if __name__ == "__main__":
    main()