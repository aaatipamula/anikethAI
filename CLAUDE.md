# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Discord bot that uses OpenAI's GPT-4o-mini (via LangChain) to simulate conversation in a sarcastic, Twitch-chatter style. It also posts RSS feed updates on a schedule and maintains a starboard.

## Environment setup

Copy `.env` to `src/data/.env` with these variables:
```
TOKEN=           # Discord bot token
OPENAI_API_KEY=  # OpenAI key
COMMAND_PREFIX=  # e.g. "!"
DUMP_CHANNEL=    # Discord channel ID for error logging
ABOUT_ME=        # Bot description shown in help
TIMEZONE=        # pytz timezone string, e.g. "America/Chicago"
START_HOUR=      # Hour (0-23) for first daily RSS post
```

## Running

```bash
# Local (from repo root)
python3 src/main.py

# Docker
docker build -t anikethai .
docker run --env-file src/data/.env anikethai
```

Package management uses `uv` with `pyproject.toml`. The lockfile is `requirements.txt` (used by Docker).

## Architecture

All source lives in `src/`. The entry point is `main.py`, which:
1. Loads env vars and creates the `discord.py` `commands.Bot`
2. Initializes a shared `TopicQueue` instance
3. Creates `AdminCog` and `UserCog` and registers them in `on_ready`
4. Starts two background `tasks.loop` tasks: `set_status` and `update_rss_channel`

**Key modules:**
- `chain.py` — builds the LangChain `LLMChain` with the system prompt and `ConversationBufferWindowMemory`. Call `create_aniketh_ai(memory)` to get a chain; call `chain.predict(user_message=...)` to generate responses.
- `database.py` — SQLite via SQLAlchemy. Two tables: `Users` (stores per-channel conversation memory as JSON) and `StarredMessages` (maps original message ID → starboard message ID). Call `get_user_mem(channel_id)` / `dump_user_mem(channel_id, mem)` around every AI response.
- `topicQueue.py` — in-memory queue of topics (max 30, max 50 chars each). `pick_topic()` removes and returns a random topic, falling back to a default string if empty.
- `ext.py` — all Discord embed builders plus the `help_command` function. Help content is driven by `src/data/commands.json`.
- `consts.py` — `NO_TOKENS` (rate-limit fallback messages) and `RANDOM_REPLYS` (probabilistic keyword triggers).
- `util.py` — `normalize_tz` converts a pytz timezone + start hour into four `datetime.time` objects spaced 6 hours apart (used to schedule RSS updates).

**Cog responsibilities:**
- `AdminCog` — owner-only commands under the `admin` group. Manages RSS feeds (stored in `src/data/rss.txt`), controls background loops, sets starboard config on `UserCog`, and handles bot lock/unlock.
- `UserCog` — user-facing commands (`request`, `rm`, `topics`, `help`) plus `on_message` (AI reply when mentioned) and `on_reaction_add`/`on_reaction_remove` (starboard logic).

**Data files** (all under `src/data/`):
- `.env` — environment variables (not committed)
- `bot.db` — SQLite database (auto-created on first run)
- `rss.txt` — persisted RSS feed URLs, one per line
- `commands.json` — help system content
