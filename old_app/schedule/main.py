import asyncio
from loguru import logger

from .schedule_parser import ScheduleParser
from ..database import init_db


async def parser_init(schedule_id, interval = 12 * 60 * 60):
    await init_db()
    parser = ScheduleParser(schedule_id)
    while True:

        try:
            await parser.run()
        except Exception as e:
            logger.error(f"Parser error: {e}")
            continue
        logger.info(f"Next parsing in {interval // (60 * 60)} hours.")
        await asyncio.sleep(interval)