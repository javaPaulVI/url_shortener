from fastapi import FastAPI, APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from api.db.models import URLItem, StatRequest
from db import StatsTable, URLsTable
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