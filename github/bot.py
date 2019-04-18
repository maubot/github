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
from typing import Type, Dict
import random
import string

from sqlalchemy import Table, Column, String
from mautrix.types import UserID
from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper

from maubot import Plugin, MessageEvent
from maubot.handlers import command

from .api import GitHubClient, GitHubWebhookReceiver

secret_charset = string.ascii_letters + string.digits


class Config(BaseProxyConfig):
    def do_update(self, helper: ConfigUpdateHelper) -> None:
        if helper.source.get("secret", "generate") == "generate":
            helper.base["secret"] = "".join(random.choices(secret_charset, k=64))
        else:
            helper.copy("secret")


class GitHubBot(Plugin):
    webhook_receiver: GitHubWebhookReceiver
    clients: Dict[UserID, GitHubClient]


    async def start(self) -> None:
        await super().start()
        self.config.load_and_update()
        self.clients = {}
        self.webhook_receiver = GitHubWebhookReceiver(self.webapp, self.config["secret"])
        self.webhook_receiver.add_handler("*", self.webhook)

    async def webhook(self, data: Dict) -> None:
        self.log.debug("Webhook data:", data)

    @command.new("github")
    async def github(self, evt: MessageEvent) -> None:
        pass

    @github.subcommand("login")
    async def login(self, evt: MessageEvent) -> None:

    @github.subcommand("create")
    @command.argument("repo", required=False, matches=r"([A-Za-z0-9-_])/([A-Za-z0-9-_])")
    @command.argument("data", required=True, pass_raw=True)
    async def create_issue(self, evt: MessageEvent, repo: str, data: str) -> None:
        title, body = data.split("\n", 1) if "\n" in data else data, ""


    @classmethod
    def get_config_class(cls) -> Type[BaseProxyConfig]:
        return Config
