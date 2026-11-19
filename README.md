# BSC Wallet Guard — Agent Games Wildcard

A wallet security guard agent for BNB Chain (chain 56). It screens a token
approval before you sign it and returns a plain verdict — **SAFE**, **RISKY**,
or **BLOCK** — with the exact reasons, using only public on-chain data.

## Why it matters

BSC users sign token approvals blind. A single unlimited approval to a
malicious spender can drain a wallet. This agent checks the spender and the
token on-chain first and explains the risk in plain language, before any
signature happens. It never asks for keys, never signs anything, and never
moves funds.

## What it checks

Given a spender address (and optionally a token and an amount), it runs four
live checks against a public BSC JSON-RPC endpoint:

1. **Spender is a contract** — `eth_getCode`. An approval to a plain wallet
   (EOA, no contract code) is almost never legitimate → **BLOCK**.
2. **Known spender** — a small allowlist of well-known contracts
   (PancakeSwap V2/V3 routers, PodMint proxy). An unknown contract is
   flagged → **RISKY**, with advice to verify its source code first.
3. **Unlimited approval** — an amount at/near max uint256 is flagged →
   **RISKY**, with advice to approve an exact amount instead.
4. **Token sanity** — the token must itself be a contract
   (`eth_getCode`); its symbol is read on-chain via `eth_call`. A token
   with no contract code → **BLOCK**.

What it does **not** do (yet): it does not verify a contract's published
source code, detect honeypot tokens, or check scam databases. The verdict
rests on the four checks above.

## Endpoint

Pure-stdlib Python, no dependencies. Run it:

```bash
python3 server.py [port]   # default port 8080
```

- `GET /health` → `{"ok": true, "service": "bsc-wallet-guard"}`
- `GET /` → usage info
- `POST /guard` with JSON:
  `{"spender": "0x...", "token": "0x...", "amount": "...", "owner": "0x..."}`
  (`spender` is required; the rest are optional.)

Response:

```json
{"verdict": "SAFE|RISKY|BLOCK", "reasons": ["..."], "checks": {...}}
```

## Examples (verified live against BSC)

Approval to the PancakeSwap V2 router, limited amount, USDT token:

```bash
curl -X POST localhost:8080/guard -H 'Content-Type: application/json' \
  -d '{"spender":"0x10ED43C718714eb63d5aA57B78B54704E256024E",
       "token":"0x55d398326f99059fF775485246999027B3197955",
       "amount":"1000000000000000000"}'
```

```json
{"verdict": "SAFE",
 "reasons": ["Known spender: PancakeSwap V2 Router.",
             "Approval is a limited amount."],
 "checks": {"spender_is_contract": true,
            "known_spender": "PancakeSwap V2 Router",
            "unlimited": false,
            "token_is_contract": true,
            "token_symbol": "USDT"}}
```

An unlimited approval to an unknown contract → `RISKY`; an approval to a
plain wallet (EOA) → `BLOCK`.

## Build context

Built for **Agent Games Season 01, Wildcard track** (zkVerify), November
2026. The agent is a single-file guard (`guard.py`) plus a thin HTTP
wrapper (`server.py`), standard library only. It reads the public BSC
endpoint `https://bsc-dataseed.binance.org/` — no API key, no account, no
private data. Verdict logic is deterministic: same input, same verdict.
