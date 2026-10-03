"""Model registry. Add a provider by writing an adapter and listing it here."""
from thinkcheck.models.base import Generation, Model


def get_model(key: str) -> Model:
    """Build a model from a key like 'ollama:qwen2.5:7b'."""
    provider, _, name = key.partition(":")
    if provider == "ollama":
        from thinkcheck.models.ollama_model import OllamaModel
        return OllamaModel(name)
    raise ValueError(f"unknown provider {provider!r} in {key!r} (known: ollama)")


__all__ = ["Generation", "Model", "get_model"]
