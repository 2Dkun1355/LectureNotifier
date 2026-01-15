from fastapi import FastAPI, status
from app.routers import user_router, lesson_router, group_router, subscription_router

app = FastAPI(
    title="LNUVMB Lecture Schedule API",
    description="API for accessing lecture schedules at the "
                "Lviv National University of Veterinary Medicine and"
                " Biotechnologies named after S.Z. Gzhytskyi.",
    version="0.0.1",
    contact={
        "name": "2DKun1355 & ul-romaniuk",
        "github": "https://github.com/2Dkun1355/LectureNotifier",
    }
)

app.include_router(user_router)
app.include_router(lesson_router)
app.include_router(group_router)
app.include_router(subscription_router)


@app.get("/info", status_code=status.HTTP_200_OK)
async def health_check():
    return {
        "title": app.title,
        "description": app.description,
        "version": app.version,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app="main:app", host="0.0.0.0", port=8000, reload=True)
