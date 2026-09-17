"""Testlerde kullanilan basit veri olusturuculari."""

from datetime import date

from app.models import Department, EnergyType, Meter, MeterReading


def energy_type(db, name="Elektrik", unit="kWh", price=0.0) -> EnergyType:
    record = EnergyType(name=name, unit=unit, unit_price=price, is_active=True)
    db.add(record)
    db.commit()
    return record


def department(db, name="Üretim") -> Department:
    record = Department(name=name, is_active=True)
    db.add(record)
    db.commit()
    return record


def meter(
    db,
    name,
    energy,
    dept=None,
    multiplier=1.0,
    is_main=False,
    is_active=True,
) -> Meter:
    record = Meter(
        name=name,
        energy_type_id=energy.id,
        department_id=dept.id if dept else None,
        multiplier=multiplier,
        is_main=is_main,
        is_active=is_active,
    )
    db.add(record)
    db.commit()
    return record


def readings(db, record, values: dict[str, float]) -> None:
    """values: {"2026-01-01": 1000, ...}"""
    for day, value in values.items():
        db.add(
            MeterReading(
                meter_id=record.id,
                reading_date=date.fromisoformat(day),
                index_value=value,
            )
        )
    db.commit()


def production(db, values: dict[str, tuple[float, str]]) -> None:
    """values: {"2026-01-31": (120, "ton"), ...}"""
    from app.models import Production

    for day, (quantity, unit) in values.items():
        db.add(
            Production(
                production_date=date.fromisoformat(day),
                quantity=quantity,
                unit=unit,
            )
        )
    db.commit()


def direct_consumption(db, energy, year_month: str, quantity: float, note=None):
    """Bir ay ve enerji turu icin dogrudan tuketim kaydi (ornegin faturadan)."""
    from app.models import DirectConsumption

    year, month = (int(part) for part in year_month.split("-"))
    record = DirectConsumption(
        period_date=date(year, month, 1),
        energy_type_id=energy.id,
        quantity=quantity,
        note=note,
    )
    db.add(record)
    db.commit()
    return record
