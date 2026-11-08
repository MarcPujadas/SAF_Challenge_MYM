from fastapi import APIRouter

from app.common import success
from app.services.catalog_service import (
    get_current_user,
    get_service_resources,
    list_services,
    list_spaces,
)


router = APIRouter(prefix="/api/v1")


@router.get("/users/me")
def current_user():
    return success(get_current_user())


@router.get("/spaces")
def get_spaces():
    return success(list_spaces())


@router.get("/services")
def get_services():
    return success(list_services())


@router.get("/services/{service_id}/spaces")
def get_service_spaces(service_id: str):
    return success(get_service_resources(service_id))
