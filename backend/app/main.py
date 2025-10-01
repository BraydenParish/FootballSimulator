from fastapi import FastAPI

app = FastAPI(title="NFL GM Simulator API")


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Simple health endpoint to verify the service is running."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
