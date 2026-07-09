import uuid
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, AnyHttpUrl, Field, ConfigDict, field_validator

class URLBase(BaseModel):
    original_url: AnyHttpUrl

class URLCreate(URLBase):
    custom_alias: Optional[str] = Field(
        None, 
        min_length=3, 
        max_length=30, 
        pattern=r"^[a-zA-Z0-9_-]+$",
    )
    expires_at: Optional[datetime] = None

    @field_validator("expires_at")
    @classmethod
    def validate_expires_at(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is not None:
            if v.tzinfo is None:
                v = v.replace(tzinfo=timezone.utc)
            if v <= datetime.now(timezone.utc):
                raise ValueError("Expiration date must be in the future")
        return v

class URLResponse(BaseModel):
    id: int
    original_url: str
    short_code: str
    expires_at: Optional[datetime]
    created_at: datetime
    user_id: Optional[uuid.UUID]
    short_url: str

    model_config = ConfigDict(from_attributes=True)
