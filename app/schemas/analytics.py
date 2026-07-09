import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class ClickEventResponse(BaseModel):
    id: uuid.UUID
    clicked_at: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]
    referrer: Optional[str]

    model_config = ConfigDict(from_attributes=True)

class URLAnalyticsResponse(BaseModel):
    short_code: str
    original_url: str
    total_clicks: int
    clicks: List[ClickEventResponse]

    model_config = ConfigDict(from_attributes=True)
