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
from typing import Optional, Dict, Union, Tuple, Any, Awaitable
import random
import string

from aiohttp import ClientSession
from yarl import URL


class GitHubClient:
    api_url: URL = URL("https://api.github.com/graphql")
    login_url: URL = URL("https://github.com/login/oauth/authorize")
    login_finish_url: URL = URL("https://github.com/login/oauth/access_token")

    client_id: str
    client_secret: str

    http: ClientSession
    token: str
    _login_state: str

    def __init__(self, http: ClientSession, client_id: str, client_secret: str, token: str) -> None:
        self.http = http
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = token
        self._login_state = ""

    def get_login_url(self, redirect_uri: Union[str, URL], scope: str = "user repo") -> URL:
        self._login_state = "".join(random.choices(string.ascii_lowercase + string.digits, k=64))
        return self.login_url.with_query({
            "client_id": self.client_id,
            "redirect_uri": str(redirect_uri),
            "scope": scope,
            "state": self._login_state,
        })

    async def finish_login(self, code: str, state: str) -> None:
        if state != self._login_state:
            raise ValueError("Invalid state")
        resp = await self.http.post(self.login_finish_url, json={
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "state": self._login_state,
        }, headers={
            "Accept": "application/json",
        })
        data = await resp.json()
        self.token = data["access_token"]

    @staticmethod
    def _parse_key(key: str) -> Tuple[str, Optional[str]]:
        if '.' not in key:
            return key, None
        key, next_key = key.split('.', 1)
        if len(key) > 0 and key[0] == "[":
            end_index = next_key.index("]")
            key = key[1:] + "." + next_key[:end_index]
            next_key = next_key[end_index + 2:] if len(next_key) > end_index + 1 else None
        return key, next_key

    def _recursive_get(self, data: Dict, key: str) -> Any:
        key, next_key = self._parse_key(key)
        if next_key is not None:
            return self._recursive_get(data[key], next_key)
        return data[key]

    def query(self, query: str, args: str = "", variables: Optional[Dict] = None,
              path: Optional[str] = None) -> Awaitable[Any]:
        return self.call("query", query, args, variables, path)

    def mutate(self, query: str, args: str = "", variables: Optional[Dict] = None,
               path: Optional[str] = None) -> Awaitable[Any]:
        return self.call("mutation", query, args, variables, path)

    async def call(self, query_type: str, query: str, args: str, variables: Optional[Dict] = None,
                   path: Optional[str] = None) -> Any:
        full_query = query_type
        if args:
            full_query += f" ({args})"
        full_query += " {%s}" % query
        resp = await self.call_raw(full_query, variables)
        print(resp)
        if path:
            return self._recursive_get(resp["data"], path)
        return resp["data"]

    async def call_raw(self, query: str, variables: Optional[Dict] = None) -> dict:
        resp = await self.http.post(self.api_url,
                                    json={
                                        "query": query,
                                        "variables": variables or {}
                                    },
                                    headers={
                                        "Authorization": f"token {self.token}",
                                        "Accept": "application/json",
                                    })
        return await resp.json()
