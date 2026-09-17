"""Tanim ekranlari: bolum, enerji turu, sayac ve enerji donusum katsayilari.

Bu ekranlarin tek amaci sonraki asamadaki elle veri girisine saglam bir temel
hazirlamaktir. Kayitlar silinmez; kullanilmayan tanimlar pasife alinir.
"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import calc, units
from app.db import get_session
from app.models import (
    Department,
    EnergyConversion,
    EnergyType,
    Meter,
    MeterReading,
)
from app.web import (
    flash,
    optional_text,
    parse_date,
    parse_number,
    render,
    required_text,
)

router = APIRouter(prefix="/tanimlar")


class ConfirmationRequired(ValueError):
    """Geri alinmasi zor bir degisiklik icin kullanicidan acik onay bekleniyor."""


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
    current_energy_type_id: int | None = None,
) -> dict:
    clean_name = required_text(name, "Sayaç adı", 120)
    if _name_in_use(db, Meter, clean_name, exclude_id=exclude_id):
        raise ValueError(f"'{clean_name}' adında bir sayaç zaten var.")

    if not (energy_type_id or "").strip():
        raise ValueError("Enerji türü seçilmelidir.")
    energy_type = db.get(EnergyType, int(energy_type_id))
    if energy_type is None:
        raise ValueError("Seçilen enerji türü bulunamadı.")
    # Pasif tur yalnizca zaten ona bagli olan sayacta kalabilir; yeni bir
    # sayac pasif ture baglanamaz, mevcut sayac pasif ture tasinamaz.
    if not energy_type.is_active and energy_type.id != current_energy_type_id:
        raise ValueError(
            f"'{energy_type.name}' pasif bir enerji türü. Pasif türlere yeni "
            "sayaç bağlanamaz."
        )

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


def _require_energy_type_change_confirmation(
    db: Session, meter: Meter, values: dict, onay: str | None
) -> None:
    """Okumasi olan bir sayacin enerji turu degistiriliyorsa acik onay ister.

    MVP'de tanimlarin tarihsel versiyonu tutulmaz: tur degisince o sayacin
    GECMIS okumalari da yeni turden sayilmaya baslar, birimi ve enerji anlami
    degisir. Sessizce yapilmasi yanlis raporlar uretir; bu yuzden kullanicidan
    ayrica onay alinir. Okumasi olmayan sayacta boyle bir risk yoktur.
    """
    if values["energy_type_id"] == meter.energy_type_id or onay is not None:
        return

    reading_count = db.scalar(
        select(func.count())
        .select_from(MeterReading)
        .where(MeterReading.meter_id == meter.id)
    )
    if not reading_count:
        return

    new_type = db.get(EnergyType, values["energy_type_id"])
    raise ConfirmationRequired(
        f"'{meter.name}' sayacının {reading_count} okuması var. Enerji türü "
        f"'{meter.energy_type.name}' ({meter.energy_type.unit}) → "
        f"'{new_type.name}' ({new_type.unit}) olarak değiştirilirse bu "
        "okumalardan hesaplanan GEÇMİŞ tüketimler de yeni enerji türüne ve "
        "birimine göre sayılır; geçmiş dönem raporları, maliyetler ve EnPI "
        "değerleri değişir. Devam etmek için aşağıdaki onay kutusunu işaretleyin."
    )


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
    onay: str | None = Form(None),
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
            current_energy_type_id=meter.energy_type_id,
        )
        _require_energy_type_change_confirmation(db, meter, values, onay)
    except ValueError as error:
        return render(
            request,
            "meter_edit.html",
            db,
            status_code=400,
            meter=meter,
            error=str(error),
            confirm_needed=isinstance(error, ConfirmationRequired),
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


# --------------------------------------------------------------------------- #
# Enerji donusum katsayilari
#
# 1 <enerji turu birimi> = factor GJ. Yalnizca matematiksel olarak
# cevrilemeyen birimler (Sm3, kg, lt gibi) icin gereklidir; kWh/MJ/GJ gibi
# enerji birimleri zaten standart donusumle cevrilir. Kullanici yine de
# isterse standart degerin yerine kendi katsayisini tanimlayabilir.
# --------------------------------------------------------------------------- #


def _conversion_page_context(db: Session) -> dict:
    records = calc.energy_conversion_records(db)
    return {
        "energy_types": db.scalars(_active_first(EnergyType)).all(),
        "records": [
            {
                "record": record,
                # Kullanicinin katsayiyi tanidik bir birimde gorebilmesi icin.
                "kwh": units.convert(record.factor, calc.REFERENCE_ENERGY_UNIT, "kWh"),
            }
            for record in sorted(
                records,
                key=lambda item: (item.energy_type.name, item.valid_from),
                reverse=True,
            )
        ],
        "reference_unit": calc.REFERENCE_ENERGY_UNIT,
    }


def _read_conversion_form(
    db: Session, energy_type_id: str, factor: str, valid_from: str, source: str
) -> dict:
    if not (energy_type_id or "").strip():
        raise ValueError("Enerji türü seçilmelidir.")
    energy_type = db.get(EnergyType, int(energy_type_id))
    if energy_type is None:
        raise ValueError("Seçilen enerji türü bulunamadı.")

    value = parse_number(factor, "Katsayı")
    if value <= 0:
        raise ValueError("Katsayı sıfırdan büyük olmalıdır.")

    start = parse_date(valid_from, "Geçerlilik başlangıcı")
    existing = db.scalars(
        select(EnergyConversion).where(
            EnergyConversion.energy_type_id == energy_type.id,
            EnergyConversion.valid_from == start,
        )
    ).first()
    if existing is not None:
        raise ValueError(
            f"'{energy_type.name}' için {start.strftime('%d.%m.%Y')} tarihinden "
            "geçerli bir katsayı zaten tanımlı."
        )

    return {
        "energy_type_id": energy_type.id,
        "factor": value,
        "valid_from": start,
        "source": required_text(source or "Kullanıcı", "Kaynak", 120),
    }


@router.get("/donusum-katsayilari")
def conversions(request: Request, db: Session = Depends(get_session)):
    return render(request, "conversions.html", db, **_conversion_page_context(db))


@router.post("/donusum-katsayilari")
def create_conversion(
    request: Request,
    energy_type_id: str = Form(""),
    factor: str = Form(""),
    valid_from: str = Form(""),
    source: str = Form(""),
    note: str = Form(""),
    db: Session = Depends(get_session),
):
    try:
        values = _read_conversion_form(db, energy_type_id, factor, valid_from, source)
    except ValueError as error:
        return render(
            request,
            "conversions.html",
            db,
            status_code=400,
            error=str(error),
            form={
                "energy_type_id": energy_type_id,
                "factor": factor,
                "valid_from": valid_from,
                "source": source,
                "note": note,
            },
            **_conversion_page_context(db),
        )

    db.add(EnergyConversion(**values, note=optional_text(note, "Not", 500)))
    db.commit()
    flash(request, "Dönüşüm katsayısı kaydedildi.")
    return RedirectResponse("/tanimlar/donusum-katsayilari", status_code=303)


@router.post("/donusum-katsayilari/{conversion_id}/sil")
def delete_conversion(
    request: Request, conversion_id: int, db: Session = Depends(get_session)
):
    """Katsayi silinince o donem icin donusum yapilamaz hale gelebilir.

    Bu durumda toplam enerji sessizce eksik hesaplanmaz; ekranda katsayinin
    bulunamadigi acikca yazilir.
    """
    record = db.get(EnergyConversion, conversion_id)
    if record is None:
        return render(request, "not_found.html", db, status_code=404, what="Katsayı")

    name = record.energy_type.name
    label = record.valid_from.strftime("%d.%m.%Y")
    db.delete(record)
    db.commit()
    flash(request, f"{name} · {label} tarihli dönüşüm katsayısı silindi.")
    return RedirectResponse("/tanimlar/donusum-katsayilari", status_code=303)
