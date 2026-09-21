from __future__ import annotations

from dairyos_assistant.service import Assistant


def test_operational_refusal_is_deterministic_without_model():
    response = Assistant().answer("What is my COP today?")

    assert response["decision"] == "REFUSE_OPERATIONAL_DATA"
    assert response["stage"] in {"GUIDANCE_ANSWERED", "RELATED_GUIDANCE"}
    assert response["text"]
    assert response["operational_data_access"] == "NONE"
    assert response["verbatim"] is True
