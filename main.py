import os
import requests
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="WoS & Elsevier MCP Server")

API_KEY = os.getenv("WOS_API_KEY", "")

@app.get("/")
def home():
    return {"status": "MCP Server Active"}

# 1. ChatGPT MCP 핸드셰이크 및 통신 엔드포인트 (POST /mcp)
@app.post("/mcp")
async def handle_mcp(request: Request):
    body = await request.json()
    method = body.get("method")
    msg_id = body.get("id", 1)

    # ChatGPT의 초기 연결 검증 (Initialize)
    if method == "initialize":
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "wos-elsevier-search",
                    "version": "1.0.0"
                }
            }
        })

    # 사용 가능한 도구 목록 제공 (tools/list)
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

    # 실제 논문 검색 실행 (tools/call)
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
                    "content": [
                        {
                            "type": "text",
                            "text": result_text
                        }
                    ]
                }
            })

    # 기타 통지(Notification) 처리
    return JSONResponse({"jsonrpc": "2.0", "id": msg_id, "result": {}})

@app.get("/mcp")
async def handle_mcp_get():
    return {"status": "MCP Endpoint Ready. Use POST for MCP JSON-RPC requests."}
