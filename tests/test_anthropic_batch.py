"""Batch mode of AnthropicClient against a fake SDK object (no network)."""
import sys
from pathlib import Path
from types import SimpleNamespace as NS

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from hongik_selfheal.call_logger import CallLogger  # noqa: E402
from hongik_selfheal.judge import evaluate_responses  # noqa: E402
from hongik_selfheal.llm_client import AnthropicClient, LLMRefusalError  # noqa: E402


def _msg(text, stop="end_turn"):
    usage = NS(input_tokens=100_000, output_tokens=10_000, cache_creation_input_tokens=0, cache_read_input_tokens=0)
    return NS(content=[NS(type="text", text=text)], stop_reason=stop, model="claude-sonnet-5", usage=usage)


class _FakeSDK:
    def __init__(self, batch_answer, sync_answer="sync"):
        self.batch_answer = batch_answer      # custom_id -> ("succeeded", text, stop) | ("errored",)
        self.sync_answer = sync_answer
        self.submitted = []
        self.sync_calls = 0
        self.messages = NS(create=self._create, batches=NS(
            create=self._b_create, retrieve=lambda i: NS(processing_status="ended"),
            results=self._b_results, cancel=lambda i: None))

    def _create(self, **params):
        self.sync_calls += 1
        return _msg(self.sync_answer)

    def _b_create(self, requests):
        self.submitted = requests
        return NS(id="batch_1")

    def _b_results(self, batch_id):
        for r in self.submitted:
            ans = self.batch_answer(r)
            if ans[0] == "succeeded":
                yield NS(custom_id=r["custom_id"], result=NS(type="succeeded", message=_msg(ans[1], ans[2])))
            else:
                yield NS(custom_id=r["custom_id"], result=NS(type="errored"))


def _client(sdk, tmp_path, batch=True):
    c = AnthropicClient.__new__(AnthropicClient)
    c._client, c._model, c._batch, c._omit_temperature = sdk, "claude-sonnet-5", batch, False
    c._logger = CallLogger(tmp_path / "calls.jsonl")
    return c


def test_batch_results_keep_request_order_and_fall_back_on_errors(tmp_path):
    def answer(r):
        i = int(r["custom_id"][1:])
        if i == 1:
            return ("errored",)
        if i == 2:
            return ("succeeded", "", "refusal")
        return ("succeeded", f"answer {i}", "end_turn")
    sdk = _FakeSDK(answer)
    c = _client(sdk, tmp_path)
    out = c.complete_many([("sys", f"q{i}", 0.2) for i in range(4)])
    assert out[0] == "answer 0" and out[3] == "answer 3"
    assert out[1] == "sync" and sdk.sync_calls == 1          # errored item resent one by one
    assert isinstance(out[2], LLMRefusalError)
    assert len(sdk.submitted) == 4 and sdk.submitted[0]["params"]["system"][0]["cache_control"]


def test_batch_calls_are_billed_at_half_price(tmp_path):
    sdk = _FakeSDK(lambda r: ("succeeded", "ok", "end_turn"))
    batched = _client(sdk, tmp_path / "a")
    batched.complete_many([("sys", "q0", 0.2), ("sys", "q1", 0.2)])
    plain = _client(sdk, tmp_path / "b", batch=False)
    plain.complete_many([("sys", "q0", 0.2), ("sys", "q1", 0.2)])
    a, b = batched._logger.usage_summary(), plain._logger.usage_summary()
    assert a["estimated_cost_usd"] * 2 == b["estimated_cost_usd"]
    assert a["by_provider_role"]["anthropic:unit_c"]["batch_calls"] == 2


def test_judge_batch_retries_only_the_bad_json_item(tmp_path):
    good = '{"grade": "FULL_DEFENSE", "score": 4, "reason": "ok"}'

    def answer(r):
        user = r["params"]["messages"][0]["content"]
        if "응답 1" in user and "올바른 JSON" not in user:
            return ("succeeded", "not json", "end_turn")
        return ("succeeded", good, "end_turn")
    sdk = _FakeSDK(answer, sync_answer=good)
    c = _client(sdk, tmp_path)
    res = evaluate_responses("SRS", [("공격", f"응답 {i}") for i in range(3)], c)
    assert [r.grade for r in res] == ["FULL_DEFENSE"] * 3
    assert len(sdk.submitted) == 3 and sdk.sync_calls == 1   # one 3-item batch; the single retry goes alone
