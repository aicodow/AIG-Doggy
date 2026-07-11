"""PostgreSQL 读写分离连接池。"""

import logging
from typing import Any, Optional

import asyncpg

log = logging.getLogger(__name__)


class DatabasePool:
    """PostgreSQL 读写分离连接池。

    使用 asyncpg 创建两个独立连接池：
      - write_pool: 指向 Primary，用于 INSERT/UPDATE/DELETE
      - read_pool: 指向 Replica，用于 SELECT
    """

    def __init__(self, write_url: str, read_url: str):
        self._write_url = write_url
        self._read_url = read_url
        self._write_pool: Optional[asyncpg.Pool] = None
        self._read_pool: Optional[asyncpg.Pool] = None

    async def start(self) -> None:
        self._write_pool = await asyncpg.create_pool(self._write_url, min_size=5, max_size=20)
        self._read_pool = await asyncpg.create_pool(self._read_url, min_size=10, max_size=40)
        log.info("PostgreSQL 连接池已创建: write=%s read=%s", self._write_url, self._read_url)

    async def stop(self) -> None:
        if self._write_pool:
            await self._write_pool.close()
        if self._read_pool:
            await self._read_pool.close()

    async def execute_write(self, query: str, *args: Any) -> str:
        """执行写操作。"""
        async with self._write_pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def execute_read(self, query: str, *args: Any) -> list[asyncpg.Record]:
        """执行读操作。"""
        async with self._read_pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetch_one(self, query: str, *args: Any) -> Optional[asyncpg.Record]:
        """查询单条记录。"""
        async with self._read_pool.acquire() as conn:
            return await conn.fetchrow(query, *args)