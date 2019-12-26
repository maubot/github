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
from typing import Type
import string
import random

from sqlalchemy import MetaData

from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper
from mautrix.types import MessageType

from maubot import Plugin

from .webhook_secret_manager import WebhookSecretManager
from .webhook_handler import WebhookHandler
from .client_manager import ClientManager
from .api import GitHubWebhookReceiver
from .commands import Commands

secret_charset = string.ascii_letters + string.digits


class Config(BaseProxyConfig):
    def do_update(self, helper: ConfigUpdateHelper) -> None:
        helper.copy("client_id")
        helper.copy("client_secret")
        helper.base["webhook_key"] = ("".join(random.choices(secret_charset, k=64))
                                      if helper.source.get("webhook_key", "generate") == "generate"
                                      else helper.source["webhook_key"])


class GitHubBot(Plugin):
    webhook_receiver: GitHubWebhookReceiver
    webhook_secrets: WebhookSecretManager
    webhook_handler: WebhookHandler
    clients: ClientManager
    commands: Commands

    async def start(self) -> None:
        self.config.load_and_update()

        metadata = MetaData()

        self.clients = ClientManager(self.config["client_id"], self.config["client_secret"],
                                     self.http, self.database, metadata)
        self.webhook_secrets = WebhookSecretManager(self.config["webhook_key"],
                                                    self.database, metadata)
        self.webhook_handler = WebhookHandler(bot=self)
        self.webhook_receiver = GitHubWebhookReceiver(handler=self.webhook_handler,
                                                      secrets=self.webhook_secrets)
        self.commands = Commands(bot=self)

        metadata.create_all(self.database)
        self.clients.load_db()

        self.register_handler_class(self.webhook_receiver)
        self.register_handler_class(self.clients)
        self.register_handler_class(self.commands)

    def on_external_config_update(self) -> None:
        self.config.load_and_update()
        self.clients.client_id = self.config["client_id"]
        self.clients.client_secret = self.config["client_secret"]
        self.webhook_handler.msgtype = MessageType(self.config["msgtype"])

    @classmethod
    def get_config_class(cls) -> Type[BaseProxyConfig]:
        return Config
