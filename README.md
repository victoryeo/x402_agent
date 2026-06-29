# AI Engine Service (FastAPI)

## Setup

1. Copy `.env.example` to `.env` and set Supabase credentials (use anon key).
2. Set `DASHSCOPE_API_KEY`, `DASHSCOPE_BASE_URL` (use `https://dashscope-intl.aliyuncs.com`), and (optionally) `QWEN_MODEL` for the default chatbot.
3. Set `OPENAI_API_KEY` and (optionally) `OPENAI_MODEL` if you want the OpenAI endpoint.
4. Install dependencies: `pip install -r requirements.txt`
5. Run: `uvicorn app.main:app --reload --port 8001`

## Endpoints

- `GET /health`

## Analysis

The x402 payment AI Agent is supported via:

1. x402_wallet.py — Initializes an EVM-based x402 client from X402_EVM_PRIVATE_KEY env var using EthAccountSigner. The pay_and_retry method wraps x402HttpxClient which automatically handles 402 Payment Required responses.

2. tools.py:call_x402_api — Tool exposed to the LLM agent, delegates to x402_wallet.pay_and_retry().

3. agent.py — AgenticAI passes the wallet to the tool so the LLM can call paid APIs via x402.

4. main.py:66-73 — Wallet initialized at startup and injected into AgenticAI.

### How to use it:

Set X402_EVM_PRIVATE_KEY in your .env with an Ethereum private key (the wallet pays for API access). Then the agent's /agent endpoint can call the call_x402_api tool, which automatically retries 402 responses by crafting and
sending payment payloads.

curl -X POST http://localhost:8001/agent -H "Content-Type: application/json" \
 -d '{"message": "search the web for AI news"}'

### To be improved:

- Only EVM is configured via register_exact_evm_client — SVM (Solana) and TVM are available in the x402 package but unused
- No server-side x402 resource server is set up (This is only the client side)
- No facilitator is configured
- No endpoints to receive x402 payments (no paywall on your own APIs)
