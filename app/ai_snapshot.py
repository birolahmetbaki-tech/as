"""AI'ye gonderilecek deterministik veri anlik goruntusu.

Snapshot, AI'nin uzerinde HESAP YAPACAGI veri degildir; uygulamanin zaten
hesaplamis oldugu sonuclarin tasindigi veridir. Butun degerler ai_tools
uzerinden mevcut calc / dashboard / reports fonksiyonlarindan gelir.

Ham sayac okumalari ve gereksiz kayitlar snapshot'a konmaz.
"""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import ai_tools, calc, dashboard
from app.models import EnergyType, Settings


def default_period() -> str:
    """Icinde bulunulan ay."""
    return date.today().strftime("%Y-%m")


def _default_energy_type_id(db: Session) -> int | None:
    """Tanim sirasindaki ilk enerji turu (panelin varsayilaniyla ayni kural)."""
    return db.scalars(select(EnergyType.id).order_by(EnergyType.id)).first()


def build_snapshot(
    db: Session,
    year_month: str | None = None,
    energy_type_id: int | None = None,
    uretim_birimi: str | None = None,
) -> dict:
    """Bir donem ve bir enerji turu icin AI'ye verilecek veri paketi."""
    period = year_month or default_period()
    start, end = dashboard.month_bounds(period)
    settings = db.get(Settings, 1)

    snapshot: dict = {
        "donem": period,
        "donem_adi": dashboard.month_label(period),
        "fabrika": {
            "ad": settings.factory_name if settings else "Fabrika",
            "para_birimi": settings.currency if settings else ai_tools.DEFAULT_CURRENCY,
        },
        "veri_kapsami": ai_tools.get_data_coverage(db),
        "tanimlar": ai_tools.list_definitions(db),
    }

    selected_id = energy_type_id or _default_energy_type_id(db)
    if selected_id is None:
        # Henuz enerji turu tanimlanmamis: uydurulacak hicbir sey yok.
        snapshot["enerji"] = None
        snapshot["bolum_dagilimi"] = None
        snapshot["uretim_ve_enpi"] = []
        snapshot["trend"] = None
        snapshot["hedefler"] = []
        return snapshot

    snapshot["enerji"] = ai_tools.get_dashboard_summary(db, period, selected_id)
    snapshot["bolum_dagilimi"] = ai_tools.get_department_breakdown(
        db, selected_id, start, end
    )
    # Her uretim birimi icin ayri satir; birimler asla birlestirilmez.
    snapshot["uretim_ve_enpi"] = [
        ai_tools.get_production_and_enpi(db, unit, selected_id, start, end)
        for unit in calc.production_units(db, start=start, end=end)
    ]
    snapshot["trend"] = ai_tools.get_trend(
        db, selected_id, period, uretim_birimi=uretim_birimi
    )
    snapshot["hedefler"] = ai_tools.get_targets(db, start, end)["hedefler"]
    return snapshot
