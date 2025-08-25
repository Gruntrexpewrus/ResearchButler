"""Quantum trivia provider.

This module stores a curated list of short facts or trivia about
quantum computing and related topics.  The dashboard uses these
trivia items to add a bit of variety and education to the daily
report.  If you come across an interesting tidbit, feel free to
append it to the list below.
"""

import random

# A list of fun facts about quantum computing and quantum mechanics.  Each
# entry should be a single sentence so it fits nicely into the UI.
TRIVIA_LIST = [
    "The concept of qubits was proposed in 1985 by physicist David Deutsch.",
    "Quantum computers exploit superposition and entanglement to perform certain calculations faster than classical computers.",
    "Shor’s algorithm, discovered in 1994, showed that quantum computers could factor large numbers exponentially faster than classical algorithms.",
    "Quantum error correction codes are essential for building reliable quantum computers.",
    "The Bloch sphere is a geometrical representation of the pure state space of a two-level quantum system (qubit).",
    "In 2019, Google claimed quantum supremacy by performing a computation in 200 seconds that would take a classical supercomputer thousands of years.",
    "The term ‘quantum annealing’ refers to a method used by D-Wave computers to solve optimisation problems.",
    "Quantum machine learning aims to combine quantum computing with artificial intelligence to process data more efficiently.",
    "The no-cloning theorem states that it is impossible to create an identical copy of an arbitrary unknown quantum state.",
    "IBM’s Quantum Experience allows researchers to run experiments on real quantum hardware via the cloud.",
]

# A list of light‑hearted quantum computing jokes.  These are meant
# to amuse and can serve as a fallback if dynamic joke generation
# fails.  You may add to or modify this list at will.
JOKES_LIST = [
    "Why did the qubit cross the road? To get to the other side… of the superposition!",
    "Heisenberg was driving and got pulled over. The officer asked, 'Do you know how fast you were going?' Heisenberg replied, 'No, but I know exactly where I am.'",
    "A quantum physicist orders a beer… and doesn’t because they simultaneously did and didn't order one.",
    "Why don’t quantum physicists tell jokes? They can never be sure if you’ll collapse in laughter or groan in superposition.",
    "Schrödinger’s cat walks into a bar… and doesn’t.",
]


def generate_quantum_joke() -> str:
    """Generate a quantum-themed joke using a lightweight language model.

    This helper uses the Hugging Face ``text-generation`` pipeline with
    the ``distilgpt2`` model to produce a short, novel joke.  If the
    model cannot be loaded (for example, due to missing dependencies
    or lack of network access on first run), the function falls back
    to selecting a random joke from ``JOKES_LIST``.  The output is
    stripped of the original prompt and whitespace.
    """
    try:
        from transformers import pipeline
        # Load the pipeline.  ``distilgpt2`` is small (~90 MB) and
        # suitable for joke generation.  We limit the length to 40 tokens.
        gen = pipeline(
            "text-generation",
            model="distilgpt2",
            device=-1,  # CPU only; GPU will be used if available
        )
        prompt = "Tell me a quantum computing joke:"
        result = gen(prompt, max_length=40, num_return_sequences=1, do_sample=True, temperature=0.9)[0]
        # Remove the prompt from the generated text
        text: str = result.get("generated_text", "").strip()
        if text.startswith(prompt):
            joke = text[len(prompt):].strip()
        else:
            joke = text
        # If the model generates nothing beyond the prompt, fall back
        if not joke:
            raise ValueError("Empty generation")
        # Capitalise first letter and remove trailing punctuation if needed
        return joke[0].upper() + joke[1:]
    except Exception:
        # Fall back to a static joke from the list on any error
        return random.choice(JOKES_LIST) if JOKES_LIST else ""


def get_trivia_pair() -> (str, str):
    """Return a pair consisting of a fact and a joke.

    The first element is a factual trivia item drawn from
    ``TRIVIA_LIST``.  The second is a light‑hearted quantum joke
    selected from ``JOKES_LIST``.  We avoid generating jokes via
    language models here because the results can be overly long or
    inconsistent.  If either list is empty, an empty string is
    returned for that element.
    """
    fact = random.choice(TRIVIA_LIST) if TRIVIA_LIST else ""
    joke = random.choice(JOKES_LIST) if JOKES_LIST else ""
    return fact, joke
