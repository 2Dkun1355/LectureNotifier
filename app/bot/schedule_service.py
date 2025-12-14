from datetime import datetime
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from ..database.models import Lesson, Subscription
from ..database.session import AsyncSessionLocal


class ScheduleService:
    """Сервіс для отримання розкладу занять."""
    DAYS = {1: "Понеділок", 2: "Вівторок", 3: "Середа", 4: "Четвер",
            5: "Пʼятниця", 6: "Субота", 7: "Неділя"}
    WEEK_MAP = {"numerator": "чис.", "denominator": "знам."}

    def __init__(self):
        self._cache: dict[str, list] = {}

    async def load_cache(self):
        """Завантажує всі уроки з БД у пам'ять."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Lesson).options(selectinload(Lesson.group)))
            lessons = result.scalars().all()

        self._cache.clear()
        for lesson in lessons:
            group_name = lesson.group.name
            self._cache.setdefault(group_name, []).append(lesson)

    async def format_lesson(self, lesson: Lesson) -> str:
        """Форматує урок у рядок для Telegram."""
        return (
            f"{lesson.lesson_number}. {lesson.subject} | "
            f"{lesson.start_time or "--:--"} - {lesson.end_time or "--:--"} | "
            f"{lesson.teacher or "Не вказано"} | "
            f"{lesson.room or '-'}"
        )

    async def today_schedule(self, group_name, week_type: str = "numerator") -> str:
        weekday = datetime.today().isoweekday()
        lessons = [
            lesson for lesson in self._cache.get(group_name, [])
            if lesson.week_day == weekday and lesson.week_type == week_type
        ]

        if not lessons:
            return "😱 Сьогодні немає занять."

        formatted = [f"Розклад на сьогодні:\n"]
        formatted += [await self.format_lesson(lesson) for lesson in lessons]
        return "\n".join(formatted)

    async def week_schedule(self, group_name, week_type: str = "numerator") -> str:
        lessons = [l for l in self._cache.get(group_name, []) if l.week_type == week_type]
        if not lessons:
            return "😁 На цей тиждень немає занять."

        output = [f"Розклад на тиждень:"]
        current_day = None
        for lesson in sorted(lessons, key=lambda lesson: (lesson.week_day, lesson.lesson_number)):
            if current_day != lesson.week_day:
                current_day = lesson.week_day
                output.append(f"\n{self.DAYS.get(current_day)}:\n")
            output.append(await self.format_lesson(lesson))
        return "\n".join(output)
