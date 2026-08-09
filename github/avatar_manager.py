from typing import TYPE_CHECKING
from dataclasses import dataclass
import asyncio
import time

from mautrix.types import ContentURI

from .db import DBManager

if TYPE_CHECKING:
    from .bot import GitHubBot

_TTL = 3600
_DB_TOUCH_INTERVAL = 86400
_ERROR_BACKOFF = 300


@dataclass
class _Entry:
    mxc: ContentURI
    etag: str | None
    fetched_at_mono: float
    db_fetched_at_wall: int


class AvatarManager:
    bot: "GitHubBot"
    _db: DBManager
    _entries: dict[str, _Entry]
    _inflight: dict[str, asyncio.Task[ContentURI]]

    def __init__(self, bot: "GitHubBot") -> None:
        self.bot = bot
        self._db = bot.db
        self._entries = {}
        self._inflight = {}

    async def load_db(self) -> None:
        rows = await self._db.get_avatars()
        now_mono = time.monotonic()
        now_wall = int(time.time())
        entries: dict[str, _Entry] = {}
        for avatar in rows:
            db_fetched_at = int(avatar.fetched_at or 0)
            # Map wall-clock fetched_at to monotonic so TTL survives restarts.
            elapsed = max(0, now_wall - db_fetched_at) if db_fetched_at > 0 else _TTL + 1
            entries[avatar.url] = _Entry(
                mxc=ContentURI(avatar.mxc),
                etag=avatar.etag,
                fetched_at_mono=now_mono - elapsed,
                db_fetched_at_wall=db_fetched_at,
            )
        self._entries = entries

    async def get_mxc(self, url: str) -> ContentURI:
        entry = self._entries.get(url)
        if entry is not None and (time.monotonic() - entry.fetched_at_mono) < _TTL:
            return entry.mxc

        task = self._inflight.get(url)
        if task is None:
            task = asyncio.create_task(self._fetch(url))
            self._inflight[url] = task
            task.add_done_callback(lambda _t, u=url: self._inflight.pop(u, None))
        return await task

    async def _fetch(self, url: str) -> ContentURI:
        entry = self._entries.get(url)
        headers: dict[str, str] = {}
        if entry is not None and entry.etag:
            headers["If-None-Match"] = entry.etag

        try:
            async with self.bot.http.get(url, headers=headers) as resp:
                if resp.status == 304 and entry is not None:
                    entry.fetched_at_mono = time.monotonic()
                    now_wall = int(time.time())
                    if now_wall - entry.db_fetched_at_wall >= _DB_TOUCH_INTERVAL:
                        await self._db.put_avatar(
                            url, entry.mxc, etag=entry.etag, fetched_at=now_wall
                        )
                        entry.db_fetched_at_wall = now_wall
                    return entry.mxc

                resp.raise_for_status()
                data = await resp.read()
                new_etag = resp.headers.get("ETag")
        except Exception:
            if entry is None:
                raise
            self.bot.log.warning("Avatar fetch failed, serving cached", exc_info=True)
            entry.fetched_at_mono = time.monotonic() - _TTL + _ERROR_BACKOFF
            return entry.mxc

        mxc = await self.bot.client.upload_media(data)
        now_wall = int(time.time())
        self._entries[url] = _Entry(
            mxc=mxc,
            etag=new_etag,
            fetched_at_mono=time.monotonic(),
            db_fetched_at_wall=now_wall,
        )
        await self._db.put_avatar(url, mxc, etag=new_etag, fetched_at=now_wall)
        return mxc
