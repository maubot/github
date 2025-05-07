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
from aiohttp import ClientError, ClientSession, web

from maubot.handlers import web as web_handler
from mautrix.types import UserID

from .api import GitHubClient
from .db import DBManager


class ClientManager:
    client_id: str
    client_secret: str
    _clients: dict[UserID, GitHubClient]
    _db: DBManager
    _http: ClientSession

    def __init__(self, client_id: str, client_secret: str, http: ClientSession, db: DBManager):
        self.client_id = client_id
        self.client_secret = client_secret
        self._db = db
        self._http = http
        self._clients = {}

    async def load_db(self) -> None:
        self._clients = {
            user_id: self._make(token) for user_id, token in await self._db.get_clients()
        }

    def _make(self, token: str) -> GitHubClient:
        return GitHubClient(
            http=self._http,
            client_id=self.client_id,
            client_secret=self.client_secret,
            token=token,
        )

    async def put(self, user_id: UserID, token: str) -> None:
        await self._db.put_client(user_id, token)

    async def remove(self, user_id: UserID) -> None:
        self._clients.pop(user_id, None)
        await self._db.delete_client(user_id)

    def get_all(self) -> dict[UserID, GitHubClient]:
        return self._clients.copy()

    def get(self, user_id: UserID, create: bool = False) -> GitHubClient | None:
        try:
            return self._clients[user_id]
        except KeyError:
            if create:
                client = self._make("")
                self._clients[user_id] = client
                return client
            return None

    @web_handler.get("/auth")
    async def login_callback(self, request: web.Request) -> web.Response:
        # TODO fancy webpages here
        try:
            error_code = request.query["error"]
            error_msg = request.query["error_description"]
            error_uri = request.query.get("error_uri", "<no URI provided>")
        except KeyError:
            pass
        else:
            return web.Response(
                status=400,
                text=f"Failed to log in: {error_code}\n\n"
                f"{error_msg}\n\n"
                f"More info at {error_uri}",
            )
        try:
            user_id = UserID(request.query["user_id"])
            code = request.query["code"]
            state = request.query["state"]
        except KeyError as e:
            return web.Response(status=400, text=f"Missing {e.args[0]} parameter")
        client = self.get(user_id)
        if not client:
            return web.Response(status=401, text="Invalid state token")
        try:
            await client.finish_login(code, state)
        except ValueError:
            return web.Response(status=401, text="Invalid state token")
        except (KeyError, ClientError):
            return web.Response(status=401, text="Failed to finish login")
        resp = await client.query("viewer { login }")
        user = resp["viewer"]["login"]
        await self.put(user_id, client.token)
        return web.Response(status=200, text=f"Logged in as {user}")
