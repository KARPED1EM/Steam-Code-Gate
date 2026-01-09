from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.gzip import GZipMiddleware

from src.config import config
from src.database.init_db import setup_database
from src.routes import admin, auth, home


class CacheControlMiddleware(BaseHTTPMiddleware):
    """Add cache control headers for static files"""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/static/"):
            # Cache static files for 1 year (immutable resources)
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_database()
    yield
    # Shutdown - cleanup thread pools
    from src.routes import admin, home
    if hasattr(admin, '_thread_pool'):
        admin._thread_pool.shutdown(wait=True)
    if hasattr(home, '_thread_pool'):
        home._thread_pool.shutdown(wait=True)


app = FastAPI(title="Steam Code Gate", lifespan=lifespan)

# Add GZip compression middleware to reduce response sizes
app.add_middleware(GZipMiddleware, minimum_size=500)

# Add cache control middleware for static files
app.add_middleware(CacheControlMiddleware)

# Static files with caching headers for production performance
app.mount(
    "/static",
    StaticFiles(directory=config.STATIC_DIR, html=False),
    name="static"
)

app.include_router(auth.router, tags=["Authentication"])
app.include_router(home.router, tags=["Home"])
app.include_router(admin.router, tags=["Admin"])


@app.exception_handler(HTTPException)
async def auth_redirect_handler(request: Request, exc: HTTPException):
    if exc.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN):
        path = request.url.path
        if request.method == "GET" and not path.startswith("/api/"):
            if path not in {"/login", "/logout"}:
                return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    return await http_exception_handler(request, exc)


@app.get("/")
async def root():
    return RedirectResponse(url="/login")


if __name__ == "__main__":
    import os
    import uvicorn

    # Only enable reload in development environment (default: production)
    is_dev = os.getenv("ENVIRONMENT", "").lower() == "development"
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=is_dev)
