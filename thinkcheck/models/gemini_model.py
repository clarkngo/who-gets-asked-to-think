"""Google Gemini via the google-genai SDK (Gemini Developer API, key in GEMINI_API_KEY)."""
import os
import time

from google import genai
from google.genai import errors, types

from thinkcheck.models.base import Generation, Model

# List prices in USD per 1M tokens, from ai.google.dev/gemini-api/docs/pricing (checked Oct 3, 2026).
# Thinking tokens are billed as output. On the free tier nothing is charged; cost_usd then records
# the list-price equivalent, so the budget guard still holds if billing is ever enabled.
PRICES = {
    "gemini-3.8-flash": {"input": 0.75, "output": 3.75},     # through Dec 31, 2026
    "gemini-3.5-flash-lite": {"input": 0.30, "output": 2.50},
}
# Worst case for the budget guard: a long prompt plus a very long answer (thinking included).
WORST_CASE_TOKENS = {"input": 2_000, "output": 65_536}
RETRY_STATUS = {429, 500, 503}
# We send no tools; disabling the SDK's tool-calling helper changes nothing about sampling or
# thinking, and silences its warning.
CONFIG = types.GenerateContentConfig(
    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True))
MAX_RETRIES = 6


class GeminiModel(Model):
    provider = "google"

    def __init__(self, name: str, billing: str | None = None):
        super().__init__(name)
        if name not in PRICES:
            raise ValueError(f"no price on file for {name}; add it to PRICES first")
        key = os.environ.get("GEMINI_API_KEY")
        if not key:
            raise RuntimeError("GEMINI_API_KEY is not set (put it in .env)")
        self.client = genai.Client(api_key=key)
        self.billing = billing or os.environ.get("GEMINI_BILLING", "free_tier")

    def _cost(self, input_tokens, output_tokens):
        p = PRICES[self.name]
        return ((input_tokens or 0) * p["input"] + (output_tokens or 0) * p["output"]) / 1_000_000

    def describe(self) -> dict:
        return {
            "provider": self.provider,
            "model": self.name,
            "api": "Gemini Developer API (google-genai generate_content)",
            "billing": self.billing,
            "prices_per_mtok_usd": PRICES[self.name],
            "cost_usd_note": "list-price estimate; $0 actually charged on the free tier",
            "settings": "provider defaults: thinking level, temperature, top_p, max_output_tokens not overridden; "
                        "SDK automatic function calling disabled (no tools sent)",
            "system_prompt_sent": None,
        }

    def max_cost_per_call(self) -> float:
        return self._cost(WORST_CASE_TOKENS["input"], WORST_CASE_TOKENS["output"])

    def generate(self, prompt: str, seed: int) -> Generation:
        # seed is unused: we keep provider-default sampling, as for Claude.
        retries = []
        for attempt in range(MAX_RETRIES + 1):
            try:
                resp = self.client.models.generate_content(model=self.name, contents=prompt, config=CONFIG)
                break
            except errors.APIError as exc:
                if exc.code not in RETRY_STATUS or attempt == MAX_RETRIES:
                    raise
                wait = min(30 * 2 ** attempt, 300)
                retries.append({"code": exc.code, "status": exc.status, "waited_s": wait})
                time.sleep(wait)

        usage = resp.usage_metadata
        prompt_tokens = usage.prompt_token_count if usage else None
        visible = usage.candidates_token_count if usage else None
        thoughts = usage.thoughts_token_count if usage else None
        billed_output = (visible or 0) + (thoughts or 0)
        candidate = resp.candidates[0] if resp.candidates else None
        finish = candidate.finish_reason.name if candidate and candidate.finish_reason else None
        if candidate is None and resp.prompt_feedback is not None:
            finish = f"blocked:{resp.prompt_feedback.block_reason}"
        return Generation(
            text=resp.text or "",
            model_id=resp.model_version or self.name,
            stop_reason=finish,
            input_tokens=prompt_tokens,
            output_tokens=billed_output,
            cost_usd=self._cost(prompt_tokens, billed_output),
            extra={
                "visible_output_tokens": visible,
                "thinking_tokens": thoughts,
                "response_id": resp.response_id,
                "retries": retries,
            },
        )
