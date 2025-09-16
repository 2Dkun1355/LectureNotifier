import asyncio
from bot import NotifierBot
from schedule import ScheduleParser

async def main():
    parser = ScheduleParser()
    bot = NotifierBot(parser)

    await parser.run()
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
