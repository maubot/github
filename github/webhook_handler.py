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
import re

from jinja2 import TemplateNotFound
import attr

from mautrix.types import TextMessageEventContent, Format, MessageType, RoomID
from mautrix.util.formatter import parse_html

from .webhook_manager import WebhookInfo
from .template import TemplateManager, TemplateUtil
from .api.types import Event, ACTION_TYPES, MetaAction

if TYPE_CHECKING:
    from .bot import GitHubBot


class WebhookMessageInfo(NamedTuple):
    room_id: RoomID
    delivery_id: str
    event: Event


spaces = re.compile(" +")
space = " "


class WebhookHandler:
    log: logging.Logger
    bot: 'GitHubBot'
    msgtype: MessageType
    messages: TemplateManager
    templates: TemplateManager

    def __init__(self, bot: 'GitHubBot') -> None:
        self.bot = bot
        self.log = self.bot.log.getChild("webhook")
        self.msgtype = MessageType(bot.config["msgtype"]) or MessageType.NOTICE
        self.messages = TemplateManager(self.bot.config, "messages")
        self.templates = TemplateManager(self.bot.config, "templates")

    def reload_templates(self) -> None:
        self.messages.reload()
        self.templates.reload()

    async def __call__(self, evt_type: str, evt: Event, delivery_id: str, webhook_info: WebhookInfo
                       ) -> None:
        evt_info = WebhookMessageInfo(room_id=webhook_info.room_id, delivery_id=delivery_id,
                                      event=evt)
        if evt_type == "ping":
            self.log.debug(f"Received ping for {webhook_info}: {evt.zen}")
            webhook_info = self.bot.webhooks.set_github_id(webhook_info, evt.hook_id)
        elif evt_type == "meta" and evt.action == MetaAction.DELETED:
            self.log.debug(f"Received delete hook for {webhook_info}")
            self.bot.webhooks.delete(webhook_info.id)
        try:
            await self._send_message(evt_type, evt_info)
        except TemplateNotFound:
            self.log.debug(f"Unhandled event of type {type(evt)} -- {delivery_id} {webhook_info}")

    async def _send_message(self, template: str, info: WebhookMessageInfo) -> None:
        tpl = self.messages[template]
        aborted = False

        def abort() -> None:
            nonlocal aborted
            aborted = True

        args = {
            **attr.asdict(info.event, recurse=False),
            **ACTION_TYPES,
            "util": TemplateUtil,
            "abort": abort,
        }
        args["templates"] = self.templates.proxy(args)
        content = TextMessageEventContent(msgtype=self.msgtype, format=Format.HTML,
                                          formatted_body=tpl.render(**args))
        if not content.formatted_body or aborted:
            return
        content.formatted_body = spaces.sub(space, content.formatted_body.strip())
        content.body = parse_html(content.formatted_body)
        content["xyz.maubot.github.delivery_id"] = info.delivery_id
        await self.bot.client.send_message(info.room_id, content)
