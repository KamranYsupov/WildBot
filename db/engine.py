import os

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from db.models import Base

# SQLite
# engine = create_async_engine('sqlite+aiosqlite:///database.db', echo=True)

# # POSTGRESQL
engine = create_async_engine(
    'postgresql+asyncpg://'
    + str(os.environ.get('DB_USER'))
    + ':'
    + str(os.environ.get('DB_PASS'))
    + '@'
    + str(os.environ.get('DB_HOST'))
    + ':'
    + '5432/'
    + str(os.environ.get('DB_NAME')),
    echo=True
)

session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
