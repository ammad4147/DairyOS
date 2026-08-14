"""Guards G6.1 (breeding classifier unification, Phase 1, 2026-08-14).

Before this fix, three live endpoints independently classified the same
BreedingRecord rows and disagreed: dairy_kpi.py never recognized
"pregnancy_diagnosis" or "pregnancy_confirmed" — the operator UI's actual
event-type values (src/DairyOS.Web/src/App.tsx's entryConfigs.breeding) — as
pregnancy-check events at all, so its confirmed_pregnancies/
conception_rate_percent silently undercounted relative to
/farm/reproduction/overview for identical underlying data.

These tests submit events using the real operator vocabulary and assert
/farm/animals/{id}/reproduction, /farm/reproduction/overview and
/farm/kpis/overview now agree, using the shared
dairyos.herd.reproduction.services.reproductive_event_classifier module.
"""


def _record_breeding(client, animal_id, event_type, result):
    response = client.post(
        "/farm/breeding",
        json={
            "animal_id": animal_id,
            "event_type": event_type,
            "technician": "Dr Vet",
            "result": result,
            "operator": "Dr Vet",
        },
    )
    assert response.status_code == 200, response.text
    return response


def test_pregnancy_diagnosis_is_confirmed_on_every_live_endpoint(client, registered_animal):
    """The concrete regression this fix closes: before the fix, dairy_kpi.py
    never matched "pregnancy_diagnosis" as a pregnancy check at all, so a
    real confirmed pregnancy recorded through the actual operator UI form
    would silently disappear from /farm/kpis/overview while still showing
    up on /farm/reproduction/overview."""
    _record_breeding(client, registered_animal, "insemination", "completed")
    _record_breeding(client, registered_animal, "pregnancy_diagnosis", "pregnant")

    reproduction = client.get("/farm/reproduction/overview").json()
    assert reproduction["confirmed_pregnancies"] == 1
    assert reproduction["pregnancy_checks"] == 1
    assert reproduction["conception_rate_percent"] == 100.0

    kpis = client.get("/farm/kpis/overview?days=365").json()
    assert kpis["kpis"]["confirmed_pregnancies"] == 1
    assert kpis["kpis"]["pregnancy_checks"] == 1
    assert kpis["kpis"]["conception_rate_percent"] == 100.0

    status = client.get(f"/farm/animals/{registered_animal}/reproduction").json()
    assert status["state"] == "PREGNANT"


def test_bare_pregnancy_confirmed_event_is_confirmed_everywhere(client, registered_animal):
    """A bare "pregnancy_confirmed" event (no separate pregnancy_diagnosis
    check) must also be counted as confirmed on every endpoint, and must
    NOT be double-counted as a pregnancy_check (matches the pre-existing,
    test-locked reproduction_management.py behavior this fix preserves)."""
    _record_breeding(client, registered_animal, "pregnancy_confirmed", "confirmed")

    reproduction = client.get("/farm/reproduction/overview").json()
    assert reproduction["confirmed_pregnancies"] == 1
    assert reproduction["pregnancy_checks"] == 0

    kpis = client.get("/farm/kpis/overview?days=365").json()
    assert kpis["kpis"]["confirmed_pregnancies"] == 1
    # dairy_kpi.py reports a zero count as None ("absence of data must never
    # render as good news" — see its module docstring); reproduction_
    # management.py reports a literal 0 for the same concept. Pre-existing,
    # deliberate difference between the two endpoints, not part of this fix.
    assert kpis["kpis"]["pregnancy_checks"] is None

    status = client.get(f"/farm/animals/{registered_animal}/reproduction").json()
    assert status["state"] == "PREGNANT"


def test_pregnancy_negative_is_a_check_but_not_confirmed(client, registered_animal):
    """New in this fix: pregnancy_negative previously wasn't counted as a
    pregnancy_check at all on either live endpoint (a real undercount, not
    just an inconsistency). Now both agree it is a check, and neither
    counts it as confirmed."""
    _record_breeding(client, registered_animal, "pregnancy_negative", "open")

    reproduction = client.get("/farm/reproduction/overview").json()
    assert reproduction["pregnancy_checks"] == 1
    assert reproduction["confirmed_pregnancies"] == 0

    kpis = client.get("/farm/kpis/overview?days=365").json()
    assert kpis["kpis"]["pregnancy_checks"] == 1
    # See the comment in test_bare_pregnancy_confirmed_event_is_confirmed_everywhere:
    # dairy_kpi.py reports a zero count as None, not 0.
    assert kpis["kpis"]["confirmed_pregnancies"] is None

    status = client.get(f"/farm/animals/{registered_animal}/reproduction").json()
    assert status["state"] == "OPEN"


def test_full_event_sequence_agrees_across_all_three_endpoints(client, registered_animal):
    """A realistic sequence of events, submitted with the real operator
    vocabulary, must yield mutually consistent counts and a correct final
    per-animal state across all three live endpoints."""
    _record_breeding(client, registered_animal, "heat_detected", "detected")
    _record_breeding(client, registered_animal, "insemination", "completed")
    _record_breeding(client, registered_animal, "pregnancy_diagnosis", "pregnant")
    _record_breeding(client, registered_animal, "pregnancy_confirmed", "confirmed")
    _record_breeding(client, registered_animal, "calving", "completed")

    reproduction = client.get("/farm/reproduction/overview").json()
    assert reproduction["heat_detections"] == 1
    assert reproduction["inseminations"] == 1
    assert reproduction["pregnancy_checks"] == 1
    assert reproduction["confirmed_pregnancies"] == 2
    assert reproduction["calvings"] == 1

    kpis = client.get("/farm/kpis/overview?days=365").json()
    assert kpis["kpis"]["inseminations"] == 1
    assert kpis["kpis"]["pregnancy_checks"] == 1
    assert kpis["kpis"]["confirmed_pregnancies"] == 2
    assert (
        kpis["kpis"]["conception_rate_percent"]
        == reproduction["conception_rate_percent"]
    )

    status = client.get(f"/farm/animals/{registered_animal}/reproduction").json()
    assert status["state"] == "CALVED"
