# Bottled AI + LLM Advisor

A minimal, drop-in LLM decision advisor for [Bottled AI](https://github.com/xaved88/bottled_ai), the Slay the Spire bot. DeepSeek is the default; any OpenAI-compatible endpoint works.

This is not a full bot. It adds **one worked handler** (card rewards) to a Bottled AI checkout, with a strict JSON choice contract and a rule-based fallback. Combat stays with Bottled AI's simulator.

## Design

- The LLM is used for out-of-combat choices only. The included example is card rewards; the same shape extends to boss relics, shops, upgrades, and Neow.
- At most two API calls per decision: one attempt, plus one retry after an invalid response. The model returns an option index, never a game command.
- Any failure — missing key, missing SDK, timeout, invalid JSON — returns `None` and the handler falls back.
- The transport is provider-neutral (`LLM_BASE_URL`), with DeepSeek defaults.
- The synchronous call blocks the game loop. Keep the timeout short; 30 seconds is the default.

## Provenance

This is a cleaned, minimal extraction of a working private Bottled AI fork. The private branch also contained decision-specific handlers, game-data tables, and training-data export scripts; those are intentionally excluded because they are game-specific, not MIT-clean, or not needed to show the integration.

## Files

```
rs/ai/llm_advisor/
  client.py       lazy OpenAI-compatible client
  config.py       env-driven settings
  core.py         ask/parse/retry + logging
  prompts.py      generic system prompt + card reward example
  context.py      small GameState -> dict adapter
  handlers/       one card reward handler
  strategy.py     example strategy wiring
tests/test_core.py       parser/retry tests, no game needed
tests/bottled_ai/        context tests, run inside a Bottled AI checkout
main.py.patch            opt-in strategy selection
```

## Diff against upstream

The full change against `xaved88/bottled_ai` `main` is 10 files, +502/−1: nine new files under `rs/ai/llm_advisor/`, plus two lines in `main.py`.

- Commit: <https://github.com/samdoidge/bottled_ai/commit/e30d70a>
- Compare: <https://github.com/xaved88/bottled_ai/compare/main...samdoidge:llm-advisor-example>
- Patch: [`llm-advisor.patch`](llm-advisor.patch)

## Install

1. Clone [Bottled AI](https://github.com/xaved88/bottled_ai) and follow its setup (CommunicationMod, mods).
2. Copy `rs/ai/llm_advisor` into the same path in your Bottled AI checkout.
3. Install the SDK:

   ```sh
   pip install -r requirements.txt
   ```

4. Set the environment:

   ```sh
   export LLM_API_KEY="..."
   export LLM_MODEL="deepseek-chat"    # or deepseek-reasoner
   ```

5. Select the strategy in `main.py`:

   ```python
   from rs.ai.llm_advisor.strategy import LLM_IRONCLAD
   strategy = LLM_IRONCLAD
   ```

   Or apply `main.py.patch`.

## Configuration

| Variable | Default | Notes |
| --- | --- | --- |
| `LLM_API_KEY` | empty | Required; without it the advisor disables cleanly |
| `LLM_BASE_URL` | `https://api.deepseek.com` | Any OpenAI-compatible base URL |
| `LLM_MODEL` | `deepseek-chat` | `deepseek-reasoner` also works |
| `LLM_TIMEOUT` | `30` | Seconds per request |
| `LLM_MAX_TOKENS` | `500` | Raise for reasoning models |
| `LLM_TEMPERATURE` | `0.2` | 0.0–2.0 |

Per-decision switches live in `config.py` (`ENABLED`). Only decisions with an LLM handler can be enabled.

## How a decision works

1. The handler matches a card-reward screen and an available `choose` command.
2. It builds a small context: deck counts, relics, floor, act, HP.
3. Choices are card names, plus `SKIP` when the game offers it.
4. `ask_ai()` sends the system prompt, a mode prompt, numbered options, and compact JSON context.
5. The response must be `{"choice": N, "reason": "..."}`. The index is validated; one retry is allowed.
6. The handler sends `choose N` or skips. If the LLM fails, it takes the first offered card (or skips only when there are no choices), so an API outage does not silently skip every reward.

## Limits and safety

- Costs and latency: one call per decision; the default is 30 seconds, two attempts. Lower `LLM_TIMEOUT` if the bot feels sluggish.
- Logs: `logs/llm_advisor.log` contains the full prompt, choices, context, and response. It is gitignored; review it before sharing.
- The model cannot emit commands. It can only pick an index that is validated against the option list.
- Prompt injection is bounded by the index validation; mod-provided names can still appear in context.
- No game data, card tables, training data, or API keys are included.
- Not affiliated with Bottled AI, DeepSeek, or the Slay the Spire rights holders.

## Tests

```sh
python -m unittest discover -s tests -p 'test_core.py' -v
```

The `tests/bottled_ai` context tests require a Bottled AI checkout because the adapter imports `rs.machine`.

## Credits

- [Bottled AI](https://github.com/xaved88/bottled_ai), MIT © 2024 Logan Bentley & Robert Aiking.
- Extracted from a private Bottled AI fork, MIT © 2026 Sam Doidge.
