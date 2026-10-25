# -*- coding: utf-8 -*-
"""
VākyaSetu sandhi engine (v2) — Mayank's module.

What it does
------------
Input : one Sanskrit sentence (Devanagari).
Output: ordered list of split words + a per-token breakdown that says
        * which words came from which written token,
        * which real sandhi junctions were undone (with Pāṇinian rule),
        * how sure the engine is, and what the alternatives were.

How it decides (per written token)
----------------------------------
1. Propose *surface variants* (undo word-final alternations such as  rAmo -> rAmaH).
2. Ask sanskrit_parser (Heritage lexicon) for up to N segmentation paths of every variant.
   Its ranking is arbitrary (scoring is off), so ranking is done here.
3. Keep a candidate only if
     - every piece is >= 2 phonemes,
     - every piece is a word in the Heritage lexicon,
     - every junction can be re-created by forward sandhi (sanskrit_parser Sandhi.join),
     - every junction is a REAL fusion (surface differs from plain concatenation) or a
       word boundary written together (left piece ends in m / visarga).
   Nothing is hard-coded per sentence.
4. Rank survivors: fewer pieces first, then common-function-word prior. A tie that the prior
   cannot break is reported as 'ambiguous' with alternatives — never silently picked.
5. If nothing survives, the token is kept intact and flagged 'unattested'.

If sanskrit_parser cannot be loaded the engine says so (engine.degraded = True, warnings in
every response, ERROR in the log) instead of quietly falling back to guesses.
"""
from __future__ import annotations

import logging
import threading
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from .phonetics import (
    SandhiRule, classify_junction, first_sound, normalize_text, pausa, split_tokens,
    surface_variants, to_devanagari, to_piece_form, to_slp1,
)
from .priors import FUNCTION_WORDS, PRIOR_WEIGHT, UPASARGAS

logger = logging.getLogger(__name__)
for _name in ("sanskrit_parser", "sanskrit_util", "sqlalchemy"):
    logging.getLogger(_name).setLevel(logging.WARNING)

ENGINE_VERSION = "2.0"
MAX_PATHS = 12
MAX_TOKEN_PHONEMES = 40      # longer tokens are not searched: cost explodes and the answer is unreliable
_DEVANAGARI_ONLY = set(range(0x0900, 0x0980))


# =========================================================================== #
# lexicon / segmentation backend (sanskrit_parser)
# =========================================================================== #
class LexiconBackend:
    """Thin, cached, thread-safe wrapper around sanskrit_parser. Fails loudly, not silently."""

    _instance: Optional["LexiconBackend"] = None
    _instance_lock = threading.Lock()

    def __init__(self) -> None:
        self.ok = False
        self.error: Optional[str] = None
        self.lm_ranking = False          # True when sanskrit_parser's language-model path scoring is active
        self._lock = threading.RLock()
        self._word_cache: Dict[str, bool] = {}
        self._path_cache: Dict[str, List[List[str]]] = {}
        self._join_cache: Dict[Tuple[str, str], Optional[Set[str]]] = {}
        try:
            from sanskrit_parser.base.sanskrit_base import SanskritObject
            from sanskrit_parser.parser.sandhi import Sandhi
            from sanskrit_parser.parser.sandhi_analyzer import LexicalSandhiAnalyzer
            from indic_transliteration import sanscript

            self._SanskritObject = SanskritObject
            self._SLP1 = sanscript.SLP1
            self._analyzer = LexicalSandhiAnalyzer()
            self._sandhi = Sandhi()
            self._self_test()
            self.ok = True
            try:                          # path scoring needs these two; without them path order is arbitrary
                import gensim, sentencepiece  # noqa: F401
                self.lm_ranking = True
            except Exception:  # noqa: BLE001
                logger.warning("gensim/sentencepiece missing: sanskrit_parser path ranking is OFF; "
                               "install them (pip install gensim sentencepiece) for reliable splits")
        except Exception as exc:  # noqa: BLE001 - we want the reason, whatever it is
            self.error = f"{type(exc).__name__}: {exc}"
            logger.error("sanskrit_parser backend UNAVAILABLE -> sandhi engine is DEGRADED (%s)", self.error)

    @classmethod
    def shared(cls) -> "LexiconBackend":
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # ---- self test: known answers; if these fail the install is broken ------ #
    def _self_test(self) -> None:
        if not self.is_word("rAmas"):
            raise RuntimeError("self-test failed: 'rAmas' not recognised by the lexicon")
        paths = self.paths("aTEkadA", 8)
        if ["aTa", "ekadA"] not in paths:
            raise RuntimeError(f"self-test failed: aTEkadA paths = {paths[:3]}")

    # ---- primitives -------------------------------------------------------- #
    def _obj(self, slp1: str):
        return self._SanskritObject(slp1, encoding=self._SLP1)

    def is_word(self, piece: str) -> Optional[bool]:
        """True/False if the lexicon knows the form; None when the backend is down."""
        if not hasattr(self, "_analyzer"):
            return None
        if piece in self._word_cache:
            return self._word_cache[piece]
        forms = [piece] if not piece.endswith("H") else [to_piece_form(piece)]
        val = False
        with self._lock:
            for f in forms:
                try:
                    if self._analyzer.getMorphologicalTags(self._obj(f)):
                        val = True
                        break
                except Exception as exc:  # noqa: BLE001
                    logger.debug("lexicon lookup failed for %r: %s", f, exc)
        self._word_cache[piece] = val
        return val

    _LAKARAS = frozenset({"law", "laN", "lfw", "low", "viDiliN", "liw", "luN", "lfN", "ASIrliN"})

    def is_finite_verb(self, piece: str) -> bool:
        """True when the lexicon analyses `piece` as a finite verb form (tiṅanta)."""
        if not hasattr(self, "_analyzer"):
            return False
        with self._lock:
            try:
                res = self._analyzer.getMorphologicalTags(self._obj(to_piece_form(piece)))
            except Exception:  # noqa: BLE001
                return False
        return any(self._LAKARAS & {str(t) for t in tags} for _, tags in (res or []))

    def paths(self, slp1: str, n: int = MAX_PATHS) -> List[List[str]]:
        if not hasattr(self, "_analyzer"):
            return []
        key = f"{slp1}|{n}"
        if key in self._path_cache:
            return self._path_cache[key]
        out: List[List[str]] = []
        with self._lock:
            try:
                graph = self._analyzer.getSandhiSplits(self._obj(slp1))
                if graph is not None:
                    out = [[str(w) for w in p] for p in graph.find_all_paths(max_paths=n)]
            except Exception as exc:  # noqa: BLE001
                logger.warning("segmentation failed for %r: %s", slp1, exc)
        self._path_cache[key] = out
        return out

    def joins(self, left: str, right: str) -> Optional[Set[str]]:
        """All surface forms that forward sandhi can produce for left + right (spaces removed)."""
        if not hasattr(self, "_sandhi"):
            return None
        key = (left, right)
        if key in self._join_cache:
            return self._join_cache[key]
        res: Optional[Set[str]] = None
        with self._lock:
            try:
                raw = self._sandhi.join(self._obj(left), self._obj(right))
                if raw:
                    res = {str(j).replace(" ", "") for j in raw}
            except Exception as exc:  # noqa: BLE001
                logger.debug("join failed for %r + %r: %s", left, right, exc)
        self._join_cache[key] = res
        return res


# =========================================================================== #
# data structures
# =========================================================================== #
@dataclass
class Junction:
    left: str                      # Devanagari, citation form
    right: str
    changed: bool                  # True = surface differs from plain concatenation
    rule: Optional[SandhiRule] = None


@dataclass
class Candidate:
    pieces: List[str]              # SLP1, sanskrit_parser sandhi-form
    alternation: Optional[str]     # label of the word-final alternation that was undone
    valid: List[Optional[bool]]
    junctions: List[Junction] = field(default_factory=list)
    prior: int = 0
    rank: int = 99                 # position in sanskrit_parser's (LM-scored) path list; 99 = not listed
    unfused: bool = False          # every junction is a plain compound / prefixed verb -> one word, not a split
    groups: List[str] = field(default_factory=list)   # surface words after merging unfused neighbours (SLP1)

    @property
    def words(self) -> List[str]:
        return [to_devanagari(pausa(p)) for p in (self.groups or self.pieces)]

    @property
    def parts(self) -> List[str]:
        """All lexicon pieces (used to show the members of a plain compound)."""
        return [to_devanagari(pausa(p)) for p in self.pieces]

    @property
    def key(self) -> Tuple[str, ...]:
        return tuple(pausa(p) for p in (self.groups or self.pieces))

    @property
    def n_words(self) -> int:
        return len(self.groups or self.pieces)

    @property
    def all_valid(self) -> bool:
        return all(v is True for v in self.valid)


@dataclass
class TokenAnalysis:
    surface: str
    words: List[str]
    status: str                    # resolved | ambiguous | compound | unattested | passthrough | unavailable
    confidence: float
    evidence: List[str]
    junctions: List[Junction] = field(default_factory=list)
    alternatives: List[List[str]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    alternation: Optional[str] = None
    external_rule: Optional[SandhiRule] = None       # rule for a word-final change across a space
    external_junction: Optional[str] = None
    all_valid: bool = False
    members: List[str] = field(default_factory=list)   # parts of a plain compound (no sandhi), for the UI

    def to_dict(self) -> Dict[str, Any]:
        return {
            "surface": self.surface,
            "words": self.words,
            "status": self.status,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "junctions": [
                {"left": j.left, "right": j.right, "changed": j.changed,
                 "rule": _rule_dict(j.rule, f"{j.left} + {j.right}")} for j in self.junctions
            ],
            "alternatives": self.alternatives,
            "compound_members": self.members,
            "warnings": self.warnings,
        }


class RuleDict(dict):
    """Dictionary that also allows attribute access (e.g. r.rule_name, r.sutra)."""
    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise AttributeError(item)
    def __setattr__(self, key, value):
        self[key] = value

def _rule_dict(rule: Optional[SandhiRule], junction: str) -> Optional[Dict[str, str]]:
    if rule is None:
        return None
    return RuleDict({
        "junction": junction,
        "rule_name": rule.rule_name,
        "sutra": rule.sutra,
        "sandhi_type": rule.sandhi_type,
        "explanation": rule.explanation,
        "explanation_en": rule.explanation_en,
    })


@dataclass
class SandhiSplitResult:
    """Duck-type compatible with the old SandhiSplitResult used by tests / orchestrator."""
    split_words: List[str]
    confidence: float
    all_candidates: List[Dict[str, Any]]
    rules: List[Dict[str, str]]
    surface_tokens: List[str]
    reconstructed_words: List[str]
    status: str
    warnings: List[str]
    tokens: List[TokenAnalysis]
    degraded: bool
    validation_summary: Dict[str, Any]


def _plain_flags(surface: str, pieces: List[str]) -> List[Optional[bool]]:
    """
    For every junction: True if the written surface shows both neighbours unchanged (plain
    concatenation), False if letters changed there, None if we cannot tell (no surface given).
    Walks the pieces along the surface; after a change it re-synchronises on the next piece.
    """
    if not surface:
        return [None] * (len(pieces) - 1)
    flags: List[Optional[bool]] = []
    pos = 0
    for left, right in zip(pieces, pieces[1:]):
        if surface.startswith(left + right[:1], pos):
            flags.append(True)
            pos += len(left)
        else:
            flags.append(False)
            idx = surface.find(right[1:3] or right, pos + max(0, len(left) - 1))
            pos = max(idx - 1, pos) if idx > 0 else pos + len(left)
    return flags


# =========================================================================== #
# engine
# =========================================================================== #
class SandhiEngine:
    @classmethod
    def explain_sandhi_rule(cls, c1: str, c2: str):
        from app.services.sandhi_engine.phonetics import classify_junction, to_slp1
        slp1_left = to_slp1(c1)
        slp1_right = to_slp1(c2)
        rule = classify_junction(slp1_left, slp1_right)
        if not rule and slp1_left.endswith("H"):
            rule = classify_junction(slp1_left[:-1] + "s", slp1_right) or classify_junction(slp1_left[:-1] + "r", slp1_right)
        if not rule:
            return None
        return RuleDict({
            "junction": f"{c1} + {c2}",
            "rule_name": rule.rule_name,
            "sutra": rule.sutra,
            "sandhi_type": rule.sandhi_type,
            "explanation": rule.explanation,
            "explanation_en": rule.explanation_en,
        })

    def __init__(self, backend: Optional[LexiconBackend] = None, cache_size: int = 2048) -> None:
        self.backend = backend or LexiconBackend.shared()
        self._cache: "OrderedDict[str, SandhiSplitResult]" = OrderedDict()
        self._cache_lock = threading.Lock()
        self._cache_size = cache_size

    @property
    def degraded(self) -> bool:
        return not self.backend.ok

    # ------------------------------------------------------------------ #
    # candidate generation and filtering
    # ------------------------------------------------------------------ #
    def _evaluate(self, pieces: List[str], alternation: Optional[str], rank: int = 99,
                  surface: str = "") -> Optional[Candidate]:
        """
        Turn a list of pieces into a Candidate, or None if it cannot be right.

        None when: a piece is a single phoneme, or forward sandhi cannot join two neighbouring pieces.
        A junction where nothing is fused (plain compound member, or upasarga + finite verb) is not a
        place to split: neighbouring pieces are merged into one word instead ("groups"). If every
        junction merges, the candidate is a plain compound (`unfused`).
        """
        # fragments: a piece shorter than 3 phonemes must be a very common function word (na, ca, tu, hi, ...)
        if len(pieces) > 1 and any(len(p.replace("'", "")) < 3 and pausa(p) not in FUNCTION_WORDS for p in pieces):
            return None
        if any(len(p.replace("'", "")) < 2 for p in pieces):
            return None
        be = self.backend
        valid = [be.is_word(p) for p in pieces]
        cand = Candidate(pieces=pieces, alternation=alternation, valid=valid, rank=rank)
        groups: List[str] = [pieces[0]]
        plain = _plain_flags(surface, pieces)
        for k, (left, right) in enumerate(zip(pieces, pieces[1:])):
            joins = be.joins(left, right)
            if not joins:
                return None                     # forward sandhi cannot produce this junction
            rule = None if plain[k] else classify_junction(left, right)   # no letter changed -> no sandhi rule
            changed = rule is not None
            prefixed_verb = pausa(left) in UPASARGAS and be.is_finite_verb(right)
            if prefixed_verb or (not changed and left[-1] not in "msH"):
                # merge `right` into the current word: plain concatenation, or the real joined form
                merged = groups[-1] + right
                if prefixed_verb:
                    hit = [j for j in joins if j in surface] if surface else []
                    merged = min(hit, key=len) if hit else merged
                groups[-1] = merged
                continue
            groups.append(right)
            cand.junctions.append(Junction(
                to_devanagari(pausa(left)), to_devanagari(pausa(right)), changed, rule))
        cand.groups = groups
        cand.unfused = len(groups) == 1 and len(pieces) > 1
        cand.prior = PRIOR_WEIGHT * sum(1 for p in (groups or pieces) if pausa(p) in FUNCTION_WORDS)
        return cand

    def analyze_token(self, surface: str, next_token: Optional[str] = None) -> TokenAnalysis:
        if not surface or any(ord(ch) not in _DEVANAGARI_ONLY for ch in surface):
            return TokenAnalysis(surface, [surface] if surface else [], "passthrough", 1.0,
                                 ["not Devanagari text: left unchanged"])
        slp = to_slp1(surface)
        if len(slp.replace("'", "")) > MAX_TOKEN_PHONEMES:
            return TokenAnalysis(surface, [surface], "unattested", 0.2,
                                 ["token longer than %d phonemes: not searched" % MAX_TOKEN_PHONEMES],
                                 warnings=["'%s' is too long to split reliably (stacked compound or missing spaces?); "
                                           "kept as one word" % surface])
        # Check modern lexicon (Central Sanskrit University neologisms & modern loanwords: सङ्गणकेन, मोबाइलेन, etc.)
        try:
            from app.core.modern_lexicon import MODERN_SANSKRIT_TERMS
            clean_s = surface.strip("।,॥.?!;:\"'()")
            is_modern = clean_s in MODERN_SANSKRIT_TERMS
            if not is_modern:
                for sfx in ["ेण", "ेन", "ाय", "ात्", "ात", "स्य", "े", "ाणि", "ैः", "ेषु", "म्", "ं", "ः"]:
                    if clean_s.endswith(sfx) and clean_s[:-len(sfx)] in MODERN_SANSKRIT_TERMS:
                        is_modern = True
                        break
            if is_modern:
                return TokenAnalysis(surface, [clean_s], "resolved", 0.98,
                                     ["attested in Central Sanskrit University modern lexicon"],
                                     all_valid=True)
        except Exception:
            pass

        next_initial = first_sound(to_slp1(next_token)) if next_token else None
        variants = surface_variants(slp, next_initial)

        if self.degraded:                       # say so, never guess
            return self._finish_unverified(
                surface, variants, ["lexicon backend unavailable: token returned without verification"])

        # ---- 1. generate + filter candidates -------------------------------------------------
        pool: "OrderedDict[Tuple[Tuple[str, ...], Optional[str]], Candidate]" = OrderedDict()
        for var in variants:
            raw_paths = self.backend.paths(var.text) if self.backend.ok else []
            intact_piece = [to_piece_form(var.text)]
            for rank, path in enumerate(raw_paths):
                self._add(pool, self._evaluate(path, var.alternation, rank, var.text))
            if intact_piece not in raw_paths:
                self._add(pool, self._evaluate(intact_piece, var.alternation, 50, var.text))

        warnings: List[str] = []
        if self.degraded:
            warnings.append("lexicon backend unavailable: token returned without verification")
            return self._finish_unverified(surface, variants, warnings)

        all_valid = [c for c in pool.values() if c.all_valid]
        if any(c.alternation is None for c in all_valid):
            # 'A'->'AH' and 'ir/ur'->'iH' are only guesses: use them when the written form has no valid reading
            all_valid = [c for c in all_valid if c.alternation not in ("visarga_drop", "visarga_r")]
        valid = [c for c in all_valid if not c.unfused]
        unfused = [c for c in all_valid if c.unfused]
        intact_variants = {c.alternation for c in valid if len(c.pieces) == 1}

        # prefix + finite verb written whole (praRamati = pra + Ramati): never split it
        pv = self._prefixed_verb(slp, variants)
        if pv is not None and not intact_variants:
            return pv

        def eligible(c: Candidate) -> bool:
            if c.n_words == 1:
                return True
            if c.alternation in intact_variants:
                return all(
                    j.rule is not None
                    and j.rule.sandhi_type == "स्वरसन्धिः"
                    and not (j.rule.rule_name == "पूर्वरूपसन्धिः" and "ऽ" not in surface and "'" not in surface)
                    for j in c.junctions
                )
            return True

        cands = [c for c in valid if eligible(c)]
        if not cands:
            if unfused:
                return self._compound(surface, self._pick_members(unfused, None), variants, warnings)
            return self._finish_unverified(surface, variants, warnings, attested=False)

        # ---- 2. rank --------------------------------------------------------------------------
        wants_alt = next_initial is not None

        def key(c: Candidate):
            alt_pref = 0 if (c.alternation and wants_alt) else 1       # undo word-final alternation when context calls for it
            lm = c.rank if self.backend.lm_ranking else 0              # path order is only meaningful with the LM on
            return (alt_pref, lm, c.n_words, c.rank)

        cands.sort(key=key)
        best = cands[0]
        if self.backend.lm_ranking:
            # near-tie (same variant, same word count, LM rank within 1): prefer the segmentation that uses
            # more very common function words (kaH+api over ko+api, na+etat over nA+etat)
            close = [c for c in cands if c.alternation == best.alternation and c.n_words == best.n_words
                     and c.rank - best.rank <= 1]
            top = max(close, key=lambda c: (c.prior, -c.rank))
            if top.prior > best.prior:
                cands.remove(top)
                cands.insert(0, top)
                best = top
        if best.n_words > 1 and unfused:
            # reading the word as a plain compound (no sandhi) over the fused split we found -> keep the token whole
            u = min(unfused, key=lambda c: (c.n_words, c.rank))
            if not self.backend.lm_ranking or u.rank < best.rank:
                return self._compound(surface, self._pick_members(unfused, u), variants, warnings)
        others = [c for c in cands[1:] if c.key != best.key]
        alts = [c.words for c in others[:3]]

        evidence = ["every piece found in the Heritage lexicon"]
        if best.n_words > 1:
            evidence.append("every junction re-created by forward sandhi")
        status, conf = "resolved", 0.9
        if not others:
            evidence.append("only one valid segmentation")
            conf = 0.95
        else:
            rival = next((c for c in others if c.alternation == best.alternation
                          and c.n_words == best.n_words and c.prior >= best.prior
                          and abs(c.rank - best.rank) <= 1 and c.n_words > 1), None)
            if rival is not None or not self.backend.lm_ranking and any(
                    c.n_words == best.n_words and c.prior == best.prior for c in others):
                status, conf = "ambiguous", 0.5
                evidence.append("several equally plausible segmentations; showing the top-ranked one")
            else:
                conf = 0.8
                evidence.append("ranked first by sanskrit_parser language model" if self.backend.lm_ranking
                                else "chosen by fewest pieces / function-word prior (LM ranking is off)")
        if best.alternation and any(c.alternation is None and len(c.pieces) == 1 for c in valid):
            status, conf = "ambiguous", min(conf, 0.6)
            evidence.append("the written form is also a valid word")
        if best.n_words > 1 and any(len(c.pieces) == 1 and c.alternation == best.alternation for c in valid):
            evidence.append("also valid as a single (lexicalised) word")
            alts.append(next(c.words for c in valid if len(c.pieces) == 1 and c.alternation == best.alternation))
        return self._build(surface, best, status, conf, evidence, alts, warnings, next_token)

    @staticmethod
    def _add(pool, cand: Optional[Candidate]) -> None:
        if cand is None:
            return
        k = (cand.key, cand.alternation)
        if k not in pool:
            pool[k] = cand
            return
        existing = pool[k]
        if existing.all_valid and not cand.all_valid:
            return
        if cand.all_valid and not existing.all_valid:
            pool[k] = cand
            return
        if (len(cand.pieces), cand.rank) < (len(existing.pieces), existing.rank):
            pool[k] = cand

    # ------------------------------------------------------------------ #
    def _build(self, surface, best: Candidate, status, conf, evidence, alts, warnings, next_token) -> TokenAnalysis:
        ta = TokenAnalysis(surface, best.words, status, conf, evidence, best.junctions, alts, warnings,
                           alternation=best.alternation, all_valid=True)
        if best.alternation and next_token:
            rule = classify_junction(best.pieces[-1], to_slp1(next_token))
            if rule:
                ta.external_rule = rule
                ta.external_junction = f"{best.words[-1]} + {next_token}"
        return ta

    @staticmethod
    def _pick_members(unfused: List[Candidate], preferred: Optional[Candidate]) -> Candidate:
        """Readable member list for a compound: fewest pieces first, then language-model rank."""
        return min(unfused, key=lambda c: (len(c.pieces), c.rank))

    def _prefixed_verb(self, slp: str, variants) -> Optional[TokenAnalysis]:
        """upasarga + finite verb written as one word (pra+Ramati). Returns a 'compound' analysis."""
        if self.degraded:
            return None
        text = variants[0].text
        for up in sorted(UPASARGAS, key=len, reverse=True):
            if text.startswith(up) and len(text) > len(up) + 2:
                rest = text[len(up):]
                for cand in {rest, "n" + rest[1:] if rest.startswith("R") else rest}:
                    if self.backend.is_finite_verb(cand):
                        word = to_devanagari(pausa(to_piece_form(text)))
                        return TokenAnalysis(
                            to_devanagari(slp), [word], "compound", 0.85,
                            ["upasarga + finite verb written as one word: kept whole"],
                            all_valid=True, members=[to_devanagari(up), to_devanagari(pausa(cand))])
        return None

    def _compound(self, surface, u: Candidate, variants, warnings) -> TokenAnalysis:
        """Plain compound / prefixed verb written without sandhi: keep whole, expose the parts."""
        var = next((v for v in variants if v.alternation == u.alternation), variants[0])
        word = to_devanagari(pausa(to_piece_form(var.text)))
        return TokenAnalysis(surface, [word], "compound", 0.75,
                             ["made of lexicon words joined without sandhi: kept whole, parts shown for reference"],
                             warnings=warnings, alternation=u.alternation, all_valid=True, members=u.parts)

    def _finish_unverified(self, surface, variants, warnings, attested: bool = True) -> TokenAnalysis:
        """No lexicon-valid candidate: keep the token intact and say so."""
        chosen = next((v for v in variants if v.alternation == "visarga_u"), variants[0])
        word = to_devanagari(pausa(to_piece_form(chosen.text)))
        if not self.degraded:
            warnings.append(f"'{surface}' is not in the lexicon (proper noun, typo, or rare form); "
                            "kept as one word without splitting")
        status = "unavailable" if self.degraded else "unattested"
        return TokenAnalysis(surface, [word], status, 0.3 if not self.degraded else 0.0,
                             ["no lexicon-valid segmentation found"], warnings=warnings,
                             alternation=chosen.alternation)

    # ------------------------------------------------------------------ #
    # sentence level
    # ------------------------------------------------------------------ #
    def split(self, text: str) -> SandhiSplitResult:
        norm = normalize_text(text)
        with self._cache_lock:
            if norm in self._cache:
                self._cache.move_to_end(norm)
                return self._cache[norm]

        tokens = split_tokens(norm)
        analyses: List[TokenAnalysis] = []
        for i, tok in enumerate(tokens):
            nxt = tokens[i + 1] if i + 1 < len(tokens) else None
            analyses.append(self.analyze_token(tok, nxt))

        words = [w for a in analyses for w in a.words]
        rules: List[Dict[str, str]] = []
        for a in analyses:
            if a.external_rule:
                rules.append(_rule_dict(a.external_rule, a.external_junction or ""))
            for j in a.junctions:
                if j.rule:
                    rules.append(_rule_dict(j.rule, f"{j.left} + {j.right}"))

        warnings = [w for a in analyses for w in a.warnings]
        if self.degraded:
            warnings.insert(0, f"DEGRADED: sanskrit_parser unavailable ({self.backend.error})")

        if not words:
            status = "unsplit"
        elif any(a.status == "ambiguous" for a in analyses):
            status = "ambiguous"
        else:
            status = "resolved"

        confs = [a.confidence for a in analyses]
        conf = round(min(confs), 2) if confs else 1.0     # a sentence is as sure as its weakest token

        candidates = [{
            "words": words,
            "surface_tokens": tokens,
            "reconstructed_words": words,
            "confidence": conf,
            "rules": rules,
        }]
        # extra sentence-level candidates for ambiguous tokens (at most 2 more)
        for i, a in enumerate(analyses):
            if a.status == "ambiguous" and a.alternatives and len(candidates) < 3:
                alt_words: List[str] = []
                for j, b in enumerate(analyses):
                    alt_words += a.alternatives[0] if j == i else b.words
                candidates.append({"words": alt_words, "surface_tokens": tokens,
                                   "reconstructed_words": alt_words,
                                   "confidence": round(conf * 0.8, 2), "rules": []})

        validation = {
            "all_valid": all(a.all_valid for a in analyses if a.status != "passthrough") if analyses else True,
            "verified_count": sum(1 for a in analyses if a.all_valid),
            "unverified_count": sum(1 for a in analyses if a.status in ("unattested", "unavailable")),
            "unattested_tokens": [a.surface for a in analyses if a.status == "unattested"],
            "lexicon": "sanskrit_parser / Sanskrit Heritage",
            "note": "confidence values are heuristic evidence levels, not calibrated probabilities",
        }
        result = SandhiSplitResult(words, conf, candidates, rules, tokens, words, status, warnings,
                                   analyses, self.degraded, validation)
        with self._cache_lock:
            if len(self._cache) >= self._cache_size:
                self._cache.popitem(last=False)
            self._cache[norm] = result
        return result


# =========================================================================== #
# module-level API (kept compatible with the previous interface)
# =========================================================================== #
_engine: Optional[SandhiEngine] = None
_engine_lock = threading.Lock()


def get_sandhi_service() -> SandhiEngine:
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                _engine = SandhiEngine()
                if _engine.degraded:
                    logger.error("Sandhi engine started in DEGRADED mode: %s", _engine.backend.error)
                else:
                    logger.info("Sandhi engine %s ready (sanskrit_parser backend OK)", ENGINE_VERSION)
    return _engine


def segment_sanskrit(sentence: str, max_paths: int = MAX_PATHS) -> Dict[str, Any]:
    """
    Public interface for the backend.

    Returns
    -------
    {
      "input", "normalized",
      "status":   "resolved" | "ambiguous" | "unsplit",
      "words":    [...],                     # flat, ordered: what Shrinivas's morphology consumes
      "tokens":   [ {surface, words, status, confidence, evidence, junctions, alternatives, warnings} ],
      "candidates": [ {words, surface_tokens, reconstructed_words, confidence, rules} ],
      "rules":    [ {junction, rule_name, sutra, sandhi_type, explanation, explanation_en} ],
      "validation": {...}, "warnings": [...],
      "engine":   {"name": "vakyasetu-sandhi", "version", "backend", "degraded"}
    }
    """
    eng = get_sandhi_service()
    res = eng.split(sentence)
    return {
        "input": sentence,
        "normalized": normalize_text(sentence),
        "status": res.status,
        "words": res.split_words,
        "tokens": [t.to_dict() for t in res.tokens],
        "candidates": res.all_candidates,
        "rules": res.rules,
        "validation": res.validation_summary,
        "warnings": res.warnings,
        "engine": {"name": "vakyasetu-sandhi", "version": ENGINE_VERSION,
                   "backend": "sanskrit_parser", "degraded": res.degraded,
                   "lm_ranking": get_sandhi_service().backend.lm_ranking},
    }
