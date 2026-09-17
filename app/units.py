"""Birim envanteri ve MATEMATIKSEL birim donusumleri.

Bu modul yalnizca sabit oranli donusum yapar: ayni boyuttaki (dimension) iki
birim arasinda cevirir. Veritabanina dokunmaz, internete cikmaz, ayar
okumaz; saf bir hesap kutuphanesidir ve tek basina test edilebilir.

ONEMLI AYRIM
------------
Matematiksel birim donusumu   kWh -> MJ, MJ -> GJ, kg -> ton
    Sabittir, her yerde aynidir, burada tanimlidir.

Enerji icerigi katsayisi      Sm3 dogal gaz -> GJ, kg komur -> GJ, kg LPG -> GJ
    Yakitin kalitesine, tedarikciye ve olcum bazina (UID/HHV, AID/LHV) gore
    degisir. BURADA TANIMLI DEGILDIR ve olmamalidir: bir yakit icin buraya
    "makul" bir varsayilan yazmak, yanlis sonucu dogru gibi gostermek olur.
    Bu katsayilar kullanici tarafindan tanimlanir (energy_conversion tablosu)
    ve calc modulunden okunur.

BOYUTLAR
--------
Bugun yalnizca ENERJI boyutu kayitlidir; sistemde kullanilan tek boyut budur.
Altyapi boyut kavrami uzerine kuruldugu icin uzunluk, alan, hacim, kutle,
basinc, guc, zaman, debi, elektriksel birimler ve yogunluk gibi boyutlar
ileride yalnizca register() cagrilariyla eklenebilir; baska hicbir yerde
degisiklik gerekmez.

Sicaklik bir istisnadir: Celsius/Fahrenheit donusumu sabit oran degil
kaydirmali (afin) bir donusumdur. Sicaklik eklenecegi gun Unit'in carpan
disinda bir kayma degeri de tasimasi gerekir; bugun bilerek eklenmemistir.
"""

from dataclasses import dataclass

DIMENSION_ENERGY = "enerji"


class UnknownUnit(ValueError):
    """Tanimsiz birim kodu."""


class DimensionMismatch(ValueError):
    """Farkli boyuttaki birimler arasinda donusum istendi."""


@dataclass(frozen=True)
class Unit:
    """Bir birim ve boyutunun referans birimine gore carpani.

    factor: 1 <code> kac <referans birim> eder. Ornek: 1 kWh = 0,0036 GJ.
    """

    code: str
    name: str
    dimension: str
    factor: float


_UNITS: dict[str, Unit] = {}
_REFERENCE: dict[str, str] = {}


def register(code: str, name: str, dimension: str, factor: float) -> Unit:
    """Envantere birim ekler. Bir boyutun ILK birimi referans olmak zorundadir.

    Referans birimin carpani 1.0'dir; bir boyutun referansi sonradan
    degistirilmez.
    """
    if code in _UNITS:
        raise ValueError(f"'{code}' birimi zaten tanimli.")
    if dimension not in _REFERENCE:
        if factor != 1.0:
            raise ValueError(
                f"'{dimension}' boyutunun ilk birimi referans olmalidir "
                "(carpan 1.0)."
            )
        _REFERENCE[dimension] = code
    if factor <= 0:
        raise ValueError(f"'{code}' birimi icin carpan sifirdan buyuk olmalidir.")

    unit = Unit(code=code, name=name, dimension=dimension, factor=factor)
    _UNITS[code] = unit
    return unit


def reference_unit(dimension: str) -> str:
    """Boyutun referans birimi (enerji icin GJ)."""
    try:
        return _REFERENCE[dimension]
    except KeyError:
        raise UnknownUnit(f"'{dimension}' boyutunda tanimli birim yok.") from None


def find(code: str | None) -> Unit | None:
    """Birimi kodundan bulur; buyuk/kucuk harf farkini gozetmez. Yoksa None."""
    text = (code or "").strip()
    if not text:
        return None
    if text in _UNITS:
        return _UNITS[text]
    target = text.casefold()
    for unit in _UNITS.values():
        if unit.code.casefold() == target:
            return unit
    return None


def get(code: str) -> Unit:
    """Birimi kodundan bulur; yoksa UnknownUnit yukseltir."""
    unit = find(code)
    if unit is None:
        raise UnknownUnit(f"'{code}' tanimli bir birim degil.")
    return unit


def is_known(code: str | None) -> bool:
    return find(code) is not None


def dimension_of(code: str | None) -> str | None:
    unit = find(code)
    return unit.dimension if unit else None


def units_of(dimension: str) -> tuple[Unit, ...]:
    """Bir boyutun butun birimleri, buyukten kucuge degil tanim sirasinda."""
    return tuple(unit for unit in _UNITS.values() if unit.dimension == dimension)


def factor_between(from_code: str, to_code: str) -> float:
    """1 <from_code> kac <to_code> eder?"""
    source, target = get(from_code), get(to_code)
    if source.dimension != target.dimension:
        raise DimensionMismatch(
            f"'{source.code}' ({source.dimension}) ile '{target.code}' "
            f"({target.dimension}) ayni boyutta degil; donusturulemez."
        )
    return source.factor / target.factor


def convert(value: float, from_code: str, to_code: str) -> float:
    """Degeri ayni boyuttaki baska bir birime cevirir."""
    return value * factor_between(from_code, to_code)


def to_reference(value: float, from_code: str) -> float:
    """Degeri kendi boyutunun referans birimine cevirir."""
    unit = get(from_code)
    return value * unit.factor


# --------------------------------------------------------------------------- #
# Enerji birimleri. Referans: GJ
#
# Kaynak degerler (tanim geregi sabittir, olcume bagli degildir):
#   1 Wh    = 3.600 J          (1 W x 1 saat)
#   1 cal   = 4,1868 J         (uluslararasi tablo kalorisi)
#   1 TEP   = 41,868 GJ        (= 10 Gcal = 11.630 kWh, IEA/ISO tanimi)
#   1 BTU   = 1.055,05585262 J (uluslararasi tablo BTU'su)
# --------------------------------------------------------------------------- #

register("GJ", "gigajul", DIMENSION_ENERGY, 1.0)
register("J", "jul", DIMENSION_ENERGY, 1e-9)
register("kJ", "kilojul", DIMENSION_ENERGY, 1e-6)
register("MJ", "megajul", DIMENSION_ENERGY, 1e-3)
register("TJ", "terajul", DIMENSION_ENERGY, 1e3)

register("Wh", "vatsaat", DIMENSION_ENERGY, 3.6e-6)
register("kWh", "kilovatsaat", DIMENSION_ENERGY, 3.6e-3)
register("MWh", "megavatsaat", DIMENSION_ENERGY, 3.6)
register("GWh", "gigavatsaat", DIMENSION_ENERGY, 3.6e3)

register("kcal", "kilokalori", DIMENSION_ENERGY, 4.1868e-6)
register("Mcal", "megakalori", DIMENSION_ENERGY, 4.1868e-3)
register("Gcal", "gigakalori", DIMENSION_ENERGY, 4.1868)

register("TEP", "ton eşdeğer petrol", DIMENSION_ENERGY, 41.868)
register("kgep", "kilogram eşdeğer petrol", DIMENSION_ENERGY, 41.868e-3)

# British / US customary
register("BTU", "British thermal unit", DIMENSION_ENERGY, 1.05505585262e-6)
register("MMBTU", "milyon BTU", DIMENSION_ENERGY, 1.05505585262)
register("therm", "therm", DIMENSION_ENERGY, 0.105505585262)

ENERGY_REFERENCE = reference_unit(DIMENSION_ENERGY)
