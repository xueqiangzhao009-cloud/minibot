"""Feishu/Lark channel implementation using lark-oapi SDK with WebSocket long connection."""

import asyncio
import importlib.util
import json
import os
import re
import threading
import uuid
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Literal

from loguru import logger
from pydantic import Field

from minibot.bus.bus import MessageBus
from minibot.bus.events import InboundMessage, OutboundMessage
from minibot.channels.base import BaseChannel
from minibot.config.schema import Base

FEISHU_AVAILABLE = importlib.util.find_spec("lark_oapi") is not None

MSG_TYPE_MAP = {
    "image": "[image]",
    "audio": "[audio]",
    "file": "[file]",
    "sticker": "[sticker]",
}


def _extract_share_card_content(content_json: dict, msg_type: str) -> str:
    """Extract text representation from share cards and interactive messages."""
    parts = []

    if msg_type == "share_chat":
        parts.append(f"[shared chat: {content_json.get('chat_id', '')}]")
    elif msg_type == "share_user":
        parts.append(f"[shared user: {content_json.get('user_id', '')}]")
    elif msg_type == "interactive":
        parts.extend(_extract_interactive_content(content_json))
    elif msg_type == "share_calendar_event":
        parts.append(f"[shared calendar event: {content_json.get('event_key', '')}]")
    elif msg_type == "system":
        parts.append("[system message]")
    elif msg_type == "merge_forward":
        parts.append("[merged forward messages]")

    return "\n".join(parts) if parts else f"[{msg_type}]"


def _extract_interactive_content(content: dict) -> list[str]:
    """Recursively extract text and links from interactive card content."""
    parts = []

    if isinstance(content, str):
        try:
            content = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            return [content] if content.strip() else []

    if not isinstance(content, dict):
        return parts

    if "title" in content:
        title = content["title"]
        if isinstance(title, dict):
            title_content = title.get("content", "") or title.get("text", "")
            if title_content:
                parts.append(f"title: {title_content}")
        elif isinstance(title, str):
            parts.append(f"title: {title}")

    for elements in (
        content.get("elements", []) if isinstance(content.get("elements"), list) else []
    ):
        for element in elements:
            parts.extend(_extract_element_content(element))

    card = content.get("card", {})
    if card:
        parts.extend(_extract_interactive_content(card))

    header = content.get("header", {})
    if header:
        header_title = header.get("title", {})
        if isinstance(header_title, dict):
            header_text = header_title.get("content", "") or header_title.get("text", "")
            if header_text:
                parts.append(f"title: {header_text}")

    return parts


def _extract_element_content(element: dict) -> list[str]:
    """Extract content from a single card element."""
    parts = []

    if not isinstance(element, dict):
        return parts

    tag = element.get("tag", "")

    if tag in ("markdown", "lark_md"):
        content = element.get("content", "")
        if content:
            parts.append(content)

    elif tag == "div":
        text = element.get("text", {})
        if isinstance(text, dict):
            text_content = text.get("content", "") or text.get("text", "")
            if text_content:
                parts.append(text_content)
        elif isinstance(text, str):
            parts.append(text)
        for field in element.get("fields", []):
            if isinstance(field, dict):
                field_text = field.get("text", {})
                if isinstance(field_text, dict):
                    c = field_text.get("content", "")
                    if c:
                        parts.append(c)

    elif tag == "a":
        href = element.get("href", "")
        text = element.get("text", "")
        if href:
            parts.append(f"link: {href}")
        if text:
            parts.append(text)

    elif tag == "button":
        text = element.get("text", {})
        if isinstance(text, dict):
            c = text.get("content", "")
            if c:
                parts.append(c)
        url = element.get("url", "") or element.get("multi_url", {}).get("url", "")
        if url:
            parts.append(f"link: {url}")

    elif tag == "img":
        alt = element.get("alt", {})
        parts.append(alt.get("content", "[image]") if isinstance(alt, dict) else "[image]")

    elif tag == "note":
        for ne in element.get("elements", []):
            parts.extend(_extract_element_content(ne))

    elif tag == "column_set":
        for col in element.get("columns", []):
            for ce in col.get("elements", []):
                parts.extend(_extract_element_content(ce))

    elif tag == "plain_text":
        content = element.get("content", "")
        if content:
            parts.append(content)

    else:
        for ne in element.get("elements", []):
            parts.extend(_extract_element_content(ne))

    return parts


def _extract_post_content(content_json: dict) -> tuple[str, list[str]]:
    """Extract text and image keys from Feishu post (rich text) message."""

    def _parse_block(block: dict) -> tuple[str | None, list[str]]:
        if not isinstance(block, dict) or not isinstance(block.get("content"), list):
            return None, []
        texts, images = [], []
        if title := block.get("title"):
            texts.append(title)
        for row in block["content"]:
            if not isinstance(row, list):
                continue
            for el in row:
                if not isinstance(el, dict):
                    continue
                tag = el.get("tag")
                if tag in ("text", "a"):
                    texts.append(el.get("text", ""))
                elif tag == "at":
                    texts.append(f"@{el.get('user_name', 'user')}")
                elif tag == "code_block":
                    lang = el.get("language", "")
                    code_text = el.get("text", "")
                    texts.append(f"\n```{lang}\n{code_text}\n```\n")
                elif tag == "img" and (key := el.get("image_key")):
                    images.append(key)
        return (" ".join(texts).strip() or None), images

    root = content_json
    if isinstance(root, dict) and isinstance(root.get("post"), dict):
        root = root["post"]
    if not isinstance(root, dict):
        return "", []

    if "content" in root:
        text, imgs = _parse_block(root)
        if text or imgs:
            return text or "", imgs

    for key in ("zh_cn", "en_us", "ja_jp"):
        if key in root:
            text, imgs = _parse_block(root[key])
            if text or imgs:
                return text or "", imgs
    for val in root.values():
        if isinstance(val, dict):
            text, imgs = _parse_block(val)
            if text or imgs:
                return text or "", imgs

    return "", []


def _extract_post_text(content_json: dict) -> str:
    """Extract plain text from Feishu post (rich text) message content."""
    text, _ = _extract_post_content(content_json)
    return text


class FeishuConfig(Base):
    """Feishu/Lark channel configuration using WebSocket long connection."""

    enabled: bool = False
    app_id: str = ""
    app_secret: str = ""
    encrypt_key: str = ""
    verification_token: str = ""
    allow_from: list[str] = Field(default_factory=list)
    react_emoji: str = "THUMBSUP"
    done_emoji: str | None = None
    tool_hint_prefix: str = "\U0001f527"
    group_policy: Literal["open", "mention"] = "mention"
    reply_to_message: bool = False
    streaming: bool = True
    domain: Literal["feishu", "lark"] = "feishu"


@dataclass
class _FeishuStreamBuf:
    """Per-chat streaming accumulator using CardKit streaming API."""

    text: str = ""
    card_id: str | None = None
    sequence: int = 0
    last_edit: float = 0.0


class FeishuChannel(BaseChannel):
    """
    Feishu/Lark channel using WebSocket long connection.

    Uses WebSocket to receive events - no public IP or webhook required.
    """

    name = "feishu"
    display_name = "Feishu"

    _STREAM_EDIT_INTERVAL = 0.5

    @classmethod
    def default_config(cls) -> dict[str, Any]:
        return FeishuConfig().model_dump(by_alias=True)

    def __init__(self, config: Any, bus: MessageBus):
        if isinstance(config, dict):
            config = FeishuConfig.model_validate(config)
        super().__init__(config, bus)
        self.config: FeishuConfig = config
        self._client: Any = None
        self._ws_client: Any = None
        self._ws_thread: threading.Thread | None = None
        self._processed_message_ids: OrderedDict[str, None] = OrderedDict()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._stream_bufs: dict[str, _FeishuStreamBuf] = {}
        self._bot_open_id: str | None = None

    async def start(self) -> None:
        """Start the Feishu bot with WebSocket long connection."""
        if not FEISHU_AVAILABLE:
            logger.error("Feishu SDK not installed. Run: pip install lark-oapi")
            return

        if not self.config.app_id or not self.config.app_secret:
            logger.error("Feishu app_id and app_secret not configured")
            return

        import lark_oapi as lark
        from lark_oapi.api.im.v1 import P2ImMessageReceiveV1

        self._running = True
        self._loop = asyncio.get_running_loop()

        domain = lark.const.LARK_DOMAIN if self.config.domain == "lark" else lark.const.FEISHU_DOMAIN
        self._client = (
            lark.Client.builder()
            .app_id(self.config.app_id)
            .app_secret(self.config.app_secret)
            .domain(domain)
            .log_level(lark.LogLevel.INFO)
            .build()
        )

        builder = (
            lark.EventDispatcherHandler.builder(
                self.config.encrypt_key or "",
                self.config.verification_token or "",
            )
            .register_p2_im_message_receive_v1(self._on_message_sync)
        )

        event_handler = builder.build()

        self._ws_client = lark.ws.Client(
            self.config.app_id,
            self.config.app_secret,
            domain=domain,
            event_handler=event_handler,
            log_level=lark.LogLevel.INFO,
        )

        def run_ws():
            import time
            import lark_oapi.ws.client as _lark_ws_client

            ws_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(ws_loop)
            _lark_ws_client.loop = ws_loop
            try:
                while self._running:
                    try:
                        self._ws_client.start()
                    except Exception as e:
                        logger.warning("Feishu WebSocket error: {}", e)
                    if self._running:
                        time.sleep(5)
            finally:
                ws_loop.close()

        self._ws_thread = threading.Thread(target=run_ws, daemon=True)
        self._ws_thread.start()

        self._bot_open_id = await asyncio.get_running_loop().run_in_executor(
            None, self._fetch_bot_open_id
        )
        if self._bot_open_id:
            logger.info("Feishu bot open_id: {}", self._bot_open_id)

        logger.info("Feishu bot started with WebSocket long connection")

        while self._running:
            await asyncio.sleep(1)

    async def stop(self) -> None:
        """Stop the Feishu bot."""
        self._running = False
        logger.info("Feishu bot stopped")

    def _fetch_bot_open_id(self) -> str | None:
        """Fetch the bot's own open_id via GET /open-apis/bot/v3/info."""
        try:
            import lark_oapi as lark

            request = (
                lark.BaseRequest.builder()
                .http_method(lark.HttpMethod.GET)
                .uri("/open-apis/bot/v3/info")
                .token_types({lark.AccessTokenType.APP})
                .build()
            )
            response = self._client.request(request)
            if response.success():
                data = json.loads(response.raw.content)
                bot = (data.get("data") or data).get("bot") or data.get("bot") or {}
                return bot.get("open_id")
            logger.warning("Failed to get bot info: code={}, msg={}", response.code, response.msg)
            return None
        except Exception as e:
            logger.warning("Error fetching bot info: {}", e)
            return None

    def _is_bot_mentioned(self, message: Any) -> bool:
        """Check if the bot is @mentioned in the message."""
        raw_content = message.content or ""
        if "@_all" in raw_content:
            return True

        for mention in getattr(message, "mentions", None) or []:
            mid = getattr(mention, "id", None)
            if not mid:
                continue
            mention_open_id = getattr(mid, "open_id", None) or ""
            if self._bot_open_id:
                if mention_open_id == self._bot_open_id:
                    return True
            else:
                if not getattr(mid, "user_id", None) and mention_open_id.startswith("ou_"):
                    return True
        return False

    def _is_group_message_for_bot(self, message: Any) -> bool:
        """Allow group messages when policy is open or bot is @mentioned."""
        if self.config.group_policy == "open":
            return True
        return self._is_bot_mentioned(message)

    def _add_reaction_sync(self, message_id: str, emoji_type: str) -> str | None:
        """Sync helper for adding reaction (runs in thread pool)."""
        from lark_oapi.api.im.v1 import (
            CreateMessageReactionRequest,
            CreateMessageReactionRequestBody,
            Emoji,
        )

        try:
            request = (
                CreateMessageReactionRequest.builder()
                .message_id(message_id)
                .request_body(
                    CreateMessageReactionRequestBody.builder()
                    .reaction_type(Emoji.builder().emoji_type(emoji_type).build())
                    .build()
                )
                .build()
            )

            response = self._client.im.v1.message_reaction.create(request)

            if not response.success():
                logger.warning("Failed to add reaction: code={}, msg={}", response.code, response.msg)
                return None
            else:
                return response.data.reaction_id if response.data else None
        except Exception as e:
            logger.warning("Error adding reaction: {}", e)
            return None

    async def _add_reaction(self, message_id: str, emoji_type: str = "THUMBSUP") -> str | None:
        """Add a reaction emoji to a message (non-blocking)."""
        if not self._client:
            return None

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._add_reaction_sync, message_id, emoji_type)

    def _extract_message_text(self, message: Any, event: Any) -> str:
        """Extract text content from a Feishu message."""
        msg_type = getattr(message, "msg_type", "") or ""
        content_str = getattr(message, "content", "") or "{}"

        try:
            content = json.loads(content_str) if isinstance(content_str, str) else content_str
        except json.JSONDecodeError:
            return content_str

        if msg_type == "text":
            return content.get("text", "") if isinstance(content, dict) else ""
        elif msg_type in MSG_TYPE_MAP:
            return MSG_TYPE_MAP[msg_type]
        elif msg_type == "post":
            return _extract_post_text(content)
        elif msg_type in ("share_chat", "share_user", "share_calendar_event", "system", "merge_forward"):
            return _extract_share_card_content(content, msg_type)
        elif msg_type == "interactive":
            return "\n".join(_extract_interactive_content(content))

        return content_str

    def _on_message_sync(self, data: Any) -> None:
        """Sync event handler that schedules async processing."""
        if not self._running:
            return

        try:
            asyncio.get_running_loop().run_in_executor(None, self._process_message_sync, data)
        except Exception as e:
            logger.error("Error scheduling message processing: {}", e)

    def _process_message_sync(self, data: Any) -> None:
        """Process message in thread pool."""
        try:
            event = P2ImMessageReceiveV1.parse_obj(data) if hasattr(data, "__class__") and hasattr(data.__class__, "parse_obj") else data
            message = getattr(event, "event", None)
            if not message:
                return

            message_id = getattr(message, "message_id", "") or ""
            if message_id in self._processed_message_ids:
                return
            self._processed_message_ids[message_id] = None
            if len(self._processed_message_ids) > 1000:
                excess = len(self._processed_message_ids) - 800
                for _ in range(excess):
                    self._processed_message_ids.popitem(last=False)

            sender = getattr(message, "sender", None)
            sender_id = getattr(sender, "sender_id", {}).get("open_id", "") if sender else ""
            chat_id = getattr(message, "chat_id", "") or ""

            is_p2p = getattr(message, "chat_type", "") == "p2p"
            if not is_p2p and not self._is_group_message_for_bot(message):
                return

            text = self._extract_message_text(message, event)
            if not text or not text.strip():
                return

            mentions = getattr(message, "mentions", None)
            text = self._resolve_mentions(text, mentions)

            asyncio.create_task(
                self._handle_message(
                    sender_id=sender_id,
                    chat_id=chat_id,
                    content=text,
                    metadata={
                        "message_id": message_id,
                        "msg_type": getattr(message, "msg_type", ""),
                        "chat_type": getattr(message, "chat_type", ""),
                    },
                )
            )

            if self.config.react_emoji:
                asyncio.create_task(self._add_reaction(message_id, self.config.react_emoji))

        except Exception as e:
            logger.exception("Error processing Feishu message: {}")

    def _resolve_mentions(self, text: str, mentions: list | None) -> str:
        """Replace @_user_n placeholders with actual user info."""
        if not mentions or not text:
            return text

        for mention in mentions:
            key = mention.key or None
            if not key or key not in text:
                continue

            user_id_obj = mention.id or None
            if not user_id_obj:
                continue

            open_id = user_id_obj.open_id
            user_id = user_id_obj.user_id
            name = mention.name or key

            if open_id and user_id:
                replacement = f"@{name} ({open_id}, user id: {user_id})"
            elif open_id:
                replacement = f"@{name} ({open_id})"
            else:
                replacement = f"@{name}"

            text = text.replace(key, replacement)

        return text

    async def send(self, msg: OutboundMessage) -> None:
        """Send a message through Feishu."""
        if not self._client:
            return

        chat_id = msg.chat_id
        content = msg.content

        try:
            from lark_oapi.api.im.v1 import CreateMessageRequest, CreateMessageRequestBody

            request = (
                CreateMessageRequest.builder()
                .receive_id(chat_id)
                .request_body(
                    CreateMessageRequestBody.builder()
                    .msg_type("text")
                    .content(json.dumps({"text": content}, ensure_ascii=False))
                    .build()
                )
                .build()
            )

            response = await asyncio.get_running_loop().run_in_executor(
                None, lambda: self._client.im.v1.message.create(request)
            )

            if not response.success():
                logger.error("Failed to send Feishu message: code={}, msg={}", response.code, response.msg)
        except Exception as e:
            logger.error("Error sending Feishu message: {}", e)

    async def send_delta(self, chat_id: str, delta: str, metadata: dict[str, Any] | None = None) -> None:
        """Send streaming text chunk."""
        if not self._client or not delta:
            return

        buf = self._stream_bufs.get(chat_id)
        if not buf:
            buf = _FeishuStreamBuf()
            self._stream_bufs[chat_id] = buf

        buf.text += delta
