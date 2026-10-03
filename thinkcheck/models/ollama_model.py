"""Local models served by Ollama (free; run on this machine)."""
import json
import os
import urllib.request

import ollama

from thinkcheck.models.base import Generation, Model

# Settings we set explicitly. Anything not listed uses the model's / Ollama's defaults, and
# describe() records what those defaults were (the Modelfile has no PARAMETER lines for qwen2.5).
OPTIONS = {
    "num_ctx": 8192,      # room for prompt + a long answer
    "num_predict": 4096,  # cap runaway generations; a hit shows up as stop_reason "length"
}


class OllamaModel(Model):
    provider = "ollama"

    def __init__(self, name: str):
        super().__init__(name)
        self.host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        self.client = ollama.Client(host=self.host)
        self._description = None

    def describe(self) -> dict:
        if self._description is None:
            listed = {m.model: m for m in self.client.list().models}
            if self.name not in listed:
                raise RuntimeError(f"{self.name} is not pulled in Ollama (run: ollama pull {self.name})")
            info = self.client.show(self.name)
            modelfile = info.modelfile or ""
            with urllib.request.urlopen(f"{self.host}/api/version", timeout=5) as r:
                server_version = json.load(r).get("version")
            self._description = {
                "provider": self.provider,
                "server_version": server_version,
                "model": self.name,
                "digest": listed[self.name].digest,
                "quantization": info.details.quantization_level if info.details else None,
                "parameter_size": info.details.parameter_size if info.details else None,
                "default_system_prompt": next(
                    (line[len("SYSTEM "):] for line in modelfile.splitlines() if line.startswith("SYSTEM ")), None),
                "modelfile_parameters": [l for l in modelfile.splitlines() if l.startswith("PARAMETER")],
                "options_set": dict(OPTIONS),
                "sampling": "Ollama/model defaults (temperature etc. not overridden); seed set per call",
                "system_prompt_sent": None,
            }
        return self._description

    def generate(self, prompt: str, seed: int) -> Generation:
        resp = self.client.chat(
            model=self.name,
            messages=[{"role": "user", "content": prompt}],
            options={**OPTIONS, "seed": seed},
            stream=False,
        )
        return Generation(
            text=resp.message.content,
            model_id=resp.model,
            stop_reason=resp.done_reason,
            input_tokens=resp.prompt_eval_count,
            output_tokens=resp.eval_count,
            cost_usd=0.0,
            extra={"total_duration_ns": resp.total_duration, "created_at": str(resp.created_at)},
        )
