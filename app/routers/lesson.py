from fastapi import APIRouter, status

lesson_router = APIRouter(prefix="/v1/lessons", tags=["Lessons"])


@lesson_router.get("/", status_code=status.HTTP_200_OK)
async def get_all_lesson():
    return {"message": "get all"}


@lesson_router.get("/{lesson_id}", status_code=status.HTTP_200_OK)
async def get_user_one(lesson_id: int):
    return {"message": f"get one {lesson_id}"}


@lesson_router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user():
    return {"message": "create"}


@lesson_router.put("/{lesson_id}", status_code=status.HTTP_202_ACCEPTED)
async def update_user(lesson_id: int):
    return {"message": f"update {lesson_id}"}


@lesson_router.delete("/{lesson_id}", status_code=status.HTTP_202_ACCEPTED)
async def delete_user(lesson_id: int):
    return {"message": f"delete {lesson_id}"}