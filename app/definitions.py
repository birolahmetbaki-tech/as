"""Tanim ekranlari: bolum, enerji turu ve sayac.

Bu ekranlarin tek amaci sonraki asamadaki elle veri girisine saglam bir temel
hazirlamaktir. Kayitlar silinmez; kullanilmayan tanimlar pasife alinir.
"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Department, EnergyType, Meter
from app.web import flash, optional_text, parse_number, render, required_text

router = APIRouter(prefix="/tanimlar")


def _name_in_use(db: Session, model, name: str, exclude_id: int | None = None) -> bool:
    """Ayni isim (buyuk/kucuk harf farki gozetmeden) daha once kullanilmis mi?

    Karsilastirma Python tarafinda yapilir; SQLite'in lower() islevi yalnizca
    ASCII harfleri kucultur ve Turkce karakterlerde yanilir. Tanim tablolari
    kucuk oldugu icin bu yaklasim yeterlidir.
    """
    query = select(model.name)
    if exclude_id is not None:
        query = query.where(model.id != exclude_id)
    target = name.casefold()
    return any(existing.casefold() == target for existing in db.scalars(query))


def _active_first(model):
    return select(model).order_by(model.is_active.desc(), func.lower(model.name))


# --------------------------------------------------------------------------- #
# Bolum
# --------------------------------------------------------------------------- #


@router.get("/bolumler")
def departments(request: Request, db: Session = Depends(get_session)):
    return render(
        request,
        "departments.html",
        db,
        departments=db.scalars(_active_first(Department)).all(),
    )


@router.post("/bolumler")
def create_department(
    request: Request,
    name: str = Form(""),
    db: Session = Depends(get_session),
):
    try:
        clean_name = required_text(name, "Bölüm adı", 120)
        if _name_in_use(db, Department, clean_name):
            raise ValueError(f"'{clean_name}' adında bir bölüm zaten var.")
    except ValueError as error:
        return render(
            request,
            "departments.html",
            db,
            status_code=400,
            departments=db.scalars(_active_first(Department)).all(),
            error=str(error),
            form={"name": name},
        )

    db.add(Department(name=clean_name))
    db.commit()
    flash(request, f"'{clean_name}' bölümü eklendi.")
    return RedirectResponse("/tanimlar/bolumler", status_code=303)


@router.get("/bolumler/{department_id}")
def edit_department_form(
    request: Request, department_id: int, db: Session = Depends(get_session)
):
    department = db.get(Department, department_id)
    if department is None:
        return render(request, "not_found.html", db, status_code=404, what="Bölüm")
    return render(request, "department_edit.html", db, department=department)


@router.post("/bolumler/{department_id}")
def edit_department(
    request: Request,
    department_id: int,
    name: str = Form(""),
    is_active: str | None = Form(None),
    db: Session = Depends(get_session),
):
    department = db.get(Department, department_id)
    if department is None:
        return render(request, "not_found.html", db, status_code=404, what="Bölüm")
    try:
        clean_name = required_text(name, "Bölüm adı", 120)
        if _name_in_use(db, Department, clean_name, exclude_id=department_id):
            raise ValueError(f"'{clean_name}' adında başka bir bölüm zaten var.")
    except ValueError as error:
        return render(
            request,
            "department_edit.html",
            db,
            status_code=400,
            department=department,
            error=str(error),
            form={"name": name, "is_active": is_active is not None},
        )

    department.name = clean_name
    department.is_active = is_active is not None
    db.commit()
    flash(request, f"'{clean_name}' bölümü güncellendi.")
    return RedirectResponse("/tanimlar/bolumler", status_code=303)


# --------------------------------------------------------------------------- #
# Enerji turu
# --------------------------------------------------------------------------- #


@router.get("/enerji-turleri")
def energy_types(request: Request, db: Session = Depends(get_session)):
    return render(
        request,
        "energy_types.html",
        db,
        energy_types=db.scalars(_active_first(EnergyType)).all(),
    )


def _read_energy_type_form(
    db: Session, name: str, unit: str, unit_price: str, exclude_id: int | None = None
) -> dict:
    clean_name = required_text(name, "Enerji türü adı", 60)
    if _name_in_use(db, EnergyType, clean_name, exclude_id=exclude_id):
        raise ValueError(f"'{clean_name}' adında bir enerji türü zaten var.")
    price = parse_number(unit_price, "Birim fiyat")
    if price < 0:
        raise ValueError("Birim fiyat negatif olamaz.")
    return {
        "name": clean_name,
        "unit": required_text(unit, "Birim", 20),
        "unit_price": price,
    }


@router.post("/enerji-turleri")
def create_energy_type(
    request: Request,
    name: str = Form(""),
    unit: str = Form(""),
    unit_price: str = Form("0"),
    db: Session = Depends(get_session),
):
    try:
        values = _read_energy_type_form(db, name, unit, unit_price)
    except ValueError as error:
        return render(
            request,
            "energy_types.html",
            db,
            status_code=400,
            energy_types=db.scalars(_active_first(EnergyType)).all(),
            error=str(error),
            form={"name": name, "unit": unit, "unit_price": unit_price},
        )

    db.add(EnergyType(**values))
    db.commit()
    flash(request, f"'{values['name']}' enerji türü eklendi.")
    return RedirectResponse("/tanimlar/enerji-turleri", status_code=303)


@router.get("/enerji-turleri/{energy_type_id}")
def edit_energy_type_form(
    request: Request, energy_type_id: int, db: Session = Depends(get_session)
):
    energy_type = db.get(EnergyType, energy_type_id)
    if energy_type is None:
        return render(request, "not_found.html", db, status_code=404, what="Enerji türü")
    return render(request, "energy_type_edit.html", db, energy_type=energy_type)


@router.post("/enerji-turleri/{energy_type_id}")
def edit_energy_type(
    request: Request,
    energy_type_id: int,
    name: str = Form(""),
    unit: str = Form(""),
    unit_price: str = Form("0"),
    is_active: str | None = Form(None),
    db: Session = Depends(get_session),
):
    energy_type = db.get(EnergyType, energy_type_id)
    if energy_type is None:
        return render(request, "not_found.html", db, status_code=404, what="Enerji türü")
    try:
        values = _read_energy_type_form(
            db, name, unit, unit_price, exclude_id=energy_type_id
        )
    except ValueError as error:
        return render(
            request,
            "energy_type_edit.html",
            db,
            status_code=400,
            energy_type=energy_type,
            error=str(error),
            form={
                "name": name,
                "unit": unit,
                "unit_price": unit_price,
                "is_active": is_active is not None,
            },
        )

    for field, value in values.items():
        setattr(energy_type, field, value)
    energy_type.is_active = is_active is not None
    db.commit()
    flash(request, f"'{energy_type.name}' enerji türü güncellendi.")
    return RedirectResponse("/tanimlar/enerji-turleri", status_code=303)


# --------------------------------------------------------------------------- #
# Sayac
# --------------------------------------------------------------------------- #


def _meter_page_context(db: Session) -> dict:
    """Sayac formunda kullanilan secim listeleri."""
    return {
        "energy_types": db.scalars(
            select(EnergyType)
            .where(EnergyType.is_active.is_(True))
            .order_by(func.lower(EnergyType.name))
        ).all(),
        "departments": db.scalars(
            select(Department)
            .where(Department.is_active.is_(True))
            .order_by(func.lower(Department.name))
        ).all(),
    }


def _meters(db: Session):
    return db.scalars(
        select(Meter).order_by(Meter.is_active.desc(), func.lower(Meter.name))
    ).all()


def _read_meter_form(
    db: Session,
    name: str,
    energy_type_id: str,
    department_id: str,
    serial_no: str,
    multiplier: str,
    is_main: str | None,
    exclude_id: int | None = None,
) -> dict:
    clean_name = required_text(name, "Sayaç adı", 120)
    if _name_in_use(db, Meter, clean_name, exclude_id=exclude_id):
        raise ValueError(f"'{clean_name}' adında bir sayaç zaten var.")

    if not (energy_type_id or "").strip():
        raise ValueError("Enerji türü seçilmelidir.")
    energy_type = db.get(EnergyType, int(energy_type_id))
    if energy_type is None:
        raise ValueError("Seçilen enerji türü bulunamadı.")

    department = None
    if (department_id or "").strip():
        department = db.get(Department, int(department_id))
        if department is None:
            raise ValueError("Seçilen bölüm bulunamadı.")

    value = parse_number(multiplier, "Çarpan")
    if value <= 0:
        raise ValueError("Çarpan sıfırdan büyük olmalıdır.")

    return {
        "name": clean_name,
        "energy_type_id": energy_type.id,
        "department_id": department.id if department else None,
        "serial_no": optional_text(serial_no, "Seri no", 60),
        "multiplier": value,
        "is_main": is_main is not None,
    }


@router.get("/sayaclar")
def meters(request: Request, db: Session = Depends(get_session)):
    return render(
        request, "meters.html", db, meters=_meters(db), **_meter_page_context(db)
    )


@router.post("/sayaclar")
def create_meter(
    request: Request,
    name: str = Form(""),
    energy_type_id: str = Form(""),
    department_id: str = Form(""),
    serial_no: str = Form(""),
    multiplier: str = Form("1"),
    is_main: str | None = Form(None),
    db: Session = Depends(get_session),
):
    form = {
        "name": name,
        "energy_type_id": energy_type_id,
        "department_id": department_id,
        "serial_no": serial_no,
        "multiplier": multiplier,
        "is_main": is_main is not None,
    }
    try:
        values = _read_meter_form(
            db, name, energy_type_id, department_id, serial_no, multiplier, is_main
        )
    except ValueError as error:
        return render(
            request,
            "meters.html",
            db,
            status_code=400,
            meters=_meters(db),
            error=str(error),
            form=form,
            **_meter_page_context(db),
        )

    db.add(Meter(**values))
    db.commit()
    flash(request, f"'{values['name']}' sayacı eklendi.")
    return RedirectResponse("/tanimlar/sayaclar", status_code=303)


@router.get("/sayaclar/{meter_id}")
def edit_meter_form(request: Request, meter_id: int, db: Session = Depends(get_session)):
    meter = db.get(Meter, meter_id)
    if meter is None:
        return render(request, "not_found.html", db, status_code=404, what="Sayaç")
    return render(
        request, "meter_edit.html", db, meter=meter, **_meter_page_context(db)
    )


@router.post("/sayaclar/{meter_id}")
def edit_meter(
    request: Request,
    meter_id: int,
    name: str = Form(""),
    energy_type_id: str = Form(""),
    department_id: str = Form(""),
    serial_no: str = Form(""),
    multiplier: str = Form("1"),
    is_main: str | None = Form(None),
    is_active: str | None = Form(None),
    db: Session = Depends(get_session),
):
    meter = db.get(Meter, meter_id)
    if meter is None:
        return render(request, "not_found.html", db, status_code=404, what="Sayaç")
    try:
        values = _read_meter_form(
            db,
            name,
            energy_type_id,
            department_id,
            serial_no,
            multiplier,
            is_main,
            exclude_id=meter_id,
        )
    except ValueError as error:
        return render(
            request,
            "meter_edit.html",
            db,
            status_code=400,
            meter=meter,
            error=str(error),
            form={
                "name": name,
                "energy_type_id": energy_type_id,
                "department_id": department_id,
                "serial_no": serial_no,
                "multiplier": multiplier,
                "is_main": is_main is not None,
                "is_active": is_active is not None,
            },
            **_meter_page_context(db),
        )

    for field, value in values.items():
        setattr(meter, field, value)
    meter.is_active = is_active is not None
    db.commit()
    flash(request, f"'{meter.name}' sayacı güncellendi.")
    return RedirectResponse("/tanimlar/sayaclar", status_code=303)
