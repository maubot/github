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
from typing import Dict, Optional

from sqlalchemy import MetaData, Table, Column, String
from sqlalchemy.engine.base import Engine
from aiohttp import web, ClientError, ClientSession

from mautrix.types import UserID
from maubot.handlers import web as web_handler

from .api import GitHubClient


class ClientManager:
    client_id: str
    client_secret: str
    _clients: Dict[UserID, GitHubClient]
    _table: Table
    _db: Engine
    _http: ClientSession

    def __init__(self, client_id: str, client_secret: str, http: ClientSession,
                 db: Engine, metadata: MetaData):
        self.client_id = client_id
        self.client_secret = client_secret
        self._db = db
        self._http = http
        self._table = Table("client", metadata,
                            Column("user_id", String(255), primary_key=True),
                            Column("token", String(255), nullable=False))
        self._clients = {}

    def load_db(self) -> None:
        self._clients = {user_id: self._make(token)
                         for user_id, token
                         in self._db.execute(self._table.select())}

    def _make(self, token: str) -> GitHubClient:
        return GitHubClient(http=self._http,
                            client_id=self.client_id,
                            client_secret=self.client_secret,
                            token=token)

    def _save(self, user_id: UserID, token: str) -> None:
        with self._db.begin() as conn:
            conn.execute(self._table.delete().where(self._table.c.user_id == user_id))
            conn.execute(self._table.insert().values(user_id=user_id, token=token))

    def get(self, user_id: UserID, create: bool = False) -> Optional[GitHubClient]:
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
        self._save(user_id, client.token)
        return web.Response(status=200, text=f"Logged in as {user}")
