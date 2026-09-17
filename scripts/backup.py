"""Veritabaninin guvenli yedegini alir.

Kullanim:
    python scripts/backup.py              -> backups/ klasorune yazar
    python scripts/backup.py D:\\Yedek     -> verilen klasore yazar

Neden duz dosya kopyasi yetmez:
Uygulama SQLite'i WAL kipinde calistirir. Bu kipte henuz ana dosyaya
islenmemis kayitlar 'enerji.db-wal' dosyasinda bekler. Uygulama aciken
yalnizca 'enerji.db' kopyalanirsa bu kayitlar yedege GIRMEZ; yedek sessizce
eksik olur. Bu betik SQLite'in kendi yedekleme arayuzunu kullanir, bu yuzden
uygulama calisirken de tam ve tutarli bir kopya uretir.

Harici bir program (sqlite3.exe gibi) gerekmez; yalnizca Python kullanilir.
"""

import sqlite3
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config  # noqa: E402

BASE_DIR = Path(__file__).resolve().parent.parent


def database_path() -> Path:
    """Ayarlardaki veritabani dosyasinin gercek yolu."""
    url = config.database_url()
    if not url.startswith("sqlite"):
        raise SystemExit(f"Bu betik yalnizca SQLite icindir. Ayarli veritabani: {url}")
    return Path(url.split("///", 1)[1])


def backup(source: Path, target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    damga = datetime.now().strftime("%Y-%m-%d_%H%M")
    target = target_dir / f"enerji-{damga}.db"
    sira = 2
    while target.exists():
        target = target_dir / f"enerji-{damga}-{sira}.db"
        sira += 1

    # Salt okunur baglanti: yedek alirken veritabanina yazilmaz.
    kaynak = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    hedef = sqlite3.connect(target)
    try:
        with hedef:
            kaynak.backup(hedef)
    finally:
        hedef.close()
        kaynak.close()

    # Yedek tek dosya olarak dursun; yanindaki -wal/-shm gereksizdir.
    for ek in ("-wal", "-shm"):
        yan = Path(str(target) + ek)
        if yan.exists():
            yan.unlink()
    return target


if __name__ == "__main__":
    source = database_path()
    if not source.is_file():
        raise SystemExit(
            f"Veritabani bulunamadi: {source}\n"
            "Once 'alembic upgrade head' calistirip uygulamayi bir kez acin."
        )

    target_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE_DIR / "backups"
    target = backup(source, target_dir)
    boyut = target.stat().st_size
    print(f"Yedek alindi: {target}")
    print(f"Boyut       : {boyut:,} bayt".replace(",", "."))
    print(
        "\nBu dosyayi USB bellege veya baska bir diske de kopyalayin; "
        "ayni bilgisayarda durursa disk arizasinda veriyle birlikte kaybolur."
    )
