from fastapi import Depends
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncEngine
from sqlalchemy.orm import declarative_base
from typing import Annotated

engine: AsyncEngine = create_async_engine("sqlite+aiosqlite:///test.db")
AsyncSessionLocal = async_sessionmaker(engine)
Base = declarative_base()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def delete_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

async def get_session():
    async with AsyncSessionLocal() as session:
        yield session

Session = Annotated[AsyncSessionLocal, Depends(get_session)]