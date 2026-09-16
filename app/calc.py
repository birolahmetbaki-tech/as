"""Enerji tuketimi hesaplama cekirdegi.

Bu modul sistemdeki tuketim hesabinin TEK kaynagidir. Dashboard, raporlar,
hedefler ve ileride AI kendi hesabini yapmaz; hepsi buradaki sonuclari kullanir.

Temel kurallar:

* Tuketim = (yeni endeks - onceki endeks) x sayac carpani
* Tuketim, ikinci okumanin tarihine yazilir.
* Bir sayacin ilk okumasi icin tuketim uretilmez (karsilastirilacak onceki
  okuma yoktur).
* Fabrika toplaminda, bir enerji turunde ana sayac tanimliysa yalnizca ana
  sayaclar kullanilir; ana sayac yoksa o turdeki tum sayaclar kullanilir.

Gruplama islevleri veritabanina dokunmaz; yalnizca hesaplanmis kayitlar
uzerinde calisir. Bu sayede kolayca test edilebilirler.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Meter, MeterReading, Production

UNASSIGNED_DEPARTMENT = "Bölümsüz"

PERIOD_DAY = "gun"
PERIOD_MONTH = "ay"
PERIOD_YEAR = "yil"


@dataclass(frozen=True)
class Consumption:
    """Iki ardisik okuma arasindaki tuketim.

    Hesabin nasil olustugu izlenebilsin diye kaynak okumalar ve kullanilan
    carpan da tasinir.
    """

    reading_date: date  # tuketimin yazildigi tarih (ikinci okumanin tarihi)
    previous_date: date
    meter_id: int
    meter_name: str
    energy_type_id: int
    energy_type_name: str
    unit: str
    department_id: int | None
    department_name: str | None
    previous_index: float
    index_value: float
    multiplier: float
    consumption: float

    @property
    def department_label(self) -> str:
        return self.department_name or UNASSIGNED_DEPARTMENT


# --------------------------------------------------------------------------- #
# Tuketim uretimi
# --------------------------------------------------------------------------- #


def _pair_readings(meter: Meter, readings: list[MeterReading]) -> list[Consumption]:
    """Bir sayacin okumalarini kronolojik olarak esleyip tuketim uretir."""
    entries: list[Consumption] = []
    for previous, current in zip(readings, readings[1:]):
        entries.append(
            Consumption(
                reading_date=current.reading_date,
                previous_date=previous.reading_date,
                meter_id=meter.id,
                meter_name=meter.name,
                energy_type_id=meter.energy_type_id,
                energy_type_name=meter.energy_type.name,
                unit=meter.energy_type.unit,
                department_id=meter.department_id,
                department_name=meter.department.name if meter.department else None,
                previous_index=previous.index_value,
                index_value=current.index_value,
                multiplier=meter.multiplier,
                consumption=(current.index_value - previous.index_value)
                * meter.multiplier,
            )
        )
    return entries


def meter_consumptions(
    db: Session,
    meter_id: int,
    start: date | None = None,
    end: date | None = None,
) -> list[Consumption]:
    """Tek bir sayacin tuketim kayitlari.

    Tarih araligi, tuketimin yazildigi tarihe (ikinci okuma) gore suzulur.
    Esleme her zaman sayacin tum okumalari uzerinden yapilir; boylece aralik
    basindaki tuketim, araligin disinda kalan onceki okumayla dogru eslesir.
    """
    meter = db.get(Meter, meter_id)
    if meter is None:
        return []
    readings = list(
        db.scalars(
            select(MeterReading)
            .where(MeterReading.meter_id == meter_id)
            .order_by(MeterReading.reading_date, MeterReading.id)
        )
    )
    return _in_range(_pair_readings(meter, readings), start, end)


def consumptions(
    db: Session,
    start: date | None = None,
    end: date | None = None,
    energy_type_id: int | None = None,
    meter_ids: list[int] | None = None,
) -> list[Consumption]:
    """Birden fazla sayac icin tuketim kayitlari, tarihe gore sirali.

    meter_ids verilmezse butun sayaclar hesaba katilir. Pasif sayaclarin
    gecmis okumalari da hesaba dahildir; pasiflik yalnizca yeni veri girisini
    kapatir, gecmisi silmez.
    """
    query = select(Meter).options(
        joinedload(Meter.energy_type), joinedload(Meter.department)
    )
    if energy_type_id is not None:
        query = query.where(Meter.energy_type_id == energy_type_id)
    if meter_ids is not None:
        if not meter_ids:
            return []
        query = query.where(Meter.id.in_(meter_ids))

    entries: list[Consumption] = []
    for meter in db.scalars(query):
        readings = list(
            db.scalars(
                select(MeterReading)
                .where(MeterReading.meter_id == meter.id)
                .order_by(MeterReading.reading_date, MeterReading.id)
            )
        )
        entries.extend(_pair_readings(meter, readings))

    entries.sort(key=lambda entry: (entry.reading_date, entry.meter_name))
    return _in_range(entries, start, end)


def _in_range(
    entries: list[Consumption], start: date | None, end: date | None
) -> list[Consumption]:
    return [
        entry
        for entry in entries
        if (start is None or entry.reading_date >= start)
        and (end is None or entry.reading_date <= end)
    ]


# --------------------------------------------------------------------------- #
# Ana sayac / alt sayac kurali
# --------------------------------------------------------------------------- #


def factory_meter_ids(db: Session, energy_type_id: int | None = None) -> list[int]:
    """Fabrika toplaminda kullanilacak sayaclar.

    Bir enerji turunde ana sayac tanimliysa yalnizca o turun ana sayaclari
    kullanilir; tanimli degilse o turdeki tum sayaclar kullanilir. Kural her
    enerji turu icin ayri ayri uygulanir.
    """
    query = select(Meter)
    if energy_type_id is not None:
        query = query.where(Meter.energy_type_id == energy_type_id)

    by_energy_type: dict[int, list[Meter]] = defaultdict(list)
    for meter in db.scalars(query):
        by_energy_type[meter.energy_type_id].append(meter)

    selected: list[int] = []
    for meters in by_energy_type.values():
        main_meters = [meter for meter in meters if meter.is_main]
        selected.extend(meter.id for meter in (main_meters or meters))
    return sorted(selected)


def factory_consumptions(
    db: Session,
    start: date | None = None,
    end: date | None = None,
    energy_type_id: int | None = None,
) -> list[Consumption]:
    """Fabrika toplami icin tuketim kayitlari (ana sayac kurali uygulanir)."""
    return consumptions(
        db,
        start=start,
        end=end,
        energy_type_id=energy_type_id,
        meter_ids=factory_meter_ids(db, energy_type_id),
    )


# --------------------------------------------------------------------------- #
# Toplama ve gruplama (veritabanina dokunmaz)
# --------------------------------------------------------------------------- #


def total(entries: list[Consumption]) -> float:
    return sum(entry.consumption for entry in entries)


def period_key(day: date, period: str) -> str:
    if period == PERIOD_DAY:
        return day.isoformat()
    if period == PERIOD_MONTH:
        return f"{day.year:04d}-{day.month:02d}"
    if period == PERIOD_YEAR:
        return f"{day.year:04d}"
    raise ValueError(f"Bilinmeyen dönem: {period}")


def group_by_period(
    entries: list[Consumption], period: str = PERIOD_MONTH
) -> dict[str, float]:
    """Donem bazinda toplam tuketim. Anahtarlar kronolojik siradadir."""
    totals: dict[str, float] = defaultdict(float)
    for entry in entries:
        totals[period_key(entry.reading_date, period)] += entry.consumption
    return {key: totals[key] for key in sorted(totals)}


def group_by_department(entries: list[Consumption]) -> dict[str, float]:
    """Bolum bazinda toplam tuketim. Bolumu olmayan sayaclar 'Bölümsüz'."""
    totals: dict[str, float] = defaultdict(float)
    for entry in entries:
        totals[entry.department_label] += entry.consumption
    return dict(
        sorted(totals.items(), key=lambda item: (-item[1], item[0]))
    )


# --------------------------------------------------------------------------- #
# Uretim ve enerji performansi (EnPI)
# --------------------------------------------------------------------------- #


def production_total(
    db: Session,
    unit: str,
    start: date | None = None,
    end: date | None = None,
) -> float:
    """Belirtilen uretim biriminde donem uretim toplami.

    Farkli birimler (ton, adet, m3) asla toplanmaz; her zaman tek bir birim
    icin hesaplanir.
    """
    query = select(Production).where(Production.unit == unit)
    if start is not None:
        query = query.where(Production.production_date >= start)
    if end is not None:
        query = query.where(Production.production_date <= end)
    return sum(record.quantity for record in db.scalars(query))


def production_units(
    db: Session, start: date | None = None, end: date | None = None
) -> list[str]:
    """Donemde kayit girilmis uretim birimleri, uretimi cok olandan az olana."""
    query = select(Production)
    if start is not None:
        query = query.where(Production.production_date >= start)
    if end is not None:
        query = query.where(Production.production_date <= end)

    totals: dict[str, float] = defaultdict(float)
    for record in db.scalars(query):
        totals[record.unit] += record.quantity
    return [unit for unit, _ in sorted(totals.items(), key=lambda item: -item[1])]


def production_by_period(
    db: Session,
    unit: str,
    start: date | None = None,
    end: date | None = None,
    period: str = PERIOD_MONTH,
) -> dict[str, float]:
    """Donem bazinda uretim toplami (tek birim)."""
    query = select(Production).where(Production.unit == unit)
    if start is not None:
        query = query.where(Production.production_date >= start)
    if end is not None:
        query = query.where(Production.production_date <= end)

    totals: dict[str, float] = defaultdict(float)
    for record in db.scalars(query):
        totals[period_key(record.production_date, period)] += record.quantity
    return {key: totals[key] for key in sorted(totals)}


def enpi(energy: float, production: float) -> float | None:
    """Enerji performans gostergesi: enerji / uretim.

    Uretim yoksa (veya sifirsa) gosterge tanimsizdir; sayi uretmek yerine
    None doner. Boylece ekranda "veri yok" olarak gosterilebilir.
    """
    if not production:
        return None
    return energy / production


def enpi_series(
    db: Session,
    unit: str,
    energy_type_id: int,
    start: date | None = None,
    end: date | None = None,
    period: str = PERIOD_MONTH,
) -> dict[str, float | None]:
    """Donem bazinda EnPI serisi: (fabrika tuketimi) / (uretim).

    Enerji tarafinda ana sayac kurali gecerlidir. Uretimi olmayan donemler
    None degeri tasir; tuketimi olmayan donem sifir enerji ile hesaplanir.
    """
    energy_totals = group_by_period(
        factory_consumptions(db, start=start, end=end, energy_type_id=energy_type_id),
        period,
    )
    production_totals = production_by_period(db, unit, start=start, end=end, period=period)

    keys = sorted(set(energy_totals) | set(production_totals))
    return {
        key: enpi(energy_totals.get(key, 0.0), production_totals.get(key, 0.0))
        for key in keys
    }
