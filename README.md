# humuter-cli

**Deploy AI agents from your terminal.**

Humuter is a platform for deploying AI agents that handle community management, sales, standups, and analytics on Telegram, Discord, and Slack. This is the official command-line interface.

```
  ██   ██ ██    ██ ███    ███ ██    ██ ████████ ███████ ██████
  ██   ██ ██    ██ ████  ████ ██    ██    ██    ██      ██   ██
  ███████ ██    ██ ██ ████ ██ ██    ██    ██    █████   ██████
  ██   ██ ██    ██ ██  ██  ██ ██    ██    ██    ██      ██   ██
  ██   ██  ██████  ██      ██  ██████     ██    ███████ ██   ██
```

## Install

```bash
pip install humuter-cli
```

Requires Python 3.10+.

## Quick start

```bash
# Sign in via browser (device flow)
humuter login

# Launch the interactive dashboard
humuter

# Or use standalone commands
humuter agents list
humuter credits
```

## Interactive dashboard

Running `humuter` with no arguments opens a full-screen Textual TUI with keyboard-driven navigation:

| Key | Action |
|-----|--------|
| `d` | Dashboard (overview) |
| `a` | Agents list |
| `n` | New agent |
| `b` | Billing & credits |
| `c` | Chat (test your agent) |
| `q` | Quit |

From the dashboard you can create agents, configure them, connect Telegram bots, chat with them live, and monitor usage — all without leaving the terminal.

## Commands

### Auth

```bash
humuter login    # Open browser, authenticate, store credentials
humuter logout   # Clear stored credentials
```

### Agents

```bash
humuter agents list                 # List all your agents
humuter agents status <AGENT_ID>    # Show agent details
```

### Credits

```bash
humuter credits                     # Show balance and per-agent usage
```

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `HUMUTER_API_URL` | `https://platform.humuter.com` | Override the API base URL (for self-hosted or staging) |

## How authentication works

The CLI uses a **device-flow login** — no passwords touch the terminal:

1. `humuter login` opens your default browser to a unique auth URL
2. You sign in on humuter.com (existing session or new login)
3. The CLI polls until the browser confirms, then stores the token locally

Credentials are stored in `~/.humuter/credentials.json` with `0o600` permissions (readable only by you). The CLI automatically refreshes expired tokens using the stored refresh token.

To sign out: `humuter logout` (removes the credentials file).

## What can I do with it?

- **Create and manage AI agents** — community managers, sales agents, team managers, community analysts
- **Connect Telegram bots** via BotFather token or personal account (MTProto)
- **Chat with your agents** directly in the terminal to test responses
- **Monitor usage and billing** — see token consumption, message counts, credits remaining
- **Generate API keys** for programmatic access to the agent chat API

For full agent deployment (training data, group setup, RAG), the dashboard at [humuter.com/dashboard](https://humuter.com/dashboard) is still the fastest path.

## Architecture

The CLI is a thin HTTP client — all business logic (LLM calls, RAG, tool execution, spam detection, analytics) lives on the Humuter backend. This repo is safe to audit, fork, and contribute to.

```
humuter-cli (this repo, Python + Textual)
    │
    └── HTTPS → platform.humuter.com/api/*
                    │
                    ├── Supabase (Postgres + auth)
                    ├── Anthropic / OpenAI (LLMs)
                    └── Restext (RAG)
```

## Contributing

Issues and PRs welcome. If you find a bug or want a feature, open an issue on GitHub. For platform-level questions, DM [@mainhooman](https://t.me/mainhooman) on Telegram.

## License

MIT — see [LICENSE](./LICENSE).

## Links

- **Dashboard:** [humuter.com](https://humuter.com)
- **Docs:** [humuter.com/docs](https://humuter.com/docs)
- **Telegram:** [@mainhooman](https://t.me/mainhooman)
