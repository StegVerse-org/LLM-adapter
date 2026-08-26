from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from llm_adapter.provider_surface_knowledge import ProviderSurfaceKnowledgeError, resolve_provider_surface_question

class ProviderSurfaceKnowledgeTests(unittest.TestCase):
    def _registry(self, observations):
        payload={"schema":"stegverse.kv.provider-surface-capability-registry/v1","state":"PARTIALLY_VERIFIED","authority_effect":"NONE","provider_families":["icloud"],"observations":observations}
        td=tempfile.TemporaryDirectory(); path=Path(td.name)/"registry.json"; path.write_text(json.dumps(payload),encoding="utf-8")
        return td,path

    def test_empty_registry_returns_transparent_unknown(self):
        td,path=self._registry([])
        try:
            answer=resolve_provider_surface_question("Why is Safari with iCloud different on iPhone?",path=path)
            self.assertIsNotNone(answer); self.assertEqual(answer.match_state,"UNKNOWN_UNVERIFIED")
            self.assertIn("will not infer",answer.answer)
        finally: td.cleanup()

    def test_verified_tuple_returns_recorded_route(self):
        obs={"provider":"icloud","device_class":"iphone","platform":"ios","access_surface":"browser","knowledge_state":"VERIFIED","capabilities":{},"preferred_route":"os_file_provider","fallback_route":"browser","limitations":["background sync is weaker"],"evidence":{"source_type":"conformance_test","source_ref":"evidence:test","observed_at":"2026-08-26","version":"1"}}
        td,path=self._registry([obs])
        try:
            answer=resolve_provider_surface_question("Why is Safari with iCloud different on iPhone?",path=path)
            self.assertEqual(answer.match_state,"VERIFIED"); self.assertIn("os_file_provider",answer.answer)
            self.assertIn("background sync is weaker",answer.answer)
        finally: td.cleanup()

    def test_missing_registry_fails_closed(self):
        with self.assertRaises(ProviderSurfaceKnowledgeError):
            resolve_provider_surface_question("Why is Safari with iCloud different?",path="/definitely/missing.json")

if __name__=="__main__": unittest.main()
