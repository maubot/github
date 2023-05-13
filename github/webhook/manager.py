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
from typing import Dict, Union, Optional, Any, Generator
from uuid import UUID, uuid4
import hashlib
import hmac

from sqlalchemy import MetaData, Table, Column, String, Integer, UniqueConstraint, and_
from sqlalchemy.engine.base import Engine

from mautrix.types import UserID, RoomID, EventType, StateEvent, RoomTombstoneStateEventContent
from maubot.handlers import event

from ..util import UUIDType


class WebhookInfo:
    __slots__ = ("id", "repo", "user_id", "room_id", "github_id", "_secret_key", "__initialized")
    id: UUID
    repo: str
    user_id: UserID
    room_id: RoomID
    github_id: Optional[int]

    def __init__(self, id: UUID, repo: str, user_id: UserID, room_id: RoomID,
                 github_id: Optional[int] = None, _secret_key: bytes = None) -> None:
        self.id = id
        self.repo = repo
        self.user_id = user_id
        self.room_id = room_id
        self.github_id = github_id
        self._secret_key = _secret_key
        self.__initialized = True

    def __repr__(self) -> str:
        return (f"WebhookInfo(id={self.id!r}, repo={self.repo!r}, user_id={self.user_id!r},"
                f" room_id={self.room_id!r}, github_id={self.github_id!r})")

    def __str__(self) -> str:
        return (f"webhook {self.id!s} (GH{self.github_id}) from {self.repo} to {self.room_id}"
                f" added by {self.user_id}")

    def __delattr__(self, item) -> None:
        raise ValueError("Can't change attributes after initialization")

    def __setattr__(self, key: str, value: Any) -> None:
        if hasattr(self, "__initialized"):
            raise ValueError("Can't change attributes after initialization")
        super().__setattr__(key, value)

    @property
    def old_secret(self) -> str:
        secret = hmac.new(key=self._secret_key, digestmod=hashlib.sha256)
        secret.update(self.id.bytes)
        secret.update(self.user_id.encode("utf-8"))
        secret.update(self.room_id.encode("utf-8"))
        return secret.hexdigest()

    @property
    def secret(self) -> str:
        secret = hmac.new(key=self._secret_key, digestmod=hashlib.sha256)
        secret.update(self.id.bytes)
        secret.update(self.user_id.encode("utf-8"))
        return secret.hexdigest()


class WebhookManager:
    _table: Table
    _db: Engine
    _secret: bytes
    _webhooks: Dict[UUID, WebhookInfo]

    def __init__(self, secret: str, db: Engine, metadata: MetaData):
        self._secret = secret.encode("utf-8")
        self._db = db
        self._table = Table("webhook", metadata,
                            Column("id", UUIDType, primary_key=True),
                            Column("repo", String(255), nullable=False),
                            Column("user_id", String(255), nullable=False),
                            Column("room_id", String(255), nullable=False),
                            Column("github_id", Integer, nullable=True),
                            UniqueConstraint("repo", "room_id"))
        self._webhooks = {}

    def create(self, repo: str, user_id: UserID, room_id: RoomID) -> WebhookInfo:
        info = WebhookInfo(id=uuid4(),
                           repo=repo,
                           user_id=user_id,
                           room_id=room_id,
                           _secret_key=self._secret)
        self._db.execute(self._table.insert().values(
            id=info.id, github_id=info.github_id, repo=repo,
            user_id=info.user_id, room_id=info.room_id))
        self._webhooks[info.id] = info
        return info

    @event.on(EventType.ROOM_TOMBSTONE)
    async def handle_room_upgrade(self, evt: StateEvent) -> None:
        assert isinstance(evt.content, RoomTombstoneStateEventContent)
        self._db.execute(
            self._table.update()
                .where(self._table.c.room_id == evt.room_id)
                .values(room_id=evt.content.replacement_room)
        )
        for webhook in self._webhooks.values():
            if webhook.room_id == evt.room_id:
                webhook.room_id = evt.content.replacement_room

    def set_github_id(self, info: WebhookInfo, github_id: int) -> WebhookInfo:
        self._db.execute(self._table.update()
                         .where(self._table.c.id == info.id)
                         .values(github_id=github_id))
        return self._select(info.id)

    def transfer(self, info: WebhookInfo, new_name: str) -> WebhookInfo:
        self._db.execute(self._table.update()
                         .where(self._table.c.id == info.id)
                         .values(repo=new_name))
        return self._select(info.id)

    def delete(self, id: UUID) -> None:
        self._db.execute(self._table.delete().where(self._table.c.id == id))
        try:
            del self._webhooks[id]
        except KeyError:
            pass

    def _execute_select(self, *where_clause) -> Optional[WebhookInfo]:
        rows = self._db.execute(self._table.select().where(where_clause[0] if len(where_clause) == 1
                                                           else and_(*where_clause)))
        try:
            info = WebhookInfo(*next(rows), _secret_key=self._secret)
            self._webhooks[info.id] = info
            return info
        except StopIteration:
            return None

    def _select(self, id: UUID) -> Optional[WebhookInfo]:
        return self._execute_select(self._table.c.id == id)

    def get(self, id: UUID) -> Optional[WebhookInfo]:
        try:
            return self._webhooks[id]
        except KeyError:
            return self._select(id)

    def get_all_for_room(self, room_id: RoomID) -> Generator[WebhookInfo, None, None]:
        rows = self._db.execute(self._table.select().where(self._table.c.room_id == room_id))
        return (WebhookInfo(*row, _secret_key=self._secret) for row in rows)

    def find(self, repo: str, room_id: RoomID) -> Optional[WebhookInfo]:
        return self._execute_select(self._table.c.repo == repo, self._table.c.room_id == room_id)

    def __delitem__(self, key: UUID) -> None:
        self.delete(key)

    def __getitem__(self, item: Union[str, UUID]) -> WebhookInfo:
        if not isinstance(item, UUID):
            item = UUID(item)
        value = self.get(item)
        if not value:
            raise KeyError(item)
        return value
