from google.cloud.sql.connector import Connector, IPTypes
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

Base = declarative_base()

# Global connector instance
_connector = None

async def get_connector():
    global _connector
    if _connector is None:
        _connector = Connector()
    return _connector

async def getconn():
    connector = await get_connector()
    conn = await connector.connect_async(
        settings.INSTANCE_CONNECTION_NAME,
        "asyncpg",
        user=settings.DB_USER,
        password=settings.DB_PASS,
        db=settings.DB_NAME,
        ip_type=IPTypes.PUBLIC, # Or PRIVATE if running within VPC
    )
    return conn

# Create the engine with the async_creator
# Note: We can't easily create the engine globally with an async creator if the connector needs async init.
# But the Connector object itself doesn't need async init, only the connect_async method.
# Wait, Connector() is not async. 

# However, creating engine usually happens at module level or startup.
# Let's create a lazy engine wrapper or just initialize it.

# If we are running locally without cloud sql connector setup variables, this might fail immediately.
# We'll assume the variables are present or will be.

if settings.INSTANCE_CONNECTION_NAME:
    engine = create_async_engine(
        "postgresql+asyncpg://",
        async_creator=getconn,
    )
else:
    # Fallback to a local DB if configured, or just empty (will fail if used)
    # This is helpful for testing or if user uses a direct URL
    engine = create_async_engine("sqlite+aiosqlite:///./test.db") 

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
