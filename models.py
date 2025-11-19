from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime


class URLItem(BaseModel):
    url: HttpUrl
    alias: str = None

class StatRequest(BaseModel):
    alias: str




class ClickEvent(BaseModel):
    short_id: str                  # the short URL identifier
    clicked_at: datetime           # timestamp of the click
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
