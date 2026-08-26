# -*- coding: utf-8 -*-
"""Centralized payload normalization and operational input boundary guards for DairyOS."""
import json

from dairyos.data.repositories.repository_factory import RepositoryFactory

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

ANIMAL_LINKED_POSTS = {
    "/farm/milk",
    "/farm/health-observations",
    "/farm/treatments",
    "/farm/breeding",
    "/farm/feed/records",
    "/farm/welfare/observations",
}

INACTIVE_LIFECYCLE_STATUSES = {"DECEASED", "SOLD", "CULLED"}
MILK_YIELD_FIELDS = ("morning_yield", "afternoon_yield", "evening_yield")


def _json_response(send, status_code: int, detail: str, *, animal_id: str | None = None):
    payload = {"detail": detail}
    if animal_id is not None:
        payload["animal_id"] = animal_id
    body = json.dumps(payload).encode("utf-8")

    async def emit():
        await send(
            {
                "type": "http.response.start",
                "status": status_code,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode("ascii")),
                ],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": body,
                "more_body": False,
            }
        )

    return emit


class PayloadNormalizationMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope.get("method") not in {"POST", "PUT", "PATCH"}:
            await self.app(scope, receive, send)
            return

        # Receive the request body packets.
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
                    path = str(scope.get("path", ""))

                    # 1. Normalize Severity.
                    if "severity" in data and isinstance(data["severity"], str):
                        raw_sev = data["severity"].strip().lower()
                        if raw_sev in SEVERITY_MAP:
                            data["severity"] = SEVERITY_MAP[raw_sev]

                    # 2. Normalize Inventory Movement Types.
                    if "movement_type" in data and isinstance(data["movement_type"], str):
                        raw_mov = data["movement_type"].strip().lower()
                        if raw_mov in INVENTORY_MOVEMENT_MAP:
                            data["movement_type"] = INVENTORY_MOVEMENT_MAP[raw_mov]

                    # 3. Reject negative milk production at the HTTP boundary.
                    # Route models historically accepted negative values even though
                    # downstream production accounting requires non-negative litres.
                    if path == "/farm/milk":
                        for field in MILK_YIELD_FIELDS:
                            value = data.get(field)
                            if value is None or value == "":
                                continue
                            try:
                                numeric_value = float(value)
                            except (TypeError, ValueError):
                                # Preserve FastAPI/Pydantic's normal 422 for malformed
                                # non-numeric values; only intercept actual negatives.
                                continue
                            if numeric_value < 0:
                                await _json_response(
                                    send,
                                    422,
                                    f"{field} must be greater than or equal to zero.",
                                )()
                                return

                    # 4. Reject operational entries for inactive animals.
                    # The integrity lookup must fail closed: if DairyOS cannot verify
                    # the animal state, the operational write must not proceed.
                    if path in ANIMAL_LINKED_POSTS and data.get("animal_id"):
                        animal_id = str(data["animal_id"])
                        try:
                            factory = RepositoryFactory.create()
                            try:
                                animal = factory.animal().get_by_animal_id(animal_id)
                            finally:
                                factory.close()
                        except Exception:
                            await _json_response(
                                send,
                                503,
                                "Animal integrity verification is temporarily unavailable; operational entry was not accepted.",
                                animal_id=animal_id,
                            )()
                            return

                        if animal is None:
                            await _json_response(
                                send,
                                422,
                                "Unknown Animal ID. Select an existing system-generated permanent Animal ID.",
                                animal_id=animal_id,
                            )()
                            return

                        lifecycle_status = str(
                            getattr(animal, "lifecycle_status", "") or ""
                        ).strip().upper()
                        active = bool(getattr(animal, "active", True))

                        if not active or lifecycle_status in INACTIVE_LIFECYCLE_STATUSES:
                            state = lifecycle_status or "INACTIVE"
                            await _json_response(
                                send,
                                422,
                                f"Animal {animal_id} is {state} and cannot accept operational entries.",
                                animal_id=animal_id,
                            )()
                            return

                    body = json.dumps(data).encode("utf-8")
            except Exception:
                # Preserve historical behavior for malformed JSON and unrelated
                # normalization failures; FastAPI will issue the authoritative 422.
                pass

        # Re-inject the normalized body into the ASGI stream.
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
            # Subsequent receive calls listen for client disconnect.
            return await receive()

        await self.app(scope, custom_receive, send)
