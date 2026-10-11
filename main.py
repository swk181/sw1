import os
import json
import asyncio
import requests
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse

app = FastAPI(title="WoS & Elsevier MCP Server")

API_KEY = os.getenv("WOS_API_KEY", "")

@app.get("/")
def home():
    return {"status": "MCP Server Active"}

# 1. ChatGPT가 MCP 규격 확인용으로 호출하는 SSE 연결 헤더 엔드포인트
@app.get("/mcp")
async def mcp_sse_endpoint(request: Request):
    async def event_generator():
        # ChatGPT에게 정상 MCP SSE 연결임을 알리는 endpoint 이벤트 전송
        endpoint_event = {
            "event": "endpoint",
            "data": "/mcp/messages"
        }
        yield f"event: endpoint\ndata: /mcp/messages\n\n"
        
        while True:
            if await request.is_disconnected():
                break
            await asyncio.sleep(15)
            yield ": keepalive\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )

# 2. ChatGPT 메시지 수신 및 도구 호출 처리 엔드포인트 (/mcp/messages)
@app.post("/mcp/messages")
async def handle_mcp_messages(request: Request):
    body = await request.json()
    method = body.get("method")
    msg_id = body.get("id", 1)

    if method == "initialize":
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "wos-elsevier-search", "version": "1.0.0"}
            }
        })

    elif method == "tools/list":
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "tools": [
                    {
                        "name": "search_literature",
                        "description": "Search scientific literature from Web of Science / Elsevier databases.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Search query keywords (e.g. LNP AND CpG ODN)"
                                },
                                "limit": {
                                    "type": "integer",
                                    "default": 10,
                                    "description": "Number of results"
                                }
                            },
                            "required": ["query"]
                        }
                    }
                ]
            }
        })

    elif method == "tools/call":
        params = body.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name == "search_literature":
            query = arguments.get("query", "")
            limit = arguments.get("limit", 10)

            if not API_KEY:
                result_text = "API_KEY is not configured on the server."
            else:
                url = f"https://api.clarivate.com/api/wos?q={query}&limit={limit}"
                headers = {"X-ApiKey": API_KEY, "Accept": "application/json"}
                try:
                    res = requests.get(url, headers=headers, timeout=10)
                    result_text = res.text
                except Exception as e:
                    result_text = f"API Request Error: {str(e)}"

            return JSONResponse({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [{"type": "text", "text": result_text}]
                }
            })

    return JSONResponse({"jsonrpc": "2.0", "id": msg_id, "result": {}})
