# github - A maubot plugin to act as a GitHub client and webhook receiver.
# Copyright (C) 2019 Tulir Asokan
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
from typing import Dict, List, Callable, Awaitable
from json import JSONDecodeError
import hashlib
import hmac

from aiohttp import web

from maubot import PluginWebApp


class GitHubWebhookReceiver:
    webapp: PluginWebApp
    handlers: Dict[str, List[Callable[[Dict], Awaitable]]]
    webhooks: Dict[str, str]

    def __init__(self, webapp: PluginWebApp) -> None:
        self.handlers = {}
        self.webhooks = {}
        self.webapp = webapp
        self.webapp.add_post("/webhook/{id}", self.handle_webhook)

    def add_handler(self, event_type: str, handler: Callable[[Dict], Awaitable]) -> None:
        self.handlers.setdefault(event_type, []).append(handler)

    def add_webhook(self, webhook_id: str, secret: str) -> None:
        self.webhooks[webhook_id] = secret

    async def handle_webhook(self, request: web.Request) -> web.Response:
        try:
            webhook_id = request.match_info["id"]
            secret = self.webhooks[webhook_id]
        except KeyError:
            return web.Response(status=404, text="Webhook not found")
        try:
            signature = request.headers["X-Hub-Signature"]
        except KeyError:
            return web.Response(status=400, text="Missing signature header")
        try:
            event_type = request.headers["X-Github-Event"]
        except KeyError:
            return web.Response(status=400, text="Missing event type header")
        try:
            delivery_id = request.headers["X-Github-Delivery"]
        except KeyError:
            return web.Response(status=400, text="Missing delivery ID header")
        digest = f"sha1={hmac.new(secret, await request.text(), hashlib.sha1).hexdigest()}"
        if not hmac.compare_digest(signature, digest):
            return web.Response(status=401, text="Invalid signature")
        try:
            data = await request.json()
        except JSONDecodeError:
            return web.Response(status=400, text="JSON parse error")
        if not data:
            return web.Response(status=400, text="Request body must be JSON")
        data["event_type"] = event_type
        data["delivery_id"] = delivery_id
        data["webhook_id"] = webhook_id
        for handler in self.handlers.get(event_type, []) + self.handlers.get("*", []):
            resp = await handler(data)
            if isinstance(resp, web.Response):
                return resp
        return web.Response(status=200)
