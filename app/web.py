"""Sayfa olusturma icin ortak yardimcilar: sablonlar, bildirimler, sayi/tarih bicimi."""

import re
from datetime import date
from pathlib import Path

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.calc import SOURCE_DIRECT
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


# Binlik ayracli yazim: 1.000 / 12.500 / 1.234.567 (basta sifir olamaz).
_THOUSANDS = re.compile(r"^-?[1-9]\d{0,2}(\.\d{3})+$")
# Cozumlemeden sonra kabul edilen son bicim.
_PLAIN_NUMBER = re.compile(r"^-?\d+(\.\d+)?$")


def parse_number(raw: str | None, field_label: str) -> float:
    """Metni sayiya cevirir; Turkce yazim bicimini dogru yorumlar.

    1.000      -> 1000      (nokta binlik ayraci)
    1.250,50   -> 1250.5    (ekranda gosterilen bicim)
    1250,5     -> 1250.5
    1250.5     -> 1250.5    (nokta ondalik ayraci)
    0,5 / 0.5  -> 0.5

    Nokta yalnizca ucer basamakli gruplari ayirdiginda binlik ayraci sayilir;
    diger durumlarda ondalik ayracidir. Tanimsiz bicimler sessizce cevrilmez,
    hata verilir.
    """
    text = (raw or "").strip().replace(" ", "").replace("\u00a0", "")
    if not text:
        raise ValueError(f"{field_label} alanı boş bırakılamaz.")

    if "," in text and "." in text:
        # Sonda gelen isaret ondalik ayracidir, digeri binlik ayracidir.
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(",", ".")
    elif _THOUSANDS.match(text):
        text = text.replace(".", "")

    if not _PLAIN_NUMBER.match(text):
        raise ValueError(
            f"{field_label} sayı olmalıdır (örnek: 1.250,50 veya 1250,5)."
        )
    return float(text)


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


def source_label(entries: list) -> str:
    """Tuketim kayitlarinin hangi kaynaktan geldigini yazar.

    Ayni AYDA iki kaynak birden bulunursa o ay dogrudan tuketimle temsil
    edilir; "Karisik" yalnizca farkli aylarin farkli kaynaktan gelmesi
    durumunda ortaya cikar.
    """
    sources = {entry.source for entry in entries}
    if not sources:
        return "—"
    if len(sources) > 1:
        return "Karışık"
    return "Doğrudan" if SOURCE_DIRECT in sources else "Sayaç"


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


MONTH_NAMES = (
    "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
)


def month_label(year_month: str) -> str:
    """'2026-01' -> 'Ocak 2026'"""
    year, month = (int(part) for part in year_month.split("-"))
    return f"{MONTH_NAMES[month - 1]} {year}"


# Sablonlarda ay adini yazdirmak icin: {{ ay_adi("2026-01") }}
templates.env.globals["ay_adi"] = month_label


def parse_id(raw: str | None, field_label: str) -> int:
    """Formdan gelen kayit numarasini cozer.

    Ekranlarda bu alanlar <select> ile doldurulur; buraya sayi disinda bir sey
    gelmesi ancak istek elle bozulursa olur. Yine de kullaniciya Python'un
    ham hata metni degil, Turkce ve sade bir mesaj gosterilir.
    """
    text = (raw or "").strip()
    if not text:
        raise ValueError(f"{field_label} seçilmelidir.")
    try:
        return int(text)
    except ValueError:
        raise ValueError(f"Geçersiz {field_label.lower()} seçimi.") from None


def parse_year_month(raw: str | None, field_label: str) -> str:
    """Ay metnini dogrular ve 'YYYY-MM' bicimine getirir."""
    text = (raw or "").strip()
    if not text:
        raise ValueError(f"{field_label} alanı boş bırakılamaz.")
    try:
        year, month = (int(part) for part in text.split("-"))
        if not (1 <= month <= 12 and 2000 <= year <= 2100):
            raise ValueError
    except ValueError:
        raise ValueError(
            f"{field_label} geçerli bir ay olmalıdır (örnek: 2026-01)."
        ) from None
    return f"{year:04d}-{month:02d}"
