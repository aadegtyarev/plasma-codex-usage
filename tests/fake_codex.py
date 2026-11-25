#!/usr/bin/env python3
"""Stands in for `codex app-server`; FAKE_CODEX_MODE picks the behaviour under test."""

import json
import os
import sys
import time

RATE_LIMITS = {
    "rateLimits": {
        "limitId": "codex",
        "primary": {"usedPercent": 30, "windowDurationMins": 10080, "resetsAt": 1796097689},
        "secondary": None,
        "planType": "prolite",
    },
    "rateLimitResetCredits": {"availableCount": 2, "credits": []},
}

MODE = os.environ.get("FAKE_CODEX_MODE", "ok")


def reply(message):
    print(json.dumps(message), flush=True)


for line in sys.stdin:
    request = json.loads(line)
    method = request.get("method")
    if MODE == "hang":
        time.sleep(60)
    if MODE == "exit":
        sys.exit(0)
    if method == "initialize":
        reply({"id": request["id"], "result": {"userAgent": "fake"}})
    elif method == "account/rateLimits/read":
        reply({"method": "account/updated", "params": {}})
        if MODE == "auth_error":
            reply({"id": request["id"], "error": {
                "code": -32600,
                "message": "codex account authentication required to read rate limits",
            }})
        elif MODE == "rpc_error":
            reply({"id": request["id"], "error": {"code": -32603, "message": "something broke"}})
        else:
            reply({"id": request["id"], "result": RATE_LIMITS})
