import json

import pytest

from llm_adapter.kimi_intr_transport import KimiTransportConfigurationError
from llm_adapter.kimi_tvc_provider_wire import (
    canonical_kimi_tvc_provider_payload,
    canonical_kimi_tvc_provider_request_hash,
    canonical_kimi_tvc_provider_wire_bytes,
)
from llm_adapter.provider_request import build_provider_request


def _request(*, messages=None, temperature=0.7):
    return build_provider_request(
        provider="kimi",
        model="kimi-k3",
        messages=messages or [{"role": "user", "content": "hello exact wire"}],
        temperature=temperature,
    )


def test_text_wire_matches_tvc_openai_chat_completions_payload_exactly():
    request = _request()
    expected = {
        "model": "kimi-k3",
        "messages": [{"role": "user", "content": "hello exact wire"}],
        "max_tokens": 2048,
        "stream": False,
    }
    assert canonical_kimi_tvc_provider_payload(request) == expected
    assert canonical_kimi_tvc_provider_wire_bytes(request) == json.dumps(
        expected, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def test_json_wire_matches_tvc_response_format_exactly():
    payload = canonical_kimi_tvc_provider_payload(_request(), max_output_tokens=321, response_format="json")
    assert payload == {
        "model": "kimi-k3",
        "messages": [{"role": "user", "content": "hello exact wire"}],
        "max_tokens": 321,
        "stream": False,
        "response_format": {"type": "json_object"},
    }


def test_max_output_tokens_and_response_format_are_hash_bound():
    request = _request()
    base = canonical_kimi_tvc_provider_request_hash(request, max_output_tokens=10, response_format="text")
    assert base != canonical_kimi_tvc_provider_request_hash(request, max_output_tokens=11, response_format="text")
    assert base != canonical_kimi_tvc_provider_request_hash(request, max_output_tokens=10, response_format="json")


def test_legacy_temperature_is_not_part_of_tvc_provider_wire():
    first = _request(temperature=0.0)
    second = _request(temperature=1.0)
    assert canonical_kimi_tvc_provider_wire_bytes(first) == canonical_kimi_tvc_provider_wire_bytes(second)
    assert canonical_kimi_tvc_provider_request_hash(first) == canonical_kimi_tvc_provider_request_hash(second)


@pytest.mark.parametrize(
    "messages",
    [
        [{"role": "system", "content": "system"}],
        [{"role": "user", "content": "one"}, {"role": "user", "content": "two"}],
    ],
)
def test_unrepresentable_tvc_message_shapes_fail_closed(messages):
    with pytest.raises(KimiTransportConfigurationError):
        canonical_kimi_tvc_provider_payload(_request(messages=messages))
