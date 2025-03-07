import asyncio
from create_bot import db, bot, dp
from admin_router import admin_router
from user_router import user_router


async def on_startup():
    await db.create_connection()
    await db.init()


async def main():
    await on_startup()
    dp.include_router(admin_router)
    dp.include_router(user_router)
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
