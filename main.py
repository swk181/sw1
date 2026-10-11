import os
import requests
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

# 1. MCP 서버 생성
mcp = FastMCP("Web of Science & Elsevier Search")

# API Key 로드
API_KEY = os.getenv("WOS_API_KEY", "")

# 2. MCP Tool 정의 (ChatGPT가 자동으로 인식하는 검색 도구)
@mcp.tool()
def search_literature(query: str, limit: int = 10) -> str:
    """Search literature in Web of Science / Elsevier DB."""
    if not API_KEY:
        return "Error: API_KEY is not configured on the server."
    
    url = f"https://api.clarivate.com/api/wos?q={query}&limit={limit}"
    headers = {
        "X-ApiKey": API_KEY,
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        return f"API Call Error: {str(e)}"

# 3. FastAPI 앱 결합
app = FastAPI()

@app.get("/")
def home():
    return {"status": "MCP Server Active"}

# MCP HTTP/SSE 엔드포인트 마운트
app.mount("/mcp", mcp.sse_app())
