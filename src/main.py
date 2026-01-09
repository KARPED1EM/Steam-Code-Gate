from fastapi import FastAPI, Request
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


@app.get("/")
async def root():
    return RedirectResponse(url="/login")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
