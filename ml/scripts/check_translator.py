"""
End-to-end check of ml/translator.py on the REAL model and adapter.

Before running:
  * the .venv is active (your prompt starts with "(.venv)")
  * the GPU is free: `nvidia-smi` shows about 0 MiB used
  * ml/translator.py and this file (ml/scripts/check_translator.py) are in place

Run from the repo root:
    python -u ml/scripts/check_translator.py --adapter ml/checkpoints/run2_full
    python -u ml/scripts/check_translator.py --adapter ml/checkpoints/run2_full --device cpu   # if the GPU is busy

The -u flag shows each line as it happens instead of all at the end.
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the ml/ folder, where translator.py lives
from translator import Translator

SENTENCES = [
    "बालकः विद्यालयं गच्छति।",                             # one simple sentence
    "किं ते वर्तनम्? प्रतिदिनं सुवर्णशतचतुष्टयं देव!",       # two sentences, split at ? and !
    "सा पुस्तकं पठति। अहं जलं पिबामि।",                    # two sentences, split at the danda
]
BAD_INPUTS = ["", "balakah vidyalayam gacchati"]            # empty, and romanised (not Devanagari)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--adapter", required=True, help="folder with adapter_config.json")
    ap.add_argument("--device", default=None, help="cuda or cpu (default: cuda if available)")
    args = ap.parse_args()

    print("Loading model and adapter (and one warm-up sentence). The first run can take several minutes...")
    t0 = time.time()
    translator = Translator(args.adapter, device=args.device)
    print(f"Loaded in {time.time() - t0:.0f}s on {translator.device}\n")

    for text in SENTENCES:
        t0 = time.time()
        result = translator.translate(text)
        print(text)
        print(f"  -> {result['translation']}   ({time.time() - t0:.1f}s)\n")

    for bad in BAD_INPUTS:
        try:
            translator.translate(bad)
            print(f"PROBLEM: no ValueError for {bad!r}")
        except ValueError as e:
            print(f"ok, rejected {bad!r}: {e}")

    if translator.device == "cuda":
        import torch
        print(f"\nPeak GPU memory held by tensors: {torch.cuda.max_memory_allocated() / 1e9:.2f} GB "
              "(nvidia-smi will show a bit more)")
    print("\nDone. The translator works end to end.")


if __name__ == "__main__":
    main()