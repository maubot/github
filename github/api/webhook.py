# github - A maubot plugin to act as a GitHub client and webhook receiver.
# Copyright (C) 2020 Tulir Asokan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from typing import TYPE_CHECKING, Optional, Protocol
from uuid import UUID
import hashlib
import hmac
import json

from aiohttp import web
from attr import dataclass

from maubot.handlers import web as web_handler
from mautrix.types import RoomID, SerializerError

from ..db import WebhookInfo
from .types import EVENT_CLASSES, Event, EventType

if TYPE_CHECKING:
    from ..webhook import WebhookManager


class HandlerFunc(Protocol):
    async def __call__(
        self, evt_type: EventType, evt: Event, delivery_id: str, info: WebhookInfo
    ) -> None:
        pass


@dataclass(frozen=True)
class GlobalWebhookInfo(WebhookInfo):
    room_id: RoomID
    secret: str

    id: UUID = UUID(int=0)
    user_id: str = "root"
    github_id: int | None = None
    repo: str = "unknown"

    def __str__(self) -> str:
        return f"global webhook for {self.room_id!r}"


class GitHubWebhookReceiver:
    handler: "HandlerFunc"
    secrets: "WebhookManager"
    global_secret: Optional[str]

    def __init__(
        self, handler: "HandlerFunc", secrets: "WebhookManager", global_secret: Optional[str]
    ) -> None:
        self.handler = handler
        self.secrets = secrets
        self.global_secret = global_secret

    @web_handler.post("/webhook")
    async def handle_global(self, request: web.Request) -> web.Response:
        if not self.global_secret:
            return web.Response(status=403, text="global webhooks are disabled")
        try:
            room_id = RoomID(request.query["room"])
        except KeyError:
            return web.Response(status=400, text="room query param missing")
        return await self._handle(
            request, GlobalWebhookInfo(room_id=room_id, secret=self.global_secret)
        )

    @web_handler.post("/webhook/{id}")
    async def handle(self, request: web.Request) -> web.Response:
        try:
            id = UUID(request.match_info["id"])
        except ValueError:
            return web.Response(status=404, text="Invalid webhook ID")
        webhook_info = await self.secrets.get(id)
        if webhook_info is None:
            return web.Response(status=404, text="Webhook not found")
        return await self._handle(request, webhook_info)

    async def _handle(self, request: web.Request, webhook_info: "WebhookInfo") -> web.Response:
        try:
            signature = request.headers["X-Hub-Signature"]
            event_type = EventType(request.headers["X-Github-Event"])
            delivery_id = request.headers["X-Github-Delivery"]
        except KeyError as e:
            return web.Response(status=400, text=f"Missing {e.args[0]} header")
        except ValueError:
            return web.Response(status=202, text="Unsupported event type")
        text = await request.text()
        text_binary = text.encode("utf-8")
        secret = webhook_info.secret.encode("utf-8")
        digest = f"sha1={hmac.new(secret, text_binary, hashlib.sha1).hexdigest()}"
        if not hmac.compare_digest(signature, digest):
            return web.Response(status=401, text="Invalid signature")
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return web.Response(status=400, text="Malformed JSON")
        if not data:
            return web.Response(status=400, text="Malformed JSON")
        try:
            type_class = EVENT_CLASSES[event_type]
        except KeyError:
            return web.Response(status=500, text="Content class not found")
        try:
            event = type_class.deserialize(data)
        except SerializerError:
            return web.Response(status=500, text="Failed to parse event content")
        resp = await self.handler(event_type, event, delivery_id, webhook_info)
        if not isinstance(resp, web.Response):
            resp = web.Response(status=200)
        return resp
