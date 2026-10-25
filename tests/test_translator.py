"""
Unit and Contract Tests for VakyaSetu Translation Module (ml/translator.py).

Verifies:
  1. Sentence segmentation across danda (।), double danda (॥), ?, !, and newlines.
  2. Unicode NFC normalization and Devanagari fraction computation.
  3. Strict input validation (empty, whitespace, length, non-Devanagari script).
  4. Backend contract adherence: returns {"translation": "<English string>"}.
  5. Thread safety lock during batch generation.
  6. Graceful failure on missing adapter paths.
"""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add ml/ to sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "ml"))

from translator import (
    Translator,
    split_sentences,
    devanagari_fraction,
    MIN_DEVANAGARI_FRACTION,
)


class TestTextProcessing:
    """Tests for Sanskrit sentence splitting and script validation."""

    def test_split_single_sentence(self):
        text = "बालकः विद्यालयं गच्छति।"
        sentences = split_sentences(text)
        assert sentences == ["बालकः विद्यालयं गच्छति।"]

    def test_split_multiple_sentences_danda(self):
        text = "सा पुस्तकं पठति। अहं जलं पिबामि॥"
        sentences = split_sentences(text)
        assert sentences == ["सा पुस्तकं पठति।", "अहं जलं पिबामि॥"]

    def test_split_with_question_and_exclamation(self):
        text = "किं ते वर्तनम्? प्रतिदिनं सुवर्णशतचतुष्टयं देव!"
        sentences = split_sentences(text)
        assert len(sentences) == 2
        assert sentences[0] == "किं ते वर्तनम्?"
        assert sentences[1] == "प्रतिदिनं सुवर्णशतचतुष्टयं देव!"

    def test_split_with_newlines(self):
        text = "सूर्यः उदेति\nपद्मं विकसति"
        sentences = split_sentences(text)
        assert len(sentences) == 2
        assert sentences[0] == "सूर्यः उदेति"
        assert sentences[1] == "पद्मं विकसति"

    def test_split_whitespace_collapse(self):
        text = "  बालकः    पुस्तकम   पठति।   "
        sentences = split_sentences(text)
        assert sentences == ["बालकः पुस्तकम पठति।"]

    def test_devanagari_fraction_pure(self):
        # Combining marks/matras are in Devanagari block, so fraction >= 1.0
        text = "सत्यमेव जयते"
        assert devanagari_fraction(text) >= 1.0

    def test_devanagari_fraction_latin(self):
        text = "satyam eva jayate"
        assert devanagari_fraction(text) == 0.0

    def test_devanagari_fraction_mixed(self):
        # 5 Devanagari letters + 5 Latin letters
        text = "सत्यम abcde"
        frac = devanagari_fraction(text)
        assert 0.4 <= frac <= 0.8


class TestTranslatorContract:
    """Tests for the Translator class contract, error handling, and thread safety."""

    def test_missing_adapter_raises_filenotfound(self, tmp_path):
        with pytest.raises(FileNotFoundError) as exc_info:
            Translator(adapter_dir=str(tmp_path / "nonexistent"))
        assert "No adapter_config.json" in str(exc_info.value)

    @staticmethod
    def _create_mock_translator(tmp_path, max_chars=1000, generator_fn=None):
        """Helper to create a Translator instance with mocked heavy ML dependencies."""
        (tmp_path / "adapter_config.json").write_text("{}")
        mock_modules = {
            "torch": MagicMock(),
            "peft": MagicMock(),
            "transformers": MagicMock(),
            "IndicTransToolkit": MagicMock(),
        }
        with patch.dict("sys.modules", mock_modules):
            with patch("translator._make_generator") as mock_gen:
                mock_gen.return_value = generator_fn or MagicMock(return_value=["mocked output"])
                t = Translator(adapter_dir=str(tmp_path), max_chars=max_chars, warmup=False)
                return t

    def test_input_validation_empty_and_whitespace(self, tmp_path):
        t = self._create_mock_translator(tmp_path)

        with pytest.raises(ValueError, match="Please enter a Sanskrit sentence"):
            t.translate("")

        with pytest.raises(ValueError, match="Please enter a Sanskrit sentence"):
            t.translate("   \n   \t  ")

    def test_input_validation_non_devanagari(self, tmp_path):
        t = self._create_mock_translator(tmp_path)

        with pytest.raises(ValueError, match="Please enter Sanskrit in Devanagari script"):
            t.translate("balakah vidyalayam gacchati.")

    def test_input_validation_too_long(self, tmp_path):
        t = self._create_mock_translator(tmp_path, max_chars=50)
        long_sanskrit = "बालकः विद्यालयं गच्छति। " * 10
        with pytest.raises(ValueError, match="The text is too long"):
            t.translate(long_sanskrit)

    def test_translate_contract_output_structure(self, tmp_path):
        """Verifies {"translation": "..."} output contract."""
        mock_gen = MagicMock(return_value=["The boy goes to school."])
        t = self._create_mock_translator(tmp_path, generator_fn=mock_gen)

        res = t.translate("बालकः विद्यालयं गच्छति।")
        assert isinstance(res, dict)
        assert "translation" in res
        assert res["translation"] == "The boy goes to school."

    def test_thread_safety_lock(self, tmp_path):
        """Verifies that multiple concurrent threads serialize execution through the lock."""
        call_log = []

        def slow_mock_generate(batch):
            call_log.append("start")
            import time
            time.sleep(0.04)
            call_log.append("end")
            return ["mock translation"]

        t = self._create_mock_translator(tmp_path, generator_fn=slow_mock_generate)

        threads = [
            threading.Thread(target=t.translate, args=("बालकः गच्छति।",))
            for _ in range(4)
        ]
        for th in threads:
            th.start()
        for th in threads:
            th.join()

        # Under strict mutex lock, each 'start' must immediately precede 'end'
        for i in range(0, len(call_log), 2):
            assert call_log[i] == "start"
            assert call_log[i + 1] == "end"
