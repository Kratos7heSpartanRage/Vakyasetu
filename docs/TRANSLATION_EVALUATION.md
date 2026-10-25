# VākyaSetu Neural Translation Evaluation & Model Card

**Module**: Sanskrit $\rightarrow$ English Neural Translation Engine  
**Author**: Satyam (ML & Data Lead, VākyaSetu)  
**Target Domain**: School Students (CBSE / NCERT Classes 6–10)  
**Production Checkpoint**: `models/adapter/` (IndicTrans2-200M + LoRA Step 2500)  
**Last Updated**: October 2026

---

## 1. Executive Summary & Architecture

VākyaSetu integrates a sequence-to-sequence neural machine translation module tailored for Sanskrit students. Rather than relying solely on rigid rule-based parse trees or unadapted multilingual base models, we fine-tuned a state-of-the-art compact multilingual model using parameter-efficient fine-tuning (PEFT).

* **Base Model**: `ai4bharat/indictrans2-indic-en-dist-200M` (213.6M total parameters, gated on Hugging Face).
* **Adaptation Technique**: Low-Rank Adaptation (LoRA) on Query and Key projection layers (`q_proj`, `k_proj`).
  * Rank ($r$): $16$
  * Scaling Factor ($\alpha$): $32$
  * Trainable Parameters: **1.77M** (representing **0.83%** of base weights).
  * Checkpoint: Selected at Step 2500 of Run 2 (best validation performance).
* **Hardware & Production Footprint**:
  * Trained on: NVIDIA GeForce RTX 2050 Laptop GPU (4 GB VRAM) under WSL2.
  * Inference Memory: **0.92 GB** peak tensor memory (well within 4 GB laptop constraints).
  * Inference Latency: **300 ms – 900 ms** per sentence (beam size = 5).

---

## 2. Dataset Provenance & Licensing Disclosure

The translation model was adapted on the **Saamayik** corpus (`acomquest/Saamayik` on Hugging Face).

### 2.1 Corpus Breakdown
* **Raw Pairs**: 43,493
* **After Cleaning**: 42,826 training sentences, 2,416 validation sentences, 2,417 test sentences, and 4,047 out-of-domain test sentences (`test_ood`).
* **Source Composition**:
  1. *Spoken Tutorials* (23,835 pairs): Modern technical and instructional Sanskrit (e.g., software tutorials).
  2. *NIOS* (11,356 pairs): National Institute of Open Schooling secondary school curriculum.
  3. *Bible Translation (1851)* (7,838 pairs): 19th-century missionary translation into classical Sanskrit paired with King-James-style English.
  4. *Gitasopanam* (5,885 pairs): Graded conversational Sanskrit textbook exercises.

### 2.2 License & Ethical Transparency
* **No Unified Open License**: The Saamayik repository lacks a single unified open-source license; its constituent datasets carry their own origins.
* **Public Domain**: The 1851 Sanskrit Bible is in the public domain.
* **Educational Fair Use**: NIOS and Spoken Tutorials are created under government/institutional educational initiatives. For our public repository, we do not redistribute raw copyright-restricted subsets; we document data lineage transparently.

---

## 3. Quantitative Evaluation & Statistical Significance

To move beyond noisy point estimates, we report **95% Paired Bootstrap Confidence Intervals** ($B = 1,000$ resamples) and empirical one-sided $p$-values testing $H_0: \Delta \le 0$ on the official 2,417-sentence test set.

Because ~7% of the test set contains 19th-century Bible-style references that reward archaic English, we partition the test set into:
1. **Modern English References** (2,224 sentences — our true school-textbook proxy).
2. **All Test Sentences** (2,417 sentences — full official split).
3. **Bible-Style References** (193 sentences — archaic English).

### 3.1 Statistical Benchmark Table

| Evaluation Subset | Sentences ($N$) | Base Model BLEU [95% CI] | LoRA Tuned BLEU [95% CI] | $\Delta$ BLEU [95% CI] | Base Model chrF [95% CI] | LoRA Tuned chrF [95% CI] | $\Delta$ chrF [95% CI] | $p$-value |
|---|---|---|---|---|---|---|---|---|
| **Modern References** *(Textbook Proxy)* | **2,224** | 21.38 [20.17, 22.46] | **26.29 [24.78, 27.72]** | **+4.91 [3.82, 6.04]** | 46.49 [45.57, 47.52] | **50.57 [49.60, 51.68]** | **+4.08 [3.61, 4.59]** | **$p < 0.001$** |
| **Full Test Split** *(All)* | **2,417** | 19.56 [18.53, 20.41] | **24.29 [23.01, 25.56]** | **+4.73 [3.73, 5.85]** | 44.44 [43.61, 45.26] | **48.70 [47.79, 49.59]** | **+4.26 [3.79, 4.79]** | **$p < 0.001$** |
| **Bible-Style References** *(Archaic)* | **193** | 8.66 [7.33, 10.08] | **14.44 [11.73, 17.08]** | **+5.78 [3.46, 8.12]** | 32.35 [31.04, 33.72] | **37.90 [35.99, 39.65]** | **+5.55 [4.15, 7.04]** | **$p < 0.001$** |

### 3.2 Key Findings
1. **Statistically Significant Gain**: On modern sentences, our adapter achieves a **+4.91 BLEU** and **+4.08 chrF** gain. Even under the most pessimistic lower bound of the 95% confidence interval, the model delivers at least **+3.82 BLEU** and **+3.61 chrF** over the base model ($p < 0.001$).
2. **Empirical Validation of Sample Variance**: Notice the confidence interval width for BLEU on the 193 Bible sentences is **5.35 points** wide ([11.73, 17.08]), compared to only **2.94 points** on the modern split. This mathematically explains why small validation sets (e.g., 200 samples) swing wildly across training steps.

---

## 4. Training Dynamics & The Validation Size Gotcha

During development, we explored filtering out archaic Bible sentences from the training data ("Run 3"). However, Run 3 stopped early at step 500 and achieved a lower test score (21.9 BLEU vs. 24.3 BLEU). 

### The Diagnostic
Our validation monitor initially tracked BLEU on a 200-sentence dev set. In Run 3b, we tracked both validation loss and validation BLEU across 2,500 steps:

| Step | Validation Loss (Cross-Entropy) | Validation BLEU (200 rows) | Validation chrF | Observation |
|---|---|---|---|---|
| 500 | 1.714 | **24.51** | 47.79 | High BLEU artifact; worst cross-entropy loss |
| 1000 | 1.640 | 23.26 | 47.89 | Loss improving |
| 1500 | 1.627 | 23.69 | **48.67** | Near minimum loss |
| 2000 | **1.627** | 21.88 | 48.30 | **Optimal cross-entropy loss**, yet BLEU plunged 2.6 pts! |
| 2500 | 1.639 | 21.95 | 48.59 | Stable convergence |

**Takeaway for Practitioners**: On small dev sets ($N \le 200$), 4-gram overlap metrics fluctuate dramatically based on single-word synonym choices. Checkpoint selection should always prioritize **validation cross-entropy loss** or require dev splits of $N \ge 1,000$ sentences.

---

## 5. Qualitative Failure Taxonomy & Honest Scoping

Evaluating the model on classical story prose and NCERT curriculum sentences revealed four concrete error categories. Rather than hiding these, we document them systematically to define safe operational boundaries.

### 5.1 The Four Failure Classes

| Failure Mode | Sanskrit Input | Model Output | Ground Truth / Intended Meaning | Root Cause & Diagnostic |
|---|---|---|---|---|
| **1. Theological / Bible Bias** | `प्रतिदिनं सुवर्णशतचतुष्टयं देव!` | *"Every day one hundred and forty-four gold **gods**!"* | *"Four hundred gold coins every day, **Your Majesty**!"* | In classical drama and Panchatantra, *deva* (देव) is a royal honorific ("Sire / Your Majesty"). Because of the 1851 Bible corpus, the model maps *deva* to Christian theological "God/gods". |
| **1b. Archaic Phrasing** | `अथैकदा वीरवरनामा राजपुत्रः वृत्त्यर्थं... राजद्वारमुपागच्छत्।` | *"**And behold**, the king's son came out of a certain country **unto** the king."* | *"Then one day a prince named Veeravara came to the king's gate seeking livelihood."* | Presence of King-James English markers (*"And behold"*, *"unto"*) learned from the Bible subset. |
| **2. Polysemy & Vocabulary Drift** | `किं ते वर्तनम्?` | *"Do they **behave**?"* | *"What is your **salary / livelihood**?"* | *Vartanam* (वर्तनम्) means livelihood, wages, or stipend in this story context. The model selected the modern Hindi/Sanskrit meaning of "conduct / behaviour". |
| **3. Unsplit Sandhi & Compounds** | `नैतच्छक्यम्!` | *"**Naithichakyam!**"* | *"This is not possible!"* | Unsegmented sandhi ($na + etat + shakyam$). The subword tokenizer fractured the merged word, causing the beam search to fall back to transliterated phonetic syllables. |
| **4. Relation Hallucination** | `तेन सह वेदरता नाम तस्य पत्नी, शक्तिधरो नाम सुतः, वीरवती नाम कन्या च...` | *"...his wife Vedaratha, his son Suta, **his wife Shaktidharo**, and his daughter Viravati."* | *"Along with him came his wife named Vedarata, his son named Shaktidhara, and his daughter..."* | Dense lists of names and relations cause attention confusion, hallucinating a second wife from the son's name. |

### 5.2 Repetition Loop Mitigation
On complex classical stories, earlier checkpoints occasionally entered infinite repetition loops (e.g., *"and a scribe, and a scribe, and a scribe..."*).  
**Engineering Fix**: We enforce `no_repeat_ngram_size=3` directly during beam search in [`ml/translator.py`](file:///d:/c_tutorials/NLP_Project/VakyaSetu/ml/translator.py). This completely prevents n-gram recycling without degrading single-sentence fluency.

### 5.3 NCERT Test Set Caveat
We evaluated an initial 11-sentence probe from NCERT/CBSE textbooks. **We explicitly do not report aggregate BLEU scores on these 11 sentences.** Eleven unverified sentences represent an anecdotal qualitative probe, not a statistically valid test set. We use them strictly for failure discovery (shown above), relying on our 2,417-sentence bootstrap test for all quantitative claims.

---

## 6. Software Architecture & Backend Integration Contract

The module exposes a strict, thread-safe Python interface designed for zero-friction integration with the FastAPI backend.

```python
from translator import Translator

# Initialize ONCE at server startup
translator = Translator("models/adapter", device="cuda", warmup=True)

# Translate single or multi-sentence Sanskrit text
result = translator.translate("बालकः विद्यालयं गच्छति।")
# -> {"translation": "Boy goes to school."}
```

### 6.1 Defensive Engineering Guarantees
1. **Thread-Safe Mutex Lock**: PyTorch tensor operations on a single GPU are serialized via an internal `threading.Lock()` to prevent race conditions during concurrent HTTP requests.
2. **NFC Unicode Normalization**: All input is normalized to Unicode Canonical Composition (NFC) before processing.
3. **Sentence Segmentation**: Accurately splits text at `।`, `॥`, `?`, `!`, and newline boundaries.
4. **Input Validation**: Raises explicit `ValueError` (convertible to HTTP 400) for:
   * Empty or whitespace-only inputs.
   * Text exceeding `max_chars=1000`.
   * Non-Devanagari text (enforcing `MIN_DEVANAGARI_FRACTION = 0.3`).
5. **Backend Fallback Bridge**: [`backend/app/services/translation.py`](file:///d:/c_tutorials/NLP_Project/VakyaSetu/backend/app/services/translation.py) automatically resolves the adapter path and falls back gracefully to the rule-based Kāraka engine if model weights are unavailable.

---

## 7. Verification & Test Suite

The module is verified via a mock-based test suite that executes in **under 2 seconds** on any CPU:

```bash
# Run unit and contract tests
pytest tests/test_translator.py -v

# Run statistical bootstrap evaluation
python3 ml/scripts/bootstrap_eval.py
```
