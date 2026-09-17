"""Yedegi geri yukler.

Kullanim:
    python scripts/restore.py                       -> yedekleri listeler
    python scripts/restore.py backups/enerji-....db -> o yedegi geri yukler

ONEMLI: Geri yuklemeden once uygulamayi kapatin. Geri yukleme, mevcut
veritabaninin uzerine yazar; islemden once mevcut veritabani otomatik olarak
'geri-yukleme-oncesi-...' adiyla yedeklenir, boylece yanlis dosya secilse bile
eski duruma donulebilir.
"""

import sqlite3
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.backup import BASE_DIR, backup, database_path  # noqa: E402

# Yedegin gercekten bu uygulamaya ait oldugunu gosteren tablolar.
BEKLENEN_TABLOLAR = {"energy_type", "meter", "meter_reading", "direct_consumption"}


def tablolar(path: Path) -> set[str]:
    baglanti = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        return {
            satir[0]
            for satir in baglanti.execute(
                "select name from sqlite_master where type='table'"
            )
        }
    finally:
        baglanti.close()


def yedekleri_listele(klasor: Path) -> list[Path]:
    if not klasor.is_dir():
        return []
    return sorted(klasor.glob("*.db"), key=lambda p: p.stat().st_mtime, reverse=True)


def restore(source: Path, target: Path) -> None:
    """Yedegi calisan veritabaninin uzerine yazar."""
    kaynak = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    hedef = sqlite3.connect(target)
    try:
        with hedef:
            kaynak.backup(hedef)
    finally:
        hedef.close()
        kaynak.close()


if __name__ == "__main__":
    hedef = database_path()
    yedek_klasoru = BASE_DIR / "backups"

    if len(sys.argv) < 2:
        mevcut = yedekleri_listele(yedek_klasoru)
        if not mevcut:
            raise SystemExit(
                f"{yedek_klasoru} klasorunde yedek yok.\n"
                "Yedek almak icin: python scripts/backup.py"
            )
        print("Mevcut yedekler (en yeni ustte):\n")
        for dosya in mevcut:
            an = datetime.fromtimestamp(dosya.stat().st_mtime)
            print(f"  {dosya}  ({an:%d.%m.%Y %H:%M}, {dosya.stat().st_size:,} bayt)")
        print("\nGeri yuklemek icin dosya yolunu verin:")
        print(f"  python scripts/restore.py {mevcut[0]}")
        raise SystemExit(0)

    source = Path(sys.argv[1])
    if not source.is_file():
        raise SystemExit(f"Yedek dosyasi bulunamadi: {source}")

    try:
        bulunan = tablolar(source)
    except sqlite3.DatabaseError as hata:
        raise SystemExit(f"Bu dosya bir SQLite veritabani degil: {source} ({hata})")
    eksik = BEKLENEN_TABLOLAR - bulunan
    if eksik:
        raise SystemExit(
            f"Bu dosya bu uygulamanin yedegine benzemiyor; su tablolar yok: "
            f"{', '.join(sorted(eksik))}"
        )

    print(f"Geri yuklenecek yedek : {source}")
    print(f"Yazilacak veritabani  : {hedef}")
    print("\nUygulamanin KAPALI oldugundan emin olun.")
    onay = input("Devam edilsin mi? (evet/hayir): ").strip().lower()
    if onay not in ("e", "evet"):
        raise SystemExit("Islem iptal edildi. Hicbir sey degismedi.")

    if hedef.is_file():
        guvenlik = backup(hedef, yedek_klasoru)
        yeni_ad = guvenlik.with_name(
            f"geri-yukleme-oncesi-{datetime.now():%Y-%m-%d_%H%M}.db"
        )
        guvenlik.rename(yeni_ad)
        print(f"\nMevcut veritabani once yedeklendi: {yeni_ad}")
    else:
        hedef.parent.mkdir(parents=True, exist_ok=True)

    restore(source, hedef)
    for ek in ("-wal", "-shm"):
        yan = Path(str(hedef) + ek)
        if yan.exists():
            yan.unlink()
    print(f"\nGeri yukleme tamamlandi: {hedef}")
    print("Uygulamayi yeniden baslatabilirsiniz.")
