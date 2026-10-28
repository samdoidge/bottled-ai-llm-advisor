"""Tests for the provider-neutral LLM advisor core."""
import unittest
from unittest.mock import Mock, patch


class TestParseResponse(unittest.TestCase):
    """Test response parsing - critical for reliability."""

    def test_valid_json(self):
        from rs.ai.llm_advisor.core import parse_response
        self.assertEqual(1, parse_response('{"choice": 1}', 3))

    def test_json_with_reason(self):
        from rs.ai.llm_advisor.core import parse_response
        self.assertEqual(0, parse_response('{"choice": 0, "reason": "good card"}', 3))

    def test_markdown_wrapped(self):
        from rs.ai.llm_advisor.core import parse_response
        self.assertEqual(2, parse_response('```json\n{"choice": 2}\n```', 3))

    def test_plain_markdown_block(self):
        from rs.ai.llm_advisor.core import parse_response
        self.assertEqual(1, parse_response('```\n{"choice": 1}\n```', 3))

    def test_string_number(self):
        from rs.ai.llm_advisor.core import parse_response
        self.assertEqual(1, parse_response('{"choice": "1"}', 3))

    def test_plain_number(self):
        from rs.ai.llm_advisor.core import parse_response
        self.assertEqual(0, parse_response('0', 3))

    def test_number_in_text(self):
        from rs.ai.llm_advisor.core import parse_response
        self.assertEqual(2, parse_response('I think\n2\nis best', 3))

    def test_out_of_range_high(self):
        from rs.ai.llm_advisor.core import parse_response
        self.assertIsNone(parse_response('{"choice": 5}', 3))

    def test_out_of_range_negative(self):
        from rs.ai.llm_advisor.core import parse_response
        self.assertIsNone(parse_response('{"choice": -1}', 3))

    def test_garbage(self):
        from rs.ai.llm_advisor.core import parse_response
        self.assertIsNone(parse_response('I think B is best', 3))

    def test_empty(self):
        from rs.ai.llm_advisor.core import parse_response
        self.assertIsNone(parse_response('', 3))


class TestAskAI(unittest.TestCase):
    """Test ask_ai with mocked client."""

    @patch('rs.ai.llm_advisor.core.get_client')
    @patch('rs.ai.llm_advisor.core.is_enabled')
    def test_success(self, mock_enabled, mock_get_client):
        from rs.ai.llm_advisor.core import ask_ai

        mock_enabled.return_value = True
        mock_resp = Mock()
        mock_resp.choices = [Mock()]
        mock_resp.choices[0].message.content = '{"choice": 1, "reason": "good"}'
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_resp
        mock_get_client.return_value = mock_client

        result = ask_ai("card_reward", ["A", "B", "C"], {}, "system prompt")
        self.assertEqual(1, result)

    @patch('rs.ai.llm_advisor.core.is_enabled')
    def test_disabled_returns_none(self, mock_enabled):
        from rs.ai.llm_advisor.core import ask_ai
        mock_enabled.return_value = False
        self.assertIsNone(ask_ai("card_reward", ["A", "B"], {}, "sys"))

    @patch('rs.ai.llm_advisor.core.get_client')
    def test_no_client_returns_none(self, mock_get_client):
        from rs.ai.llm_advisor.core import ask_ai
        mock_get_client.return_value = None
        self.assertIsNone(ask_ai("card_reward", ["A", "B"], {}, "sys"))

    @patch('rs.ai.llm_advisor.core.get_client')
    @patch('rs.ai.llm_advisor.core.is_enabled')
    def test_api_error_returns_none(self, mock_enabled, mock_get_client):
        from rs.ai.llm_advisor.core import ask_ai

        mock_enabled.return_value = True
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_get_client.return_value = mock_client

        self.assertIsNone(ask_ai("card_reward", ["A"], {}, "sys"))

    @patch('rs.ai.llm_advisor.core.get_client')
    @patch('rs.ai.llm_advisor.core.is_enabled')
    def test_retries_on_parse_failure(self, mock_enabled, mock_get_client):
        from rs.ai.llm_advisor.core import ask_ai

        mock_enabled.return_value = True

        # First response unparseable, second is good
        mock_resp1 = Mock()
        mock_resp1.choices = [Mock()]
        mock_resp1.choices[0].message.content = 'garbage'

        mock_resp2 = Mock()
        mock_resp2.choices = [Mock()]
        mock_resp2.choices[0].message.content = '{"choice": 1}'

        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = [mock_resp1, mock_resp2]
        mock_get_client.return_value = mock_client

        result = ask_ai("card_reward", ["A", "B"], {}, "sys")
        self.assertEqual(1, result)
        self.assertEqual(2, mock_client.chat.completions.create.call_count)


class TestIsEnabled(unittest.TestCase):
    """Test is_enabled function."""

    @patch('rs.ai.llm_advisor.core.get_client')
    def test_enabled_with_client(self, mock_get_client):
        from rs.ai.llm_advisor.core import is_enabled
        mock_get_client.return_value = Mock()
        self.assertTrue(is_enabled("card_reward"))

    @patch('rs.ai.llm_advisor.core.get_client')
    def test_disabled_without_client(self, mock_get_client):
        from rs.ai.llm_advisor.core import is_enabled
        mock_get_client.return_value = None
        self.assertFalse(is_enabled("card_reward"))

    @patch('rs.ai.llm_advisor.core.get_client')
    def test_disabled_decision_type(self, mock_get_client):
        from rs.ai.llm_advisor.core import is_enabled
        mock_get_client.return_value = Mock()
        self.assertFalse(is_enabled("boss_relic"))  # Disabled in config


if __name__ == '__main__':
    unittest.main()
