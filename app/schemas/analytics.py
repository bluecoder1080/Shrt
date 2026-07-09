from datetime import date
from typing import List
from pydantic import BaseModel, ConfigDict

class DailyClicksResponse(BaseModel):
    date: date
    click_count: int
    
    model_config = ConfigDict(from_attributes=True)

class CountryClicksResponse(BaseModel):
    country_code: str
    click_count: int
    
    model_config = ConfigDict(from_attributes=True)

class ReferrerClicksResponse(BaseModel):
    referrer: str
    click_count: int
    
    model_config = ConfigDict(from_attributes=True)

class AttributeClicksResponse(BaseModel):
    name: str
    click_count: int
    
    model_config = ConfigDict(from_attributes=True)

class URLAnalyticsSummaryResponse(BaseModel):
    short_code: str
    original_url: str
    total_clicks: int
    clicks_over_time: List[DailyClicksResponse]
    top_countries: List[CountryClicksResponse]
    top_referrers: List[ReferrerClicksResponse]
    device_breakdown: List[AttributeClicksResponse]
    browser_breakdown: List[AttributeClicksResponse]
    os_breakdown: List[AttributeClicksResponse]
