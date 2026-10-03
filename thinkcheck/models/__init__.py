"""Model registry. Add a provider by writing an adapter and listing it here."""
from thinkcheck.models.base import Generation, Model


def get_model(key: str) -> Model:
    """Build a model from a key like 'ollama:qwen2.5:7b' or 'google:gemini-3.8-flash'."""
    provider, _, name = key.partition(":")
    if provider == "ollama":
        from thinkcheck.models.ollama_model import OllamaModel
        return OllamaModel(name)
    if provider == "google":
        from thinkcheck.models.gemini_model import GeminiModel
        return GeminiModel(name)
    raise ValueError(f"unknown provider {provider!r} in {key!r} (known: ollama, google)")


__all__ = ["Generation", "Model", "get_model"]
