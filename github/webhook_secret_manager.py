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
from typing import Dict, Optional
from dataclasses import dataclass
from uuid import UUID, uuid4
import hashlib
import hmac

from sqlalchemy import MetaData, Table, Column, String, Integer
from sqlalchemy.engine.base import Engine

from mautrix.types import UserID, RoomID

from .util import UUIDType


@dataclass(frozen=True)
class WebhookInfo:
    id: UUID
    repo: str
    user_id: UserID
    room_id: RoomID
    github_id: Optional[int] = None
    _secret_key: Optional[bytes] = None

    def __init__(self, id: UUID, repo: str, user_id: UserID, room_id: RoomID,
                 github_id: Optional[int] = None, *, _manager: 'WebhookSecretManager') -> None:
        super().__init__(id, repo, user_id, room_id, github_id,
                         _secret_key=_manager._secret.encode("utf-8"))

    def __hash__(self) -> int:
        return hash(self.id.int)

    @property
    def secret(self) -> str:
        secret = hmac.new(key=self._secret_key, digestmod=hashlib.sha256)
        secret.update(self.id.bytes)
        secret.update(self.repo.encode("utf-8"))
        secret.update(self.user_id.encode("utf-8"))
        secret.update(self.room_id.encode("utf-8"))
        return secret.hexdigest()


class WebhookSecretManager:
    _table: Table
    _db: Engine
    _secret: str
    _webhooks: Dict[UUID, WebhookInfo]

    def __init__(self, secret: str, db: Engine, metadata: MetaData):
        self._secret = secret
        self._db = db
        self._table = Table("webhook", metadata,
                            Column("id", UUIDType, primary_key=True),
                            Column("repo", String(255), nullable=False),
                            Column("user_id", String(255), nullable=False),
                            Column("room_id", String(255), nullable=False),
                            Column("github_id", Integer, nullable=True))
        self._clients = {}

    def create(self, repo: str, user_id: UserID, room_id: RoomID) -> WebhookInfo:
        info = WebhookInfo(id=uuid4(),
                           repo=repo,
                           user_id=user_id,
                           room_id=room_id,
                           _manager=self)
        self._db.execute(self._table.insert().values(
            id=info.id, github_id=info.github_id, repo=repo,
            user_id=info.user_id, room_id=info.room_id))
        self._webhooks[info.id] = info
        return info

    def set_github_id(self, info: WebhookInfo, github_id: int) -> WebhookInfo:
        self._db.execute(self._table.update()
                         .where(self._table.c.id == info.id)
                         .values(github_id=github_id))
        return self._select(info.id)

    def delete(self, id: UUID) -> None:
        self._db.execute(self._table.delete().where(self._table.c.id == id))
        try:
            del self._webhooks[id]
        except KeyError:
            pass

    def _select(self, id: UUID) -> Optional[WebhookInfo]:
        rows = self._db.execute(self._table.select().where(self._table.c.id == id))
        try:
            info = WebhookInfo(*next(rows), _manager=self)
            self._webhooks[info.id] = info
            return info
        except StopIteration:
            return None

    def get(self, id: UUID) -> Optional[WebhookInfo]:
        try:
            return self._webhooks[id]
        except KeyError:
            return self._select(id)
