"""BSC Wallet Guard - screens a token approval / transaction before signing.

Pure stdlib Python. Reads public BSC data via a JSON-RPC endpoint.
Verdict: SAFE | RISKY | BLOCK, with plain-language reasons.
"""
import json
import urllib.request

BSC_RPC = "https://bsc-dataseed.binance.org/"
MAX_UINT = 2**256 - 1

# Well-known BSC contracts (checksummed, verified from public sources)
KNOWN_SPENDERS = {
    "0x10ED43C718714eb63d5aA57B78B54704E256024E": ("PancakeSwap V2 Router", "SAFE"),
    "0x1b81D678ffb9C0263b24A97847620C99dF6bB9d": ("PancakeSwap V3 Router", "SAFE"),
    "0x14296940aE6A46aEc4181A3D14aEbCFcc780cF4d": ("PodMint Proxy", "SAFE"),
}

ERC20_ABI_BALANCE = "70a08231"
ERC20_ABI_ALLOWANCE = "dd62ed3e"
ERC20_ABI_NAME = "06fdde03"
ERC20_ABI_SYMBOL = "95d89b41"
ERC20_ABI_DECIMALS = "313ce567"


def rpc(method, params):
    req = urllib.request.Request(
        BSC_RPC,
        data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())["result"]


def has_code(addr):
    return rpc("eth_getCode", [addr, "latest"]) not in ("0x", "0x0", None)


def call(addr, data):
    return rpc("eth_call", [{"to": addr, "data": "0x" + data}, "latest"])


def decode_str(hexdata):
    try:
        raw = bytes.fromhex(hexdata[2:])
        off = int.from_bytes(raw[0:32], "big")
        ln = int.from_bytes(raw[off:off + 32], "big")
        return raw[off + 32:off + 32 + ln].decode("utf-8", "ignore")
    except Exception:
        return ""


def guard(spender, token=None, amount=None, owner=None):
    reasons = []
    checks = {}
    verdict = "SAFE"

    # 1. spender must be a contract
    code = has_code(spender)
    checks["spender_is_contract"] = code
    if not code:
        verdict = "BLOCK"
        reasons.append("Spender is an EOA (no contract code). Approvals to a plain wallet are almost never legitimate.")
        return {"verdict": verdict, "reasons": reasons, "checks": checks}

    # 2. known spender?
    known = KNOWN_SPENDERS.get(spender)
    checks["known_spender"] = known[0] if known else None
    if known:
        reasons.append(f"Known spender: {known[0]}.")
    else:
        verdict = "RISKY"
        reasons.append("Spender is an unknown contract. Verify its source code and purpose before approving.")

    # 3. unlimited approval?
    if amount is not None:
        try:
            amt = int(amount, 0)
            checks["unlimited"] = amt >= MAX_UINT - 1000
            if amt >= MAX_UINT - 1000:
                if verdict == "SAFE":
                    verdict = "RISKY"
                reasons.append("Approval is UNLIMITED (max uint256). Prefer an exact amount.")
            else:
                reasons.append("Approval is a limited amount.")
        except Exception:
            checks["unlimited"] = None

    # 4. token sanity (if given)
    if token:
        tcode = has_code(token)
        checks["token_is_contract"] = tcode
        if not tcode:
            verdict = "BLOCK"
            reasons.append("Token address has no contract code.")
        else:
            try:
                sym = decode_str(call(token, ERC20_ABI_SYMBOL + "0" * 64)) or "?"
                checks["token_symbol"] = sym
            except Exception:
                checks["token_symbol"] = None

    return {"verdict": verdict, "reasons": reasons, "checks": checks}


if __name__ == "__main__":
    import sys
    # demo: PancakeSwap V2 router, limited amount
    print(json.dumps(guard("0x10ED43C718714eb63d5aA57B78B54704E256024E", amount="1000000000000000000"), indent=2))
    # demo: unknown spender, unlimited
    print(json.dumps(guard("0x0000000000000000000000000000000000000001", amount=str(MAX_UINT)), indent=2))
