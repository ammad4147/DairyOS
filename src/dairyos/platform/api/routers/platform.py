from fastapi import APIRouter

from dairyos.platform.api.services.platform_health_service import (
    PlatformHealthService
)


router = APIRouter(
    prefix="/platform",
    tags=["platform"]
)


health_service = PlatformHealthService()


@router.get("/health")
def platform_health():

    health = health_service.check()

    return {
        "platform": "DairyOS",
        "status": health.status(),
        "components": {
            "runtime": health.runtime,
            "identity": health.identity,
            "security": health.security,
            "configuration": health.configuration,
        }
    }
