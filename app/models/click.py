import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import BigInteger, String, Text, DateTime, ForeignKey, func, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.url import URL

class ClickEvent(Base):
    __tablename__ = "click_events"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    url_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("urls.id", ondelete="CASCADE"), nullable=False
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    referrer: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    
    # Enriched analytics columns
    country_code: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True
    )
    device_family: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )
    browser_family: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )
    os_family: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )
    
    # Aggregation indexing flag
    aggregated: Mapped[bool] = mapped_column(
        Boolean, default=False, index=True, nullable=False
    )
    
    clicked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    url: Mapped["URL"] = relationship(
        "URL", back_populates="clicks"
    )
