"""Sayac okuma girisi.

Burada yalnizca ham endeks kaydedilir. Tuketim hesabi bu ekranda yapilmaz;
okumalardan tuketim uretme mantigi hesaplama modulunde olacaktir.
"""

from datetime import date

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.db import get_session
from app.models import Meter, MeterReading
from app.web import (
    flash,
    format_number,
    optional_text,
    parse_date,
    parse_number,
    render,
)

router = APIRouter(prefix="/okumalar")

# Listede gosterilecek en fazla kayit sayisi.
RECENT_LIMIT = 50
METER_HISTORY_LIMIT = 200


def _active_meters(db: Session) -> list[Meter]:
    return list(
        db.scalars(
            select(Meter)
            .where(Meter.is_active.is_(True))
            .order_by(func.lower(Meter.name))
        )
    )


def _last_reading(db: Session, meter_id: int) -> MeterReading | None:
    """Sayacin en son (en yeni tarihli) okumasi."""
    return db.scalars(
        select(MeterReading)
        .where(MeterReading.meter_id == meter_id)
        .order_by(MeterReading.reading_date.desc(), MeterReading.id.desc())
        .limit(1)
    ).first()


def _neighbour_readings(
    db: Session, meter_id: int, on_date: date
) -> tuple[MeterReading | None, MeterReading | None]:
    """Verilen tarihin hemen oncesindeki ve sonrasindaki okumalar."""
    previous = db.scalars(
        select(MeterReading)
        .where(MeterReading.meter_id == meter_id, MeterReading.reading_date < on_date)
        .order_by(MeterReading.reading_date.desc())
        .limit(1)
    ).first()
    following = db.scalars(
        select(MeterReading)
        .where(MeterReading.meter_id == meter_id, MeterReading.reading_date > on_date)
        .order_by(MeterReading.reading_date)
        .limit(1)
    ).first()
    return previous, following


def _page_context(db: Session, selected_meter_id: int | None) -> dict:
    """Okuma ekraninin sabit parcalari: sayac listesi, son endeksler, kayitlar."""
    meters = _active_meters(db)
    last_readings = {meter.id: _last_reading(db, meter.id) for meter in meters}

    query = (
        select(MeterReading)
        .options(joinedload(MeterReading.meter))
        .order_by(MeterReading.reading_date.desc(), MeterReading.id.desc())
    )
    selected_meter = db.get(Meter, selected_meter_id) if selected_meter_id else None
    if selected_meter is not None:
        query = query.where(MeterReading.meter_id == selected_meter.id).limit(
            METER_HISTORY_LIMIT
        )
    else:
        query = query.limit(RECENT_LIMIT)

    return {
        "meters": meters,
        # Gecmis filtresinde pasif sayaclar da secilebilir; yeni okuma girisinde
        # yalnizca aktif sayaclar listelenir.
        "all_meters": list(
            db.scalars(select(Meter).order_by(func.lower(Meter.name)))
        ),
        "last_readings": last_readings,
        "readings": list(db.scalars(query)),
        "selected_meter": selected_meter,
        "today": date.today().isoformat(),
    }


def _read_form(
    db: Session, meter_id: str, reading_date: str, index_value: str, note: str
) -> dict:
    if not (meter_id or "").strip():
        raise ValueError("Sayaç seçilmelidir.")
    meter = db.get(Meter, int(meter_id))
    if meter is None:
        raise ValueError("Seçilen sayaç bulunamadı.")
    if not meter.is_active:
        raise ValueError(
            f"'{meter.name}' pasif bir sayaç. Pasif sayaçlara yeni okuma girilemez."
        )

    on_date = parse_date(reading_date, "Tarih")
    value = parse_number(index_value, "Endeks")
    if value < 0:
        raise ValueError("Endeks negatif olamaz.")

    existing = db.scalars(
        select(MeterReading).where(
            MeterReading.meter_id == meter.id,
            MeterReading.reading_date == on_date,
        )
    ).first()
    if existing is not None:
        raise ValueError(
            f"'{meter.name}' için {on_date.strftime('%d.%m.%Y')} tarihinde "
            "zaten bir okuma var. Aynı gün için ikinci okuma girilemez."
        )

    previous, following = _neighbour_readings(db, meter.id, on_date)
    if previous is not None and value < previous.index_value:
        raise ValueError(
            f"Endeks, {previous.reading_date.strftime('%d.%m.%Y')} tarihli "
            f"önceki okumadan ({format_number(previous.index_value)}) küçük olamaz. "
            "Sayaç değiştiyse veya sıfırlandıysa bunu birlikte ele alalım."
        )
    if following is not None and value > following.index_value:
        raise ValueError(
            f"Endeks, {following.reading_date.strftime('%d.%m.%Y')} tarihli "
            f"sonraki okumadan ({format_number(following.index_value)}) büyük olamaz."
        )

    return {
        "meter_id": meter.id,
        "reading_date": on_date,
        "index_value": value,
        "note": optional_text(note, "Açıklama", 500),
    }


@router.get("")
def readings(
    request: Request, sayac: int | None = None, db: Session = Depends(get_session)
):
    return render(request, "readings.html", db, **_page_context(db, sayac))


@router.post("")
def create_reading(
    request: Request,
    meter_id: str = Form(""),
    reading_date: str = Form(""),
    index_value: str = Form(""),
    note: str = Form(""),
    db: Session = Depends(get_session),
):
    try:
        values = _read_form(db, meter_id, reading_date, index_value, note)
    except ValueError as error:
        selected = int(meter_id) if (meter_id or "").strip().isdigit() else None
        return render(
            request,
            "readings.html",
            db,
            status_code=400,
            error=str(error),
            form={
                "meter_id": meter_id,
                "reading_date": reading_date,
                "index_value": index_value,
                "note": note,
            },
            **_page_context(db, selected),
        )

    db.add(MeterReading(**values))
    db.commit()
    flash(
        request,
        f"{values['reading_date'].strftime('%d.%m.%Y')} tarihli okuma kaydedildi.",
    )
    return RedirectResponse(f"/okumalar?sayac={values['meter_id']}", status_code=303)
