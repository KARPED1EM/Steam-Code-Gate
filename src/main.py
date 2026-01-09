from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from src.config import config
from src.database.init_db import setup_database
from src.routes import admin, auth, home

app = FastAPI(title="Steam Code Gate")

app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")

app.include_router(auth.router, tags=["Authentication"])
app.include_router(home.router, tags=["Home"])
app.include_router(admin.router, tags=["Admin"])


@app.on_event("startup")
async def startup_event():
    setup_database()


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
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
