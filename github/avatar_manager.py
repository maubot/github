from typing import TYPE_CHECKING
import asyncio

from sqlalchemy import MetaData, Table, Column, Text
from sqlalchemy.engine.base import Engine

from mautrix.types import ContentURI

from .db import DBManager

if TYPE_CHECKING:
    from .bot import GitHubBot


class AvatarManager:
    bot: 'GitHubBot'
    _avatars: dict[str, ContentURI]
    _db: DBManager
    _lock: asyncio.Lock

    def __init__(self, bot: 'GitHubBot') -> None:
        self.bot = bot
        self._db = bot.db
        self._lock = asyncio.Lock()
        self._avatars = {}

    async def load_db(self) -> None:
        self._avatars = {url: ContentURI(mxc)
                         for url, mxc
                         in await self._db.get_avatars()}

    async def get_mxc(self, url: str) -> ContentURI:
        try:
            return self._avatars[url]
        except KeyError:
            pass
        async with self.bot.http.get(url) as resp:
            resp.raise_for_status()
            data = await resp.read()
        async with self._lock:
            try:
                return self._avatars[url]
            except KeyError:
                pass
            mxc = await self.bot.client.upload_media(data)
            self._avatars[url] = mxc
            await self._db.put_avatar(url, mxc)
        return mxc
