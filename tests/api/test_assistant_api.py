from dairyos.assistant.knowledge import GroundedAssistant, LocalVectorIndex


def test_assistant_exposes_broad_read_only_grounded_coverage():
    assistant = GroundedAssistant()
    coverage = assistant.coverage()

    assert coverage["read_only"] is True
    assert coverage["items"] >= 100
    assert "VALIDATED" in coverage["implementation_anchor_statuses"]
    assert coverage["implementation_anchor_statuses"].get("BLOCKED", 0) == 0
    assert "health-and-veterinary" in coverage["domains"]


def test_local_vector_index_retrieves_packaged_guidance():
    assistant = GroundedAssistant()
    matches = LocalVectorIndex(assistant.records.values()).search(
        "How do I record a missed milk entry?"
    )

    assert matches
    assert matches[0].similarity > 0
    assert any("milk" in match.record.title.lower() for match in matches)


def test_assistant_answers_dairyos_workflow_with_sop_shape():
    result = GroundedAssistant().answer("How do I record a missed milk entry?")

    assert result["answer_type"] == "SOP / CHECKLIST"
    assert result["steps"]
    assert result["expected_result"]
    assert result["review"]["implementation_validation"]["status"] in {
        "VALIDATED",
        "NOT_APPLICABLE",
    }
    assert result["related"]


def test_assistant_answers_health_questions_as_educational_information():
    result = GroundedAssistant().answer(
        "What are the signs of mastitis?",
        role="Veterinary / Health",
    )

    assert result["answer_type"] == "INFORMATION"
    assert result["scope"] == "Educational health and veterinary information"
    assert result["answer"]
    assert result["safety"]
    assert result["selected_role_guidance"]


def test_assistant_does_not_invent_answers_outside_grounded_coverage():
    result = GroundedAssistant().answer(
        "What is the private weather satellite policy for DairyOS?"
    )

    assert result["answer_type"] == "INSUFFICIENT_COVERAGE"
    assert result["safety"] == "No live data was read and no farm record was changed."
