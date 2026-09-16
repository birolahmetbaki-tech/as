"""Aylik enerji tuketim hedefleri.

Hedef: ay + enerji turu + hedef tuketim. Ayni ay ve ayni enerji turu icin tek
hedef bulunur. Hedefler ileriye donuk belirlendigi icin gelecek aylar serbesttir.

Hedefe gore durum hesabi burada degil, calc.target_status icinde yapilir.
"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.db import get_session
from app.models import EnergyType, Target
from app.web import flash, month_label, parse_number, parse_year_month, render

router = APIRouter(prefix="/hedefler")


def _page_context(db: Session) -> dict:
    return {
        "energy_types": list(
            db.scalars(
                select(EnergyType)
                .where(EnergyType.is_active.is_(True))
                .order_by(EnergyType.id)
            )
        ),
        "targets": [
            {"record": record, "label": month_label(record.year_month)}
            for record in db.scalars(
                select(Target)
                .options(joinedload(Target.energy_type))
                .order_by(Target.year_month.desc(), func.lower(EnergyType.name))
                .join(EnergyType)
            )
        ],
    }


def _read_form(
    db: Session,
    year_month: str,
    energy_type_id: str,
    value: str,
    exclude_id: int | None = None,
) -> dict:
    month = parse_year_month(year_month, "Ay")

    if not (energy_type_id or "").strip():
        raise ValueError("Enerji türü seçilmelidir.")
    energy_type = db.get(EnergyType, int(energy_type_id))
    if energy_type is None:
        raise ValueError("Seçilen enerji türü bulunamadı.")

    target_value = parse_number(value, "Hedef tüketim")
    if target_value <= 0:
        raise ValueError("Hedef tüketim sıfırdan büyük olmalıdır.")

    query = select(Target).where(
        Target.year_month == month,
        Target.energy_type_id == energy_type.id,
    )
    if exclude_id is not None:
        query = query.where(Target.id != exclude_id)
    existing = db.scalars(query).first()
    if existing is not None:
        raise ValueError(
            f"{month_label(month)} ayı için '{energy_type.name}' hedefi zaten "
            "tanımlı. Bir ay ve enerji türü için tek hedef tutulur."
        )

    return {
        "year_month": month,
        "energy_type_id": energy_type.id,
        "target_value": target_value,
    }


@router.get("")
def targets(request: Request, db: Session = Depends(get_session)):
    return render(request, "targets.html", db, **_page_context(db))


@router.post("")
def create_target(
    request: Request,
    year_month: str = Form(""),
    energy_type_id: str = Form(""),
    target_value: str = Form(""),
    db: Session = Depends(get_session),
):
    try:
        values = _read_form(db, year_month, energy_type_id, target_value)
    except ValueError as error:
        return render(
            request,
            "targets.html",
            db,
            status_code=400,
            error=str(error),
            form={
                "year_month": year_month,
                "energy_type_id": energy_type_id,
                "target_value": target_value,
            },
            **_page_context(db),
        )

    db.add(Target(**values))
    db.commit()
    flash(request, f"{month_label(values['year_month'])} hedefi kaydedildi.")
    return RedirectResponse("/hedefler", status_code=303)


@router.get("/{target_id}")
def edit_target_form(
    request: Request, target_id: int, db: Session = Depends(get_session)
):
    target = db.get(Target, target_id)
    if target is None:
        return render(request, "not_found.html", db, status_code=404, what="Hedef")
    return render(request, "target_edit.html", db, target=target, **_page_context(db))


@router.post("/{target_id}")
def edit_target(
    request: Request,
    target_id: int,
    year_month: str = Form(""),
    energy_type_id: str = Form(""),
    target_value: str = Form(""),
    db: Session = Depends(get_session),
):
    """Yanlis girilen hedefi duzeltir. Panel ve raporlar guncel hedefi kullanir."""
    target = db.get(Target, target_id)
    if target is None:
        return render(request, "not_found.html", db, status_code=404, what="Hedef")
    try:
        values = _read_form(
            db, year_month, energy_type_id, target_value, exclude_id=target_id
        )
    except ValueError as error:
        return render(
            request,
            "target_edit.html",
            db,
            status_code=400,
            target=target,
            error=str(error),
            form={
                "year_month": year_month,
                "energy_type_id": energy_type_id,
                "target_value": target_value,
            },
            **_page_context(db),
        )

    for field, value in values.items():
        setattr(target, field, value)
    db.commit()
    flash(request, f"{month_label(target.year_month)} hedefi güncellendi.")
    return RedirectResponse("/hedefler", status_code=303)


@router.post("/{target_id}/sil")
def delete_target(request: Request, target_id: int, db: Session = Depends(get_session)):
    target = db.get(Target, target_id)
    if target is None:
        return render(request, "not_found.html", db, status_code=404, what="Hedef")

    label = month_label(target.year_month)
    name = target.energy_type.name
    db.delete(target)
    db.commit()
    flash(request, f"{label} · {name} hedefi silindi.")
    return RedirectResponse("/hedefler", status_code=303)
