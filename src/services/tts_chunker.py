"""TTS Text Chunking and Cache Key Generator."""

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class TextChunkSpec:
    """Bounded text chunk specification."""

    chunk_index: int
    text: str
    word_count: int


class TTSChunker:
    """Splits narrative text into natural chunks targeting 120-300 words."""

    PIPELINE_VERSION = "1.0"

    def chunk_text(
        self, text: str, target_word_count: int = 180, min_word_count: int = 60
    ) -> List[TextChunkSpec]:
        """Chunk text at paragraph/sentence boundaries avoiding micro-chunks."""
        if not text.strip():
            return []

        # Split into paragraphs first
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        chunks: List[TextChunkSpec] = []
        curr_words: List[str] = []
        curr_sentences: List[str] = []
        chunk_idx = 0

        for p in paragraphs:
            # Split paragraph into sentences
            sentences = re.split(r"(?<=[.!?])\s+", p)

            for s in sentences:
                s_words = s.split()
                if not s_words:
                    continue

                if len(curr_words) + len(s_words) > target_word_count and len(curr_words) >= min_word_count:
                    # Emit current chunk
                    chunk_text = " ".join(curr_sentences)
                    chunks.append(
                        TextChunkSpec(
                            chunk_index=chunk_idx,
                            text=chunk_text,
                            word_count=len(curr_words),
                        )
                    )
                    chunk_idx += 1
                    curr_words = []
                    curr_sentences = []

                curr_words.extend(s_words)
                curr_sentences.append(s)

        if curr_sentences:
            chunk_text = " ".join(curr_sentences)
            chunks.append(
                TextChunkSpec(
                    chunk_index=chunk_idx,
                    text=chunk_text,
                    word_count=len(curr_words),
                )
            )

        return chunks

    def compute_cache_key(
        self,
        text: str,
        provider: str,
        model: str,
        voice: str,
        language: str = "en-us",
        rate: float = 1.0,
        extra_config: Dict[str, Any] = None,
    ) -> str:
        """Compute deterministic SHA-256 cache key for an audio chunk."""
        text_hash = hashlib.sha256(text.strip().encode("utf-8")).hexdigest()
        config_str = json.dumps(extra_config or {}, sort_keys=True)
        raw_key = f"{text_hash}|{provider}|{model}|{voice}|{language}|{rate}|{config_str}|{self.PIPELINE_VERSION}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
