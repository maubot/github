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
from typing import Awaitable

from aiohttp import ClientSession


class GitHubClient:
    api_url: str = "https://api.github.com/graphql"
    client: ClientSession
    token: str

    def __init__(self, client: ClientSession, secret: str) -> None:
        self.client = client
        self.token = secret
        pass

    def get(self, query: str) -> Awaitable[dict]:
        return self._query("GET", query)

    def post(self, query: str) -> Awaitable[dict]:
        return self._query("POST", query)

    async def _query(self, method: str, query: str) -> dict:
        resp = await self.client.request(method, self.api_url, json={"query": query})
        return await resp.json()
