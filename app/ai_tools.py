"""AI icin read-only veri katmani.

Bu dosya YENI BIR HESAPLAMA MOTORU DEGILDIR. Tek isi, mevcut guvenilir
hesaplama fonksiyonlarinin (calc / dashboard / reports) sonuclarini alip
JSON'a cevrilebilir duz sozluklere donusturmektir:

    mevcut uygulama hesaplari  ->  ai_tools  ->  dict / list / str / float / None

Kurallar:
* Hicbir fonksiyon yazma yapmaz: INSERT/UPDATE/DELETE/commit/flush yoktur.
* Cikti hicbir zaman ORM nesnesi, Session, Query veya date/Decimal icermez.
  Tarihler "2026-01-31" (gun) veya "2026-01" (ay) bicimindeki metinlerdir.
* Turetilmis hicbir deger burada yeniden hesaplanmaz; fark, yuzde, maliyet,
  EnPI ve hedef durumu mevcut fonksiyonlardan oldugu gibi alinir.
"""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import calc, dashboard, reports
from app.models import (
    Department,
    EnergyType,
    Meter,
    MeterReading,
    Production,
    Settings,
)
from app.web import month_label, parse_date

DEFAULT_CURRENCY = "TL"


# --------------------------------------------------------------------------- #
# Ic yardimcilar (disari veri sizdirmayan donusturuculer)
# --------------------------------------------------------------------------- #


def _as_date(value: date | str) -> date:
    """date nesnesini veya 'YYYY-MM-DD' metnini date'e cevirir."""
    if isinstance(value, date):
        return value
    return parse_date(value, "Tarih")


def _day(value: date | None) -> str | None:
    return value.isoformat() if value else None


def _currency(db: Session) -> str:
    settings = db.get(Settings, 1)
    return settings.currency if settings else DEFAULT_CURRENCY


def _energy_type(db: Session, energy_type_id: int) -> EnergyType:
    energy_type = db.get(EnergyType, energy_type_id)
    if energy_type is None:
        raise ValueError(f"Enerji türü bulunamadı (id: {energy_type_id}).")
    return energy_type


def _energy_type_payload(energy_type: EnergyType) -> dict:
    return {
        "id": energy_type.id,
        "ad": energy_type.name,
        "birim": energy_type.unit,
        "birim_fiyat": float(energy_type.unit_price),
        "aktif": bool(energy_type.is_active),
    }


# --------------------------------------------------------------------------- #
# 1. Tanimlar
# --------------------------------------------------------------------------- #


def list_definitions(db: Session) -> dict:
    """Sistemde gercekten tanimli olan enerji turleri, bolumler ve sayaclar.

    AI'nin olmayan bir bolum veya sayac uydurmasini engellemek icindir.
    """
    energy_types = list(db.scalars(select(EnergyType).order_by(EnergyType.id)))
    departments = list(db.scalars(select(Department).order_by(Department.id)))
    meters = list(db.scalars(select(Meter).order_by(Meter.id)))

    return {
        "enerji_turleri": [_energy_type_payload(item) for item in energy_types],
        "bolumler": [
            {"id": item.id, "ad": item.name, "aktif": bool(item.is_active)}
            for item in departments
        ],
        "sayaclar": [
            {
                "id": meter.id,
                "ad": meter.name,
                "enerji_turu": meter.energy_type.name,
                "enerji_turu_id": meter.energy_type_id,
                "bolum": meter.department.name if meter.department else None,
                "seri_no": meter.serial_no,
                "carpan": float(meter.multiplier),
                "ana_sayac": bool(meter.is_main),
                "aktif": bool(meter.is_active),
            }
            for meter in meters
        ],
    }


# --------------------------------------------------------------------------- #
# 2. Veri kapsami
# --------------------------------------------------------------------------- #


def get_data_coverage(db: Session) -> dict:
    """Hangi tarih araliginda veri var?

    AI'nin veri bulunmayan donemler icin uydurma cevap vermesini onler.
    Mevcut fonksiyonlarda kapsam bilgisi bulunmadigi icin burada dogrudan
    (yalnizca okuma yapan) toplama sorgulari kullanilir.
    """
    first_reading, last_reading, reading_count = db.execute(
        select(
            func.min(MeterReading.reading_date),
            func.max(MeterReading.reading_date),
            func.count(MeterReading.id),
        )
    ).one()
    first_production, last_production, production_count = db.execute(
        select(
            func.min(Production.production_date),
            func.max(Production.production_date),
            func.count(Production.id),
        )
    ).one()

    return {
        "ilk_okuma": _day(first_reading),
        "son_okuma": _day(last_reading),
        "okuma_sayisi": int(reading_count),
        "uretim_baslangic": _day(first_production),
        "uretim_bitis": _day(last_production),
        "uretim_kayit_sayisi": int(production_count),
        "uretim_birimleri": calc.production_units(db),
    }


# --------------------------------------------------------------------------- #
# 3. Donem ozeti
# --------------------------------------------------------------------------- #


def get_dashboard_summary(db: Session, year_month: str, energy_type_id: int) -> dict:
    """Bir ayin ozeti: tuketim, maliyet, onceki donem farki, hedef durumu.

    Butun degerler dashboard.energy_summary'den gelir; burada yeniden
    hesaplama yapilmaz.
    """
    energy_type = _energy_type(db, energy_type_id)
    summary = dashboard.energy_summary(db, energy_type, year_month)
    change = summary["change"]
    target = summary["target"]

    return {
        "donem": year_month,
        "donem_adi": month_label(year_month),
        "enerji_turu": _energy_type_payload(energy_type),
        "tuketim": summary["total"],
        "maliyet": summary["cost"],
        "para_birimi": _currency(db),
        "onceki_donem": {
            "donem": dashboard.shift_month(year_month, -1),
            "donem_adi": summary["previous_label"],
            "tuketim": change["previous"],
            "fark": change["difference"],
            "yuzde": change["percent"],
        },
        "hedef": (
            {
                "hedef": target["target"],
                "gerceklesen": target["actual"],
                "fark": target["difference"],
                "yuzde": target["percent"],
                "asildi": target["exceeded"],
                "durum": "hedef aşıldı" if target["exceeded"] else "hedef içinde",
            }
            if target
            else None
        ),
    }


# --------------------------------------------------------------------------- #
# 4. Serbest tarih araliginda tuketim
# --------------------------------------------------------------------------- #


def get_energy_consumption(
    db: Session,
    start: date | str,
    end: date | str,
    energy_type_id: int | None = None,
) -> dict:
    """Secilen aralikta fabrika tuketimi ve maliyeti (enerji turu basina).

    Farkli enerji turleri asla tek toplamda birlestirilmez; her tur kendi
    birimiyle ayri satirda kalir.
    """
    start_date, end_date = _as_date(start), _as_date(end)
    rows = reports.rows_by_energy_type(db, start_date, end_date)
    if energy_type_id is not None:
        _energy_type(db, energy_type_id)
        rows = [row for row in rows if row["energy_type"].id == energy_type_id]

    return {
        "baslangic": _day(start_date),
        "bitis": _day(end_date),
        "para_birimi": _currency(db),
        "satirlar": [
            {
                "enerji_turu_id": row["energy_type"].id,
                "enerji_turu": row["energy_type"].name,
                "birim": row["energy_type"].unit,
                "tuketim": row["total"],
                "maliyet": row["cost"],
            }
            for row in rows
        ],
    }


# --------------------------------------------------------------------------- #
# 5. Bolum kirilimi
# --------------------------------------------------------------------------- #


def get_department_breakdown(
    db: Session, energy_type_id: int, start: date | str, end: date | str
) -> dict:
    """Bolum dagilimi ve olculmeyen pay.

    Ana sayac / alt sayac / olculmeyen / kapsam uyarisi kurallari
    dashboard.department_breakdown icinde kalir; burada yalnizca duz JSON'a
    cevrilir.
    """
    energy_type = _energy_type(db, energy_type_id)
    start_date, end_date = _as_date(start), _as_date(end)

    factory_total = calc.total(
        calc.factory_consumptions(
            db, start=start_date, end=end_date, energy_type_id=energy_type.id
        )
    )
    breakdown = dashboard.department_breakdown(
        db, energy_type, start_date, end_date, factory_total
    )

    return {
        "baslangic": _day(start_date),
        "bitis": _day(end_date),
        "enerji_turu": energy_type.name,
        "birim": energy_type.unit,
        "fabrika_toplami": factory_total,
        "satirlar": [
            {
                "bolum": row["label"],
                "tuketim": row["value"],
                "pay": row["share"],
                "olculen": row["measured"],
            }
            for row in breakdown["rows"]
        ],
        "olculen_toplam": breakdown["measured"],
        "olculmeyen": breakdown["unmeasured"],
        "olcum_uyarisi": breakdown["scope_warning"],
    }


# --------------------------------------------------------------------------- #
# 6. Uretim ve EnPI
# --------------------------------------------------------------------------- #


def get_production_and_enpi(
    db: Session,
    unit: str,
    energy_type_id: int,
    start: date | str,
    end: date | str,
) -> dict:
    """Tek bir uretim birimi ve tek bir enerji turu icin uretim ve EnPI.

    EnPI degeri calc.enpi()'den alinir; burada bolme islemi yapilmaz.
    Uretim yoksa EnPI None doner.
    """
    energy_type = _energy_type(db, energy_type_id)
    start_date, end_date = _as_date(start), _as_date(end)

    produced = calc.production_total(db, unit, start=start_date, end=end_date)
    consumed = calc.total(
        calc.factory_consumptions(
            db, start=start_date, end=end_date, energy_type_id=energy_type.id
        )
    )

    return {
        "baslangic": _day(start_date),
        "bitis": _day(end_date),
        "uretim_birimi": unit,
        "uretim": produced,
        "enerji_turu": energy_type.name,
        "enerji_birimi": energy_type.unit,
        "tuketim": consumed,
        "enpi": calc.enpi(consumed, produced),
        "enpi_birimi": f"{energy_type.unit}/{unit}",
    }


# --------------------------------------------------------------------------- #
# 7. Trend
# --------------------------------------------------------------------------- #


def get_trend(
    db: Session,
    energy_type_id: int,
    year_month: str,
    months: int = dashboard.TREND_MONTHS,
    uretim_birimi: str | None = None,
) -> dict:
    """Secilen ay dahil son aylarin tuketim ve EnPI serisi.

    dashboard.monthly_trend ve dashboard.enpi_trend 12 aya sabittir; bu
    asamada dashboard.py degistirilmedigi icin baska bir ay sayisi
    desteklenmez ve acikca hata verilir.

    EnPI serisi tek bir uretim birimi icindir. Birim verilmezse, donemde en
    cok uretim yapilan birim secilir; hic uretim yoksa EnPI serisi bos kalir.
    """
    if months != dashboard.TREND_MONTHS:
        raise ValueError(
            f"Trend yalnızca {dashboard.TREND_MONTHS} ay için üretilebilir."
        )

    energy_type = _energy_type(db, energy_type_id)
    consumption = dashboard.monthly_trend(db, energy_type, year_month)

    first_month = dashboard.shift_month(year_month, -(months - 1))
    window_start, _ = dashboard.month_bounds(first_month)
    _, window_end = dashboard.month_bounds(year_month)
    units = calc.production_units(db, start=window_start, end=window_end)
    unit = uretim_birimi if uretim_birimi in units else (units[0] if units else None)

    enpi_points: list[dict] = []
    if unit is not None:
        series = dashboard.enpi_trend(db, energy_type, unit, year_month)
        enpi_points = [
            {"donem": point["month"], "deger": point["value"]}
            for point in series["points"]
        ]

    return {
        "donem": year_month,
        "ay_sayisi": months,
        "enerji_turu": energy_type.name,
        "birim": energy_type.unit,
        "tuketim": [
            {"donem": point["month"], "deger": point["value"]}
            for point in consumption
        ],
        "uretim_birimi": unit,
        "enpi_birimi": f"{energy_type.unit}/{unit}" if unit else None,
        "enpi": enpi_points,
    }


# --------------------------------------------------------------------------- #
# 8. Hedefler
# --------------------------------------------------------------------------- #


def get_targets(db: Session, start: date | str, end: date | str) -> dict:
    """Araliga tamamen giren aylarin hedefleri ve gerceklesme durumu."""
    start_date, end_date = _as_date(start), _as_date(end)
    rows = reports.target_rows(db, start_date, end_date)

    return {
        "baslangic": _day(start_date),
        "bitis": _day(end_date),
        "hedefler": [
            {
                "donem_adi": row["label"],
                "enerji_turu": row["energy_type"].name,
                "birim": row["energy_type"].unit,
                "hedef": row["status"]["target"],
                "gerceklesen": row["status"]["actual"],
                "fark": row["status"]["difference"],
                "yuzde": row["status"]["percent"],
                "asildi": row["status"]["exceeded"],
                "durum": (
                    "hedef aşıldı" if row["status"]["exceeded"] else "hedef içinde"
                ),
            }
            for row in rows
        ],
    }


# --------------------------------------------------------------------------- #
# Merkezi kayit
# --------------------------------------------------------------------------- #

# Yalnizca merkezi erisim icindir; bu asamada hicbir modele baglanmaz.
TOOLS = {
    "list_definitions": list_definitions,
    "get_data_coverage": get_data_coverage,
    "get_dashboard_summary": get_dashboard_summary,
    "get_energy_consumption": get_energy_consumption,
    "get_department_breakdown": get_department_breakdown,
    "get_production_and_enpi": get_production_and_enpi,
    "get_trend": get_trend,
    "get_targets": get_targets,
}
