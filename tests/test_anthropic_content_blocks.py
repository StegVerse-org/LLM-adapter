import unittest

from llm_adapter.anthropic_intr_transport import PayloadRejected, normalize_content_blocks


class AnthropicContentBlockTests(unittest.TestCase):
    def test_order_and_verbatim_blocks_preserved(self):
        content = [
            {"type": "text", "text": "hello"},
            {"type": "tool_use", "id": "tool-1", "name": "lookup", "input": {"q": "x"}},
            {"type": "text", "text": "world"},
        ]
        rows, output, lossy = normalize_content_blocks(content)
        self.assertEqual([r["index"] for r in rows], [0, 1, 2])
        self.assertEqual(rows[1]["block"], content[1])
        self.assertEqual(rows[1]["tool_name"], "lookup")
        self.assertEqual(rows[1]["tool_use_id"], "tool-1")
        self.assertEqual(output, "hello\nworld")
        self.assertTrue(lossy)

    def test_unknown_block_fails_closed_by_default(self):
        with self.assertRaises(PayloadRejected):
            normalize_content_blocks([{"type": "future_type", "x": 1}])

    def test_unknown_block_can_only_be_explicitly_admitted(self):
        rows, output, lossy = normalize_content_blocks([{"type": "future_type", "x": 1}], allow_unknown_block_types=True)
        self.assertEqual(rows[0]["block"], {"type": "future_type", "x": 1})
        self.assertEqual(output, "")
        self.assertTrue(lossy)


if __name__ == "__main__":
    unittest.main()
