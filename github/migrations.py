# github - A maubot plugin to act as a GitHub client and webhook receiver.
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
from mautrix.util.async_db import Connection, Scheme, UpgradeTable

upgrade_table = UpgradeTable()


@upgrade_table.register(description="Latest revision", upgrades_to=1)
async def upgrade_latest(conn: Connection, scheme: Scheme) -> None:
    needs_migration = False
    if await conn.table_exists("webhook"):
        needs_migration = True
        await conn.execute(
            """
            ALTER TABLE webhook RENAME TO webhook_old;
            ALTER TABLE client RENAME TO client_old;
            ALTER TABLE matrix_message RENAME TO matrix_message_old;
        """
        )
    await conn.execute(
        f"""CREATE TABLE client (
            user_id TEXT NOT NULL,
            token   TEXT NOT NULL,
            PRIMARY KEY (user_id)
        )"""
    )
    await conn.execute(
        """CREATE TABLE webhook (
            id        uuid NOT NULL,
            repo      TEXT NOT NULL,
            user_id   TEXT NOT NULL,
            room_id   TEXT NOT NULL,
            secret    TEXT NOT NULL,
            github_id INTEGER,
            PRIMARY KEY (id),
            CONSTRAINT webhook_repo_room_unique UNIQUE (repo, room_id)
        )"""
    )
    await conn.execute(
        """CREATE TABLE matrix_message (
            message_id TEXT NOT NULL,
            room_id    TEXT NOT NULL,
            event_id   TEXT NOT NULL,
            PRIMARY KEY (message_id, room_id)
        )"""
    )
    await conn.execute(
        """CREATE TABLE IF NOT EXISTS avatar (
            url TEXT NOT NULL,
            mxc TEXT NOT NULL,
            PRIMARY KEY (url)
        )"""
    )
    if needs_migration:
        await migrate_legacy_to_v1(conn)


async def migrate_legacy_to_v1(conn: Connection) -> None:
    await conn.execute("INSERT INTO client (user_id, token) SELECT user_id, token FROM client_old")
    await conn.execute(
        "INSERT INTO matrix_message (message_id, room_id, event_id) SELECT message_id, room_id, event_id FROM matrix_message_old"
    )
    await conn.execute("CREATE TABLE needs_post_migration(noop INTEGER PRIMARY KEY)")
