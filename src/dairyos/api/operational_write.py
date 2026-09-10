"""Explicit route boundary for atomic operational commands."""

from functools import wraps
from hashlib import sha256
from inspect import signature
from uuid import uuid4

from fastapi import HTTPException

from dairyos.application.operational_write import (
    OperationalWriteService,
    RequestIdentityConflict,
    transaction_container,
)


def operational_write(function):
    parameters = signature(function)

    @wraps(function)
    def wrapped(*args, **kwargs):
        arguments = parameters.bind(*args, **kwargs)
        arguments.apply_defaults()
        container = arguments.arguments["container"]
        if getattr(container, "_operational_write_active", False):
            return function(*args, **kwargs)
        request = {
            key: value for key, value in arguments.arguments.items()
            if key not in {"container", "current_user"}
        }
        body = request.get("entry", request.get("payload"))
        if body is None:
            body = next(
                (
                    value
                    for key, value in request.items()
                    if key not in {"container", "current_user"}
                    and hasattr(value, "model_dump")
                ),
                {},
            )
        body = body or {}
        if hasattr(body, "model_dump"):
            body = body.model_dump(mode="json")
        client_id = body.get("request_id") or str(uuid4())
        body_key = "entry" if "entry" in request else "payload"
        if body_key not in request:
            body_key = next(
                (
                    key for key, value in request.items()
                    if key not in {"container", "current_user"}
                    and hasattr(value, "model_dump")
                ),
                None,
            )
        if body_key is not None:
            request[body_key] = {
                key: value for key, value in body.items() if key != "request_id"
            }
        if not isinstance(client_id, str) or not 1 <= len(client_id) <= 128:
            raise HTTPException(422, "request_id must be a string of 1 to 128 characters")
        # Preserve direct-call compatibility for lightweight repositories used
        # by unit tests and legacy adapters. They do not expose the durable
        # application engine/ingestion service required by this boundary.
        repository_factory = getattr(container, "repository_factory", None)
        if (
            getattr(repository_factory, "session", None) is None
            or not hasattr(container, "input_ingestion_service")
        ):
            return function(*args, **kwargs)
        user = arguments.arguments.get("current_user")
        actor = str(user.get("sub")) if isinstance(user, dict) else str(body.get("operator", "API"))
        request["actor"] = actor
        identity = sha256(
            f"{function.__module__}.{function.__name__}:{actor}:{client_id}".encode()
        ).hexdigest()
        service = OperationalWriteService(
            container.repository_factory.session.get_bind(), container.input_ingestion_service
        )

        def mutate(factory, gateway):
            arguments.arguments["container"] = transaction_container(container, factory, gateway)
            return function(*arguments.args, **arguments.kwargs)

        try:
            response = service.execute(request_id=identity, request=request, mutation=mutate)
        except RequestIdentityConflict as exc:
            raise HTTPException(409, str(exc)) from exc
        response["request_id"] = client_id
        return response

    return wrapped
