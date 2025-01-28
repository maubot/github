from typing import TYPE_CHECKING
import asyncio

from sqlalchemy import MetaData, Table, Column, Text
from sqlalchemy.engine.base import Engine

from mautrix.types import ContentURI

if TYPE_CHECKING:
    from .bot import GitHubBot


class AvatarManager:
    bot: 'GitHubBot'
    _avatars: dict[str, ContentURI]
    _table: Table
    _db: Engine
    _lock: asyncio.Lock

    def __init__(self, bot: 'GitHubBot', metadata: MetaData) -> None:
        self.bot = bot
        self._db = bot.database
        self._table = Table("avatar", metadata,
                            Column("url", Text, primary_key=True),
                            Column("mxc", Text, nullable=False))
        self._lock = asyncio.Lock()
        self._avatars = {}

    def load_db(self) -> None:
        self._avatars = {url: ContentURI(mxc)
                         for url, mxc
                         in self._db.execute(self._table.select())}

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
            with self._db.begin() as conn:
                conn.execute(self._table.insert().values(url=url, mxc=mxc))
        return mxc
