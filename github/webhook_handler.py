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
from typing import NamedTuple, TYPE_CHECKING
import logging

from mautrix.types import TextMessageEventContent, Format, MessageType, RoomID
from maubot.matrix import parse_formatted

from .webhook_secret_manager import WebhookInfo
from .util.types import Event, PingEvent, StarEvent, StarAction, IssuesEvent

if TYPE_CHECKING:
    from .bot import GitHubBot


class WebhookMessageInfo(NamedTuple):
    delivery_id: str
    room_id: str


class WebhookHandler:
    log: logging.Logger
    bot: 'GitHubBot'
    msgtype: MessageType

    def __init__(self, bot: 'GitHubBot') -> None:
        self.bot = bot
        self.log = self.bot.log.getChild("webhook")
        self.msgtype = MessageType(bot.config["msgtype"]) or MessageType.NOTICE

    async def __call__(self, evt: Event, delivery_id: str, webhook_info: WebhookInfo) -> None:
        if isinstance(evt, PingEvent):
            await self.handle_ping(evt, webhook_info)
        elif isinstance(evt, StarEvent):
            await self.handle_star(evt, delivery_id, webhook_info)
        elif isinstance(evt, IssuesEvent):
            print("Issue event", evt)
        else:
            self.log.debug(f"Unhandled event: {evt} -- {delivery_id} {webhook_info}")

    async def handle_ping(self, evt: PingEvent, webhook_info: WebhookInfo) -> None:
        webhook_info = self.bot.webhook_secrets.set_github_id(webhook_info, evt.hook_id)
        self.log.debug(f"Received ping for {webhook_info}: {evt.zen}")

    async def handle_star(self, evt: StarEvent, delivery_id: str, webhook_info: WebhookInfo) -> None:
        action = "starred" if evt.action == StarAction.CREATED else "unstarred"
        msg = (f"[[{evt.repository.full_name}]({evt.repository.html_url})] Repo {action} by"
               f" [{evt.sender.name or evt.sender.login}]({evt.sender.html_url})")
        await self.send_message(webhook_info.room_id, msg, delivery_id=delivery_id)

    async def handle_issue(self, evt: IssuesEvent, delivery_id: str, webhook_info: WebhookInfo) -> None:

    async def send_message(self, room_id: RoomID, msg: str, delivery_id: str) -> None:
        content = TextMessageEventContent(msgtype=self.msgtype, format=Format.HTML)
        content.body, content.formatted_body = parse_formatted(msg)
        content["xyz.maubot.github.delivery_id"] = delivery_id
        await self.bot.client.send_message(room_id, content)
