"""Gosterge paneli.

Burada hicbir tuketim hesabi yeniden yazilmaz; butun rakamlar calc modulunden
gelir. Bu dosyanin isi, calc sonuclarini ekranda gosterilecek hale getirmektir.

Bolum dagilimi kurali (5. asamada kararlastirildi):
  Fabrika toplami      -> ana sayac kurali (calc.factory_consumptions)
  Bolum dagilimi       -> bolume bagli alt sayaclar
  Olculmeyen / dagitilmamis -> fabrika toplami - bolum alt sayaclari toplami
Bu fark negatif cikarsa normal tuketim gibi gosterilmez; olcum kapsami uyarisi
olarak gosterilir.
"""

from calendar import monthrange
from datetime import date

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import calc
from app.db import get_session
from app.models import EnergyType, Meter, Settings, Target
from app.web import render

router = APIRouter()

TREND_MONTHS = 12


# --------------------------------------------------------------------------- #
# Donem yardimcilari
# --------------------------------------------------------------------------- #


def month_bounds(year_month: str) -> tuple[date, date]:
    """'2026-02' -> (2026-02-01, 2026-02-28)"""
    year, month = (int(part) for part in year_month.split("-"))
    return date(year, month, 1), date(year, month, monthrange(year, month)[1])


def shift_month(year_month: str, months: int) -> str:
    year, month = (int(part) for part in year_month.split("-"))
    index = year * 12 + (month - 1) + months
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def month_label(year_month: str) -> str:
    names = [
        "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
        "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
    ]
    year, month = (int(part) for part in year_month.split("-"))
    return f"{names[month - 1]} {year}"


def _valid_month(raw: str | None) -> str:
    try:
        month_bounds(raw or "")
    except (ValueError, IndexError):
        return date.today().strftime("%Y-%m")
    return raw


# --------------------------------------------------------------------------- #
# Veri toplama
# --------------------------------------------------------------------------- #


def department_meter_ids(db: Session, energy_type_id: int) -> list[int]:
    """Bolum dagiliminda kullanilacak sayaclar: bolume bagli alt sayaclar."""
    return list(
        db.scalars(
            select(Meter.id).where(
                Meter.energy_type_id == energy_type_id,
                Meter.is_main.is_(False),
                Meter.department_id.is_not(None),
            )
        )
    )


def _change(current: float, previous: float) -> dict | None:
    """Onceki doneme gore fark. Onceki donem sifirsa yuzde hesaplanmaz."""
    difference = current - previous
    return {
        "previous": previous,
        "difference": difference,
        "percent": (difference / previous * 100) if previous else None,
    }


def energy_summary(db: Session, energy_type: EnergyType, year_month: str) -> dict:
    """Bir enerji turu icin secilen donemin ozeti."""
    start, end = month_bounds(year_month)
    entries = calc.factory_consumptions(
        db, start=start, end=end, energy_type_id=energy_type.id
    )
    total = calc.total(entries)

    previous_month = shift_month(year_month, -1)
    previous_start, previous_end = month_bounds(previous_month)
    previous_total = calc.total(
        calc.factory_consumptions(
            db, start=previous_start, end=previous_end, energy_type_id=energy_type.id
        )
    )

    target = db.scalars(
        select(Target).where(
            Target.year_month == year_month,
            Target.energy_type_id == energy_type.id,
        )
    ).first()

    return {
        "energy_type": energy_type,
        "total": total,
        "cost": total * energy_type.unit_price,
        "change": _change(total, previous_total),
        "previous_label": month_label(previous_month),
        "target": (
            {
                "value": target.target_value,
                "percent": (total / target.target_value * 100)
                if target.target_value
                else None,
                "exceeded": total > target.target_value,
            }
            if target
            else None
        ),
    }


def department_breakdown(
    db: Session, energy_type: EnergyType, year_month: str, factory_total: float
) -> dict:
    """Bolum dagilimi ve olculmeyen pay."""
    start, end = month_bounds(year_month)
    entries = calc.consumptions(
        db,
        start=start,
        end=end,
        meter_ids=department_meter_ids(db, energy_type.id),
    )
    departments = calc.group_by_department(entries)
    measured = calc.total(entries)
    unmeasured = factory_total - measured

    rows = [
        {"label": label, "value": value, "measured": True}
        for label, value in departments.items()
    ]
    # Olculmeyen pay yalnizca anlamliysa gosterilir.
    if unmeasured > 0:
        rows.append(
            {"label": "Ölçülmeyen / dağıtılmamış", "value": unmeasured, "measured": False}
        )

    largest = max((row["value"] for row in rows), default=0)
    for row in rows:
        row["ratio"] = (row["value"] / largest * 100) if largest > 0 else 0
        row["share"] = (row["value"] / factory_total * 100) if factory_total else None

    return {
        "rows": rows,
        "measured": measured,
        "unmeasured": unmeasured,
        # Negatif fark = bolum sayaclari fabrika toplamindan fazla olcuyor.
        "scope_warning": unmeasured < 0,
    }


def monthly_trend(db: Session, energy_type: EnergyType, year_month: str) -> list[dict]:
    """Secilen ay dahil son 12 ayin fabrika tuketimi."""
    first_month = shift_month(year_month, -(TREND_MONTHS - 1))
    start, _ = month_bounds(first_month)
    _, end = month_bounds(year_month)

    totals = calc.group_by_period(
        calc.factory_consumptions(
            db, start=start, end=end, energy_type_id=energy_type.id
        ),
        calc.PERIOD_MONTH,
    )

    months = [shift_month(first_month, offset) for offset in range(TREND_MONTHS)]
    values = [totals.get(month, 0.0) for month in months]
    largest = max(values, default=0)
    return [
        {
            "month": month,
            "label": month_label(month),
            "short": month_label(month).split(" ")[0][:3],
            "value": value,
            "ratio": (value / largest * 100) if largest > 0 else 0,
            "selected": month == year_month,
        }
        for month, value in zip(months, values)
    ]


# --------------------------------------------------------------------------- #
# Rota
# --------------------------------------------------------------------------- #


@router.get("/")
def dashboard(
    request: Request,
    donem: str | None = None,
    enerji: int | None = None,
    db: Session = Depends(get_session),
):
    year_month = _valid_month(donem)
    # Tanim sirasi korunur: ilk tanimlanan enerji turu varsayilan secimdir.
    energy_types = list(db.scalars(select(EnergyType).order_by(EnergyType.id)))

    if not energy_types:
        return render(request, "dashboard.html", db, year_month=year_month)

    selected = next(
        (item for item in energy_types if item.id == enerji), energy_types[0]
    )
    summary = energy_summary(db, selected, year_month)
    settings = db.get(Settings, 1)

    return render(
        request,
        "dashboard.html",
        db,
        year_month=year_month,
        month_label=month_label(year_month),
        energy_types=energy_types,
        selected_energy=selected,
        summary=summary,
        breakdown=department_breakdown(db, selected, year_month, summary["total"]),
        trend=monthly_trend(db, selected, year_month),
        currency=settings.currency if settings else "TL",
        all_summaries=[
            energy_summary(db, energy_type, year_month) for energy_type in energy_types
        ],
    )
