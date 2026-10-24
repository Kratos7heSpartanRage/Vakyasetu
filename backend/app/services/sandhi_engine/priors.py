# -*- coding: utf-8 -*-
"""
Tie-break prior for the segmenter: very frequent Sanskrit function words (SLP1, pausa form).

This is NOT a validity lexicon (validity comes from the Heritage lexicon inside sanskrit_parser).
It is only used when two segmentations are both fully valid and equally long, so that
'na + etat + Sakyam' beats the equally-valid but rarer 'nA + etat + Sakyam'.
Keep it small and general-purpose; never add words just to make one benchmark sentence pass.
"""
FUNCTION_WORDS = frozenset("""
na ca api eva iti atha aTa tatra atra yatra kutra sarvatra yadi tadA yadA kadA yaTA taTA evam
kim kaH kA saH sA tat etat idam ayam iyam eSaH eSA aham tvam vayam yUyam mAm tvAm tu hi vA
kila nUnam punaH saha vinA prati asmi asti santi Asit AsIt bhavati bhavanti iva ittham
sa sA te ye ke tu hi vA nu aTa
atra tasmAt yasmAt kasmAt tena yena kena tasya yasya kasya te ye ke
""".split())

PRIOR_WEIGHT = 1

# The 22 classical upasargas (prefixes) in sanskrit_parser sandhi-form. A prefix followed by a finite verb
# (upa+agacCat -> upAgacCat) is one word in textbook prose, so it is not split.
UPASARGAS = frozenset("""
pra parA apa sam anu ava nis nir dus dur vi A ni aDi api ati su ud ut aBi prati pari upa
""".split())
