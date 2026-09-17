"""Uygulama girisi: rotalar ve oturum yonetimi."""

import time
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app import (
    config,
    dashboard,
    definitions,
    direct,
    production,
    readings,
    reports,
    security,
    targets,
)
from app.web import render

BASE_DIR = Path(__file__).resolve().parent

LOGIN_PATH = "/giris"
PUBLIC_PATHS = (LOGIN_PATH, "/static", "/saglik")

# Basit kaba kuvvet korumasi: ayni IP icin art arda hatali denemeler.
_MAX_ATTEMPTS = 5
_LOCK_SECONDS = 60
_failed_attempts: dict[str, tuple[int, float]] = {}


def _is_locked(client: str) -> bool:
    count, last = _failed_attempts.get(client, (0, 0.0))
    return count >= _MAX_ATTEMPTS and (time.monotonic() - last) < _LOCK_SECONDS


def _record_failure(client: str) -> None:
    count, last = _failed_attempts.get(client, (0, 0.0))
    if time.monotonic() - last >= _LOCK_SECONDS:
        count = 0
    _failed_attempts[client] = (count + 1, time.monotonic())


def create_app() -> FastAPI:
    app = FastAPI(title="Enerji Izleme", docs_url=None, redoc_url=None)
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

    @app.middleware("http")
    async def require_login(request: Request, call_next):
        path = request.url.path
        if not path.startswith(PUBLIC_PATHS) and not request.session.get("auth"):
            return RedirectResponse(LOGIN_PATH, status_code=303)
        return await call_next(request)

    @app.exception_handler(RequestValidationError)
    async def gecersiz_adres(request: Request, hata: RequestValidationError):
        """Adresteki bozuk degerler icin ham JSON yerine Turkce sayfa.

        Ekranlardaki baglantilar ve formlar bu duruma dusmez; bu yalnizca
        adres cubugu elle duzenlendiginde devreye girer.
        """
        return render(
            request,
            "invalid_request.html",
            status_code=400,
        )

    @app.get("/saglik")
    async def health():
        return {"status": "ok"}

    @app.get(LOGIN_PATH, response_class=HTMLResponse)
    async def login_form(request: Request):
        if request.session.get("auth"):
            return RedirectResponse("/", status_code=303)
        return render(request, "login.html", error=None)

    @app.post(LOGIN_PATH, response_class=HTMLResponse)
    async def login(request: Request, password: str = Form(...)):
        client = request.client.host if request.client else "bilinmeyen"
        if _is_locked(client):
            return render(
                request,
                "login.html",
                status_code=429,
                error="Çok fazla hatalı deneme. Bir dakika sonra tekrar deneyin.",
            )
        if security.verify_password(password, config.password_hash()):
            _failed_attempts.pop(client, None)
            request.session["auth"] = True
            return RedirectResponse("/", status_code=303)
        _record_failure(client)
        return render(request, "login.html", status_code=401, error="Parola hatalı.")

    @app.post("/cikis")
    async def logout(request: Request):
        request.session.clear()
        return RedirectResponse(LOGIN_PATH, status_code=303)

    app.include_router(dashboard.router)
    app.include_router(definitions.router)
    app.include_router(readings.router)
    app.include_router(production.router)
    app.include_router(direct.router)
    app.include_router(targets.router)
    app.include_router(reports.router)

    # Oturum ara katmani en son eklenir; boylece en distaki katman olur ve
    # yukaridaki giris kontrolu request.session'a erisebilir.
    app.add_middleware(
        SessionMiddleware,
        secret_key=config.secret_key(),
        session_cookie="enerji_oturum",
        https_only=config.secure_cookie(),
        same_site="lax",
        max_age=60 * 60 * 12,
    )
    return app


app = create_app()
