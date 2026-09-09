from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic liveness probe for the SURAKSHA backend."""
    return {
        "status": "ok",
        "service": "suraksha-backend",
        "version": "0.1.0",
    }
