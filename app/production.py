"""Uretim verisi girisi.

Uretim kaydi sade tutulur: tarih, miktar ve birim. Ayni tarih ve ayni birim
icin tek kayit bulunur; boylece ayni uretim yanlislikla iki kez girilmez.
Farkli birimler (ton, adet, m3) hicbir zaman birbirine toplanmaz.
"""

from datetime import date

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Production
from app.web import flash, parse_date, parse_number, render, required_text

router = APIRouter(prefix="/uretim")

RECENT_LIMIT = 50


def _known_units(db: Session) -> list[str]:
    """Daha once kullanilmis uretim birimleri (yazim bicimi korunur)."""
    seen: dict[str, str] = {}
    for unit in db.scalars(select(Production.unit)):
        seen.setdefault(unit.casefold(), unit)
    return sorted(seen.values(), key=str.casefold)


def _normalised_unit(db: Session, unit: str) -> str:
    """Ayni birimin farkli yazimlarini tek yazima baglar: 'Ton' -> 'ton'."""
    for known in _known_units(db):
        if known.casefold() == unit.casefold():
            return known
    return unit


def _records(db: Session) -> list[Production]:
    return list(
        db.scalars(
            select(Production)
            .order_by(Production.production_date.desc(), Production.id.desc())
            .limit(RECENT_LIMIT)
        )
    )


def _read_form(db: Session, production_date: str, quantity: str, unit: str) -> dict:
    on_date = parse_date(production_date, "Tarih")
    if on_date > date.today():
        raise ValueError(
            "Üretim tarihi bugünden ileri olamaz "
            f"(bugün: {date.today().strftime('%d.%m.%Y')})."
        )

    amount = parse_number(quantity, "Üretim miktarı")
    if amount <= 0:
        raise ValueError("Üretim miktarı sıfırdan büyük olmalıdır.")

    clean_unit = _normalised_unit(db, required_text(unit, "Birim", 20))

    existing = db.scalars(
        select(Production).where(
            Production.production_date == on_date,
            Production.unit == clean_unit,
        )
    ).first()
    if existing is not None:
        raise ValueError(
            f"{on_date.strftime('%d.%m.%Y')} tarihinde '{clean_unit}' birimi için "
            "zaten bir üretim kaydı var. Aynı gün ve birim için tek kayıt tutulur."
        )

    return {"production_date": on_date, "quantity": amount, "unit": clean_unit}


@router.get("")
def production(request: Request, db: Session = Depends(get_session)):
    return render(
        request,
        "production.html",
        db,
        records=_records(db),
        units=_known_units(db),
        today=date.today().isoformat(),
    )


@router.post("")
def create_production(
    request: Request,
    production_date: str = Form(""),
    quantity: str = Form(""),
    unit: str = Form(""),
    db: Session = Depends(get_session),
):
    try:
        values = _read_form(db, production_date, quantity, unit)
    except ValueError as error:
        return render(
            request,
            "production.html",
            db,
            status_code=400,
            error=str(error),
            records=_records(db),
            units=_known_units(db),
            today=date.today().isoformat(),
            form={
                "production_date": production_date,
                "quantity": quantity,
                "unit": unit,
            },
        )

    db.add(Production(**values))
    db.commit()
    flash(
        request,
        f"{values['production_date'].strftime('%d.%m.%Y')} tarihli üretim kaydedildi.",
    )
    return RedirectResponse("/uretim", status_code=303)
