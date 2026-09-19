from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health", summary="Basic backend health")
def health() -> dict:
    return {"status": "ok", "service": "floodroute-backend"}
