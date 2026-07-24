"""
OAMI API Routes
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.dashboard.market_indices import MarketIndexFeed

router = APIRouter()

templates = Jinja2Templates(directory="templates")


@router.get("/")
async def home():
    return {
        "application": settings.app["name"],
        "version": settings.app["version"],
        "status": "running",
    }


@router.get("/health")
async def health():
    return {
        "status": "healthy"
    }


@router.get("/api/market-indices")
async def market_indices():
    """Expose passive index snapshots for the dashboard only."""
    feed = MarketIndexFeed(
        settings.observability.get(
            "analytics_database_path", "data/oami_analytics.sqlite3"
        )
    )
    return {"indices": feed.latest()}


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):

    print("=" * 60)
    print("STEP 1 : Dashboard route reached")
    print("=" * 60)

    try:

        print("STEP 2 : Loading dashboard template...")

        response = templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={
                "request": request,
                "title": "OAMI Dashboard",
                "refresh_interval": settings.dashboard.get("refresh_interval", 1),
            },
        )

        print("STEP 3 : Template loaded successfully")

        return response

    except Exception as e:

        print("=" * 60)
        print("TEMPLATE ERROR")
        print(type(e).__name__)
        print(str(e))
        print("=" * 60)

        raise
