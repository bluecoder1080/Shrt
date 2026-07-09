from datetime import date
from sqlalchemy import BigInteger, String, Text, Date, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class DailyClicksSummary(Base):
    __tablename__ = "clicks_daily_summary"
    
    url_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("urls.id", ondelete="CASCADE"), primary_key=True
    )
    date: Mapped[date] = mapped_column(
        Date, primary_key=True
    )
    click_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

class CountryClicksSummary(Base):
    __tablename__ = "clicks_country_summary"
    
    url_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("urls.id", ondelete="CASCADE"), primary_key=True
    )
    country_code: Mapped[str] = mapped_column(
        String(10), primary_key=True
    )
    click_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

class ReferrerClicksSummary(Base):
    __tablename__ = "clicks_referrer_summary"
    
    url_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("urls.id", ondelete="CASCADE"), primary_key=True
    )
    referrer: Mapped[str] = mapped_column(
        Text, primary_key=True
    )
    click_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

class DeviceClicksSummary(Base):
    __tablename__ = "clicks_device_summary"
    
    url_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("urls.id", ondelete="CASCADE"), primary_key=True
    )
    device_family: Mapped[str] = mapped_column(
        String(50), primary_key=True
    )
    browser_family: Mapped[str] = mapped_column(
        String(50), primary_key=True
    )
    os_family: Mapped[str] = mapped_column(
        String(50), primary_key=True
    )
    click_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
