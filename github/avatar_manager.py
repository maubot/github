from typing import TYPE_CHECKING, Optional
import asyncio
import time

from sqlalchemy import Column, MetaData, Table, Text
from sqlalchemy.engine.base import Engine

from mautrix.types import ContentURI

from .db import DBManager

if TYPE_CHECKING:
    from .bot import GitHubBot


class AvatarManager:
    bot: "GitHubBot"
    _avatars: dict[str, ContentURI]
    _etag: dict[str, Optional[str]]
    _fetched_at: dict[str, int]
    _db: DBManager
    _lock: asyncio.Lock

    def __init__(self, bot: "GitHubBot") -> None:
        self.bot = bot
        self._db = bot.db
        self._lock = asyncio.Lock()
        self._avatars = {}
        self._etag = {}
        self._fetched_at = {}

    async def load_db(self) -> None:
        rows = await self._db.get_avatars()
        self._avatars = {avatar.url: ContentURI(avatar.mxc) for avatar in rows}
        self._etag = {avatar.url: avatar.etag for avatar in rows}
        self._fetched_at = {avatar.url: int(avatar.fetched_at or 0) for avatar in rows}

    async def get_mxc(self, url: str) -> ContentURI:
        now = int(time.time())
        # 5 min TTL
        if url in self._avatars and (now - self._fetched_at.get(url, 0)) < 300:
            return self._avatars[url]

        headers: dict[str, str] = {}
        etag = self._etag.get(url)
        if etag:
            headers["If-None-Match"] = etag

        async with self.bot.http.get(url, headers=headers) as resp:
            if resp.status == 304 and url in self._avatars:
                # Unchanged: bump fetched_at and persist
                self._fetched_at[url] = now
                await self._db.put_avatar(
                    url,
                    self._avatars[url],
                    etag=self._etag.get(url),
                    fetched_at=now,
                )
                return self._avatars[url]

            resp.raise_for_status()
            data = await resp.read()
            new_etag = resp.headers.get("ETag")

        async with self._lock:
            # Race guard with same TTL inside the lock
            if url in self._avatars and (now - self._fetched_at.get(url, 0)) < 300:
                return self._avatars[url]

            mxc = await self.bot.client.upload_media(data)
            self._avatars[url] = mxc
            self._etag[url] = new_etag
            self._fetched_at[url] = now
            await self._db.put_avatar(url, mxc, etag=new_etag, fetched_at=now)
            return mxc
