from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.common import ApiError, error_payload
from app.database.database import init_db
from app.routers.health import router as health_router
from app.routers.safi_admin import router as api_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="SAF Hack API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(api_router)


@app.exception_handler(ApiError)
async def api_error_handler(_: Request, exc: ApiError):
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(exc.code, exc.message),
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    _: Request,
    __: RequestValidationError,
):
    return JSONResponse(
        status_code=422,
        content=error_payload("INVALID_REQUEST", "Invalid request payload."),
    )
