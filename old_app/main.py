import multiprocessing
import asyncio
from old_app.bot.main import bot_init
from old_app.schedule.main import parser_init
from old_app.config import BOT_TOKEN, SCHEDULE_ID

def run_bot():
    asyncio.run(bot_init(BOT_TOKEN))

def run_parser():
    asyncio.run(parser_init(SCHEDULE_ID))


if __name__ == "__main__":
    processing_bot = multiprocessing.Process(target=run_bot)
    processing_parser = multiprocessing.Process(target=run_parser)

    processing_bot.start()
    processing_parser.start()

    processing_bot.join()
    processing_parser.join()
