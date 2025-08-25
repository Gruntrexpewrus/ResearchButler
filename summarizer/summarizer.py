"""Wrapper around Hugging Face summarisation models.

This module defines a simple summariser class built on top of the
Transformers pipeline API.  By default it uses the
`facebook/bart‑large‑cnn` model, which is designed for abstractive
summarisation of news articles.  The summariser splits long
documents into manageable chunks, summarises each chunk separately
and then summarises the concatenated output again to produce a
concise final summary.

The summariser loads the model lazily on first use so that
initialising the class does not block the application startup.
"""

from __future__ import annotations

import logging
from typing import List

from transformers import pipeline

logger = logging.getLogger(__name__)


class Summarizer:
    """Text summarisation utility using Hugging Face pipelines."""

    def __init__(self, model_name: str = "facebook/bart-large-cnn") -> None:
        self.model_name = model_name
        self._summarizer = None

    @property
    def summarizer(self):
        """Lazily initialise the summarisation pipeline.

        The first call will download the model if necessary.  Subsequent
        calls reuse the loaded model.
        """
        if self._summarizer is None:
            try:
                # Initialise the Hugging Face pipeline.  Passing
                # `device=-1` forces the pipeline to use the CPU.  If
                # you have a GPU and a CUDA‑enabled PyTorch
                # installation, you can remove this argument and the
                # pipeline will automatically select the GPU.
                self._summarizer = pipeline(
                    "summarization",
                    model=self.model_name,
                    tokenizer=self.model_name,
                    device=-1,
                )
                logger.info("Loaded summarisation model %s", self.model_name)
            except Exception as exc:
                # Reraise the exception after logging so callers know
                # something went wrong.
                logger.error("Failed to load summarisation model: %s", exc)
                raise
        return self._summarizer

    def _chunk_text(self, text: str, max_tokens: int = 900) -> List[str]:
        """Split a long piece of text into smaller chunks.

        The `bart-large-cnn` model can process roughly 1024 tokens.
        Splitting at sentence boundaries yields more coherent summaries.
        Here we simply split on periods if the text is too long.  More
        advanced segmentation (e.g. via nltk) could be added later.
        """
        # Split on periods followed by a space to approximate sentences.
        # This is a crude heuristic; for more precise segmentation you
        # could integrate the `nltk` library and use its sentence
        # tokenizer.  However, adding NLTK would add a dependency and
        # increase the installation footprint, so this simple approach
        # strikes a balance between accuracy and complexity.
        sentences = text.split(". ")
        chunks: List[str] = []
        current_chunk: List[str] = []
        current_length = 0
        for sentence in sentences:
            # Approximate token count by word count.  This avoids
            # importing a tokenizer from Transformers just to count
            # tokens, which would introduce additional overhead.  For
            # typical English text the difference between words and
            # tokens is small enough that this approximation works well.
            length = len(sentence.split())
            if current_length + length > max_tokens and current_chunk:
                # When adding the next sentence would exceed the limit,
                # finalise the current chunk and start a new one.
                chunks.append(". ".join(current_chunk))
                current_chunk = [sentence]
                current_length = length
            else:
                current_chunk.append(sentence)
                current_length += length
        if current_chunk:
            chunks.append(". ".join(current_chunk))
        return chunks

    def summarize(self, text: str, *, max_length: int = 150, min_length: int = 30) -> str:
        """Generate a concise summary for the given text.

        For long documents the text is divided into chunks, each chunk is
        summarised individually and the intermediate summaries are
        concatenated and summarised again.

        Parameters
        ----------
        text:
            The input text to summarise.
        max_length:
            Maximum length of the final summary in tokens (approximate).
        min_length:
            Minimum length of the final summary in tokens (approximate).

        Returns
        -------
        str
            The generated summary.  If the summarisation pipeline fails,
            the original text is returned.
        """
        if not text:
            return ""
        try:
            # Split the text into manageable chunks
            chunks = self._chunk_text(text)
            summaries: List[str] = []
            for chunk in chunks:
                # Summarise each chunk individually.  We disable
                # sampling to make the output deterministic.
                result = self.summarizer(
                    chunk,
                    max_length=max_length,
                    min_length=min_length,
                    do_sample=False,
                    clean_up_tokenization_spaces=True,
                )
                if result and isinstance(result, list):
                    summaries.append(result[0]["summary_text"])
            if not summaries:
                # If no summary could be produced, return the original text
                return text
            # If the document was split into multiple chunks, summarise
            # the concatenated summaries again to obtain a single
            # coherent paragraph.  This second pass often produces
            # shorter and more fluent summaries.
            combined = " ".join(summaries)
            if len(summaries) > 1:
                final = self.summarizer(
                    combined,
                    max_length=max_length,
                    min_length=min_length,
                    do_sample=False,
                    clean_up_tokenization_spaces=True,
                )
                combined = final[0]["summary_text"] if final else combined
            return combined.strip()
        except Exception as exc:
            # Log the error and fall back to returning the original text
            logger.error("Summarisation failed: %s", exc)
            return text
