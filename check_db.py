import asyncio
from database import init_db, close_db


async def main():
    try:
        await init_db()
        print("NEON CONNECTED")
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())