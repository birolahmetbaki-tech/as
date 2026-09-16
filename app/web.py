"""Sayfa olusturma icin ortak yardimcilar: sablonlar, bildirimler, sayi/tarih bicimi."""

from datetime import date
from pathlib import Path

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.models import Settings

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def format_number(value: float | int | None, decimals: int = 2) -> str:
    """Sayiyi Turkce bicimde yazar: 1.234,50"""
    if value is None:
        return ""
    text = f"{float(value):,.{decimals}f}"
    return text.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


templates.env.filters["sayi"] = format_number


def parse_number(raw: str | None, field_label: str) -> float:
    """Metni sayiya cevirir. Virgul de ondalik ayraci olarak kabul edilir."""
    text = (raw or "").strip().replace(" ", "").replace(",", ".")
    if not text:
        raise ValueError(f"{field_label} alanı boş bırakılamaz.")
    try:
        return float(text)
    except ValueError:
        raise ValueError(f"{field_label} sayı olmalıdır.") from None


def required_text(raw: str | None, field_label: str, max_length: int) -> str:
    text = (raw or "").strip()
    if not text:
        raise ValueError(f"{field_label} alanı boş bırakılamaz.")
    if len(text) > max_length:
        raise ValueError(f"{field_label} en fazla {max_length} karakter olabilir.")
    return text


def optional_text(raw: str | None, field_label: str, max_length: int) -> str | None:
    text = (raw or "").strip()
    if not text:
        return None
    if len(text) > max_length:
        raise ValueError(f"{field_label} en fazla {max_length} karakter olabilir.")
    return text


def flash(request: Request, message: str) -> None:
    """Yonlendirme sonrasi bir kez gosterilecek bilgi mesaji birakir."""
    request.session.setdefault("flash", []).append(message)


def render(
    request: Request,
    template_name: str,
    db: Session | None = None,
    status_code: int = 200,
    **context,
) -> HTMLResponse:
    settings = db.get(Settings, 1) if db is not None else None
    context.setdefault("factory_name", settings.factory_name if settings else "Fabrika")
    context["flash_messages"] = request.session.pop("flash", [])
    return templates.TemplateResponse(
        request, template_name, context, status_code=status_code
    )


def parse_date(raw: str | None, field_label: str) -> date:
    """Tarih metnini cozer. 2026-01-31 ve 31.01.2026 bicimleri kabul edilir."""
    text = (raw or "").strip()
    if not text:
        raise ValueError(f"{field_label} alanı boş bırakılamaz.")
    for parser in (date.fromisoformat, _parse_dotted_date):
        try:
            return parser(text)
        except ValueError:
            continue
    raise ValueError(f"{field_label} geçerli bir tarih olmalıdır (örnek: 31.01.2026).")


def _parse_dotted_date(text: str) -> date:
    day, month, year = (int(part) for part in text.split("."))
    return date(year, month, day)
