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
from typing import Dict, Union, Callable, Awaitable
from json import JSONDecodeError
import hashlib
import hmac

from aiohttp import web


class GitHubWebhookReceiver:
    handler: Callable[[Dict], Awaitable]
    secret: Callable[[web.Request], str]

    def __init__(self, handler: Callable[[Dict], Awaitable],
                 secret: Union[str, Callable[[web.Request], str]]) -> None:
        self.handler = handler
        self.secret = lambda r: secret if isinstance(secret, str) else secret

    async def handle(self, request: web.Request) -> web.Response:
        try:
            secret = self.secret(request)
        except KeyError:
            return web.Response(status=404, text="Webhook not found")
        try:
            signature = request.headers["X-Hub-Signature"]
            event_type = request.headers["X-Github-Event"]
            delivery_id = request.headers["X-Github-Delivery"]
        except KeyError as e:
            return web.Response(status=400, text=f"Missing {e.args[0]} header")
        digest = f"sha1={hmac.new(secret, await request.text(), hashlib.sha1).hexdigest()}"
        if not hmac.compare_digest(signature, digest):
            return web.Response(status=401, text="Invalid signature")
        try:
            data = await request.json()
        except JSONDecodeError:
            return web.Response(status=400, text="JSON parse error")
        if not data:
            return web.Response(status=400, text="Request body must be JSON")
        data["__event_type__"] = event_type
        data["__delivery_id__"] = delivery_id
        data["__secret__"] = secret
        data["__request__"] = request
        resp = await self.handler(data)
        if not isinstance(resp, web.Response):
            resp = web.Response(status=200)
        return resp
