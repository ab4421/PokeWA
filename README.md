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
4. For remote deployments set a secret in `WHATSAPP_API_TOKEN`. When the token is present the REST API requires callers to provide the same value in an `X-API-Key` header.

## Run the FastMCP server

1. Make sure the Go bridge is running and reachable.
2. From the project root, launch the MCP server:
   ```bash
   export WHATSAPP_API_TOKEN=<same value used by the bridge>
   python src/server.py
   ```
3. The server listens on `0.0.0.0:8000` by default. Override with:
   - `PORT` / `HOST` – change the HTTP bind address.
   - `MCP_TRANSPORT=stdio` – switch to stdio transport when integrating with Claude Desktop directly.
   - `WHATSAPP_API_BASE_URL` – override the bridge URL (defaults to `http://localhost:8080/api`). For Render, point this to the hosted bridge URL ending in `/api` (for example `https://whatsapp-bridge.onrender.com/api`).
   - `WHATSAPP_MESSAGES_DB` – point to a different SQLite database if the bridge runs elsewhere.
   - `WHATSAPP_API_TOKEN` – the API key shared with the Go bridge so authenticated requests succeed.

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

## Configuration

- `WHATSAPP_BRIDGE_PORT` – Port that the Go bridge binds to (Render injects this automatically).
- `WHATSAPP_API_TOKEN` – Shared secret required by the bridge and Python client to authorize requests.
- `WHATSAPP_API_BASE_URL` – Base URL for the bridge's REST API (defaults to `http://localhost:8080/api`).
- `WHATSAPP_MESSAGES_DB` – Location of the SQLite database created by the bridge (`whatsapp-bridge/store/messages.db` by default).
- `WHATSAPP_API_TIMEOUT` – Optional timeout (in seconds) for REST calls from the Python client (defaults to `30`).

## Render Deployment Notes

The provided `render.yaml` provisions both services required for a hosted deployment:

- `whatsapp-bridge` (Go) runs the WhatsApp session, mounts a persistent disk at `whatsapp-bridge/store`, and autogenerates a `WHATSAPP_API_TOKEN`. You must tail the service logs during the first deploy to capture and scan the pairing QR code. After the scan completes, the credentials remain on the disk so future restarts reconnect automatically.
- `fastmcp-server` (Python) exposes the MCP HTTP endpoint. The Render blueprint injects the same `WHATSAPP_API_TOKEN` so every request to the bridge includes the required `X-API-Key` header.

After the services are live, set `WHATSAPP_API_BASE_URL` on the FastMCP service to the bridge URL (e.g. `https://whatsapp-bridge.onrender.com/api`). If Render assigns a different hostname, update the value to match. Redeploy the FastMCP service after changing the environment variable.

### Remote pairing workflow

1. Deploy the blueprint so both services start building.
2. Open the `whatsapp-bridge` logs from the Render dashboard (Logs → Stream) to view the QR code output.
3. Scan the QR code with the WhatsApp mobile app. The bridge confirms the connection once pairing succeeds.
4. Verify that `whatsapp-bridge/store/` contains `whatsapp.db` and `messages.db` on the persistent disk. These files ensure the session survives restarts.
5. Set `WHATSAPP_API_BASE_URL` for the FastMCP service if it wasn't already configured and redeploy.

If the bridge ever loses its session (for example after deleting the disk), redeploying with an empty store will prompt a new QR code. Repeat the pairing steps above and ensure the disk remains attached so the credentials persist.

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
