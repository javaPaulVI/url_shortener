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


from tinydb import TinyDB, Query
from datetime import datetime
import random, string
import re


RESERVED_PATHS = ["shorten", "r", "stats", "docs", "redoc", "openapi.json"]

db = TinyDB("db/db.json")

def generate_short_id(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))




def sanitize_alias(alias: str) -> str:
    """Remove unsafe characters and lowercase the alias."""
    alias = re.sub(r'[^a-zA-Z0-9_-]', '', alias)
    return alias.lower()

class URLsTable:
    def __init__(self):
        self.table = db.table("urls")
        self.query = Query()


    def create_url(self, data: URLItem):
        # Sanitize custom alias
        custom_alias = sanitize_alias(data.alias) if data.alias else None

        # Check for reserved paths
        if custom_alias and custom_alias in RESERVED_PATHS:
            return {"success": False, "message": "This alias is reserved and cannot be used."}

        # Check for collision with existing short_ids
        if custom_alias and self.table.get(self.query.short_id == custom_alias):
            return {"success": False, "message": "This alias is already taken. Please choose another."}


        # Generate short_id if no custom alias
        short_id = custom_alias if custom_alias else generate_short_id()
        while self.table.get(self.query.short_id == short_id):
            short_id = generate_short_id()

        record = {
            "short_id": short_id,
            "long_url": str(data.url),  # Convert HttpUrl to string
            "created_at": datetime.now().isoformat(),
            "expires_at": None,
            "clicks": 0,
            "custom_alias": custom_alias
        }
        self.table.insert(record)

        return record

    def get_url(self, short_id: str):
        return self.table.get(self.query.short_id == short_id)

    def increment_clicks(self, short_id: str):
        url = self.get_url(short_id)
        if url:
            self.table.update({'clicks': url['clicks'] + 1}, self.query.short_id == short_id)
        return url

class StatsTable:
    def __init__(self):
        self.table = db.table("clicks")

    def add_click(self, short_id: str, ip_address: str = None, user_agent: str = None):
        record = {
            "short_id": short_id,
            "clicked_at": datetime.now().isoformat(),
            "ip_address": ip_address,
            "user_agent": user_agent
        }
        self.table.insert(record)

    def get_clicks_for_url(self, short_id: str):
        return [r for r in self.table if r['short_id'] == short_id]



from fastapi import FastAPI, APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from mangum import Mangum

RESERVED_PATHS = ["shorten", "r", "stats", "docs", "redoc", "openapi.json"]

app = FastAPI()
api = APIRouter(prefix="/api")
router = APIRouter(prefix="/url")

url_table = URLsTable()
stats_table = StatsTable()


@api.post("/shorten")
async def shorten(item: URLItem):
    return url_table.create_url(item)


@api.post("/get_stats/{short_id}")
async def get_stats(stat_request: StatRequest):
    return stats_table.get_clicks_for_url(stat_request.alias)


@app.get("/r/{short_id}")
def redirect(short_id: str, request: Request):
    # Retrieve client IP and user-agent
    client_ip = request.headers.get("x-forwarded-for", request.client.host)
    user_agent = request.headers.get("user-agent")

    # Increment clicks
    url = url_table.increment_clicks(short_id)
    if not url:
        raise HTTPException(status_code=404, detail="Short URL not found")

    # Record click event
    stats_table.add_click(
        short_id=short_id,
        ip_address=client_ip,
        user_agent=user_agent
    )

    # Return redirect URL (or use FastAPI RedirectResponse)
    return RedirectResponse(url["long_url"])


@api.get("/get_redirect_url/{short_id}")
def get_redirect_url(short_id: str):
    # Increment clicks
    url = url_table.increment_clicks(short_id)
    if not url:
        raise HTTPException(status_code=404, detail="Short URL not found")

    return { "long_url": url["long_url"]}
app.include_router(api)
app.include_router(router)

Mangum(app)