import asyncio
import os

import asyncpg


MAX_RETRIES = 30
RETRY_DELAY = 2


DATABASE_URL = (
    f"postgresql://"
    f"{os.environ['POSTGRES_USER']}:"
    f"{os.environ['POSTGRES_PASSWORD']}@"
    f"{os.environ['POSTGRES_HOST']}:"
    f"{os.environ['POSTGRES_DB_PORT']}/"
    f"{os.environ['POSTGRES_DB']}"
)


async def wait_for_db() -> None:
    print("Waiting for PostgreSQL...")

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            conn = await asyncpg.connect(DATABASE_URL)
            await conn.close()

            print("PostgreSQL is ready.")
            return

        except Exception as exc:
            print(
                f"[{attempt}/{MAX_RETRIES}] "
                f"PostgreSQL is unavailable: {exc}"
            )

            await asyncio.sleep(RETRY_DELAY)

    raise RuntimeError(
        "Could not connect to PostgreSQL."
    )


if __name__ == "__main__":
    asyncio.run(wait_for_db())
