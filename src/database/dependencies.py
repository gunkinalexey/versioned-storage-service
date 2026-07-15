from collections.abc import AsyncGenerator

from database.client_async import AsyncClient


async def get_db_client() -> AsyncGenerator[AsyncClient, None]:
    db_client = await AsyncClient.create()
    try:
        yield db_client
    finally:
        await db_client.close()
