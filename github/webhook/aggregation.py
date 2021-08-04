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
from typing import Dict, Tuple, Set, Callable, Type, Optional, Any, TYPE_CHECKING
import asyncio

from .manager import WebhookInfo
from github.api.types import (Event, EventType, Action, IssueAction, PullRequestAction,
                              CommentAction, ACTION_CLASSES)

if TYPE_CHECKING:
    from .handler import WebhookHandler


class PendingAggregation:
    def noop(self) -> None:
        pass

    def start_label_aggregation(self) -> None:
        self.aggregation = {
            "added_labels": [],
            "removed_labels": [],
        }
        if self.event.action == self.action_type.LABELED:
            self.aggregation["added_labels"].append(self.event.label)
        else:
            self.aggregation["removed_labels"].append(self.event.label)
        self.event.action = self.action_type.X_LABEL_AGGREGATE

    def start_open_label_dropping(self) -> None:
        event_field = (self.event.issue if self.event_type == EventType.ISSUES
                       else self.event.pull_request)
        self._label_ids = {label.id for label in event_field.labels}

    def start_milestone_aggregation(self) -> None:
        if self.event.action == self.action_type.MILESTONED:
            self.aggregation["to"] = self.event.milestone
        elif self.event.action == self.action_type.DEMILESTONED:
            self.aggregation["from"] = self.event.milestone

    aggregation_starters: Dict[Tuple[EventType, Action], Callable] = {
        (EventType.ISSUES, IssueAction.OPENED): start_open_label_dropping,
        (EventType.ISSUES, IssueAction.LABELED): start_label_aggregation,
        (EventType.ISSUES, IssueAction.UNLABELED): start_label_aggregation,
        (EventType.ISSUES, IssueAction.MILESTONED): start_milestone_aggregation,
        (EventType.ISSUES, IssueAction.DEMILESTONED): start_milestone_aggregation,
        (EventType.PULL_REQUEST, PullRequestAction.OPENED): start_open_label_dropping,
        (EventType.PULL_REQUEST, PullRequestAction.LABELED): start_label_aggregation,
        (EventType.PULL_REQUEST, PullRequestAction.UNLABELED): start_label_aggregation,
        (EventType.ISSUE_COMMENT, CommentAction.CREATED): noop,
        (EventType.ISSUES, IssueAction.REOPENED): noop,
        (EventType.ISSUES, IssueAction.CLOSED): noop,
    }

    timeout = 1

    handler: 'WebhookHandler'
    webhook_info: WebhookInfo
    delivery_ids: Set[str]
    event_type: EventType
    action_type: Type[Action]
    event: Event
    aggregation: Dict[str, Any]
    postpone: asyncio.Event

    _label_ids: Optional[Set[int]]

    def __init__(self, handler: 'WebhookHandler', evt_type: EventType, evt: Event, delivery_id: str,
                 webhook_info: WebhookInfo) -> None:
        self.handler = handler
        self.webhook_info = webhook_info
        self.event_type = evt_type
        self.event = evt
        self.aggregation = {}
        self.delivery_ids = {delivery_id}
        self.postpone = asyncio.Event()
        self.action_type = ACTION_CLASSES.get(evt_type)
        if not hasattr(self.event, "action"):
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
                                        self.delivery_ids, aggregation=self.aggregation)

    def aggregate(self, evt_type: EventType, evt: Event, delivery_id: str) -> bool:
        postpone = True
        if (evt_type == EventType.ISSUES and self.event_type == EventType.ISSUE_COMMENT
                and evt.action in (IssueAction.CLOSED, IssueAction.REOPENED)
                and evt.issue_id == self.event.issue_id
                and self.event.sender.id == evt.sender.id):
            if evt.action == IssueAction.CLOSED:
                self.aggregation["closed"] = True
            elif evt.action == IssueAction.REOPENED:
                self.aggregation["reopened"] = True
        elif (evt_type == EventType.ISSUE_COMMENT and self.event_type == EventType.ISSUES
              and evt.action == CommentAction.CREATED and self.event.sender.id == evt.sender.id
                and evt.issue_id == self.event.issue_id
              and self.event.action in (IssueAction.CLOSED, IssueAction.REOPENED)):
            self.event_type = evt_type
            self.event = evt
            if evt.action == IssueAction.CLOSED:
                self.aggregation["closed"] = True
            elif evt.action == IssueAction.REOPENED:
                self.aggregation["reopened"] = True
        elif evt_type != self.event_type:
            return False
        elif self.event_type in (EventType.ISSUES, EventType.PULL_REQUEST):
            if (self.event.action == self.action_type.OPENED
                    and evt.issue_id == self.event.issue_id
                    and evt.label and evt.label.id in self._label_ids):
                # Label was already in original event, drop the message.
                pass
            elif self.event.action == self.action_type.X_LABEL_AGGREGATE:
                if evt.action == self.action_type.LABELED:
                    self.aggregation["added_labels"].append(evt.label)
                elif evt.action == self.action_type.UNLABELED:
                    self.aggregation["removed_labels"].append(evt.label)
                else:
                    return False
            elif self.event.action in (self.action_type.MILESTONED, self.action_type.DEMILESTONED):
                if evt.action == self.action_type.MILESTONED:
                    self.aggregation["to"] = evt.milestone
                elif evt.action == self.action_type.DEMILESTONED:
                    self.aggregation["from"] = evt.milestone
                else:
                    return False
                self.event.action = self.action_type.X_MILESTONE_CHANGED
                postpone = False
            else:
                return False
        else:
            return False

        self.delivery_ids.add(delivery_id)
        if postpone:
            self.postpone.set()
        return True
