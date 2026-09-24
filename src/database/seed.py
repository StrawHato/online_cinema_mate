import asyncio

from sqlalchemy import select

from src.database.models.accounts import UserGroupModel, UserGroupEnum
from src.database.session import AsyncSessionLocal


async def seed_user_groups() -> None:
    async with AsyncSessionLocal() as session:
        created = False
        for group in UserGroupEnum:
            existing_group = await session.scalar(
                select(UserGroupModel).where(
                    UserGroupModel.name == group
                )
            )

            if existing_group is None:
                session.add(
                    UserGroupModel(
                        name=group,
                    )
                )
                created = True

        if created:
            await session.commit()
            print("User groups seeded successfully.")
        else:
            print("User groups already exist.")


if __name__ == "__main__":
    asyncio.run(seed_user_groups())
