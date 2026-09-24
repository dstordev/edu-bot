import redis
from loguru import logger
from redis.asyncio.client import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


async def check_redis_connection(host: str, port: int) -> bool:
    try:
        if await Redis(host=host, port=port).ping():
            return True
    except redis.ConnectionError:
        pass
    return False


async def check_postgres_connection(
    async_session_maker: async_sessionmaker[AsyncSession],
) -> bool:
    try:
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.exception(e)
    return False
