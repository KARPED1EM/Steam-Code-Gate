import os
import uvicorn

if __name__ == "__main__":
    # Only enable reload in development environment (default: production)
    is_dev = os.getenv("ENVIRONMENT", "").lower() == "development"
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=is_dev)
