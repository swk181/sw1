import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="WoS MCP Server")

WOS_API_KEY = os.getenv("WOS_API_KEY", "")

class SearchRequest(BaseModel):
    query: str
    limit: int = 10

@app.get("/")
def health_check():
    return {"status": "ok", "message": "WoS MCP Server is running"}

@app.post("/mcp/search")
def search_wos(req: SearchRequest):
    if not WOS_API_KEY:
        raise HTTPException(status_code=500, detail="WOS_API_KEY not configured")

    url = f"https://api.clarivate.com/api/wos?q={req.query}&limit={req.limit}"
    headers = {
        "X-ApiKey": WOS_API_KEY,
        "Accept": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
