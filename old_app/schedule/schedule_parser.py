import time
import pandas as pd
from loguru import logger
from sqlalchemy.future import select
from ..database.models import Lesson, Group
from ..database.session import AsyncSessionLocal


class ScheduleParser:
    """Парсер розкладу з Google Sheets у базу даних. Повна синхронізація CSV -> БД з оптимізаціями."""

    DAY_MAPPING = {"Пн": 0, "Вт": 1, "Ср": 2, "Чт": 3, "Пт": 4, "Сб": 5, "Нд": 6}
    LESSON_NUMBER_MAPPING = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5,
                             "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10}
    WEEK_TYPE_MAPPING = {"чис.": "numerator", "знам.": "denominator"}

    def __init__(self, google_sheet_id: str):
        """Ініціалізація парсера з ID Google Sheets."""
        self.google_sheet_id = google_sheet_id

    async def load_schedule(self) -> pd.DataFrame:
        """Завантажує розклад з Google Sheets у DataFrame."""
        logger.info("Loading schedule from Google Sheets...")
        start_time = time.time()
        df = pd.read_csv(
            f"https://docs.google.com/spreadsheets/d/e/{self.google_sheet_id}/pub?output=csv",
            header=1
        )
        logger.success(f"Schedule loaded in {time.time() - start_time:.3f}s")
        return df

    async def detect_groups_and_rooms(self, df: pd.DataFrame) -> tuple[list[str], dict[str, str]]:
        """Визначає колонки груп та відповідні колонки для кімнат."""
        group_columns = [
            column for column in df.columns[5:]
            if not column.endswith(".1") and not column.startswith("Unnamed")
        ]
        room_columns = {group: group + ".1" for group in group_columns if group + ".1" in df.columns}
        return group_columns, room_columns

    @staticmethod
    def clean_value(value: any) -> str | None:
        """Очищує значення від NaN та пробілів."""
        if pd.isna(value):
            return None
        return str(value).strip()

    def parse_lesson_row(self, df: pd.DataFrame, row_index: int, group_name: str, room_column: str | None) -> dict | None:
        """Парсить один урок із DataFrame. Повертає словник з даними уроку або None."""
        main_row = df.iloc[row_index]
        teacher_row = df.iloc[row_index + 1]
        start_time = self.clean_value(main_row["Unnamed: 3"])
        end_time = self.clean_value(teacher_row["Unnamed: 3"])
        week_day = self.DAY_MAPPING.get(self.clean_value(main_row["Unnamed: 1"]))
        lesson_number = self.LESSON_NUMBER_MAPPING.get(self.clean_value(main_row["Unnamed: 2"]))
        week_type = self.WEEK_TYPE_MAPPING.get(self.clean_value(main_row["Шифр групи"]))
        subject = self.clean_value(main_row[group_name])
        teacher = self.clean_value(teacher_row[group_name])
        room = self.clean_value(teacher_row[room_column]) if room_column else None

        if not lesson_number or not subject:
            return None

        return {
            "week_day": week_day,
            "lesson_number": lesson_number,
            "week_type": week_type,
            "start_time": start_time,
            "end_time": end_time,
            "subject": subject,
            "teacher": teacher,
            "room": room
        }

    async def get_or_create_group(self, session, group_name: str) -> Group:
        """Отримує групу з бази даних або створює нову."""
        result = await session.execute(select(Group).where(Group.name == group_name))
        group = result.scalars().first()
        if not group:
            group = Group(name=group_name)
            session.add(group)
            await session.flush()
        return group

    async def process_group(self, df: pd.DataFrame, group_name: str, room_columns: dict, session):
        """Синхронізує уроки однієї групи з CSV."""
        group = await self.get_or_create_group(session, group_name)
        room_column = room_columns.get(group_name)

        csv_lessons = []
        row_index = 0
        while row_index < len(df) - 1:
            lesson_data = self.parse_lesson_row(df, row_index, group_name, room_column)
            if lesson_data:
                csv_lessons.append(lesson_data)
                row_index += 2
            else:
                row_index += 1

        result = await session.execute(select(Lesson).where(Lesson.group_id == group.id))
        db_lessons = {(l.week_day, l.lesson_number, l.week_type): l for l in result.scalars().all()}

        csv_keys = {(l["week_day"], l["lesson_number"], l["week_type"]) for l in csv_lessons}
        for key, db_lesson in db_lessons.items():
            if key not in csv_keys:
                await session.delete(db_lesson)

        for lesson_data in csv_lessons:
            key = (lesson_data["week_day"], lesson_data["lesson_number"], lesson_data["week_type"])
            db_lesson = db_lessons.get(key)
            if db_lesson:
                changed = any(
                    getattr(db_lesson, field) != lesson_data[field]
                    for field in ["start_time", "end_time", "subject", "teacher", "room"]
                )
                if changed:
                    for field in ["start_time", "end_time", "subject", "teacher", "room"]:
                        setattr(db_lesson, field, lesson_data[field])
            else:
                session.add(Lesson(group_id=group.id, **lesson_data))

    async def process_all_groups(self, df: pd.DataFrame, group_columns: list[str], room_columns: dict):
        """Обробляє всі групи та синхронізує базу повністю."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Group))
            db_groups = {g.name: g for g in result.scalars().all()}

            csv_group_names = set(group_columns)
            for name, group in db_groups.items():
                if name not in csv_group_names:
                    await session.delete(group)

            for group_name in group_columns:
                await self.process_group(df, group_name, room_columns, session)

            await session.commit()

    async def run(self):
        """Головний метод для повного оновлення розкладу."""
        start_time = time.time()
        logger.info("Updating schedule...")
        df = await self.load_schedule()
        group_columns, room_columns = await self.detect_groups_and_rooms(df)
        await self.process_all_groups(df, group_columns, room_columns)
        logger.success(f"Schedule updated successfully in {time.time() - start_time:.3f}s")
