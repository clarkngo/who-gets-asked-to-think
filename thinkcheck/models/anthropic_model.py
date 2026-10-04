"""Anthropic Claude via the official anthropic SDK (key in ANTHROPIC_API_KEY)."""
import os

import anthropic

from thinkcheck.models.base import Generation, Model

# List prices in USD per 1M tokens (Claude API pricing, checked Oct 4, 2026).
# Thinking tokens are billed as output and are included in usage.output_tokens.
PRICES = {
    "claude-sonnet-5-5": {"input": 2.00, "output": 10.00},
}
# The API requires max_tokens; it caps visible answer + thinking. Our one explicit setting.
MAX_TOKENS = 16_000
WORST_CASE_INPUT_TOKENS = 2_000


class AnthropicModel(Model):
    provider = "anthropic"

    def __init__(self, name: str):
        super().__init__(name)
        if name not in PRICES:
            raise ValueError(f"no price on file for {name}; add it to PRICES first")
        # Credentials come from the environment (ANTHROPIC_API_KEY, loaded from .env by the runner).
        # The SDK retries 408/409/429/5xx and connection errors with backoff.
        # An organization-level key (not scoped to a workspace) must name the workspace to use;
        # set ANTHROPIC_WORKSPACE_ID in .env for that. The ID itself is not written to the data.
        workspace = os.environ.get("ANTHROPIC_WORKSPACE_ID")
        headers = {"anthropic-workspace-id": workspace} if workspace else None
        self.workspace_header = bool(workspace)
        self.client = anthropic.Anthropic(max_retries=5, default_headers=headers)

    def _cost(self, input_tokens, output_tokens):
        p = PRICES[self.name]
        return ((input_tokens or 0) * p["input"] + (output_tokens or 0) * p["output"]) / 1_000_000

    def describe(self) -> dict:
        return {
            "provider": self.provider,
            "model": self.name,
            "api": "Claude Messages API (anthropic SDK messages.create, non-streaming)",
            "prices_per_mtok_usd": PRICES[self.name],
            "settings": {
                "max_tokens": MAX_TOKENS,
                "thinking": "not set (model default: adaptive)",
                "effort": "not set (model default)",
                "sampling": "not settable on this model; provider default",
                "refusal_fallbacks": "not enabled: a refusal is logged as-is rather than rerouted to another model",
            },
            "system_prompt_sent": None,
            "workspace_header_sent": self.workspace_header,
        }

    def max_cost_per_call(self) -> float:
        return self._cost(WORST_CASE_INPUT_TOKENS, MAX_TOKENS)

    def generate(self, prompt: str, seed: int) -> Generation:
        # seed is unused: sampling parameters can't be set on this model.
        resp = self.client.messages.create(
            model=self.name,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(block.text for block in resp.content if block.type == "text")
        stop_details = getattr(resp, "stop_details", None)
        return Generation(
            text=text,
            model_id=resp.model,
            stop_reason=resp.stop_reason,
            input_tokens=resp.usage.input_tokens,
            output_tokens=resp.usage.output_tokens,
            cost_usd=self._cost(resp.usage.input_tokens, resp.usage.output_tokens),
            extra={
                "message_id": resp.id,
                "content_block_types": [block.type for block in resp.content],
                "stop_details": stop_details.model_dump() if stop_details is not None else None,
            },
        )
