"""Contract tests for the bounded AI Assistant planner and response boundary."""

from dairyos.assistant.agentic import AgenticAssistant, AssistantToolRegistry
from dairyos.assistant.contracts import AssistantResponse
from dairyos.assistant.routing import classify_request


def test_live_data_plan_bypasses_knowledge_retrieval_by_default():
    classification = classify_request(
        "What was the average and maximum COP/L in September 2026?"
    )

    assert classification.live_data_required is True
    assert classification.documentation_required is False
    assert "read_cop_metrics" in classification.tools
    assert "search_knowledge_base" not in classification.tools


def test_guidance_and_clinical_plans_request_reference_only_when_needed():
    guidance = classify_request("How do I record a missed milk entry?")
    clinical = classify_request("A cow has fever and reduced appetite.")

    assert guidance.live_data_required is False
    assert guidance.documentation_required is True
    assert guidance.tools == ("read_safety_policy", "search_knowledge_base")
    assert clinical.live_data_required is True
    assert clinical.documentation_required is True
    assert "read_health_insight" in clinical.tools
    assert "search_knowledge_base" in clinical.tools


def test_live_health_history_bypasses_knowledge_retrieval():
    classification = classify_request(
        "Which sick animals have persisted health evidence and what was recorded?"
    )

    assert classification.live_data_required is True
    assert classification.documentation_required is False
    assert "read_health_insight" in classification.tools
    assert "search_knowledge_base" not in classification.tools

    period_summary = classify_request("What was the health situation in July 2026?")
    assert period_summary.live_data_required is True
    assert period_summary.documentation_required is False
    assert "search_knowledge_base" not in period_summary.tools


def test_typed_tool_schemas_are_closed_and_paginated():
    schemas = {item["name"]: item for item in AssistantToolRegistry().schemas()}

    for name in schemas:
        assert schemas[name]["parameters"]["additionalProperties"] is False
    data_properties = schemas["read_operational_data"]["parameters"]["properties"]
    log_properties = schemas["read_operational_logs"]["parameters"]["properties"]
    assert "page" in data_properties
    assert "page_size" in data_properties
    assert "page" in log_properties
    assert "page_size" in log_properties


def test_state_machine_emits_typed_response_without_knowledge_for_live_question(
    monkeypatch,
):
    assistant = AgenticAssistant()

    def fake_execute(name, arguments):
        if name == "read_safety_policy":
            return {
                "read_only": True,
                "writes_allowed": False,
                "note": "AI Assistant never authorises or performs farm-data writes.",
            }
        if name == "read_cop_metrics":
            return {
                "status": "OK",
                "data_status": "OK",
                "period": {
                    "effective_start": "2026-09-01",
                    "effective_end": "2026-09-30",
                },
                "period_cop_per_litre": 1.2,
                "average_daily_cop_per_litre": 1.1,
                "maximum_daily_cop_per_litre": 1.4,
                "period_milk_litres": 1000,
                "valid_daily_days": 30,
                "calculation_basis": "governed persisted authority",
                "source_tables": ["milk_production", "feed_ration"],
                "read_only": True,
                "database_read": True,
            }
        raise AssertionError(f"unexpected tool: {name}")

    monkeypatch.setattr(assistant.registry, "execute", fake_execute)
    payload = assistant.ask("What was the average and maximum COP/L in September 2026?")
    response = AssistantResponse.model_validate(payload)

    states = [item.get("state") for item in response.execution_trace]
    assert states[:1] == ["INPUT"]
    assert "PLAN" in states
    assert "ACT" in states
    assert "OBSERVE" in states
    assert states[-1] == "SYNTHESIZE"
    assert response.source_mode == "LIVE_ONLY"
    assert response.database_read is True
    assert response.agentic is True
    assert "search_knowledge_base" not in response.plan
    assert response.evidence


def test_state_machine_has_one_bounded_diagnostic_iteration(monkeypatch):
    assistant = AgenticAssistant()

    def fake_execute(name, arguments):
        if name == "read_safety_policy":
            return {
                "read_only": True,
                "writes_allowed": False,
                "note": "AI Assistant never authorises or performs farm-data writes.",
            }
        if name == "read_cop_metrics":
            raise RuntimeError("disposable COP authority unavailable")
        if name == "read_operational_logs":
            return {
                "data_status": "LIVE_PERSISTED_DATA",
                "database_logs": {
                    "event_journal": [],
                    "operational_events": [],
                    "projection_outbox": [],
                },
                "file_logs": [],
                "read_only": True,
                "database_read": True,
                "source_tables": ["event_journal", "operational_events"],
            }
        raise AssertionError(f"unexpected tool: {name}")

    monkeypatch.setattr(assistant.registry, "execute", fake_execute)
    response = AssistantResponse.model_validate(
        assistant.ask("What was the average COP/L in September 2026?")
    )

    states = [item.get("state") for item in response.execution_trace]
    assert states.count("ITERATE") == 1
    assert states.count("ACT") == 2
    assert states[-1] == "SYNTHESIZE"
    assert response.source_mode == "LIVE_UNAVAILABLE"
    assert "read_operational_logs" in response.tool_results
    assert "search_knowledge_base" not in response.plan
