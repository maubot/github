# github - A maubot plugin to act as a GitHub client and webhook receiver.
# Copyright (C) 2022 Sumner Evans
# Copyright (C) 2025 Tulir Asokan
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
from typing import Optional
import hashlib
import hmac
import uuid

from asyncpg import Record
from attr import dataclass

from mautrix.types import ContentURI, EventID, RoomID, UserID
from mautrix.util.async_db import Connection, Database


@dataclass(frozen=True)
class Client:
    user_id: UserID
    token: str

    @classmethod
    def from_row(cls, row: Record | None) -> Optional["Client"]:
        if not row:
            return None
        user_id = row["user_id"]
        token = row["token"]
        return cls(
            user_id=user_id,
            token=token,
        )


@dataclass(frozen=True)
class Avatar:
    url: str
    mxc: ContentURI

    @classmethod
    def from_row(cls, row: Record | None) -> Optional["Avatar"]:
        if not row:
            return None
        url = row["url"]
        mxc = row["mxc"]
        return cls(
            url=url,
            mxc=mxc,
        )


@dataclass(frozen=True)
class WebhookInfo:
    id: uuid.UUID
    repo: str
    user_id: UserID
    room_id: RoomID
    secret: str
    github_id: int | None = None

    @classmethod
    def from_row(cls, row: Record | None) -> Optional["WebhookInfo"]:
        if not row:
            return None
        id = row["id"]
        repo = row["repo"]
        user_id = row["user_id"]
        room_id = row["room_id"]
        github_id = row["github_id"]
        secret = row["secret"]
        return cls(
            id=uuid.UUID(id),
            repo=repo,
            user_id=user_id,
            room_id=room_id,
            github_id=github_id,
            secret=secret,
        )

    def __str__(self) -> str:
        return (
            f"webhook {self.id!s} (GH{self.github_id}) from {self.repo} to {self.room_id}"
            f" added by {self.user_id}"
        )


class DBManager:
    db: Database

    def __init__(self, db: Database) -> None:
        self.db = db

    async def get_event(self, message_id: str, room_id: RoomID) -> EventID | None:
        return await self.db.fetchval(
            "SELECT event_id FROM matrix_message WHERE message_id = $1 AND room_id = $2",
            message_id,
            room_id,
        )

    async def put_event(
        self,
        message_id: str,
        room_id: RoomID,
        event_id: EventID,
    ) -> None:
        await self.db.execute(
            """
            INSERT INTO matrix_message (message_id, room_id, event_id) VALUES ($1, $2, $3)
            ON CONFLICT (message_id, room_id) DO UPDATE SET event_id = excluded.event_id
            """,
            message_id,
            room_id,
            event_id,
        )

    async def get_clients(self) -> list[Client]:
        rows = await self.db.fetch("SELECT user_id, token FROM client")
        return [Client.from_row(row) for row in rows]

    async def put_client(self, user_id: UserID, token: str) -> None:
        await self.db.execute(
            """
            INSERT INTO client (user_id, token) VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE SET token = excluded.token
            """,
            user_id,
            token,
        )

    async def delete_client(self, user_id: UserID) -> None:
        await self.db.execute(
            "DELETE FROM client WHERE user_id = $1",
            user_id,
        )

    async def get_avatars(self) -> list[Avatar]:
        rows = await self.db.fetch("SELECT url, mxc FROM avatar")
        return [Avatar.from_row(row) for row in rows]

    async def put_avatar(self, url: str, mxc: ContentURI) -> None:
        await self.db.execute(
            """
            INSERT INTO avatar (url, mxc) VALUES ($1, $2)
            ON CONFLICT (url) DO NOTHING
            """,
            url,
            mxc,
        )

    async def get_webhook_by_id(self, id: uuid.UUID) -> WebhookInfo | None:
        row = await self.db.fetchrow(
            "SELECT id, repo, user_id, room_id, github_id, secret FROM webhook WHERE id = $1",
            str(id),
        )
        return WebhookInfo.from_row(row)

    async def get_webhook_by_repo(self, room_id: RoomID, repo: str) -> WebhookInfo | None:
        row = await self.db.fetchrow(
            "SELECT id, repo, user_id, room_id, github_id, secret FROM webhook WHERE room_id = $1 AND repo = $2",
            room_id,
            repo,
        )
        return WebhookInfo.from_row(row)

    async def get_webhooks_in_room(self, room_id: RoomID) -> list[WebhookInfo]:
        rows = await self.db.fetch(
            "SELECT id, repo, user_id, room_id, github_id, secret FROM webhook WHERE room_id = $1",
            room_id,
        )
        return [WebhookInfo.from_row(row) for row in rows]

    async def delete_webhook(self, id: uuid.UUID) -> None:
        await self.db.execute(
            "DELETE FROM webhook WHERE id = $1",
            str(id),
        )

    async def insert_webhook(
        self, webhook: WebhookInfo, *, _conn: Connection | None = None
    ) -> None:
        await (_conn or self.db).execute(
            """
            INSERT INTO webhook (id, repo, user_id, room_id, secret, github_id)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            str(webhook.id),
            webhook.repo,
            webhook.user_id,
            webhook.room_id,
            webhook.secret,
            webhook.github_id,
        )

    async def set_webhook_github_id(self, id: uuid.UUID, github_id: int) -> None:
        await self.db.execute(
            "UPDATE webhook SET github_id = $1 WHERE id = $2",
            github_id,
            str(id),
        )

    async def transfer_webhook_repo(self, id: uuid.UUID, new_repo: str) -> None:
        await self.db.execute(
            "UPDATE webhook SET repo = $1 WHERE id = $2",
            new_repo,
            str(id),
        )

    async def transfer_webhook_rooms(self, old_room: RoomID, new_room: RoomID) -> None:
        await self.db.execute(
            "UPDATE webhook SET room_id = $1 WHERE room_id = $2",
            new_room,
            old_room,
        )

    async def run_post_migration(self, conn: Connection, secret_key: str) -> None:
        rows = list(
            await conn.fetch("SELECT id, repo, user_id, room_id, github_id FROM webhook_old")
        )
        for row in rows:
            id = uuid.UUID(row["id"])
            secret = hmac.new(key=secret_key.encode("utf-8"), digestmod=hashlib.sha256)
            secret.update(id.bytes)
            secret.update(row["user_id"].encode("utf-8"))
            secret.update(row["room_id"].encode("utf-8"))
            new_webhook = WebhookInfo(
                id=id,
                repo=row["repo"],
                user_id=row["user_id"],
                room_id=row["room_id"],
                github_id=row["github_id"],
                secret=secret.hexdigest(),
            )
            await self.insert_webhook(new_webhook, _conn=conn)
        await conn.execute("DROP TABLE needs_post_migration")
