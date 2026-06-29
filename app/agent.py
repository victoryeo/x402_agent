import json
from typing import Any

from openai import OpenAI

from app.tools import TOOL_DEFINITIONS, call_x402_api, search_web
from app.x402_wallet import X402Wallet


SYSTEM_PROMPT = (
    "You are an agentic AI assistant with the ability to make x402 payments "
    "to access paid APIs and services. When a user asks you to do something that "
    "requires calling an external API, use the call_x402_api tool. The x402 protocol "
    "will automatically handle HTTP 402 Payment Required responses by paying from "
    "your wallet. You can also search the web for information."
)


class AgenticAI:
    def __init__(self, client: OpenAI, model: str, x402_wallet: X402Wallet):
        self.llm = client
        self.model = model
        self.x402_wallet = x402_wallet

    async def run(self, user_message: str, conversation: list[dict] | None = None) -> str:
        messages = conversation or []
        messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})
        messages.append({"role": "user", "content": user_message})

        response = self.llm.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
        )

        msg = response.choices[0].message
        if not msg.tool_calls:
            return msg.content or ""

        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in msg.tool_calls
            ],
        })

        for tc in msg.tool_calls:
            name = tc.function.name
            args = json.loads(tc.function.arguments)

            if name == "call_x402_api":
                result = await call_x402_api(self.x402_wallet, **args)
            elif name == "search_web":
                result = await search_web(**args)
            else:
                result = {"error": f"Unknown tool: {name}"}

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result, ensure_ascii=False),
            })

        final = self.llm.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        return final.choices[0].message.content or ""
