from fastapi import APIRouter

from app.common import success


router = APIRouter()


@router.get("/")
def root():
    return success({"name": "SAF Hack API", "status": "running"})


@router.get("/health")
def health():
    return success({"status": "ok"})
