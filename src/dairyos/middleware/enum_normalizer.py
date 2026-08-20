# -*- coding: utf-8 -*-
"""Centralized Enum & Payload Normalization Middleware for DairyOS.

Pure ASGI middleware that normalizes field aliases before route validation.
"""
import json

SEVERITY_MAP = {
    "high": "SEVERE",
    "urgent": "CRITICAL",
    "critical": "CRITICAL",
    "severe": "SEVERE",
    "medium": "MODERATE",
    "moderate": "MODERATE",
    "med": "MODERATE",
    "low": "LOW",
    "normal": "NORMAL",
}

INVENTORY_MOVEMENT_MAP = {
    "in": "RECEIPT",
    "inward": "RECEIPT",
    "received": "RECEIPT",
    "receipt": "RECEIPT",
    "out": "CONSUMPTION",
    "outward": "CONSUMPTION",
    "consumed": "CONSUMPTION",
    "consumption": "CONSUMPTION",
    "bought": "PURCHASE",
    "purchase": "PURCHASE",
    "buy": "PURCHASE",
    "lost": "WASTAGE",
    "waste": "WASTAGE",
    "wastage": "WASTAGE",
    "adj": "ADJUSTMENT",
    "adjustment": "ADJUSTMENT",
    "transfer": "TRANSFER",
}


class PayloadNormalizationMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope.get("method") not in {"POST", "PUT", "PATCH"}:
            await self.app(scope, receive, send)
            return

        # Receive the request body packets
        body_chunks = []
        more_body = True
        while more_body:
            message = await receive()
            if message["type"] == "http.request":
                body_chunks.append(message.get("body", b""))
                more_body = message.get("more_body", False)
            elif message["type"] == "http.disconnect":
                return

        body = b"".join(body_chunks)
        if body:
            try:
                data = json.loads(body.decode("utf-8"))
                if isinstance(data, dict):
                    # 1. Normalize Severity
                    if "severity" in data and isinstance(data["severity"], str):
                        raw_sev = data["severity"].strip().lower()
                        if raw_sev in SEVERITY_MAP:
                            data["severity"] = SEVERITY_MAP[raw_sev]

                    # 2. Normalize Inventory Movement Types
                    if "movement_type" in data and isinstance(data["movement_type"], str):
                        raw_mov = data["movement_type"].strip().lower()
                        if raw_mov in INVENTORY_MOVEMENT_MAP:
                            data["movement_type"] = INVENTORY_MOVEMENT_MAP[raw_mov]

                    body = json.dumps(data).encode("utf-8")
            except Exception:
                pass

        # Re-inject the normalized body into the ASGI stream
        sent_body = False

        async def custom_receive():
            nonlocal sent_body
            if not sent_body:
                sent_body = True
                return {
                    "type": "http.request",
                    "body": body,
                    "more_body": False,
                }
            # Subsequent receive calls listen for client disconnect
            return await receive()

        await self.app(scope, custom_receive, send)