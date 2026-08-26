"""Compatibility aliases for the pre-/auth authentication API.

The canonical authentication contract remains under /auth. These aliases keep
older local integrations and installed operator tooling functional while they
migrate, without changing authentication or authorization semantics.
"""

from fastapi import APIRouter

from dairyos.api.auth import (
    change_my_password,
    create_user,
    current_user,
    list_users,
    login,
    reset_user_password,
)

router = APIRouter(tags=["Authentication compatibility"])

router.add_api_route("/login", login, methods=["POST"])
router.add_api_route("/me", current_user, methods=["GET"])
router.add_api_route("/users", create_user, methods=["POST"])
router.add_api_route("/users", list_users, methods=["GET"])
router.add_api_route("/users/{username}/password", reset_user_password, methods=["PATCH"])
router.add_api_route("/me/password", change_my_password, methods=["POST"])
