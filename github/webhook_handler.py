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
from typing import NamedTuple, Dict, Tuple, Set, Callable, Deque, Type, Optional, TYPE_CHECKING
from collections import deque, defaultdict
from uuid import UUID
import asyncio
import logging
import re

from jinja2 import TemplateNotFound
import attr

from mautrix.types import TextMessageEventContent, Format, MessageType, RoomID
from mautrix.util.formatter import parse_html

from .webhook_manager import WebhookInfo
from .template import TemplateManager, TemplateUtil
from .api.types import (Event, EventType, Action, IssueAction, PullRequestAction, MetaAction,
                        EVENT_ARGS, OTHER_ENUMS)

if TYPE_CHECKING:
    from .bot import GitHubBot


class WebhookMessageInfo(NamedTuple):
    room_id: RoomID
    delivery_id: str
    event: Event


spaces = re.compile(" +")
space = " "


class PendingAggregation:
    def noop(self) -> None:
        pass

    def start_label_aggregation(self) -> None:
        self.event.x_added_labels = []
        self.event.x_removed_labels = []
        if self.event.action == self.action_type.LABELED:
            self.event.x_added_labels.append(self.event.label)
        else:
            self.event.x_removed_labels.append(self.event.label)
        self.event.action = self.action_type.X_LABEL_AGGREGATE

    def start_open_label_dropping(self) -> None:
        event_field = (self.event.issue if self.event_type == EventType.ISSUES
                       else self.event.pull_request)
        self._label_ids = {label.id for label in event_field.labels}

    aggregation_starters: Dict[Tuple[EventType, Action], Callable] = {
        (EventType.ISSUES, IssueAction.OPENED): start_open_label_dropping,
        (EventType.ISSUES, IssueAction.LABELED): start_label_aggregation,
        (EventType.ISSUES, IssueAction.UNLABELED): start_label_aggregation,
        (EventType.PULL_REQUEST, PullRequestAction.OPENED): start_open_label_dropping,
        (EventType.PULL_REQUEST, PullRequestAction.LABELED): start_label_aggregation,
        (EventType.PULL_REQUEST, PullRequestAction.UNLABELED): start_label_aggregation,
    }

    timeout = 1

    handler: 'WebhookHandler'
    webhook_info: WebhookInfo
    delivery_ids: Set[str]
    event_type: EventType
    action_type: Type[Action]
    event: Event
    postpone: asyncio.Event

    _label_ids: Optional[Set[int]]

    def __init__(self, handler: 'WebhookHandler', evt_type: EventType, evt: Event, delivery_id: str,
                 webhook_info: WebhookInfo) -> None:
        self.handler = handler
        self.webhook_info = webhook_info
        self.event_type = evt_type
        self.event = evt
        self.delivery_ids = {delivery_id}
        self.postpone = asyncio.Event()
        if self.event_type == EventType.ISSUES:
            self.action_type = IssueAction
        elif self.event_type == EventType.PULL_REQUEST:
            self.action_type = IssueAction
        else:
            self.event.action = None

    async def start(self) -> None:
        try:
            await self._start()
        except Exception:
            self.handler.log.exception("Fatal error in aggregation handler")

    async def _start(self) -> None:
        try:
            starter = self.aggregation_starters[self.event_type, self.event.action]
        except KeyError:
            # Nothing to aggregate, send right away
            await self._send()
            return

        starter(self)

        self.handler.pending_aggregations[self.webhook_info.id].append(self)
        await self._sleep()
        self.handler.pending_aggregations[self.webhook_info.id].remove(self)
        await self._send()

    async def _sleep(self) -> None:
        try:
            while True:
                # "sleep" until the postpone event is triggered or the timeout is reached
                await asyncio.wait_for(self.postpone.wait(), self.timeout)
                # If the event is triggered, clear it and sleep again
                self.postpone.clear()
        except asyncio.TimeoutError:
            # If the timeout is reached, stop
            pass

    async def _send(self) -> None:
        await self.handler.send_message(self.event_type, self.event, self.webhook_info.room_id,
                                        self.delivery_ids)

    def aggregate(self, evt_type: EventType, evt: Event, delivery_id: str) -> bool:
        if evt_type != self.event_type:
            return False
        elif self.event_type in (EventType.ISSUES, EventType.PULL_REQUEST):
            if self.event.action == self.action_type.OPENED and evt.label.id in self._label_ids:
                # Label was already in original event, drop the message.
                pass
            elif self.event.action == self.action_type.X_LABEL_AGGREGATE:
                if evt.action == self.action_type.LABELED:
                    self.event.x_added_labels.append(evt.label)
                elif evt.action == self.action_type.UNLABELED:
                    self.event.x_removed_labels.append(evt.label)
                else:
                    return False
            else:
                return False
        else:
            return False

        self.delivery_ids.add(delivery_id)
        self.postpone.set()
        return True


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

    async def __call__(self, evt_type: EventType, evt: Event, delivery_id: str,
                       webhook_info: WebhookInfo) -> None:
        if evt_type == "ping":
            self.log.debug(f"Received ping for {webhook_info}: {evt.zen}")
            self.bot.webhooks.set_github_id(webhook_info, evt.hook_id)
        elif evt_type == "meta" and evt.action == MetaAction.DELETED:
            self.log.debug(f"Received delete hook for {webhook_info}")
            self.bot.webhooks.delete(webhook_info.id)

        for pending in self.pending_aggregations[webhook_info.id]:
            if pending.aggregate(evt_type, evt, delivery_id):
                # Send the message normally to allow custom templates to opt out of aggregation
                await self.send_message(evt_type, evt, webhook_info.room_id, {delivery_id})
                return
        asyncio.ensure_future(PendingAggregation(self, evt_type, evt, delivery_id, webhook_info)
                              .start())

    async def send_message(self, evt_type: EventType, evt: Event, room_id: RoomID,
                           delivery_ids: Set[str]) -> None:
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
            **EVENT_ARGS[evt_type],
            **OTHER_ENUMS,
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
        content["xyz.maubot.github.delivery_ids"] = list(delivery_ids)
        await self.bot.client.send_message(room_id, content)
