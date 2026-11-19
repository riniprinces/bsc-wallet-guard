"""BSC Wallet Guard - public HTTP endpoint.

POST /guard  {"spender": "0x...", "token": "0x...", "amount": "123", "owner": "0x..."}
GET  /health -> {"ok": true}
GET  /       -> usage info
Pure stdlib (http.server). Run: python3 server.py  [port, default 8080]
"""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from guard import guard


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self._send(200, {"ok": True, "service": "bsc-wallet-guard"})
        else:
            self._send(200, {
                "service": "BSC Wallet Guard",
                "usage": "POST /guard {\"spender\": \"0x...\", \"token\": \"0x...\", \"amount\": \"...\", \"owner\": \"0x...\"}",
                "verdicts": ["SAFE", "RISKY", "BLOCK"],
                "chain": 56,
            })

    def do_POST(self):
        if self.path != "/guard":
            self._send(404, {"error": "not found, use POST /guard"})
            return
        try:
            n = int(self.headers.get("Content-Length") or 0)
            data = json.loads(self.rfile.read(n) or b"{}")
        except Exception as e:
            self._send(400, {"error": f"bad json: {e}"})
            return
        spender = data.get("spender")
        if not spender or not isinstance(spender, str) or not spender.startswith("0x"):
            self._send(400, {"error": "field 'spender' (0x address) is required"})
            return
        try:
            result = guard(
                spender=spender,
                token=data.get("token"),
                amount=data.get("amount"),
                owner=data.get("owner"),
            )
        except Exception as e:
            self._send(502, {"error": f"on-chain check failed: {e}"})
            return
        self._send(200, result)

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
