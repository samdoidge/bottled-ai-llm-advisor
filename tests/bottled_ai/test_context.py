"""Context adapter tests. Run inside a Bottled AI checkout (needs rs.machine)."""
import unittest
from unittest.mock import Mock


class TestBuildCardRewardContext(unittest.TestCase):
    """Test card reward context building."""

    def _make_mock_state(self, deck=None, relics=None, hp=None, max_hp=None, floor="5", act=1):
        """Create a mock GameState."""
        state = Mock()

        # Deck as counter dict
        deck = deck or {"Strike": 4, "Defend": 4, "Bash": 1}
        state.get_deck_card_list_by_name_with_upgrade_stripped.return_value = deck

        # Relics
        state.get_relics.return_value = relics or ["Burning Blood"]

        # Floor
        state.floor.return_value = floor

        # Game state dict
        gs = {"act": act}
        if hp is not None:
            gs["current_hp"] = hp
        if max_hp is not None:
            gs["max_hp"] = max_hp
        state.game_state.return_value = gs

        return state

    def test_basic_context(self):
        from rs.ai.llm_advisor.context import build_card_reward_context

        state = self._make_mock_state()
        ctx = build_card_reward_context(state)

        self.assertEqual(9, ctx["deck_size"])
        self.assertEqual(["Burning Blood"], ctx["relics"])
        self.assertEqual("5", ctx["floor"])

    def test_includes_hp_when_available(self):
        from rs.ai.llm_advisor.context import build_card_reward_context

        state = self._make_mock_state(hp=50, max_hp=80)
        ctx = build_card_reward_context(state)

        self.assertEqual(50, ctx["hp"])
        self.assertEqual(80, ctx["max_hp"])
        self.assertEqual(0.62, ctx["hp_pct"])  # 50/80 = 0.625, rounded to 0.62

    def test_deck_as_dict(self):
        from rs.ai.llm_advisor.context import build_card_reward_context

        state = self._make_mock_state(deck={"Strike": 3, "Inflame": 1})
        ctx = build_card_reward_context(state)

        self.assertEqual({"Strike": 3, "Inflame": 1}, ctx["deck"])


class TestBuildBossRelicContext(unittest.TestCase):
    """Test boss relic context building."""

    def test_includes_deck_and_relics(self):
        from rs.ai.llm_advisor.context import build_boss_relic_context

        state = Mock()
        state.get_deck_card_list_by_name_with_upgrade_stripped.return_value = {"Strike": 4}
        state.get_relics.return_value = ["Burning Blood", "Vajra"]
        state.game_state.return_value = {"current_hp": 60, "max_hp": 80}

        ctx = build_boss_relic_context(state)

        self.assertEqual(4, ctx["deck_size"])
        self.assertEqual({"Strike": 4}, ctx["deck"])
        self.assertEqual(60, ctx["hp"])


class TestBuildEventContext(unittest.TestCase):
    """Test event context building."""

    def test_includes_gold(self):
        from rs.ai.llm_advisor.context import build_event_context

        state = Mock()
        state.get_deck_card_list_by_name_with_upgrade_stripped.return_value = {"Strike": 4}
        state.get_relics.return_value = []
        state.floor.return_value = "10"
        state.game_state.return_value = {"act": 1}

        ctx = build_event_context(state, gold=150)

        self.assertEqual(150, ctx["gold"])
        self.assertEqual("10", ctx["floor"])


if __name__ == '__main__':
    unittest.main()
