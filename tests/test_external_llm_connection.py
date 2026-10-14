import unittest
from types import SimpleNamespace
from unittest import mock

import llm_adapter.external_llm_connection as mod

class DummyExecution:
    response_hash = "a" * 64
    egress_handoff = {"requested_disposition": "ALLOW"}
    def evidence(self): return {"authority_effect": "NONE", "egress_intr_required": True}


class ExternalLlmConnectionTests(unittest.TestCase):
    def _setattr(self, target, *args, raising=True):
        """monkeypatch.setattr equivalent: dotted-path or (object, name) form, undone after the test."""
        if isinstance(target, str):
            patcher = mock.patch(target, *args, create=not raising)
        else:
            patcher = mock.patch.object(target, *args, create=not raising)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_normalize_provider(self):
        for name, canonical in [
            ("z.ai","zai"),("zai","zai"),("deepseek","deepseek"),("kimi","kimi"),("moonshot","kimi"),("anthropic","anthropic"),("claude","anthropic"),("openai","openai"),("chatgpt","openai")
        ]:
            with self.subTest(name=name, canonical=canonical):
                assert mod.normalize_provider(name) == canonical

    def test_unknown_provider_fails_closed(self):
        with self.assertRaises(mod.ExternalLLMConnectionError): mod.normalize_provider("unknown")

    def test_compatibility_execution_dispatch(self):
        for provider, target_name in [
            ("z.ai","execute_governed_zai"),("deepseek","execute_governed_deepseek"),("kimi","execute_governed_kimi")
        ]:
            with self.subTest(provider=provider, target_name=target_name):
                seen = {}
                def fake(**kwargs): seen.update(kwargs); return DummyExecution()
                self._setattr(mod, target_name, fake)
                request = SimpleNamespace(provider=provider)
                result = mod.execute_governed_external_llm(request, session_id="s", transition_id="t", measurement_id="m", ingress_disposition="ALLOW", ingress_receipt_hash="b"*64, carrier_ref="hb32:x", credential_resolver=lambda:"secret")
                assert result.provider == mod.normalize_provider(provider)
                assert result.execution_path == "TV_TVC_RESOLVER_COMPATIBILITY"
                assert result.authority_effect == "NONE"
                assert result.egress_intr_required is True
                assert seen["ingress_disposition"] == "ALLOW"
                assert seen["credential_resolver"]() == "secret"

    def test_tvc_runtime_execution_dispatch(self):
        for provider, target_name in [
            ("z.ai","execute_governed_zai_via_tvc_runtime"),
            ("deepseek","execute_governed_deepseek_via_tvc_runtime"),
            ("kimi","execute_governed_kimi_via_tvc_runtime"),
            ("anthropic","execute_governed_anthropic_via_tvc_runtime"),
            ("openai","execute_governed_openai_via_tvc_runtime"),
        ]:
            with self.subTest(provider=provider, target_name=target_name):
                seen = {}
                def fake(**kwargs): seen.update(kwargs); return DummyExecution()
                self._setattr(mod, target_name, fake)
                request = SimpleNamespace(provider=provider)
                lease = {"decision":"ALLOW_CAPABILITY_LEASE"}
                broker = lambda operation: {"decision":"ALLOW_OPERATION_RESULT"}
                result = mod.execute_governed_external_llm(request, session_id="s", transition_id="t", measurement_id="m", ingress_disposition="ALLOW", ingress_receipt_hash="b"*64, carrier_ref="hb32:x", lease_receipt=lease, broker_submitter=broker)
                assert result.execution_path == "TVC_NON_EXPORTABLE_RUNTIME"
                assert seen["lease_receipt"] is lease
                assert seen["broker_submitter"] is broker

    def test_missing_tvc_material_fails_closed(self):
        request = SimpleNamespace(provider="z.ai")
        with self.assertRaises(mod.ExternalLLMConnectionError):
            mod.execute_governed_external_llm(request, session_id="s", transition_id="t", measurement_id="m", ingress_disposition="ALLOW", ingress_receipt_hash="b"*64, carrier_ref="hb32:x")

    def test_anthropic_rejects_direct_credential_compatibility_path(self):
        request = SimpleNamespace(provider="anthropic")
        with self.assertRaisesRegex(mod.ExternalLLMConnectionError, "canonical TVC non-exportable"):
            mod.execute_governed_external_llm(request, session_id="s", transition_id="t", measurement_id="m", ingress_disposition="ALLOW", ingress_receipt_hash="b"*64, carrier_ref="hb32:x", credential_resolver=lambda:"secret")

    def test_compatibility_egress_dispatch(self):
        execution = DummyExecution()
        result = mod.GovernedConnectionResult("kimi", execution, "TV_TVC_RESOLVER_COMPATIBILITY")
        sentinel = object()
        self._setattr(mod, "admit_kimi_egress", lambda **kwargs: sentinel)
        assert mod.admit_external_llm_egress(result, egress_disposition="ALLOW", egress_receipt_hash="c"*64, admitted_response_hash="a"*64) is sentinel

    def test_tvc_egress_dispatch(self):
        for provider, target_name in [
            ("zai","admit_zai_tvc_runtime_egress"),
            ("deepseek","admit_deepseek_tvc_runtime_egress"),
            ("kimi","admit_kimi_tvc_runtime_egress"),
            ("anthropic","admit_anthropic_tvc_runtime_egress"),
        ]:
            with self.subTest(provider=provider, target_name=target_name):
                execution = DummyExecution()
                result = mod.GovernedConnectionResult(provider, execution, "TVC_NON_EXPORTABLE_RUNTIME")
                sentinel = object()
                self._setattr(mod, target_name, lambda **kwargs: sentinel)
                assert mod.admit_external_llm_egress(result, egress_disposition="ALLOW", egress_receipt_hash="c"*64, admitted_response_hash="a"*64) is sentinel

    def test_openai_refuses_direct_credential_compatibility_path(self):
        for provider in ["openai", "chatgpt"]:
            with self.subTest(provider=provider):
                request = SimpleNamespace(provider=provider)
                with self.assertRaisesRegex(mod.ExternalLLMConnectionError, "OpenAI requires the canonical TVC"):
                    mod.execute_governed_external_llm(request, session_id="s", transition_id="t", measurement_id="m", ingress_disposition="ALLOW", ingress_receipt_hash="b"*64, carrier_ref="hb32:x", credential_resolver=lambda: "secret")

    def test_openai_compatibility_egress_is_refused(self):
        result = mod.GovernedConnectionResult("openai", DummyExecution(), "TV_TVC_RESOLVER_COMPATIBILITY")
        with self.assertRaisesRegex(mod.ExternalLLMConnectionError, "OpenAI compatibility egress"):
            mod.admit_external_llm_egress(result, egress_disposition="ALLOW", egress_receipt_hash="c"*64, admitted_response_hash="a"*64)


if __name__ == "__main__":
    unittest.main()
