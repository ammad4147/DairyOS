def calving_rule(event):

    if event.event_type == "CALVING_COMPLETED":

        return {
            "action": "CREATE_CALF_RECORD"
        }

    return None
