"""FastAPI-бэкенд проверки анкет кандидатов.

Endpoint:
  POST /screening/ — принимает анкету кандидата в формате JSON и возвращает
                    отчёт о внутренних противоречиях и соответствии должности.

Если рядом с backend собран Vue-фронтенд (``frontend/dist``), FastAPI
раздаёт его как статику на ``/``. В режиме разработки интерфейс запускается
отдельным Vite-сервером, а запросы к API проксируются на этот backend.
"""

import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.agents.screening_agent import screen_candidate
from app.schema.schemas import ScreeningRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Swagger UI и ReDoc по умолчанию подгружают JS/CSS с CDN, поэтому в
# офлайн-контуре они отключены. Включаются явно через ENABLE_API_DOCS=1.
_docs_enabled = os.getenv("ENABLE_API_DOCS", "0").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

app = FastAPI(
    title="AI Resume Screening",
    description=(
        "Проверка анкеты кандидата: внутренние противоречия и соответствие "
        "опыта целевой должности."
    ),
    version="2.0.0",
    docs_url="/docs" if _docs_enabled else None,
    redoc_url="/redoc" if _docs_enabled else None,
)

_DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"
_cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", _DEFAULT_CORS_ORIGINS).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    """Проверка доступности backend."""
    return {"status": "ok"}


@app.post("/screening/")
def screen(payload: ScreeningRequest) -> JSONResponse:
    """Проверяет анкету кандидата и возвращает структурированный отчёт.

    Тело запроса::

        {
          "candidate": { ... анкета по схеме ... }
        }

    Соответствие должности оценивается по ``positionName`` и ``department``.
    """
    logger.info(
        "Получена анкета: %s (должность: %s)",
        payload.candidate.full_name or "без имени",
        payload.candidate.position_name or "не указана",
    )
    report = screen_candidate(payload.candidate)
    return JSONResponse(content=report)


_FRONTEND_DIST = Path(__file__).resolve().parent / "static"

if _FRONTEND_DIST.is_dir():
    app.mount(
        "/",
        StaticFiles(directory=_FRONTEND_DIST, html=True),
        name="static",
    )
else:

    @app.get("/", include_in_schema=False)
    def frontend_not_built() -> dict[str, str]:
        """Подсказка, если собранный фронтенд ещё отсутствует."""
        return {
            "message": (
                "Frontend не собран. Выполните `bun run build` в каталоге "
                "frontend или запустите Vite dev-сервер."
            )
        }
