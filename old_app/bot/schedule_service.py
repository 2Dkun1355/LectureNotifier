from datetime import datetime
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from ..database.models import Lesson, Subscription
from ..database.session import AsyncSessionLocal


class ScheduleService:
    """Сервіс для отримання розкладу занять."""
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

    async def get_lesson(self, lesson_id: int) -> dict | None:
        """Повертає весь розклад."""
        for lessons in self._cache.values():
            for lesson in lessons:
                if lesson.id == lesson_id:
                    return lesson
        return None

    async def get_test_data(self) -> dict:
        """Повертає тестові дані у форматі self._cache (group_name -> список Lesson)."""
        from types import SimpleNamespace

        # Тестові уроки
        lesson1 = SimpleNamespace(
            id=2,
            group=SimpleNamespace(name="Іт-21"),
            week_type="numerator",
            day_of_week=6,
            start_time="15:45"
        )

        return {
            "Іт-21": [lesson1],
        }

    async def get_all_schedule(self) -> dict:
        """Повертає весь розклад."""
        return self._cache.copy()

    async def get_today_schedule(self, group_name: str, week_type: str = "numerator") -> dict:
        """Розклад на сьогодні у вигляді словника з ключем = номер дня тижня."""
        weekday = datetime.today().isoweekday()
        lessons = [
            lesson for lesson in self._cache.get(group_name, [])
            if lesson.week_day == weekday and lesson.week_type == week_type
        ]
        schedule = {weekday: [lesson for lesson in lessons]}
        return schedule

    async def get_week_schedule(self, group_name: str, week_type: str = "numerator") -> dict:
        """Розклад на тиждень у вигляді словника: день (int) -> список уроків."""
        lessons = [l for l in self._cache.get(group_name, []) if l.week_type == week_type]
        schedule: dict[int, list[dict]] = {}
        for lesson in lessons:
            schedule.setdefault(lesson.week_day, []).append(lesson)
        return schedule
