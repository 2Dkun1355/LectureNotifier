from fastapi import APIRouter, status

user_router = APIRouter(prefix="/v1/users", tags=["Users"])


@user_router.get("/", status_code=status.HTTP_200_OK)
async def get_all_user():
    return {"message": "get all"}


@user_router.get("/{user_id}", status_code=status.HTTP_200_OK)
async def get_user_one(user_id: int):
    return {"message": f"get one {user_id}"}


@user_router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user():
    return {"message": "create"}


@user_router.put("/{user_id}", status_code=status.HTTP_202_ACCEPTED)
async def update_user(user_id: int):
    return {"message": f"update {user_id}"}


@user_router.delete("/{user_id}", status_code=status.HTTP_202_ACCEPTED)
async def delete_user(user_id: int):
    return {"message": f"delete {user_id}"}
