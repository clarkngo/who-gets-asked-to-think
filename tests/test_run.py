from thinkcheck.models.base import Generation, Model
from thinkcheck.run import read_records, run, seed_for

PROMPTS = [
    {"prompt_id": f"T0{i}-make-en", "task_id": f"T0{i}", "function": "f", "framing": "make",
     "language": "en", "text": f"prompt {i}", "sha256": "x"}
    for i in (1, 2)
]


class FakeModel(Model):
    provider = "fake"

    def __init__(self, cost=0.0, fail_on=None):
        super().__init__("m")
        self.cost, self.fail_on, self.calls = cost, fail_on, 0

    def describe(self):
        return {"provider": "fake"}

    def generate(self, prompt, seed):
        self.calls += 1
        if prompt == self.fail_on:
            raise RuntimeError("boom")
        return Generation(text=f"answer to {prompt}", model_id="m-1", stop_reason="stop",
                          input_tokens=3, output_tokens=5, cost_usd=self.cost)

    def max_cost_per_call(self):
        return self.cost


def quiet(*_):
    pass


def test_runs_every_prompt_and_rep_then_resumes_without_repeats(tmp_path):
    out = tmp_path / "raw.jsonl"
    model = FakeModel()
    counts = run(model, PROMPTS, reps=2, out=out, budget=0, log=quiet)
    assert counts["ok"] == 4 and model.calls == 4
    again = run(model, PROMPTS, reps=2, out=out, budget=0, log=quiet)
    assert again["ok"] == 0 and again["skipped_done"] == 4 and model.calls == 4
    records = read_records(out)
    assert [r["rep"] for r in records] == [0, 0, 1, 1]  # rep-major order
    assert records[0]["seed"] == seed_for("T01-make-en", 0)


def test_errors_are_logged_and_retried_next_run(tmp_path):
    out = tmp_path / "raw.jsonl"
    counts = run(FakeModel(fail_on="prompt 2"), PROMPTS, reps=1, out=out, budget=0, log=quiet)
    assert counts == {"skipped_done": 0, "ok": 1, "error": 1, "budget_stop": False, "error_stop": False}
    retry = run(FakeModel(), PROMPTS, reps=1, out=out, budget=0, log=quiet)
    assert retry["ok"] == 1 and retry["skipped_done"] == 1
    assert len(read_records(out)) == 3  # the failed attempt stays in the log


def test_budget_stop_never_exceeds_cap(tmp_path):
    out = tmp_path / "raw.jsonl"
    counts = run(FakeModel(cost=0.40), PROMPTS, reps=3, out=out, budget=1.00, log=quiet)
    assert counts["budget_stop"] and counts["ok"] == 2
    assert sum(r["cost_usd"] for r in read_records(out)) <= 1.00


class AlwaysFails(FakeModel):
    def generate(self, prompt, seed):
        self.calls += 1
        raise RuntimeError("quota exhausted")


def test_stops_after_consecutive_errors(tmp_path):
    model = AlwaysFails()
    counts = run(model, PROMPTS, reps=5, out=tmp_path / "raw.jsonl", budget=0, log=quiet)
    assert counts["error_stop"] and model.calls == 3
