from datetime import datetime
from dairyos.core.time_utils import utcnow


def system_health():

    return {

        "status": "ONLINE",

        "timestamp": utcnow()

    }
