"""
FastAPI app entrypoint — REST endpoints for cohort state + the WebSocket
endpoint for the live dashboard.
"""
from fastapi import FastAPI

app = FastAPI(title="Clinical Deterioration Copilot")


@app.get("/health")
async def health():
    return {"status": "ok"}

# TODO: include the websocket router from src/api/websocket.py
