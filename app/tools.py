import json
from typing import Any

from app.x402_wallet import X402Wallet


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "call_x402_api",
            "description": "Call an external API. If the server returns 402 Payment Required, the x402 wallet will automatically pay and retry.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The full URL to call"},
                    "method": {"type": "string", "description": "HTTP method (GET, POST, etc)", "default": "GET"},
                    "headers": {"type": "object", "description": "Optional HTTP headers", "default": {}},
                    "body": {"type": "string", "description": "Optional request body (JSON string)", "default": None},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web for information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                },
                "required": ["query"],
            },
        },
    },
]


async def call_x402_api(
    x402_wallet: X402Wallet,
    url: str,
    method: str = "GET",
    headers: dict | None = None,
    body: str | None = None,
) -> dict:
    if not x402_wallet._initialized:
        return {"error": "x402 wallet not initialized; set X402_EVM_PRIVATE_KEY"}

    body_bytes = body.encode("utf-8") if body else None
    parsed_headers = dict(headers or {})
    if body_bytes:
        parsed_headers.setdefault("Content-Type", "application/json")

    result = await x402_wallet.pay_and_retry(url, method=method, headers=parsed_headers, body=body_bytes)
    return result


async def search_web(query: str) -> dict:
    try:
        import urllib.parse
        import urllib.request
        import json as _json

        params = urllib.parse.urlencode({"q": query, "format": "json"})
        req = urllib.request.Request(
            f"https://api.duckduckgo.com/?{params}",
            headers={"User-Agent": "x402-agent/1.0"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = _json.loads(resp.read().decode("utf-8"))
            return {"results": data.get("AbstractText", "") or data.get("Answer", "") or "No results found"}
    except Exception as e:
        return {"error": f"Search failed: {str(e)}"}
