# -*- coding: utf-8 -*-
"""
Evaluation of the VākyaSetu sandhi engine against token-aligned gold (ml/data/sandhi_gold.jsonl).

  python ml/scripts/evaluate_sandhi.py                  # all splits, per-split report
  python ml/scripts/evaluate_sandhi.py --split dev      # one split
  python ml/scripts/evaluate_sandhi.py --errors         # print every failure
  python ml/scripts/evaluate_sandhi.py --fail-under 0.8 # exit 1 if token accuracy is lower (CI)

Why these metrics (and not just "word F1")
  * token accuracy         : did the written token map to exactly the gold words?
  * outcome confusion      : gold {intact, reconstruct, split} x predicted -> shows OVER-segmentation
                             (splitting words that must stay whole) separately from missed splits.
  * accuracy by type       : visarga / vowel / consonant / compound / prefix-verb -> failure patterns for the report.
  * accuracy by status     : are 'resolved' tokens really more accurate than 'ambiguous'/'compound'? (honest calibration)
  * word-level P/R/F1      : kept for comparison with the old script (multiset of words).
The 'test' split is the only number that may be quoted as held-out accuracy.
"""
import argparse, collections, json, os, sys, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "backend"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from app.services.sandhi_engine import segment_sanskrit  # noqa: E402

GOLD = os.path.join(ROOT, "ml", "data", "sandhi_gold.jsonl")
OUT = os.path.join(ROOT, "ml", "outputs", "sandhi_eval.json")


def outcome(surface, words):
    if len(words) > 1:
        return "split"
    return "intact" if words and words[0] == surface else "reconstruct"


def prf(pred, gold):
    g = list(gold); tp = 0
    for p in pred:
        if p in g:
            g.remove(p); tp += 1
    P = tp / len(pred) if pred else 0.0
    R = tp / len(gold) if gold else 0.0
    return P, R, (2 * P * R / (P + R) if P + R else 0.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default=None)
    ap.add_argument("--errors", action="store_true")
    ap.add_argument("--fail-under", type=float, default=None)
    a = ap.parse_args()

    rows = [json.loads(l) for l in open(GOLD, encoding="utf-8") if l.strip()]
    splits = sorted({r["split"] for r in rows})
    if "test" not in splits:
        print("!! no 'test' split in the gold file: nothing here is held-out. Annotate real NCERT sentences first.\n")

    report, failures, all_ok = {}, [], True
    for split in ([a.split] if a.split else splits):
        sel = [r for r in rows if r["split"] == split]
        tok_total = tok_ok = sent_ok = 0
        by_type = collections.defaultdict(lambda: [0, 0])
        by_status = collections.defaultdict(lambda: [0, 0])
        confusion = collections.Counter()
        P = R = F = 0.0
        lat = 0.0
        for r in sel:
            t0 = time.perf_counter()
            res = segment_sanskrit(r["sentence"])
            lat += (time.perf_counter() - t0) * 1000
            pred_tokens = res["tokens"]
            gold_tokens = r["tokens"]
            if [t["surface"] for t in pred_tokens] != [t["surface"] for t in gold_tokens]:
                print(f"!! tokenisation mismatch in {r['id']}"); all_ok = False; continue
            s_ok = True
            for pt, gt in zip(pred_tokens, gold_tokens):
                ok = pt["words"] == gt["words"]
                tok_total += 1; tok_ok += ok; s_ok &= ok
                by_type[gt["type"]][0] += ok; by_type[gt["type"]][1] += 1
                by_status[pt["status"]][0] += ok; by_status[pt["status"]][1] += 1
                confusion[(outcome(gt["surface"], gt["words"]), outcome(pt["surface"], pt["words"]))] += 1
                if not ok:
                    failures.append({"split": split, "id": r["id"], "surface": gt["surface"], "type": gt["type"],
                                     "gold": gt["words"], "pred": pt["words"], "status": pt["status"],
                                     "alternatives": pt["alternatives"][:2], "members": pt["compound_members"]})
            sent_ok += s_ok
            p, rc, f = prf(res["words"], [w for t in gold_tokens for w in t["words"]])
            P += p; R += rc; F += f
        n = max(1, len(sel))
        acc = tok_ok / max(1, tok_total)
        over = sum(v for (g, p), v in confusion.items() if g in ("intact", "reconstruct") and p == "split")
        gold_whole = sum(v for (g, p), v in confusion.items() if g in ("intact", "reconstruct"))
        missed = sum(v for (g, p), v in confusion.items() if g == "split" and p != "split")
        gold_split = sum(v for (g, p), v in confusion.items() if g == "split")
        report[split] = {
            "sentences": len(sel), "tokens": tok_total, "token_accuracy": round(acc, 4),
            "sentence_exact": round(sent_ok / n, 4),
            "over_segmentation_rate": round(over / max(1, gold_whole), 4),
            "missed_split_rate": round(missed / max(1, gold_split), 4),
            "word_precision": round(P / n, 4), "word_recall": round(R / n, 4), "word_f1": round(F / n, 4),
            "avg_ms_per_sentence": round(lat / n, 1),
            "accuracy_by_type": {k: {"acc": round(v[0] / v[1], 3), "n": v[1]} for k, v in sorted(by_type.items())},
            "accuracy_by_status": {k: {"acc": round(v[0] / v[1], 3), "n": v[1]} for k, v in sorted(by_status.items())},
            "outcome_confusion": {f"{g}->{p}": v for (g, p), v in sorted(confusion.items())},
        }
        r_ = report[split]
        print("=" * 78)
        print(f" split={split}   sentences={r_['sentences']}  tokens={r_['tokens']}")
        print("=" * 78)
        print(f" token accuracy        {acc*100:6.1f}%      sentence exact   {r_['sentence_exact']*100:6.1f}%")
        print(f" over-segmentation     {r_['over_segmentation_rate']*100:6.1f}%      missed splits    {r_['missed_split_rate']*100:6.1f}%")
        print(f" word P/R/F1           {r_['word_precision']*100:5.1f} / {r_['word_recall']*100:5.1f} / {r_['word_f1']*100:5.1f}      {r_['avg_ms_per_sentence']} ms/sentence")
        print(" by type   :", "  ".join(f"{k} {v['acc']*100:.0f}% (n={v['n']})" for k, v in r_["accuracy_by_type"].items()))
        print(" by status :", "  ".join(f"{k} {v['acc']*100:.0f}% (n={v['n']})" for k, v in r_["accuracy_by_status"].items()))
        print(" confusion :", r_["outcome_confusion"], "\n")
        if a.fail_under is not None and acc < a.fail_under:
            all_ok = False

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"report": report, "failures": failures}, f, ensure_ascii=False, indent=2)
    if a.errors or failures:
        print(f"FAILURES ({len(failures)})  -> full list in {os.path.relpath(OUT, ROOT)}")
        for x in failures if a.errors else failures[:12]:
            print(f"  [{x['split']}/{x['id']}] {x['surface']:<22} type={x['type']:<14} status={x['status']:<10}"
                  f" gold={'+'.join(x['gold'])}  pred={'+'.join(x['pred'])}")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
