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
from typing import Type, Dict, Tuple, Awaitable, Callable
import string
import json

from aiohttp import web
from sqlalchemy import MetaData
from yarl import URL

from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper

from maubot import Plugin, MessageEvent
from maubot.handlers import command

from .client_manager import ClientManager
from .api import GitHubWebhookReceiver, GitHubClient

secret_charset = string.ascii_letters + string.digits


class Config(BaseProxyConfig):
    def do_update(self, helper: ConfigUpdateHelper) -> None:
        helper.copy("client_id")
        helper.copy("client_secret")


class GitHubBot(Plugin):
    webhook_receiver: GitHubWebhookReceiver
    clients: ClientManager

    async def start(self) -> None:
        await super().start()
        self.config.load_and_update()

        metadata = MetaData()
        self.clients = ClientManager(self.config["client_id"], self.config["client_secret"],
                                     self.http, self.database, metadata)
        metadata.create_all(self.database)

        self.clients.load_db()

        self.webhook_receiver = GitHubWebhookReceiver(handler=self.webhook,
                                                      secret=self.get_webhook_secret)

        self.webapp.add_post("/webhook/{id}", self.webhook_receiver.handle)
        self.webapp.add_get("/auth", self.clients.login_callback)

    def on_external_config_update(self) -> None:
        self.config.load_and_update()
        self.clients.client_id = self.config["client_id"]
        self.clients.client_secret = self.config["client_secret"]

    def get_webhook_secret(self, request: web.Request) -> str:
        request_id = request.match_info["id"]
        return "TODO"

    async def webhook(self, data: Dict) -> None:
        request_id = data["__request__"].match_info["id"]
        self.log.debug("Webhook data:", data)

    @staticmethod
    def authenticated(fn):
        async def decorator(self, evt: MessageEvent, **kwargs):
            client = self.clients.get(evt.sender)
            if not client or not client.token:
                return await evt.reply("You're not logged in. Log in with `!github login` first.")
            return await fn(self, evt, **kwargs, client=client)

        return decorator

    @command.new("github", require_subcommand=True)
    async def github(self, evt: MessageEvent) -> None:
        pass

    @github.subcommand("login", help="Log into GitHub.")
    async def login(self, evt: MessageEvent) -> None:
        redirect_url = URL(f"{self.webapp_url}/auth").with_query({"user_id": evt.sender})
        login_url = str(self.clients.get(evt.sender, create=True).get_login_url(
            redirect_uri=redirect_url,
            scope="user public_repo repo repo_deployment repo:status repo:repo_hook repo:org"))
        await evt.reply(f"[Click here to log in]({login_url})")

    @github.subcommand("ping", help="Check your login status.")
    async def ping(self, evt: MessageEvent) -> None:
        client = self.clients.get(evt.sender)
        if not client or not client.token:
            await evt.reply("You're not logged in. Log in with `!github login` first.")
            return
        username = await client.query("viewer { login }", path="viewer.login")
        await evt.reply(f"You're logged in as @{username}")

    @github.subcommand("raw", help="Make a raw GraphQL query.")
    @command.argument("query", required=True, pass_raw=True)
    @authenticated
    async def raw_query(self, evt: MessageEvent, query: str, client: GitHubClient) -> None:
        client = self.clients.get(evt.sender)
        if not client or not client.token:
            await evt.reply("You're not logged in. Log in with `!github login` first.")
            return
        variables = {}
        if "---" in query:
            query, variables = query.split("---")
            try:
                variables = json.loads(variables)
            except json.JSONDecodeError as err:
                await evt.reply(f"Failed to parse variables: {err}")
                return
        resp = await client.call_raw(query, variables)
        await evt.reply("<pre><code class='language-json'>"
                        f"{json.dumps(resp, indent=2)}"
                        "</code></pre>", allow_html=True)

    @github.subcommand("create", help="Create an issue.")
    @command.argument("repo", required=False, matches=r"([A-Za-z0-9-_]+)/([A-Za-z0-9-_]+)")
    @command.argument("data", required=True, pass_raw=True)
    @authenticated
    async def create_issue(self, evt: MessageEvent, repo: Tuple[str, str], data: str,
                           client: GitHubClient) -> None:
        title, body = data.split("\n", 1) if "\n" in data else (data, "")
        repo_id = await client.query(query="repository (name: $name, owner: $owner) { id }",
                                     args="$owner: String!, $name: String!",
                                     variables={"owner": repo[0], "name": repo[1]},
                                     path="repository.id")
        issue = await client.mutate(query="createIssue(input: $input) { issue { number url } }",
                                    args="$input: CreateIssueInput!",
                                    variables={"input": {
                                        "repositoryId": repo_id,
                                        "title": title,
                                        "body": body,
                                    }},
                                    path="createIssue.issue")
        await evt.reply(f"Created [issue #{issue['number']}]({issue['url']})")

    @classmethod
    def get_config_class(cls) -> Type[BaseProxyConfig]:
        return Config
