# Summariser Module

The summariser encapsulates all logic related to condensing long
texts into concise descriptions.  It uses
[`transformers`](https://huggingface.co/docs/transformers/en/tasks/summarization)
from Hugging Face and, by default, the `facebook/bart‑large‑cnn`
checkpoint.  Summarisation is performed locally; the model is
downloaded on first use and cached in `~/.cache/huggingface`.

## `Summarizer` class

The main entry point is the `Summarizer` class defined in
`summarizer.py`.  When instantiated, it stores the name of the model
but does **not** immediately download or load it.  The first call to
the `summarizer` property initialises a Hugging Face pipeline.  The
device is set to `-1` (CPU) by default, but if you have a GPU and the
`torch` installation detects it, the pipeline will automatically run
on the GPU.

### Key methods

* `summarizer`: Property that returns a cached Hugging Face
  `pipeline` object.  Any exceptions during initialisation are
  logged.
* `_chunk_text(text, max_tokens)`: Splits long strings into smaller
  segments by sentences, ensuring that each segment stays within a
  manageable length (roughly equivalent to the maximum sequence
  length of the model).  It operates on punctuation rather than
  external libraries to avoid additional dependencies.
* `summarize(text, max_length=150, min_length=30)`: Generates a
  summary for the given text.  If the input is longer than a single
  chunk, each chunk is summarised separately and then the chunk
  summaries are summarised again to produce the final result.  You
  can adjust `max_length` and `min_length` to control the length of
  the output.

## GPU requirements

The summarisation model will work on a CPU, but performance will be
slower on large inputs.  If your machine has a GPU with CUDA
support and you have installed PyTorch with CUDA enabled, the
pipeline will use the GPU automatically.  GPU usage is optional; the
application does not **require** a GPU to run.