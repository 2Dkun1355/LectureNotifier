from fastapi import APIRouter, status

group_router = APIRouter(prefix="/v1/groups", tags=["Groups"])


@group_router.get("/", status_code=status.HTTP_200_OK)
async def get_all_group():
    return {"message": "get all"}


@group_router.get("/{group_id}", status_code=status.HTTP_200_OK)
async def get_group_one(group_id: int):
    return {"message": f"get one {group_id}"}


@group_router.post("/", status_code=status.HTTP_201_CREATED)
async def create_group():
    return {"message": "create"}


@group_router.put("/{group_id}", status_code=status.HTTP_202_ACCEPTED)
async def update_group(group_id: int):
    return {"message": f"update {group_id}"}


@group_router.delete("/{group_id}", status_code=status.HTTP_202_ACCEPTED)
async def delete_group(group_id: int):
    return {"message": f"delete {group_id}"}
