import os
from dotenv import load_dotenv

load_dotenv()

SCHEDULE_ID = os.environ.get("SCHEDULE_ID")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")
