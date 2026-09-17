"""Dogrudan tuketim girisi (ornegin faturadan).

Sayac endeksi hesaplanmaz: donemin tuketimi dogrudan girilir. Kayit fabrika
seviyesindedir (bolumu yoktur) ve enerji turunun kendi biriminde tutulur.

Fabrika toplaminda dogrudan tuketimin sayac tuketimine gore onceligi
calc.factory_consumptions icinde uygulanir; bu modul yalnizca veri girisidir.
"""

from datetime import date

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db import get_session
from app.models import DirectConsumption, EnergyType
from app.web import (
    flash,
    month_label,
    parse_id,
    optional_text,
    parse_number,
    parse_year_month,
    render,
)

router = APIRouter(prefix="/dogrudan-tuketim")

RECENT_LIMIT = 50


def _period_start(year_month: str) -> date:
    """'2026-01' -> 2026-01-01 (kayitlar her zaman ayin ilk gununde tutulur)."""
    year, month = (int(part) for part in year_month.split("-"))
    return date(year, month, 1)


def _current_period() -> str:
    return date.today().strftime("%Y-%m")


def _page_context(db: Session) -> dict:
    records = db.scalars(
        select(DirectConsumption)
        .options(joinedload(DirectConsumption.energy_type))
        .order_by(DirectConsumption.period_date.desc(), DirectConsumption.id.desc())
        .limit(RECENT_LIMIT)
    )
    return {
        "energy_types": list(
            db.scalars(
                select(EnergyType)
                .where(EnergyType.is_active.is_(True))
                .order_by(EnergyType.id)
            )
        ),
        "records": [
            {"record": record, "label": month_label(record.period_date.strftime("%Y-%m"))}
            for record in records
        ],
        "today_period": _current_period(),
    }


def _read_form(db: Session, year_month: str, energy_type_id: str, quantity: str) -> dict:
    month = parse_year_month(year_month, "Ay")
    if month > _current_period():
        raise ValueError(
            "Gelecek ay için tüketim girilemez "
            f"(içinde bulunulan ay: {month_label(_current_period())})."
        )

    energy_type = db.get(EnergyType, parse_id(energy_type_id, "Enerji türü"))
    if energy_type is None:
        raise ValueError("Seçilen enerji türü bulunamadı.")
    if not energy_type.is_active:
        raise ValueError(
            f"'{energy_type.name}' pasif bir enerji türü. Pasif türlere yeni "
            "tüketim girilemez."
        )

    amount = parse_number(quantity, "Tüketim miktarı")
    if amount <= 0:
        raise ValueError("Tüketim miktarı sıfırdan büyük olmalıdır.")

    period_date = _period_start(month)
    existing = db.scalars(
        select(DirectConsumption).where(
            DirectConsumption.period_date == period_date,
            DirectConsumption.energy_type_id == energy_type.id,
        )
    ).first()
    if existing is not None:
        raise ValueError(
            f"{month_label(month)} ayı için '{energy_type.name}' doğrudan tüketimi "
            "zaten girilmiş. Bir ay ve enerji türü için tek kayıt tutulur."
        )

    return {
        "period_date": period_date,
        "energy_type_id": energy_type.id,
        "quantity": amount,
    }


@router.get("")
def direct_consumption(request: Request, db: Session = Depends(get_session)):
    return render(request, "direct.html", db, **_page_context(db))


@router.post("/{record_id}/sil")
def delete_direct_consumption(
    request: Request, record_id: int, db: Session = Depends(get_session)
):
    """Kayit silinince o ay icin yeniden sayac tuketimi kullanilmaya baslar."""
    record = db.get(DirectConsumption, record_id)
    if record is None:
        return render(
            request, "not_found.html", db, status_code=404, what="Doğrudan tüketim"
        )

    label = month_label(record.period_date.strftime("%Y-%m"))
    name = record.energy_type.name
    db.delete(record)
    db.commit()
    flash(request, f"{label} · {name} doğrudan tüketim kaydı silindi.")
    return RedirectResponse("/dogrudan-tuketim", status_code=303)


@router.post("")
def create_direct_consumption(
    request: Request,
    year_month: str = Form(""),
    energy_type_id: str = Form(""),
    quantity: str = Form(""),
    note: str = Form(""),
    db: Session = Depends(get_session),
):
    try:
        values = _read_form(db, year_month, energy_type_id, quantity)
    except ValueError as error:
        return render(
            request,
            "direct.html",
            db,
            status_code=400,
            error=str(error),
            form={
                "year_month": year_month,
                "energy_type_id": energy_type_id,
                "quantity": quantity,
                "note": note,
            },
            **_page_context(db),
        )

    db.add(DirectConsumption(**values, note=optional_text(note, "Not", 500)))
    db.commit()
    flash(
        request,
        f"{month_label(values['period_date'].strftime('%Y-%m'))} doğrudan tüketimi "
        "kaydedildi.",
    )
    return RedirectResponse("/dogrudan-tuketim", status_code=303)
