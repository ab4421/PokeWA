#!/usr/bin/env python3
"""FastMCP server exposing WhatsApp tools via the Go bridge."""

from __future__ import annotations

import os
from dataclasses import asdict, is_dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from whatsapp import (
    download_media as whatsapp_download_media,
    get_chat as whatsapp_get_chat,
    get_contact_chats as whatsapp_get_contact_chats,
    get_direct_chat_by_contact as whatsapp_get_direct_chat_by_contact,
    get_last_interaction as whatsapp_get_last_interaction,
    get_message_context as whatsapp_get_message_context,
    list_chats as whatsapp_list_chats,
    list_messages as whatsapp_list_messages,
    search_contacts as whatsapp_search_contacts,
    send_audio_message as whatsapp_send_audio_message,
    send_file as whatsapp_send_file,
    send_message as whatsapp_send_message,
)

mcp = FastMCP("whatsapp")


def _serialize(value: Any) -> Any:
    """Convert dataclasses and datetimes to JSON-serializable structures."""

    if is_dataclass(value):
        return _serialize(asdict(value))
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _serialize(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize(item) for item in value]
    return value


@mcp.tool()
def search_contacts(query: str) -> List[Dict[str, Any]]:
    """Search WhatsApp contacts by name or phone number."""

    contacts = whatsapp_search_contacts(query)
    return _serialize(contacts)


@mcp.tool()
def list_messages(
    after: Optional[str] = None,
    before: Optional[str] = None,
    sender_phone_number: Optional[str] = None,
    chat_jid: Optional[str] = None,
    query: Optional[str] = None,
    limit: int = 20,
    page: int = 0,
    include_context: bool = True,
    context_before: int = 1,
    context_after: int = 1,
) -> str:
    """Get WhatsApp messages matching specified criteria with optional context."""

    return whatsapp_list_messages(
        after=after,
        before=before,
        sender_phone_number=sender_phone_number,
        chat_jid=chat_jid,
        query=query,
        limit=limit,
        page=page,
        include_context=include_context,
        context_before=context_before,
        context_after=context_after,
    )


@mcp.tool()
def list_chats(
    query: Optional[str] = None,
    limit: int = 20,
    page: int = 0,
    include_last_message: bool = True,
    sort_by: str = "last_active",
) -> List[Dict[str, Any]]:
    """Get WhatsApp chats matching specified criteria."""

    chats = whatsapp_list_chats(
        query=query,
        limit=limit,
        page=page,
        include_last_message=include_last_message,
        sort_by=sort_by,
    )
    return _serialize(chats)


@mcp.tool()
def get_chat(chat_jid: str, include_last_message: bool = True) -> Dict[str, Any]:
    """Get WhatsApp chat metadata by JID."""

    chat = whatsapp_get_chat(chat_jid, include_last_message)
    return _serialize(chat)


@mcp.tool()
def get_direct_chat_by_contact(sender_phone_number: str) -> Dict[str, Any]:
    """Get WhatsApp chat metadata by sender phone number."""

    chat = whatsapp_get_direct_chat_by_contact(sender_phone_number)
    return _serialize(chat)


@mcp.tool()
def get_contact_chats(jid: str, limit: int = 20, page: int = 0) -> List[Dict[str, Any]]:
    """Get all WhatsApp chats involving the contact."""

    chats = whatsapp_get_contact_chats(jid, limit, page)
    return _serialize(chats)


@mcp.tool()
def get_last_interaction(jid: str) -> Optional[str]:
    """Get most recent WhatsApp message involving the contact."""

    return whatsapp_get_last_interaction(jid)


@mcp.tool()
def get_message_context(
    message_id: str,
    before: int = 5,
    after: int = 5,
) -> Dict[str, Any]:
    """Get context around a specific WhatsApp message."""

    context = whatsapp_get_message_context(message_id, before, after)
    return _serialize(context)


@mcp.tool()
def send_message(recipient: str, message: str) -> Dict[str, Any]:
    """Send a WhatsApp message to a person or group."""

    if not recipient:
        return {
            "success": False,
            "message": "Recipient must be provided",
        }

    success, status_message = whatsapp_send_message(recipient, message)
    return {
        "success": success,
        "message": status_message,
    }


@mcp.tool()
def send_file(recipient: str, media_path: str) -> Dict[str, Any]:
    """Send an image, video, raw audio, or document via WhatsApp."""

    success, status_message = whatsapp_send_file(recipient, media_path)
    return {
        "success": success,
        "message": status_message,
    }


@mcp.tool()
def send_audio_message(recipient: str, media_path: str) -> Dict[str, Any]:
    """Send an audio file as a WhatsApp voice message."""

    success, status_message = whatsapp_send_audio_message(recipient, media_path)
    return {
        "success": success,
        "message": status_message,
    }


@mcp.tool()
def download_media(message_id: str, chat_jid: str) -> Dict[str, Any]:
    """Download media from a WhatsApp message and get the local file path."""

    file_path = whatsapp_download_media(message_id, chat_jid)

    if file_path:
        return {
            "success": True,
            "message": "Media downloaded successfully",
            "file_path": file_path,
        }

    return {
        "success": False,
        "message": "Failed to download media",
    }


if __name__ == "__main__":
    transport = os.environ.get("MCP_TRANSPORT", "http").lower()

    if transport == "stdio":
        mcp.run(transport="stdio")
    else:
        port = int(os.environ.get("PORT", "8000"))
        host = os.environ.get("HOST", "0.0.0.0")
        print(f"Starting WhatsApp MCP server on {host}:{port} using HTTP transport")
        mcp.run(
            transport="http",
            host=host,
            port=port,
            stateless_http=True,
        )
