from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# In production, settings.DATABASE_URL should contain the postgresql+asyncpg connection string
# For fallback / local development/testing, we can use aiosqlite (sqlite+aiosqlite:///:memory:)
db_url = settings.DATABASE_URL
if not db_url or "postgresql" not in db_url and "sqlite" not in db_url:
    db_url = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(db_url, future=True, echo=False)

SessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False
)


async def get_db():
    """FastAPI dependency to yield database sessions."""
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
