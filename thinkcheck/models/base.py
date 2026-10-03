"""The interface every model adapter implements.

An adapter turns one prompt into one Generation and reports what it can about itself (exact model
version, default system prompt, settings), so every raw record is self-describing.
"""
from dataclasses import dataclass, field


@dataclass
class Generation:
    text: str                      # the visible response, exactly as returned
    model_id: str                  # the model identifier the provider reports for this call
    stop_reason: str | None        # e.g. "stop", "length", "end_turn", "max_tokens"
    input_tokens: int | None
    output_tokens: int | None
    cost_usd: float                # 0.0 for local models
    extra: dict = field(default_factory=dict)  # provider-specific details worth keeping


class Model:
    """Base class. Subclasses set `provider` and implement `describe` and `generate`."""

    provider: str = ""

    def __init__(self, name: str):
        self.name = name

    @property
    def key(self) -> str:
        """Stable identifier used in file names and records, e.g. 'ollama:qwen2.5:7b'."""
        return f"{self.provider}:{self.name}"

    def describe(self) -> dict:
        """Fixed facts about the model and settings, logged with every record."""
        raise NotImplementedError

    def generate(self, prompt: str, seed: int) -> Generation:
        raise NotImplementedError

    def max_cost_per_call(self) -> float:
        """Worst-case cost of one call, used by the runner's budget stop. 0 for free models."""
        return 0.0
