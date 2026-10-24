# -*- coding: utf-8 -*-
"""
Run this on YOUR machine first:   python ml/scripts/check_sandhi_backend.py

Prints whether sanskrit_parser really works in your environment. If it does not, the old module silently
fell back to regex guesses (that is how रामः became a verb). Exits non-zero on any problem.
"""
import os, sys, platform
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "backend"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ok = True
def line(flag, msg):
    global ok
    ok &= flag
    print(("  OK   " if flag else "  FAIL ") + msg)

print(f"python {platform.python_version()} on {platform.system()}")
for mod in ("sanskrit_parser", "indic_transliteration", "gensim", "sentencepiece"):
    try:
        m = __import__(mod); line(True, f"{mod} {getattr(m, '__version__', '')}")
    except Exception as e:
        line(False, f"{mod} not importable: {e}")

from app.services.sandhi_engine import LexiconBackend
be = LexiconBackend()
line(be.ok, "LexiconBackend self-test" + ("" if be.ok else f" -> {be.error}"))
if be.ok:
    line(be.lm_ranking, "language-model path ranking is ON" + ("" if be.lm_ranking else
         "  (pip install gensim sentencepiece; without it the library's path order is arbitrary)"))
    line(["aTa", "ekadA"] in be.paths("aTEkadA"), "segmentation: aTEkadA -> aTa + ekadA")
    line(bool(be.is_word("rAmas")), "lexicon knows rAmas")
    line(bool(be.joins("na", "etat")), "forward sandhi: na + etat")
sys.exit(0 if ok else 1)
