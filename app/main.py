import multiprocessing
import asyncio
from loguru import logger

from app.bot.bot import NotifierBot
from app.schedule.schedule_parser import ScheduleParser
from app.database.session import init_db
from app.config import BOT_TOKEN, SCHEDULE_ID

def start_bot():
    asyncio.run(run_bot())

def start_parser():
    asyncio.run(run_parser())

async def run_parser():
    await init_db()
    parser = ScheduleParser(SCHEDULE_ID)
    while True:
        try:
            await parser.run()
        except Exception as e:
            logger.error(f"Parser error: {e}")
        await asyncio.sleep(24 * 60 * 60)


async def run_bot():
    bot = NotifierBot(BOT_TOKEN)
    try:
        await bot.run()
    except Exception as e:
        logger.error(f"Bot error: {e}")


if __name__ == "__main__":
    processing_bot = multiprocessing.Process(target=start_bot)
    processing_parser = multiprocessing.Process(target=start_parser)

    processing_bot.start()
    processing_parser.start()

    processing_bot.join()
    processing_parser.join()
