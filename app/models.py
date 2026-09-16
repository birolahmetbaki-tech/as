"""Veri modeli.

MVP kapsaminda yedi tablo vardir. Tuketim, maliyet ve EnPI gibi turetilmis
degerler saklanmaz; bunlar hesaplama modulunde uretilir.
"""

from sqlalchemy import (
    Boolean,
    Date,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Settings(Base):
    """Fabrika geneli ayarlar. Tek satir tutulur (id=1)."""

    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    factory_name: Mapped[str] = mapped_column(String(120), default="Fabrika")
    currency: Mapped[str] = mapped_column(String(10), default="TL")


class EnergyType(Base):
    """Elektrik, dogal gaz, su gibi enerji turleri."""

    __tablename__ = "energy_type"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(60), unique=True)
    unit: Mapped[str] = mapped_column(String(20))
    unit_price: Mapped[float] = mapped_column(Float, default=0.0)

    meters: Mapped[list["Meter"]] = relationship(back_populates="energy_type")


class Department(Base):
    """Fabrika bolumu."""

    __tablename__ = "department"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    meters: Mapped[list["Meter"]] = relationship(back_populates="department")


class Meter(Base):
    """Sayac.

    multiplier: okunan endeks farki bu katsayi ile carpilir (varsayilan 1).
    is_main: ana sayac ise True. Ayni enerji turunde ana sayac tanimliysa
             fabrika toplami ana sayaclardan hesaplanir; boylece ana ve alt
             sayaclarin mukerrer toplanmasi onlenir.
    """

    __tablename__ = "meter"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    energy_type_id: Mapped[int] = mapped_column(ForeignKey("energy_type.id"))
    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("department.id"), nullable=True
    )
    serial_no: Mapped[str | None] = mapped_column(String(60), nullable=True)
    multiplier: Mapped[float] = mapped_column(Float, default=1.0)
    is_main: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    energy_type: Mapped["EnergyType"] = relationship(back_populates="meters")
    department: Mapped["Department | None"] = relationship(back_populates="meters")
    readings: Mapped[list["MeterReading"]] = relationship(
        back_populates="meter", cascade="all, delete-orphan"
    )


class MeterReading(Base):
    """Belirli bir tarihteki sayac endeksi. Ham veridir, tuketim degildir."""

    __tablename__ = "meter_reading"
    __table_args__ = (UniqueConstraint("meter_id", "reading_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    meter_id: Mapped[int] = mapped_column(ForeignKey("meter.id"))
    reading_date: Mapped[Date] = mapped_column(Date, index=True)
    index_value: Mapped[float] = mapped_column(Float)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    meter: Mapped["Meter"] = relationship(back_populates="readings")


class Production(Base):
    """Uretim kaydi. Birim kayit basina secilir (ton, adet vb.)."""

    __tablename__ = "production"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    production_date: Mapped[Date] = mapped_column(Date, index=True)
    quantity: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(20))


class Target(Base):
    """Aylik tuketim hedefi (enerji turu bazinda)."""

    __tablename__ = "target"
    __table_args__ = (UniqueConstraint("year_month", "energy_type_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    year_month: Mapped[str] = mapped_column(String(7))  # "2026-01"
    energy_type_id: Mapped[int] = mapped_column(ForeignKey("energy_type.id"))
    target_value: Mapped[float] = mapped_column(Float)

    energy_type: Mapped["EnergyType"] = relationship()
