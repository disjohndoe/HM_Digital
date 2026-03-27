import asyncio

from app.database import async_session
from app.utils.seed_data import seed_demo_data


async def main() -> None:
    async with async_session() as db:
        await seed_demo_data(db)


if __name__ == "__main__":
    asyncio.run(main())
