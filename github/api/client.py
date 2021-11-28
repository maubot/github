# github - A maubot plugin to act as a GitHub client and webhook receiver.
# Copyright (C) 2021 Tulir Asokan
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
from typing import Optional, Dict, Union, Any, Awaitable, List
import random
import string
import json

from aiohttp import ClientSession
from yarl import URL

from ..util import recursive_get
from .types import Webhook

OptStrList = Optional[List[str]]


class GitHubError(Exception):
    def __init__(self, message: str, documentation_url: str, status: int, **kwargs) -> None:
        super().__init__(message)
        self.documentation_url = documentation_url
        self.status = status
        self.kwargs = kwargs


class GraphQLError(Exception):
    def __init__(self, type: str, message: str, **kwargs) -> None:
        super().__init__(message)
        self.type = type
        self.kwargs = kwargs


class GitHubClient:
    base_url: URL = URL("https://api.github.com")
    api_url: URL = base_url / "graphql"
    user_base_url: URL = URL("https://github.com")
    login_url: URL = user_base_url / "login" / "oauth" / "authorize"
    login_finish_url: URL = user_base_url / "login" / "oauth" / "access_token"

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
        try:
            error = resp["errors"][0]
            raise GraphQLError(**error)
        except (KeyError, IndexError):
            try:
                data = resp["data"]
            except KeyError:
                raise GraphQLError(type="UNKNOWN_ERROR",
                                   message="Unknown error: GitHub didn't return any data")
        if path:
            return recursive_get(data, path)
        return data

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"token {self.token}",
            "Accept": "application/json",
        }

    @property
    def rest_v3_headers(self) -> Dict[str, str]:
        return {
            **self.headers,
            "Accept": "application/vnd.github.v3+json",
        }

    async def call_raw(self, query: str, variables: Optional[Dict] = None) -> dict:
        resp = await self.http.post(self.api_url,
                                    json={
                                        "query": query,
                                        "variables": variables or {}
                                    },
                                    headers=self.headers)
        return await resp.json()

    async def reset_token(self) -> Optional[str]:
        url = ((self.base_url / "applications" / self.client_id / "token")
               .with_user(self.client_id).with_password(self.client_secret))
        resp = await self.http.patch(url, json={"access_token": self.token})
        resp_data = await resp.json()
        if resp.status == 404:
            return None
        self.token = resp_data["token"]
        return self.token

    async def list_webhooks(self, owner: str, repo: str) -> List[Webhook]:
        resp = await self.http.get(self.base_url / "repos" / owner / repo / "hooks",
                                   headers=self.rest_v3_headers)
        return [Webhook.deserialize(info) for info in await resp.json()]

    async def get_webhook(self, owner: str, repo: str, hook_id: int) -> Webhook:
        resp = await self.http.get(self.base_url / "repos" / owner / repo / "hooks" / str(hook_id),
                                   headers=self.rest_v3_headers)
        data = await resp.json()
        if resp.status != 200:
            raise GitHubError(status=resp.status, **data)
        return Webhook.deserialize(data)

    async def create_webhook(self, owner: str, repo: str, url: URL, *, active: bool = True,
                             events: OptStrList = None, content_type: str = "form",
                             secret: Optional[str] = None, insecure_ssl: bool = False) -> Webhook:
        payload = {
            "name": "web",
            "config": {
                "url": str(url),
                "content_type": content_type,
                "secret": secret,
                "insecure_ssl": "1" if insecure_ssl else "0",
            },
            "events": events or ["push"],
            "active": active,
        }
        resp = await self.http.post(self.base_url / "repos" / owner / repo / "hooks",
                                    data=json.dumps(payload), headers=self.rest_v3_headers)
        data = await resp.json()
        if resp.status != 201:
            raise GitHubError(status=resp.status, **data)
        return Webhook.deserialize(data)

    async def edit_webhook(self, owner: str, repo: str, hook_id: int, *, url: Optional[URL] = None,
                           active: Optional[bool] = None, events: OptStrList = None,
                           add_events: OptStrList = None, remove_events: OptStrList = None,
                           content_type: Optional[str] = None, secret: Optional[str] = None,
                           insecure_ssl: Optional[bool] = None) -> Webhook:
        payload = {}
        if events:
            if add_events or remove_events:
                raise ValueError("Cannot override event list and add/remove at the same time")
            payload["events"] = events
        if add_events or remove_events:
            payload["add_events"] = add_events or []
            payload["remove_events"] = remove_events or []
        if active is not None:
            payload["active"] = active
        config = {}
        if url is not None:
            config["url"] = str(url)
        if content_type is not None:
            config["content_type"] = content_type
        if secret is not None:
            config["secret"] = secret
        if insecure_ssl is not None:
            config["insecure_ssl"] = "1" if insecure_ssl else "0"
        if config:
            payload["config"] = config
        resp = await self.http.patch(
            self.base_url / "repos" / owner / repo / "hooks" / str(hook_id),
            data=json.dumps(payload), headers=self.rest_v3_headers)
        data = await resp.json()
        if resp.status != 200:
            raise GitHubError(status=resp.status, **data)
        return Webhook.deserialize(data)

    async def delete_webhook(self, owner: str, repo: str, hook_id: int) -> None:
        resp = await self.http.delete(
            self.base_url / "repos" / owner / repo / "hooks" / str(hook_id),
            headers=self.rest_v3_headers,
        )
        if resp.status != 204:
            data = await resp.json()
            raise GitHubError(status=resp.status, **data)
