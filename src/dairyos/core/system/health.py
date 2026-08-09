from datetime import datetime


def system_health():

    return {

        "status": "ONLINE",

        "timestamp": datetime.utcnow()

    }
