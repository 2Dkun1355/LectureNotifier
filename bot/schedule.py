import asyncio
from loguru import logger
import pandas as pd
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import SCHEDULE_URL, UPDATE_HOUR, UPDATE_MINUTE, UPDATE_DAYS


class ScheduleParser:
    def __init__(self):
        self.schedule = {}
        self.groups = []
        self.scheduler = AsyncIOScheduler(timezone="Europe/Kyiv")

    @staticmethod
    def _clean_value(val):
        if pd.isna(val):
            return None
        return str(val).strip()

    async def _load_dataframe(self) -> pd.DataFrame:
        logger.info("Loading data from Google Sheets...")
        df = pd.read_csv(SCHEDULE_URL, header=1)
        return df

    async def _detect_columns(self, df: pd.DataFrame):
        group_columns = [
            col for col in df.columns[5:]
            if not col.endswith('.1') and not col.startswith('Unnamed')
        ]
        room_columns = {g: g + ".1" for g in group_columns if g + ".1" in df.columns}
        return group_columns, room_columns

    async def _process_group(self, df: pd.DataFrame, group: str, room_columns: dict) -> tuple:
        logger.debug(f"Processing group: {group}")
        result = {}
        room_col = room_columns.get(group)
        i = 0
        while i < len(df) - 1:
            row_main = df.iloc[i]
            row_teacher = df.iloc[i + 1]
            day = self._clean_value(row_main["Unnamed: 1"])
            lesson = self._clean_value(row_main["Unnamed: 2"])
            start_time = self._clean_value(row_main["Unnamed: 3"])
            end_time = self._clean_value(row_teacher["Unnamed: 3"])
            week_type = self._clean_value(row_main["Шифр групи"])
            subject = self._clean_value(row_main[group])
            teacher = self._clean_value(row_teacher[group])
            room = self._clean_value(row_teacher[room_col]) if room_col else None
            if not day or day == "День тижня" or not lesson or lesson == "Пара":
                i += 1
                continue
            result.setdefault(day, {}).setdefault(lesson, {})[week_type] = {
                "Початок": start_time,
                "Закінчення": end_time,
                "Предмет": subject,
                "Викладач": teacher,
                "Аудиторія": room
            }
            i += 2
        return group, result

    async def _parse_all_groups(self, df: pd.DataFrame, group_columns: list, room_columns: dict):
        results = await asyncio.gather(*(self._process_group(df, g, room_columns) for g in group_columns))
        return dict(results)

    async def update(self):
        logger.info("Updating schedule...")
        df = await self._load_dataframe()
        group_columns, room_columns = await self._detect_columns(df)
        self.schedule = await self._parse_all_groups(df, group_columns, room_columns)
        self.groups = sorted(group_columns)

        logger.success(f"Schedule updated successfully: {len(self.groups)} groups loaded")

    def start_scheduler(self):
        self.scheduler.add_job(self.update, "cron", hour=UPDATE_HOUR, minute=UPDATE_MINUTE, day_of_week=UPDATE_DAYS)
        self.scheduler.start()

    async def run(self):
        self.start_scheduler()
        await self.update()