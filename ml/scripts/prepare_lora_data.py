"""
Convert the cleaned Samayik TSVs into the folder layout IndicTrans2's LoRA script expects.

Run from the repo root, after `python ml/scripts/inspect_samayik.py --write`:
    python ml/scripts/prepare_lora_data.py                       # full data -> data/lora/
    python ml/scripts/prepare_lora_data.py --out-dir data/lora_smoke --train-limit 2000 --dev-size 200

Input  (written by inspect_samayik.py --write):
    data/processed/train_clean.tsv
    data/processed/validation.tsv

Output (layout from the IndicTrans2 huggingface_interface README; one sentence per line,
line N of the two files in a folder form one sentence pair):
    <out-dir>/train/san_Deva-eng_Latn/train.san_Deva
    <out-dir>/train/san_Deva-eng_Latn/train.eng_Latn
    <out-dir>/dev/san_Deva-eng_Latn/dev.san_Deva
    <out-dir>/dev/san_Deva-eng_Latn/dev.eng_Latn

Notes:
  * The test and test_ood splits are NOT written here. They stay in data/processed/ for evaluation.
  * Dev is a random sample of validation. The only rows dropped from it are ones with an
    empty side, because an empty line would misalign the two files.
"""

import argparse
from pathlib import Path

import pandas as pd

SRC, TGT = "san_Deva", "eng_Latn"
PAIR = f"{SRC}-{TGT}"


def read_tsv(path):
    # keep_default_na=False: sentences such as "NA" or "Null" must stay text, not become NaN
    df = pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False, na_filter=False)
    missing = {"sanskrit", "english"} - set(df.columns)
    if missing:
        raise SystemExit(f"{path} is missing columns {sorted(missing)}; found {list(df.columns)}")
    return df[["sanskrit", "english"]]


def one_line(text):
    """Guarantee a sentence occupies exactly one line."""
    return " ".join(str(text).split())


def write_pair(df, folder, split):
    folder.mkdir(parents=True, exist_ok=True)
    sa_path, en_path = folder / f"{split}.{SRC}", folder / f"{split}.{TGT}"
    sa_path.write_text("\n".join(df.sanskrit.map(one_line)) + "\n", encoding="utf-8")
    en_path.write_text("\n".join(df.english.map(one_line)) + "\n", encoding="utf-8")

    # verify: both files must have the same number of lines
    n_sa = len(sa_path.read_text(encoding="utf-8").splitlines())
    n_en = len(en_path.read_text(encoding="utf-8").splitlines())
    if not (n_sa == n_en == len(df)):
        raise SystemExit(f"Line count mismatch in {folder}: sanskrit={n_sa}, english={n_en}, rows={len(df)}")
    print(f"  {split}: {len(df)} pairs -> {folder}")
    return sa_path, en_path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in-dir", default="data/processed")
    ap.add_argument("--out-dir", default="data/lora")
    ap.add_argument("--dev-size", type=int, default=1000, help="max dev sentences sampled from validation")
    ap.add_argument("--train-limit", type=int, default=0, help="use only N random train rows (0 = all)")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    in_dir, out_dir = Path(args.in_dir), Path(args.out_dir)
    train = read_tsv(in_dir / "train_clean.tsv")
    dev = read_tsv(in_dir / "validation.tsv")

    train = train.sample(frac=1.0, random_state=args.seed).reset_index(drop=True)
    if args.train_limit:
        train = train.head(args.train_limit)

    before = len(dev)
    dev = dev[(dev.sanskrit.str.strip() != "") & (dev.english.str.strip() != "")]
    if before - len(dev):
        print(f"  dev: dropped {before - len(dev)} validation row(s) with an empty side")
    if len(dev) > args.dev_size:
        dev = dev.sample(n=args.dev_size, random_state=args.seed)
    dev = dev.reset_index(drop=True)

    print(f"Writing LoRA data to {out_dir}/")
    write_pair(train, out_dir / "train" / PAIR, "train")
    sa_path, _ = write_pair(dev, out_dir / "dev" / PAIR, "dev")

    print("\nFirst 3 training pairs:")
    for _, row in train.head(3).iterrows():
        print("  SA:", one_line(row.sanskrit))
        print("  EN:", one_line(row.english))
    print(f"\nDone. Data directory to pass to the training script: {out_dir}")


if __name__ == "__main__":
    main()