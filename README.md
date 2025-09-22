# WhatsApp MCP Server (FastMCP Template)

This repository adapts the [WhatsApp MCP project](https://github.com/lharries/whatsapp-mcp) to the FastMCP server template so it can be deployed locally or on Render and connected to the [Poke assistant](https://poke.com/). The solution keeps the original Go bridge that talks to WhatsApp Web while exposing the Model Context Protocol (MCP) tools through a FastMCP HTTP server.

## Repository Layout

- `src/server.py` – FastMCP server that exposes WhatsApp tools over HTTP or stdio.
- `src/whatsapp.py` – SQLite/database accessors and REST helpers used by the tools.
- `src/audio.py` – Optional ffmpeg-powered audio helpers for voice messages.
- `whatsapp-bridge/` – Go application that syncs with WhatsApp Web and serves a REST API.

## Prerequisites

- Go **1.24+** (required for `whatsapp-bridge`).
- Python **3.11+**.
- `ffmpeg` (optional, required only when converting arbitrary audio into WhatsApp voice messages).

## Setup

```bash
git clone <your-repo-url>
cd PokeWA
python -m venv .venv
source .venv/bin/activate  # or use your preferred environment manager
pip install -r requirements.txt
```

## Run the Go WhatsApp bridge

1. In a separate terminal, start the bridge:
   ```bash
   cd whatsapp-bridge
   go run main.go
   ```
2. On the first run a QR code is printed—scan it with the WhatsApp app on your phone to authenticate.
3. Chat history is stored in `whatsapp-bridge/store/`. If you want to choose a different port, set `WHATSAPP_BRIDGE_PORT` (defaults to `8080`).

## Run the FastMCP server

1. Make sure the Go bridge is running and reachable.
2. From the project root, launch the MCP server:
   ```bash
   python src/server.py
   ```
3. The server listens on `0.0.0.0:8000` by default. Override with:
   - `PORT` / `HOST` – change the HTTP bind address.
   - `MCP_TRANSPORT=stdio` – switch to stdio transport when integrating with Claude Desktop directly.
   - `WHATSAPP_API_BASE_URL` – override the bridge URL (defaults to `http://localhost:8080/api`).
   - `WHATSAPP_MESSAGES_DB` – point to a different SQLite database if the bridge runs elsewhere.

## Poke Integration

Once both processes are running you can add the server inside Poke (Settings → Connections) using the HTTP endpoint, e.g. `http://localhost:8000/mcp` with Streamable HTTP transport. Give the connection a descriptive name such as `whatsapp` and test with a prompt like:

```
Tell the subagent to use the "whatsapp" integration's "list_chats" tool.
```

If you change ports or run the bridge remotely, ensure `WHATSAPP_API_BASE_URL` is updated accordingly in the Python process.

## Local Testing with the MCP Inspector

```bash
python src/server.py  # in one terminal
npx @modelcontextprotocol/inspector  # in another terminal
# connect to http://localhost:8000/mcp using the Streamable HTTP transport
```

## Render Deployment Notes

The included `render.yaml` still targets the FastMCP HTTP server. Deploying the Go bridge on Render is not currently automated because it requires QR-code pairing and long-lived connections to WhatsApp Web. For cloud setups run the Go bridge on a separate machine (or self-hosted service) and point the deployed FastMCP instance at it via `WHATSAPP_API_BASE_URL`.

## Available MCP Tools

- `search_contacts`
- `list_messages`
- `list_chats`
- `get_chat`
- `get_direct_chat_by_contact`
- `get_contact_chats`
- `get_last_interaction`
- `get_message_context`
- `send_message`
- `send_file`
- `send_audio_message`
- `download_media`

All tools are thin wrappers around the original WhatsApp MCP behaviour, now exposed through the FastMCP template so they can be consumed by Poke or any other MCP-compatible client.
