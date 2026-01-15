from fastapi import APIRouter, status

subscription_router = APIRouter(prefix="/v1/subscription", tags=["Subscription"])

@subscription_router.get("/", status_code=status.HTTP_200_OK)
async def get_all_subscription():
    return {"message": "get all"}

@subscription_router.get("/{subscription_id}", status_code=status.HTTP_200_OK)
async def get_one_subscription(subscription_id: int):
    return {"message": f"get one {subscription_id}"}

@subscription_router.post("/", status_code=status.HTTP_201_CREATED)
async def create_subscription():
    return {"message": "create"}

@subscription_router.put("/{subscription_id}", status_code=status.HTTP_202_ACCEPTED)
async def update_subscription(subscription_id: int):
    return {"message": f"update {subscription_id}"}

@subscription_router.delete("/{subscription_id}", status_code=status.HTTP_202_ACCEPTED)
async def delete_subscription(subscription_id: int):
    return {"message": f"delete {subscription_id}"}