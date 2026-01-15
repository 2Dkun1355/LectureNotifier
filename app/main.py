from fastapi import FastAPI, status

app = FastAPI(
    title="LNUVMB Lecture Schedule API",
    description="API for accessing lecture schedules at the "
                "Lviv National University of Veterinary Medicine and"
                " Biotechnologies named after S.Z. Gzhytskyi.",
    version="0.0.1",
)

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app="main:old_app", host="0.0.0.0", port=8000, reload=True)
