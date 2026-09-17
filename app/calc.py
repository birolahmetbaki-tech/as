"""Enerji tuketimi hesaplama cekirdegi.

Bu modul sistemdeki tuketim hesabinin TEK kaynagidir. Dashboard, raporlar,
hedefler ve ileride AI kendi hesabini yapmaz; hepsi buradaki sonuclari kullanir.

Temel kurallar:

* Tuketim = (yeni endeks - onceki endeks) x sayac carpani
* Tuketim, BIRINCI okumanin ait oldugu takvim ayina yazilir. Sahada endeksler
  bir sonraki ayin 1. gunu okundugu icin (orn. 01.01 -> 01.02 arasindaki
  tuketim Ocak ayina aittir) donem, ikinci okumanin degil ilk okumanin
  tarihine gore belirlenir.
* Bir sayacin ilk okumasi icin tuketim uretilmez (karsilastirilacak onceki
  okuma yoktur).
* Fabrika toplami, enerji turu ve AY bazinda su oncelikle belirlenir:
    1. O ay icin dogrudan tuketim (fatura) girilmisse -> dogrudan tuketim
    2. Yoksa ana sayac tanimliysa -> ana sayaclar
    3. Yoksa -> o turdeki tum sayaclar
  Ayni ay ve enerji turu icin iki kaynak birden varsa DEGERLER TOPLANMAZ;
  dogrudan tuketim esas alinir ve cakisma consumption_conflicts ile bildirilir.

Gruplama islevleri veritabanina dokunmaz; yalnizca hesaplanmis kayitlar
uzerinde calisir. Bu sayede kolayca test edilebilirler.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app import units
from app.models import (
    DirectConsumption,
    EnergyConversion,
    EnergyType,
    Meter,
    MeterReading,
    Production,
)

UNASSIGNED_DEPARTMENT = "Bölümsüz"

SOURCE_METER = "sayac"
SOURCE_DIRECT = "dogrudan"

PERIOD_DAY = "gun"
PERIOD_MONTH = "ay"
PERIOD_YEAR = "yil"


@dataclass(frozen=True)
class Consumption:
    """Iki ardisik okuma arasindaki tuketim.

    Hesabin nasil olustugu izlenebilsin diye kaynak okumalar ve kullanilan
    carpan da tasinir.
    """

    reading_date: date  # ikinci (yeni) okumanin tarihi - izlenebilirlik icin
    previous_date: date  # birinci (onceki) okumanin tarihi
    meter_id: int | None  # dogrudan giriste yoktur
    meter_name: str | None
    energy_type_id: int
    energy_type_name: str
    unit: str
    department_id: int | None
    department_name: str | None
    previous_index: float | None  # dogrudan giriste yoktur
    index_value: float | None
    multiplier: float | None
    consumption: float
    source: str = SOURCE_METER

    @property
    def period_date(self) -> date:
        """Tuketimin ait oldugu tarih: birinci okumanin tarihi.

        Donem suzmesi ve gruplama bu tarihe gore yapilir. 01.01 -> 01.02
        arasindaki tuketim Ocak ayina yazilir.
        """
        return self.previous_date

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

    Tarih araligi, tuketimin ait oldugu tarihe (BIRINCI okuma) gore suzulur.
    Esleme her zaman sayacin tum okumalari uzerinden yapilir; boylece bir
    donemin tuketimi, donem disinda kalan (bir sonraki ayin 1'inde alinan)
    ikinci okumayla dogru eslesir.
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

    entries.sort(key=lambda entry: (entry.period_date, entry.meter_name))
    return _in_range(entries, start, end)


def _in_range(
    entries: list[Consumption], start: date | None, end: date | None
) -> list[Consumption]:
    return [
        entry
        for entry in entries
        if (start is None or entry.period_date >= start)
        and (end is None or entry.period_date <= end)
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


def direct_consumptions(
    db: Session,
    start: date | None = None,
    end: date | None = None,
    energy_type_id: int | None = None,
) -> list[Consumption]:
    """Dogrudan girilen (fatura) tuketim kayitlari.

    Fabrika seviyesindedir: sayaci ve bolumu yoktur. Donem tarihi, kaydin ait
    oldugu ayin ilk gunudur.
    """
    query = select(DirectConsumption).options(
        joinedload(DirectConsumption.energy_type)
    )
    if energy_type_id is not None:
        query = query.where(DirectConsumption.energy_type_id == energy_type_id)
    if start is not None:
        query = query.where(DirectConsumption.period_date >= start)
    if end is not None:
        query = query.where(DirectConsumption.period_date <= end)

    return [
        Consumption(
            reading_date=record.period_date,
            previous_date=record.period_date,
            meter_id=None,
            meter_name=None,
            energy_type_id=record.energy_type_id,
            energy_type_name=record.energy_type.name,
            unit=record.energy_type.unit,
            department_id=None,
            department_name=None,
            previous_index=None,
            index_value=None,
            multiplier=None,
            consumption=record.quantity,
            source=SOURCE_DIRECT,
        )
        for record in db.scalars(query.order_by(DirectConsumption.period_date))
    ]


def _month_keys(entries: list[Consumption]) -> set[tuple[int, str]]:
    """Kayitlarin kapsadigi (enerji turu, ay) ciftleri."""
    return {
        (entry.energy_type_id, period_key(entry.period_date, PERIOD_MONTH))
        for entry in entries
    }


def factory_consumptions(
    db: Session,
    start: date | None = None,
    end: date | None = None,
    energy_type_id: int | None = None,
) -> list[Consumption]:
    """Fabrika toplami icin tuketim kayitlari.

    Enerji turu ve ay bazinda oncelik: dogrudan tuketim -> ana sayac -> tum
    sayaclar. Dogrudan tuketim bulunan bir ayda o turun sayac kayitlari
    fabrika toplamina EKLENMEZ; boylece cift sayim olusmaz.
    """
    direct = direct_consumptions(
        db, start=start, end=end, energy_type_id=energy_type_id
    )
    covered = _month_keys(direct)

    meter_entries = consumptions(
        db,
        start=start,
        end=end,
        energy_type_id=energy_type_id,
        meter_ids=factory_meter_ids(db, energy_type_id),
    )
    entries = direct + [
        entry
        for entry in meter_entries
        if (entry.energy_type_id, period_key(entry.period_date, PERIOD_MONTH))
        not in covered
    ]
    entries.sort(key=lambda entry: (entry.period_date, entry.meter_name or ""))
    return entries


def consumption_conflicts(
    db: Session,
    start: date | None = None,
    end: date | None = None,
    energy_type_id: int | None = None,
) -> list[dict]:
    """Ayni ay ve enerji turunde hem dogrudan hem sayac tuketimi bulunan donemler.

    Degerler toplanmaz; fabrika toplaminda dogrudan tuketim esas alinir. Bu
    islev yalnizca kullaniciya bildirmek icin farki hesaplar.
    """
    direct = direct_consumptions(
        db, start=start, end=end, energy_type_id=energy_type_id
    )
    if not direct:
        return []

    meter_totals: dict[tuple[int, str], float] = defaultdict(float)
    for entry in consumptions(
        db,
        start=start,
        end=end,
        energy_type_id=energy_type_id,
        meter_ids=factory_meter_ids(db, energy_type_id),
    ):
        meter_totals[
            (entry.energy_type_id, period_key(entry.period_date, PERIOD_MONTH))
        ] += entry.consumption

    conflicts = []
    for entry in direct:
        key = (entry.energy_type_id, period_key(entry.period_date, PERIOD_MONTH))
        if key not in meter_totals:
            continue
        meter_total = meter_totals[key]
        difference = entry.consumption - meter_total
        conflicts.append(
            {
                "donem": key[1],
                "enerji_turu_id": entry.energy_type_id,
                "enerji_turu": entry.energy_type_name,
                "birim": entry.unit,
                "dogrudan": entry.consumption,
                "sayac": meter_total,
                "fark": difference,
                "fark_yuzde": (difference / meter_total * 100) if meter_total else None,
            }
        )
    return conflicts


def main_meter_gaps(
    db: Session,
    start: date | None = None,
    end: date | None = None,
    energy_type_id: int | None = None,
) -> list[dict]:
    """Ana sayac tanimli ama donemde ana sayac tuketimi yok; alt sayaclarda var.

    Bu durumda fabrika toplami dogru davranisla 0 (ya da eksik) cikar: ana
    sayac tanimliyken alt sayaclar onun yerine GECMEZ, yoksa mukerrer ve
    eksik olcumler birbirine karisir. Bu islev yalnizca kullaniciya durumu
    bildirmek icindir; oncelik kuralini degistirmez.

    Dogrudan tuketim girilen donemler bildirilmez: orada fabrika toplami
    zaten dogrudan degerden gelir, eksik bir sey yoktur.
    """
    query = select(EnergyType).order_by(EnergyType.id)
    if energy_type_id is not None:
        query = query.where(EnergyType.id == energy_type_id)

    gaps = []
    for energy_type in db.scalars(query):
        meters = list(
            db.scalars(select(Meter).where(Meter.energy_type_id == energy_type.id))
        )
        main_meters = [meter for meter in meters if meter.is_main]
        sub_meters = [meter for meter in meters if not meter.is_main]
        if not main_meters or not sub_meters:
            continue

        if direct_consumptions(
            db, start=start, end=end, energy_type_id=energy_type.id
        ):
            continue

        main_total = total(
            consumptions(
                db,
                start=start,
                end=end,
                meter_ids=[meter.id for meter in main_meters],
            )
        )
        if main_total:
            continue

        sub_total = total(
            consumptions(
                db,
                start=start,
                end=end,
                meter_ids=[meter.id for meter in sub_meters],
            )
        )
        if not sub_total:
            continue

        gaps.append(
            {
                "enerji_turu_id": energy_type.id,
                "enerji_turu": energy_type.name,
                "birim": energy_type.unit,
                "ana_sayaclar": [meter.name for meter in main_meters],
                "alt_toplam": sub_total,
            }
        )
    return gaps


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
        totals[period_key(entry.period_date, period)] += entry.consumption
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


# --------------------------------------------------------------------------- #
# Maliyet ve hedef
# --------------------------------------------------------------------------- #


def cost(consumption: float, unit_price: float) -> float:
    """Enerji maliyeti = tuketim x birim fiyat.

    Enerji turunun birimi ile birim fiyati uyumlu kabul edilir (orn. kWh ve
    TL/kWh). Bu asamada tarife dilimi, vergi, ek bedel veya gecmis fiyat
    takibi yoktur: her zaman enerji turunun GUNCEL birim fiyati kullanilir.
    """
    return consumption * unit_price


def target_status(actual: float, target_value: float) -> dict | None:
    """Aylik hedefe gore durum.

    Gerceklesen <= hedef ise hedef icinde, buyukse hedef asilmistir.
    Hedef sifir veya negatifse gosterge anlamsizdir; None doner.
    """
    if target_value <= 0:
        return None
    return {
        "target": target_value,
        "actual": actual,
        "difference": actual - target_value,
        "percent": actual / target_value * 100,
        "exceeded": actual > target_value,
    }


# --------------------------------------------------------------------------- #
# Birim / enerji donusumu
#
# Uygulamanin donusum icin kullandigi TEK arayuz burasidir. Dashboard,
# raporlar ve EnPI kendi donusum formulunu yazmaz.
#
# Iki ayri mekanizma vardir ve birbirine karistirilmaz:
#   1. Matematiksel birim donusumu (units modulu): kWh -> MJ -> GJ -> TEP.
#      Sabittir, herkes icin aynidir.
#   2. Enerji icerigi katsayisi (energy_conversion tablosu): Sm3 -> GJ.
#      Yakita ve olcum bazina gore degisir; kullanici girer.
#
# Oncelik sirasi:
#   a. Doneme uyan kullanici katsayisi varsa o kullanilir.
#   b. Yoksa enerji turunun birimi zaten bir enerji birimiyse (kWh, MJ...)
#      matematiksel standart donusum kullanilir.
#   c. Hicbiri yoksa donusum YAPILMAZ: convertible=False doner.
#      Varsayilan katsayi uydurulmaz, deger sessizce 0 kabul edilmez.
# --------------------------------------------------------------------------- #

REFERENCE_ENERGY_UNIT = units.ENERGY_REFERENCE  # "GJ"

# Ekranda secilebilen enerji gosterim birimleri.
DISPLAY_ENERGY_UNITS = ("kWh", "MJ", "GJ", "TEP")

FACTOR_SOURCE_STANDARD = "Standart"


@dataclass(frozen=True)
class Conversion:
    """Bir donusumun sonucu ve nasil yapildigi.

    value        : donusturulmus deger (yapilamadiysa None)
    unit         : hedef birim
    coefficient  : 1 <kaynak birim> kac <unit> eder
    source       : katsayinin kaynagi ("Standart" ya da kullanicinin yazdigi)
    convertible  : donusum yapilabildi mi
    reason       : yapilamadiysa kisa ve acik gerekce
    """

    value: float | None
    unit: str
    coefficient: float | None
    source: str | None
    convertible: bool
    reason: str | None = None


def energy_conversion_records(
    db: Session, energy_type_id: int | None = None
) -> list[EnergyConversion]:
    """Kullanici tanimli enerji icerigi katsayilari, tarihe gore sirali."""
    query = select(EnergyConversion).options(
        joinedload(EnergyConversion.energy_type)
    )
    if energy_type_id is not None:
        query = query.where(EnergyConversion.energy_type_id == energy_type_id)
    return list(
        db.scalars(
            query.order_by(
                EnergyConversion.energy_type_id, EnergyConversion.valid_from
            )
        )
    )


def active_conversion(
    records: list[EnergyConversion], on_date: date | None
) -> EnergyConversion | None:
    """Donem tarihine uyan katsayi: valid_from <= donem olan EN YENI kayit.

    on_date verilmezse en yeni katsayi kullanilir (tarihi olmayan sorgular
    icin). Donem tarihinden once baslayan hicbir katsayi yoksa None doner;
    ileri tarihli bir katsayinin gecmise uygulanmasi kasitla engellenir.
    """
    uygun = [
        record
        for record in records
        if on_date is None or record.valid_from <= on_date
    ]
    if not uygun:
        return None
    return max(uygun, key=lambda record: record.valid_from)


def convert_energy(
    db: Session,
    energy_type: EnergyType,
    value: float,
    to_unit: str = REFERENCE_ENERGY_UNIT,
    on_date: date | None = None,
    records: list[EnergyConversion] | None = None,
) -> Conversion:
    """Bir enerji turunun kendi birimindeki degerini hedef enerji birimine cevirir.

    records verilirse veritabani tekrar sorgulanmaz (toplu hesaplarda).
    """
    target = units.get(to_unit)
    if target.dimension != units.DIMENSION_ENERGY:
        raise units.DimensionMismatch(f"'{to_unit}' bir enerji birimi degil.")

    if records is None:
        records = energy_conversion_records(db, energy_type.id)
    record = active_conversion(records, on_date)

    if record is not None:
        # 1 <enerji turu birimi> = record.factor GJ
        coefficient = record.factor / target.factor
        source = record.source
    elif units.dimension_of(energy_type.unit) == units.DIMENSION_ENERGY:
        coefficient = units.factor_between(energy_type.unit, target.code)
        source = FACTOR_SOURCE_STANDARD
    else:
        return Conversion(
            value=None,
            unit=target.code,
            coefficient=None,
            source=None,
            convertible=False,
            reason=(
                f"{energy_type.name} için geçerli dönüşüm katsayısı bulunamadı "
                f"({energy_type.unit} → {target.code})."
            ),
        )

    return Conversion(
        value=value * coefficient,
        unit=target.code,
        coefficient=coefficient,
        source=source,
        convertible=True,
    )


def energy_totals(
    db: Session,
    start: date | None = None,
    end: date | None = None,
    to_unit: str = REFERENCE_ENERGY_UNIT,
) -> dict:
    """Butun enerji turlerinin ortak enerji biriminde toplami.

    Her tuketim kaydi KENDI donem tarihine gore cevrilir; boylece yil icinde
    degisen katsayilar dogru uygulanir.

    Bir enerji turu cevrilemiyorsa toplam URETILMEZ (value None, complete
    False): eksik bir toplami tam gibi gostermek yaniltici olur. Ham tuketim
    satirlari yine de doner; kullanici neyin eksik oldugunu gorur.
    """
    target = units.get(to_unit).code
    rows: list[dict] = []
    missing: list[str] = []
    running = 0.0

    for energy_type in db.scalars(select(EnergyType).order_by(EnergyType.id)):
        entries = factory_consumptions(
            db, start=start, end=end, energy_type_id=energy_type.id
        )
        if not entries:
            continue

        records = energy_conversion_records(db, energy_type.id)
        raw_total = total(entries)
        converted = 0.0
        coefficients: set[float] = set()
        sources: list[str] = []
        failure: Conversion | None = None

        for entry in entries:
            result = convert_energy(
                db,
                energy_type,
                entry.consumption,
                to_unit=target,
                on_date=entry.period_date,
                records=records,
            )
            if not result.convertible:
                failure = result
                break
            converted += result.value
            coefficients.add(result.coefficient)
            if result.source not in sources:
                sources.append(result.source)

        if failure is not None:
            missing.append(energy_type.name)
            rows.append(
                {
                    "energy_type": energy_type,
                    "raw_total": raw_total,
                    "raw_unit": energy_type.unit,
                    "value": None,
                    "coefficient": None,
                    "source": None,
                    "convertible": False,
                    "reason": failure.reason,
                }
            )
            continue

        running += converted
        rows.append(
            {
                "energy_type": energy_type,
                "raw_total": raw_total,
                "raw_unit": energy_type.unit,
                "value": converted,
                # Aralikta birden fazla katsayi gecerliyse tek bir katsayi
                # yazmak yaniltici olur.
                "coefficient": coefficients.pop() if len(coefficients) == 1 else None,
                "source": " / ".join(sources) if sources else None,
                "convertible": True,
                "reason": None,
            }
        )

    complete = not missing
    return {
        "unit": target,
        "value": running if complete else None,
        "complete": complete,
        "rows": rows,
        "missing": missing,
        "message": (
            None
            if complete
            else (
                f"Toplam enerji {target} olarak hesaplanamadı: "
                f"{', '.join(missing)} için geçerli dönüşüm katsayısı bulunamadı."
            )
        ),
    }


def combined_enpi(
    db: Session,
    production_unit: str | None,
    start: date | None = None,
    end: date | None = None,
    to_unit: str = REFERENCE_ENERGY_UNIT,
) -> dict:
    """Butun enerji turlerinin ortak birimdeki toplami / uretim.

    Enerji turlerinden biri bile cevrilemiyorsa deger URETILMEZ; eksik enerji
    ile hesaplanan bir EnPI, oldugundan iyi gorunur.
    """
    totals = energy_totals(db, start=start, end=end, to_unit=to_unit)
    produced = (
        production_total(db, production_unit, start=start, end=end)
        if production_unit
        else 0.0
    )
    return {
        "unit": totals["unit"],
        "production_unit": production_unit,
        "production": produced,
        "energy": totals,
        "value": enpi(totals["value"], produced) if totals["complete"] else None,
    }
