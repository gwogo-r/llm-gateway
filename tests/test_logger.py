from types import SimpleNamespace

from llm_gateway import TokenUsage, cost_usd, usage_from_response


def test_cost_usd_computes_from_per_million_prices():
    assert cost_usd(1_000_000, 1_000_000, price_in=2.0, price_out=10.0) == 12.0


def test_cost_usd_defaults_to_zero_for_none_prices():
    assert cost_usd(1000, 1000, price_in=None, price_out=None) == 0.0


def test_usage_from_response_extracts_tokens_and_cost():
    response = SimpleNamespace(usage=SimpleNamespace(prompt_tokens=100, completion_tokens=50))
    usage = usage_from_response(
        response, stage="extractor", model="gpt-test", price_in=2.0, price_out=10.0,
        task_id="t1", member_id="m1",
    )
    assert isinstance(usage, TokenUsage)
    assert usage.stage == "extractor"
    assert usage.prompt_tokens == 100
    assert usage.completion_tokens == 50
    assert usage.cost_usd == round(100 * 2.0 / 1_000_000 + 50 * 10.0 / 1_000_000, 6)
    assert usage.billing == "api"
    assert usage.task_id == "t1"
    assert usage.member_id == "m1"


def test_usage_from_response_handles_missing_usage_field():
    response = SimpleNamespace(usage=None)
    usage = usage_from_response(response, stage="x", model="m")
    assert usage.prompt_tokens == 0
    assert usage.completion_tokens == 0
    assert usage.cost_usd == 0.0
