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
from uuid import UUID, uuid4
import random

from mautrix.types import RoomID, UserID

from ..db import DBManager, WebhookInfo


class WebhookManager:
    _db: DBManager
    _webhooks: dict[UUID, WebhookInfo]

    def __init__(self, db: DBManager):
        self._db = db
        self._webhooks = {}

    async def create(self, repo: str, user_id: UserID, room_id: RoomID) -> WebhookInfo:
        info = WebhookInfo(
            id=uuid4(),
            repo=repo,
            user_id=user_id,
            room_id=room_id,
            secret=random.randbytes(16).hex(),
        )
        await self._db.insert_webhook(info)
        self._webhooks[info.id] = info
        return info

    async def set_github_id(self, info: WebhookInfo, github_id: int) -> WebhookInfo:
        await self._db.set_webhook_github_id(info.id, github_id)
        return await self.get_by_id(info.id)

    async def transfer_repo(self, info: WebhookInfo, new_name: str) -> WebhookInfo:
        await self._db.transfer_webhook_repo(info.id, new_name)
        return await self.get_by_id(info.id)

    async def transfer_rooms(self, old_room: RoomID, new_room: RoomID) -> list[WebhookInfo]:
        await self._db.transfer_webhook_rooms(old_room, new_room)
        return await self.get_all_for_room(new_room)

    async def delete(self, id: UUID) -> None:
        self._webhooks.pop(id, None)
        await self._db.delete_webhook(id)

    def _add_to_cache(self, info: WebhookInfo | None) -> WebhookInfo | None:
        if info is None:
            return None
        self._webhooks[info.id] = info
        return info

    async def get(self, id: UUID) -> WebhookInfo | None:
        try:
            return self._webhooks[id]
        except KeyError:
            return await self.get_by_id(id)

    async def get_by_id(self, id: UUID) -> WebhookInfo | None:
        return self._add_to_cache(await self._db.get_webhook_by_id(id))

    async def get_by_repo(self, room_id: RoomID, repo: str) -> WebhookInfo | None:
        return self._add_to_cache(await self._db.get_webhook_by_repo(room_id, repo))

    async def get_all_for_room(self, room_id: RoomID) -> list[WebhookInfo]:
        items = await self._db.get_webhooks_in_room(room_id)
        for item in items:
            self._webhooks[item.id] = item
        return items
