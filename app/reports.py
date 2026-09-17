"""Rapor ekrani.

Rapor yeni bir hesaplama sistemi degildir: butun tuketim, maliyet ve EnPI
degerleri calc modulunden gelir. Bolum kirilimi, panelde kullanilan
dashboard.department_breakdown kuralinin aynisini kullanir; boylece ana
sayaclar bolum raporunda ikinci kez sayilmaz.
"""

from datetime import date

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app import calc
from app.dashboard import department_breakdown, month_bounds, shift_month
from app.db import get_session
from app.models import EnergyType, Meter, Settings, Target
from app.web import month_label, parse_date, render, source_label

router = APIRouter(prefix="/rapor")

BREAKDOWNS = {
    "enerji": "Enerji türü",
    "sayac": "Sayaç",
    "bolum": "Bölüm",
}


def default_range() -> tuple[date, date]:
    """Varsayilan aralik: icinde bulunulan ayin basindan bugune."""
    today = date.today()
    return today.replace(day=1), today


def _energy_types(db: Session) -> list[EnergyType]:
    return list(db.scalars(select(EnergyType).order_by(EnergyType.id)))


def rows_by_energy_type(
    db: Session, start: date, end: date, totals: dict | None = None
) -> list[dict]:
    """Her enerji turunun fabrika tuketimi, kaynagi, esdegeri ve maliyeti.

    Ortak enerji birimindeki esdeger calc.energy_totals'tan gelir; rapor kendi
    donusumunu yapmaz. totals verilmezse GJ esdegeri hesaplanir.
    """
    if totals is None:
        totals = calc.energy_totals(db, start=start, end=end)
    conversions = {row["energy_type"].id: row for row in totals["rows"]}

    rows = []
    for energy_type in _energy_types(db):
        entries = calc.factory_consumptions(
            db, start=start, end=end, energy_type_id=energy_type.id
        )
        total = calc.total(entries)
        rows.append(
            {
                "energy_type": energy_type,
                "total": total,
                "cost": calc.cost(total, energy_type.unit_price),
                "source": source_label(entries),
                "conversion": conversions.get(energy_type.id),
            }
        )
    return rows


def rows_by_meter(db: Session, start: date, end: date) -> list[dict]:
    """Her sayacin kendi tuketimi.

    Ana ve alt sayaclar birlikte listelenir; bu yuzden tabloda genel toplam
    satiri gosterilmez (mukerrer sayim olurdu).
    """
    meters = db.scalars(
        select(Meter)
        .options(joinedload(Meter.energy_type), joinedload(Meter.department))
        .order_by(func.lower(Meter.name))
    )

    rows = []
    for meter in meters:
        entries = calc.meter_consumptions(db, meter.id, start=start, end=end)
        if not entries:
            continue
        total = calc.total(entries)
        rows.append(
            {
                "meter": meter,
                "total": total,
                "cost": calc.cost(total, meter.energy_type.unit_price),
            }
        )
    return rows


def rows_by_department(db: Session, start: date, end: date) -> list[dict]:
    """Enerji turu basina bolum dagilimi (panelle ayni kural)."""
    sections = []
    for energy_type in _energy_types(db):
        factory_total = calc.total(
            calc.factory_consumptions(
                db, start=start, end=end, energy_type_id=energy_type.id
            )
        )
        breakdown = department_breakdown(db, energy_type, start, end, factory_total)
        if factory_total == 0 and not breakdown["rows"]:
            continue
        sections.append(
            {
                "energy_type": energy_type,
                "factory_total": factory_total,
                "breakdown": breakdown,
            }
        )
    return sections


def production_rows(db: Session, start: date, end: date) -> list[dict]:
    """Uretim birimi x enerji turu icin uretim ve EnPI."""
    rows = []
    for unit in calc.production_units(db, start=start, end=end):
        produced = calc.production_total(db, unit, start=start, end=end)
        for energy_type in _energy_types(db):
            total = calc.total(
                calc.factory_consumptions(
                    db, start=start, end=end, energy_type_id=energy_type.id
                )
            )
            if total == 0:
                continue
            rows.append(
                {
                    "unit": unit,
                    "production": produced,
                    "energy_type": energy_type,
                    "total": total,
                    "enpi": calc.enpi(total, produced),
                }
            )
    return rows


def target_rows(db: Session, start: date, end: date) -> list[dict]:
    """Aralik icinde TAMAMEN yer alan aylarin hedefleri.

    Yarim kalan aylar raporlanmaz: yarim ayin tuketimini tam ayin hedefiyle
    karsilastirmak yaniltici olurdu.
    """
    months = []
    cursor = f"{start.year:04d}-{start.month:02d}"
    last = f"{end.year:04d}-{end.month:02d}"
    while cursor <= last:
        month_start, month_end = month_bounds(cursor)
        if month_start >= start and month_end <= end:
            months.append(cursor)
        cursor = shift_month(cursor, 1)

    rows = []
    for month in months:
        month_start, month_end = month_bounds(month)
        for target in db.scalars(
            select(Target)
            .options(joinedload(Target.energy_type))
            .where(Target.year_month == month)
            .join(EnergyType)
            .order_by(EnergyType.id)
        ):
            actual = calc.total(
                calc.factory_consumptions(
                    db,
                    start=month_start,
                    end=month_end,
                    energy_type_id=target.energy_type_id,
                )
            )
            rows.append(
                {
                    "label": month_label(month),
                    "energy_type": target.energy_type,
                    "status": calc.target_status(actual, target.target_value),
                }
            )
    return rows


@router.get("")
def report(
    request: Request,
    baslangic: str | None = None,
    bitis: str | None = None,
    kirilim: str = "enerji",
    enerji_birimi: str | None = None,
    db: Session = Depends(get_session),
):
    default_start, default_end = default_range()
    error = None
    try:
        start = parse_date(baslangic, "Başlangıç tarihi") if baslangic else default_start
        end = parse_date(bitis, "Bitiş tarihi") if bitis else default_end
        if start > end:
            raise ValueError("Başlangıç tarihi bitiş tarihinden sonra olamaz.")
    except ValueError as validation_error:
        error = str(validation_error)
        start, end = default_start, default_end

    breakdown = kirilim if kirilim in BREAKDOWNS else "enerji"
    energy_unit = (
        enerji_birimi
        if enerji_birimi in calc.DISPLAY_ENERGY_UNITS
        else calc.REFERENCE_ENERGY_UNIT
    )
    settings = db.get(Settings, 1)
    # Panelde kullanilan islevin aynisi: iki ekran ayni sayiyi gosterir.
    energy_totals = calc.energy_totals(db, start=start, end=end, to_unit=energy_unit)

    return render(
        request,
        "report.html",
        db,
        error=error,
        start=start,
        end=end,
        breakdown=breakdown,
        breakdowns=BREAKDOWNS,
        currency=settings.currency if settings else "TL",
        energy_unit=energy_unit,
        energy_units=calc.DISPLAY_ENERGY_UNITS,
        energy_totals=energy_totals,
        energy_rows=(
            rows_by_energy_type(db, start, end, energy_totals)
            if breakdown == "enerji"
            else []
        ),
        meter_rows=rows_by_meter(db, start, end) if breakdown == "sayac" else [],
        department_sections=(
            rows_by_department(db, start, end) if breakdown == "bolum" else []
        ),
        production_rows=production_rows(db, start, end),
        target_rows=target_rows(db, start, end),
        conflicts=calc.consumption_conflicts(db, start=start, end=end),
    )
