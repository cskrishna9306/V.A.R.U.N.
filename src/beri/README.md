# Beri

Beri is the **Splitwise** integration layer responsible for authenticating with the Splitwise API, resolving people and groups by name (with fuzzy string matching), and creating expenses. A separate in-memory **WSJ** (Wall Street Journal) graph tracks who owes whom for internal bookkeeping and flows used alongside live Splitwise calls.

## What it does?

- **Credentials** — Reads `SPLITWISE_CONSUMER_KEY`, `SPLITWISE_CONSUMER_SECRET`, and `SPLITWISE_API_KEY` from the environment (see `config.py`).
- **Lookup** — `get_groups`, `get_group_id`, and `get_user_id` help agents map human-readable names to Splitwise IDs.
- **Logging** — `log_expense` (and lower-level `add_transaction`) build Splitwise `Expense` payloads from amounts, participants, split policy, and optional group.
- **Models** — `User`, `Transaction`, `Debt`, and `SplitPolicy` describe participants and how a bill is split before it hits the API.
- **WSJ** — `wall_street_journal.py` maintains a directed debt graph between `User` nodes for balance-style logic outside of a single API call.

## Directory Structure

| File or folder | Role |
|----------------|------|
| `__init__.py` | Re-exports `Beri` from `ledger`. |
| `config.py` | Loads Splitwise API keys from the environment. |
| `ledger.py` | `Beri` class: Splitwise client, name resolution, expense creation, and hooks into WSJ. |
| `wall_street_journal.py` | `WSJ` class: in-memory user/debt graph and transaction count. |
| `models/` | Pydantic-style domain types: `User`, `Transaction`, `Debt`, `SplitPolicy`. |

The public entry point for the rest of the app is `Beri` in `ledger.py`, which is what Discord tools and agents import.
