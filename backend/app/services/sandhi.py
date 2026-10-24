# -*- coding: utf-8 -*-
"""
Compatibility shim + glue to the API schemas.

    from app.services.sandhi import get_sandhi_service, segment_sanskrit, to_analyze_fields, health

Implementation: app/services/sandhi_engine/ (design notes in engine.py).

Typical use in the orchestrator
-------------------------------
    result = get_sandhi_service().split(normalized_text)
    sandhi = to_analyze_fields(result)            # dict of AnalyzeResponse keyword arguments
    words  = sandhi["sandhi_splits"]              # flat list -> Shrinivas's morphology module
    response = AnalyzeResponse(..., **sandhi)

`to_analyze_fields` fills the new optional fields (sandhi_tokens, sandhi_status, sandhi_degraded,
sandhi_warnings, explanation_en) only if app.models.schemas defines them, so it works before and after
the schema patch.
"""
from typing import Any, Dict, List

from app.services.sandhi_engine import (  # noqa: F401
    ENGINE_VERSION, LexiconBackend, SandhiEngine, SandhiSplitResult, TokenAnalysis,
    get_sandhi_service, segment_sanskrit,
)

SandhiService = SandhiEngine   # old class name


def _split_single_token(self, token_text: str, max_paths: int = 5) -> List[str]:
    """Compatibility method for legacy compound splitters."""
    clean = token_text.strip("।,॥.?!;:\"'()")
    if not clean:
        return [token_text]
    try:
        analysis = self.analyze_token(clean)
        return analysis.words if analysis and analysis.words else [clean]
    except Exception:
        return [clean]


SandhiEngine._split_single_token = _split_single_token


def _schemas():
    from app.models import schemas  # local import: keeps the engine usable without the API layer
    return schemas


def _rule(sc, r: Dict[str, str]):
    kw = dict(junction=r["junction"], rule_name=r["rule_name"], sutra=r["sutra"],
              sandhi_type=r["sandhi_type"], explanation=r["explanation"])
    if "explanation_en" in getattr(sc.SandhiRuleExplanation, "model_fields", {}):
        kw["explanation_en"] = r.get("explanation_en") or None
    return sc.SandhiRuleExplanation(**kw)


def to_analyze_fields(result: SandhiSplitResult) -> Dict[str, Any]:
    """SandhiSplitResult -> keyword arguments for AnalyzeResponse (sandhi part only)."""
    sc = _schemas()
    fields: Dict[str, Any] = {
        "sandhi_splits": list(result.split_words),
        "all_sandhi_options": [
            sc.SandhiSplitOption(split_words=c["words"], confidence=min(1.0, max(0.0, c["confidence"])))
            for c in result.all_candidates
        ],
        "sandhi_rules": [_rule(sc, r) for r in result.rules],
    }
    resp_fields = getattr(sc.AnalyzeResponse, "model_fields", {})
    if "sandhi_tokens" in resp_fields and hasattr(sc, "SandhiTokenAnalysis"):
        tokens: List[Any] = []
        for t in result.tokens:
            tokens.append(sc.SandhiTokenAnalysis(
                surface=t.surface, words=t.words, status=t.status,
                confidence=min(1.0, max(0.0, t.confidence)), evidence=t.evidence,
                junctions=[sc.SandhiJunctionInfo(
                    left=j.left, right=j.right, changed=j.changed,
                    rule=_rule(sc, {"junction": f"{j.left} + {j.right}", "rule_name": j.rule.rule_name,
                                    "sutra": j.rule.sutra, "sandhi_type": j.rule.sandhi_type,
                                    "explanation": j.rule.explanation, "explanation_en": j.rule.explanation_en})
                    if j.rule else None) for j in t.junctions],
                alternatives=t.alternatives, compound_members=t.members, warnings=t.warnings))
        fields["sandhi_tokens"] = tokens
    if "sandhi_status" in resp_fields:
        fields["sandhi_status"] = result.status
    if "sandhi_degraded" in resp_fields:
        fields["sandhi_degraded"] = result.degraded
    if "sandhi_warnings" in resp_fields:
        fields["sandhi_warnings"] = list(result.warnings)
    return fields


def as_legacy_schema(result: SandhiSplitResult):
    """(split_words, [SandhiSplitOption], [SandhiRuleExplanation]) for the old orchestrator."""
    f = to_analyze_fields(result)
    return f["sandhi_splits"], f["all_sandhi_options"], f["sandhi_rules"]


def health() -> Dict[str, str]:
    """Entry for HealthStatus.services, e.g. services["sandhi"] = health()["sandhi"]."""
    be = LexiconBackend.shared()
    if not be.ok:
        return {"sandhi": f"degraded: {be.error}"}
    return {"sandhi": "ok" if be.lm_ranking else "ok (language-model ranking OFF: pip install gensim sentencepiece)"}
