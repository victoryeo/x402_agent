import os
from typing import Optional

from eth_account import Account
from x402 import x402Client
from x402.http.clients import x402HttpxClient
from x402.mechanisms.evm import EthAccountSigner
from x402.mechanisms.evm.exact.register import register_exact_evm_client


class X402Wallet:
    def __init__(self):
        self.client: x402Client | None = None
        self.signer_address: str | None = None
        self._initialized = False

    def initialize(self) -> None:
        evm_private_key = os.getenv("X402_EVM_PRIVATE_KEY", "").strip()
        if not evm_private_key:
            print("⚠️  X402_EVM_PRIVATE_KEY not set; x402 payments disabled")
            return

        account = Account.from_key(evm_private_key)
        signer = EthAccountSigner(account)
        self.signer_address = account.address

        self.client = x402Client()
        register_exact_evm_client(self.client, signer)
        self._initialized = True
        print(f"✅ x402 wallet initialized: {account.address}")

    async def pay_and_retry(self, url: str, method: str = "GET", headers: dict | None = None, body: bytes | None = None) -> dict:
        print(f"Paying and retrying x402 API call: {url} with method {method}")
        if not self._initialized or self.client is None:
            raise RuntimeError("x402 wallet not initialized")

        async with x402HttpxClient(self.client) as http:
            request_headers = dict(headers or {})
            response = await http.request(method, url, headers=request_headers, content=body)
            await response.aread()

            print(f"x402 API response: {response.status_code} {response.headers}")

            return {
                "status": response.status_code,
                "headers": dict(response.headers),
                "body": response.text,
            }
