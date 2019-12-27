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

from sqlalchemy import MetaData

from mautrix.types import MessageType

from maubot import Plugin

from .webhook_manager import WebhookManager
from .webhook_handler import WebhookHandler
from .client_manager import ClientManager
from .api import GitHubWebhookReceiver
from .commands import Commands
from .config import Config


class GitHubBot(Plugin):
    webhook_receiver: GitHubWebhookReceiver
    webhooks: WebhookManager
    webhook_handler: WebhookHandler
    clients: ClientManager
    commands: Commands
    config: Config

    async def start(self) -> None:
        self.config.load_and_update()

        metadata = MetaData()

        self.clients = ClientManager(self.config["client_id"], self.config["client_secret"],
                                     self.http, self.database, metadata)
        self.webhooks = WebhookManager(self.config["webhook_key"],
                                       self.database, metadata)
        self.webhook_handler = WebhookHandler(bot=self)
        self.webhook_receiver = GitHubWebhookReceiver(handler=self.webhook_handler,
                                                      secrets=self.webhooks)
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
        self.webhook_handler.reload_templates()

    @classmethod
    def get_config_class(cls) -> Type[Config]:
        return Config
