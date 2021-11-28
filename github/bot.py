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
from typing import Type
import asyncio

from sqlalchemy import MetaData

from maubot import Plugin

from .webhook import WebhookManager, WebhookHandler
from .client_manager import ClientManager
from .api import GitHubWebhookReceiver
from .commands import Commands
from .config import Config


class GitHubBot(Plugin):
    webhook_receiver: GitHubWebhookReceiver
    webhook_manager: WebhookManager
    webhook_handler: WebhookHandler
    clients: ClientManager
    commands: Commands
    config: Config

    async def start(self) -> None:
        self.config.load_and_update()

        metadata = MetaData()

        self.clients = ClientManager(self.config["client_id"], self.config["client_secret"],
                                     self.http, self.database, metadata)
        self.webhook_manager = WebhookManager(self.config["webhook_key"],
                                              self.database, metadata)
        self.webhook_handler = WebhookHandler(bot=self)
        self.webhook_receiver = GitHubWebhookReceiver(handler=self.webhook_handler,
                                                      secrets=self.webhook_manager,
                                                      global_secret=self.config["global_webhook_secret"])
        self.commands = Commands(bot=self)

        metadata.create_all(self.database)
        self.clients.load_db()

        self.register_handler_class(self.webhook_receiver)
        self.register_handler_class(self.clients)
        self.register_handler_class(self.commands)

    async def reset_tokens(self) -> None:
        try:
            await self._reset_tokens()
        except Exception:
            self.log.exception("Error resetting user tokens")

    async def _reset_tokens(self) -> None:
        self.config["reset_tokens"] = False
        self.config.save()
        self.log.info("Resetting all user tokens")
        for user_id, client in self.clients.get_all().items():
            self.log.debug(f"Resetting {user_id}'s token...")
            try:
                new_token = await client.reset_token()
            except Exception:
                self.log.warning(f"Failed to reset {user_id}'s token", exc_info=True)
            else:
                if new_token is None:
                    self.log.debug(f"{user_id}'s token was not valid, removing from database")
                    self.clients.remove(user_id)
                else:
                    self.log.debug(f"Successfully reset {user_id}'s token")
                    self.clients.put(user_id, new_token)
        self.log.debug("Finished resetting all user tokens")

    def on_external_config_update(self) -> None:
        self.config.load_and_update()
        self.clients.client_id = self.config["client_id"]
        self.clients.client_secret = self.config["client_secret"]
        self.webhook_handler.reload_config()
        self.commands.reload_config()

        if self.config["reset_tokens"]:
            asyncio.create_task(self.reset_tokens())

    @classmethod
    def get_config_class(cls) -> Type[Config]:
        return Config
