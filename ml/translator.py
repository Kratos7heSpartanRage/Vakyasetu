"""
VakyaSetu translation module (Sanskrit -> English) for the backend to import.

    from translator import Translator
    t = Translator("models/adapter")            # load ONCE, at server start-up
    t.translate("बालकः विद्यालयं गच्छति।")       # -> {"translation": "The boy goes to school."}

Contract for the backend
  input : one Sanskrit string in Devanagari. Several sentences are fine: the text is split after
          ।  ॥  ?  !  and at line breaks, and each sentence is translated separately.
  output: {"translation": "<English text>"}
  errors: ValueError for empty, too-long or non-Devanagari input. The backend should turn it into
          an HTTP 400 with the message.

The adapter folder (adapter_config.json + adapter_model.safetensors) comes from LoRA fine-tuning.
Set it with the constructor argument or the VAKYASETU_ADAPTER environment variable.

Notes
  * Requests are processed one at a time (a lock), because the model sits on one small GPU.
  * no_repeat_ngram=3 stops "and a scribe, and a scribe, ..." loops. Set it to 0 to switch it off.
  * Loading takes a while, and the first translation is slow (GPU kernels compile), so warmup=True
    runs one short sentence at start-up.
"""

import os
import re
import threading
import unicodedata

CKPT = "ai4bharat/indictrans2-indic-en-dist-200M"
SRC_LANG, TGT_LANG = "san_Deva", "eng_Latn"
MAX_LEN = 256
MIN_DEVANAGARI_FRACTION = 0.3

_SENTENCE_BREAK = re.compile(r"(?<=[।॥?!])\s+|\n+")
_DEVANAGARI = re.compile(r"[\u0900-\u097F]")


def split_sentences(text):
    """Split into sentences after ।  ॥  ?  ! and at line breaks; whitespace is tidied."""
    text = unicodedata.normalize("NFC", text)
    return [" ".join(p.split()) for p in _SENTENCE_BREAK.split(text) if p and p.strip()]


def devanagari_fraction(text):
    letters = [c for c in text if c.isalpha()]
    return len(_DEVANAGARI.findall(text)) / len(letters) if letters else 0.0


def _make_generator(model, tokenizer, ip, device, beams, no_repeat):
    import torch

    def generate(batch):
        prepared = ip.preprocess_batch(batch, src_lang=SRC_LANG, tgt_lang=TGT_LANG)
        inputs = tokenizer(prepared, padding="longest", truncation=True,
                           max_length=MAX_LEN, return_tensors="pt").to(device)
        kwargs = dict(max_length=MAX_LEN, num_beams=beams, num_return_sequences=1)
        if no_repeat:
            kwargs["no_repeat_ngram_size"] = no_repeat
        with torch.inference_mode():
            generated = model.generate(**inputs, **kwargs)
        decoded = tokenizer.batch_decode(generated, skip_special_tokens=True,
                                         clean_up_tokenization_spaces=True)
        return ip.postprocess_batch(decoded, lang=TGT_LANG)

    return generate


class Translator:
    def __init__(self, adapter_dir=None, device=None, beams=5, no_repeat_ngram=3,
                 max_chars=1000, batch_size=8, warmup=True):
        adapter_dir = adapter_dir or os.environ.get("VAKYASETU_ADAPTER", "models/adapter")
        if not os.path.exists(os.path.join(adapter_dir, "adapter_config.json")):
            raise FileNotFoundError(f"No adapter_config.json in {adapter_dir!r}. "
                                    "Pass adapter_dir or set VAKYASETU_ADAPTER.")

        import torch
        from IndicTransToolkit import IndicProcessor
        from peft import PeftModel
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        self.max_chars = max_chars
        self.batch_size = batch_size
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._lock = threading.Lock()

        ip = IndicProcessor(inference=True)
        tokenizer = AutoTokenizer.from_pretrained(CKPT, trust_remote_code=True)
        base = AutoModelForSeq2SeqLM.from_pretrained(CKPT, trust_remote_code=True)
        model = PeftModel.from_pretrained(base, adapter_dir).to(self.device)
        model.eval()
        self._generate = _make_generator(model, tokenizer, ip, self.device, beams, no_repeat_ngram)

        if warmup:
            self.translate("नमः।")

    def translate(self, text):
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Please enter a Sanskrit sentence.")
        if len(text) > self.max_chars:
            raise ValueError(f"The text is too long ({len(text)} characters; the limit is {self.max_chars}).")
        if devanagari_fraction(text) < MIN_DEVANAGARI_FRACTION:
            raise ValueError("Please enter Sanskrit in Devanagari script.")
        sentences = split_sentences(text)
        if not sentences:
            raise ValueError("Please enter a Sanskrit sentence.")

        outputs = []
        with self._lock:
            for i in range(0, len(sentences), self.batch_size):
                outputs.extend(self._generate(sentences[i:i + self.batch_size]))
        return {"translation": " ".join(o.strip() for o in outputs if o.strip())}