# github - A maubot plugin to act as a GitHub client and webhook receiver.
# Copyright (C) 2020 Tulir Asokan
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
from typing import Dict, Set, Deque, Optional, Any, Callable, TYPE_CHECKING
from collections import deque, defaultdict
from uuid import UUID
import asyncio
import logging
import re

from jinja2 import TemplateNotFound
import attr

from mautrix.types import TextMessageEventContent, Format, MessageType, RoomID
from mautrix.util.formatter import parse_html

from ..template import TemplateManager, TemplateUtil
from ..api.types import (Event, EventType, MetaAction, RepositoryAction, expand_enum,
                         ACTION_CLASSES, OTHER_ENUMS)
from .manager import WebhookInfo
from .aggregation import PendingAggregation

if TYPE_CHECKING:
    from ..bot import GitHubBot

spaces = re.compile(" +")
space = " "


class WebhookHandler:
    log: logging.Logger
    bot: 'GitHubBot'
    msgtype: MessageType
    messages: TemplateManager
    templates: TemplateManager
    pending_aggregations: Dict[UUID, Deque[PendingAggregation]]

    def __init__(self, bot: 'GitHubBot') -> None:
        self.bot = bot
        self.log = self.bot.log.getChild("webhook")
        self.msgtype = MessageType(bot.config["message_options.msgtype"]) or MessageType.NOTICE
        PendingAggregation.timeout = int(bot.config["message_options.aggregation_timeout"])
        self.messages = TemplateManager(self.bot.config, "messages")
        self.templates = TemplateManager(self.bot.config, "templates")
        self.pending_aggregations = defaultdict(lambda: deque())

    def reload_config(self) -> None:
        self.messages.reload()
        self.templates.reload()
        self.msgtype = MessageType(self.bot.config["message_options.msgtype"]) or MessageType.NOTICE
        PendingAggregation.timeout = int(self.bot.config["message_options.aggregation_timeout"])

    async def __call__(self, evt_type: EventType, evt: Event, delivery_id: str, info: WebhookInfo
                       ) -> None:
        if evt_type == EventType.PING:
            self.log.debug(f"Received ping for {info}: {evt.zen}")
            self.bot.webhook_manager.set_github_id(info, evt.hook_id)
        elif evt_type == EventType.META and evt.action == MetaAction.DELETED:
            self.log.debug(f"Received delete hook for {info}")
            self.bot.webhook_manager.delete(info.id)
        elif evt_type == EventType.REPOSITORY:
            if evt.action in (RepositoryAction.TRANSFERRED, RepositoryAction.RENAMED):
                action = "transfer" if evt.action == RepositoryAction.TRANSFERRED else "rename"
                name = evt.repository.full_name
                self.log.debug(f"Received {action} hook {info} -> {name}")
                self.bot.webhook_manager.transfer(info, name)
            elif evt.action == RepositoryAction.DELETED:
                self.log.debug(f"Received repo delete hook for {info}")
                self.bot.webhook_manager.delete(info.id)
        elif evt_type == EventType.PUSH and (evt.size is None or evt.distinct_size is None):
            evt.size = len(evt.commits)
            evt.distinct_size = len([commit for commit in evt.commits if commit.distinct])

        if PendingAggregation.timeout < 0:
            # Aggregations are disabled
            await self.send_message(evt_type, evt, info.room_id, {delivery_id})
            return

        for pending in self.pending_aggregations[info.id]:
            if pending.aggregate(evt_type, evt, delivery_id):
                return
        asyncio.ensure_future(PendingAggregation(self, evt_type, evt, delivery_id, info)
                              .start())

    async def send_message(self, evt_type: EventType, evt: Event, room_id: RoomID,
                           delivery_ids: Set[str], aggregation: Optional[Dict[str, Any]] = None
                           ) -> None:
        try:
            tpl = self.messages[str(evt_type)]
        except TemplateNotFound:
            self.log.debug(f"Unhandled event of type {evt_type} -- {delivery_ids}")
            return

        aborted = False

        def abort() -> None:
            nonlocal aborted
            aborted = True

        args = {
            **attr.asdict(evt, recurse=False),
            **expand_enum(ACTION_CLASSES.get(evt_type)),
            **OTHER_ENUMS,
            "util": TemplateUtil,
            "abort": abort,
            "aggregation": aggregation,
        }
        args["templates"] = self.templates.proxy(args)
        html = tpl.render(**args)
        if not html or aborted:
            return
        content = TextMessageEventContent(msgtype=self.msgtype, format=Format.HTML,
                                          formatted_body=html, body=await parse_html(html.strip()))
        content["xyz.maubot.github.webhook"] = {
            "delivery_ids": list(delivery_ids),
            "event_type": str(evt_type),
            **(evt.meta() if hasattr(evt, "meta") else {}),
        }
        await self.bot.client.send_message(room_id, content)
