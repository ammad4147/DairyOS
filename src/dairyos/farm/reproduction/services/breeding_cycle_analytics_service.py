"""Derived breeding-cycle projection and explainable reproductive analytics.

Persisted breeding events remain the source of truth.  This service never
rewrites history and never invents a reproductive fact; it partitions the
immutable event stream into operator-initiated cycles and derives analytics
from those cycles.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timezone
from typing import Any, Iterable

from dairyos.herd.reproduction.services.reproductive_event_classifier import (
    is_calving,
    is_confirmed_pregnancy,
    is_insemination,
    is_negative_pregnancy_check,
    normalize_event_type,
)


TERMINAL_OUTCOME = {
    "pregnancy_lost": "CLOSED_PREGNANCY_LOSS",
    "abortion": "CLOSED_ABORTION",
    "stillbirth": "CLOSED_STILLBIRTH",
}


def _value(record: Any, name: str, default=None):
    if isinstance(record, dict):
        return record.get(name, default)
    return getattr(record, name, default)


def _utc(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return datetime.combine(value, datetime.min.time(), tzinfo=timezone.utc)
    if isinstance(value, datetime):
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)
        except ValueError:
            return None
    return None


def _event_payload(record: Any) -> dict[str, Any]:
    timestamp = _utc(_value(record, "timestamp"))
    return {
        "record_id": str(_value(record, "record_id", "") or ""),
        "animal_id": str(_value(record, "animal_id", "") or ""),
        "event_type": normalize_event_type(_value(record, "event_type", "")),
        "result": _value(record, "result"),
        "technician": _value(record, "technician"),
        "semen_or_bull": _value(record, "semen_or_bull"),
        "notes": _value(record, "notes"),
        "timestamp": timestamp.isoformat() if timestamp else None,
        "_sort": timestamp or datetime.min.replace(tzinfo=timezone.utc),
    }


def _classifier(event: dict[str, Any]):
    class R:
        pass
    row = R()
    row.event_type = event["event_type"]
    row.result = event.get("result")
    row.timestamp = _utc(event.get("timestamp"))
    return row


def _semen_parts(value: Any) -> tuple[str | None, str | None]:
    text = str(value or "").strip()
    if not text:
        return None, None
    if "—" in text:
        semen_type, sire = [part.strip() for part in text.split("—", 1)]
        return semen_type or None, sire or None
    return None, text


class BreedingCycleProjectionService:
    """Partition breeding history into deterministic operator-initiated cycles."""

    @classmethod
    def project(cls, records: Iterable[Any]) -> list[dict[str, Any]]:
        by_animal: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for record in records:
            event = _event_payload(record)
            if event["animal_id"] and event["timestamp"]:
                by_animal[event["animal_id"]].append(event)

        cycles: list[dict[str, Any]] = []
        for animal_id, events in by_animal.items():
            events.sort(key=lambda row: (row["_sort"], row["record_id"]))
            current: dict[str, Any] | None = None
            cycle_number = 0

            for event in events:
                row = _classifier(event)
                event_type = event["event_type"]

                if is_insemination(row):
                    if current is not None and current["status"].startswith("ACTIVE_"):
                        # Defensive projection only. The command API should reject
                        # this sequence, but historical/imported data must remain
                        # analyzable instead of silently merging two services.
                        current["status"] = "CLOSED_SUPERSEDED"
                        current["outcome"] = "SUPERSEDED_BY_NEW_INSEMINATION"
                        current["closed_at"] = event["timestamp"]
                    cycle_number += 1
                    semen_type, sire_code = _semen_parts(event.get("semen_or_bull"))
                    current = {
                        "cycle_id": f"{animal_id}-C{cycle_number:03d}",
                        "animal_id": animal_id,
                        "cycle_number": cycle_number,
                        "status": "ACTIVE_INSEMINATED",
                        "outcome": None,
                        "started_at": event["timestamp"],
                        "closed_at": None,
                        "insemination_date": event["timestamp"][:10],
                        "pregnancy_confirmation_date": None,
                        "outcome_date": None,
                        "sire_code": sire_code,
                        "semen_type": semen_type,
                        "inseminator": event.get("technician"),
                        "events": [],
                    }
                    cycles.append(current)

                if current is None:
                    # Pre-cycle historical observations remain in the raw event
                    # ledger; they do not get attached to a later AI cycle.
                    continue

                current["events"].append({key: value for key, value in event.items() if key != "_sort"})

                if is_confirmed_pregnancy(row):
                    current["status"] = "ACTIVE_PREGNANT"
                    current["pregnancy_confirmation_date"] = event["timestamp"][:10]
                    continue

                if is_negative_pregnancy_check(row):
                    current["status"] = "CLOSED_NOT_PREGNANT"
                    current["outcome"] = "NOT_PREGNANT"
                    current["outcome_date"] = event["timestamp"][:10]
                    current["closed_at"] = event["timestamp"]
                    current = None
                    continue

                if event_type in TERMINAL_OUTCOME:
                    current["status"] = TERMINAL_OUTCOME[event_type]
                    current["outcome"] = event_type.upper()
                    current["outcome_date"] = event["timestamp"][:10]
                    current["closed_at"] = event["timestamp"]
                    current = None
                    continue

                if is_calving(row):
                    current["status"] = "CLOSED_CALVING"
                    current["outcome"] = "CALVING"
                    current["outcome_date"] = event["timestamp"][:10]
                    current["closed_at"] = event["timestamp"]
                    current = None

        cycles.sort(key=lambda cycle: (cycle["animal_id"], cycle["cycle_number"]))
        return cycles

    @staticmethod
    def current_by_animal(cycles: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        current: dict[str, dict[str, Any]] = {}
        for cycle in cycles:
            if str(cycle.get("status", "")).startswith("ACTIVE_"):
                current[cycle["animal_id"]] = cycle
        return current


class BreedingAnalyticsService:
    """Explainable cycle-level reproductive analytics with evidence links."""

    MIN_SIGNAL_SAMPLE = 3
    MATERIAL_RATE_GAP = 20.0

    @staticmethod
    def _rate(successes: int, observed: int) -> float | None:
        return round(successes / observed * 100, 2) if observed else None

    @classmethod
    def _group(cls, cycles: list[dict[str, Any]], key_name: str) -> list[dict[str, Any]]:
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for cycle in cycles:
            value = str(cycle.get(key_name) or "UNKNOWN").strip() or "UNKNOWN"
            groups[value].append(cycle)

        rows = []
        for value, items in groups.items():
            documented = [c for c in items if not str(c["status"]).startswith("ACTIVE_")]
            conceptions = [c for c in items if c.get("pregnancy_confirmation_date")]
            calvings = [c for c in items if c.get("outcome") == "CALVING"]
            losses = [
                c for c in items
                if c.get("outcome") in {"PREGNANCY_LOST", "ABORTION", "STILLBIRTH"}
            ]
            negative = [c for c in items if c.get("outcome") == "NOT_PREGNANT"]
            rows.append({
                "key": value,
                "cycles": len(items),
                "documented_outcomes": len(documented),
                "conceptions": len(conceptions),
                "negative_pd": len(negative),
                "pregnancy_losses": len(losses),
                "calvings": len(calvings),
                "conception_rate_percent": cls._rate(len(conceptions), len(documented)),
                "loss_rate_per_conception_percent": cls._rate(len(losses), len(conceptions)),
                "calving_rate_per_conception_percent": cls._rate(len(calvings), len(conceptions)),
                "cycle_ids": [c["cycle_id"] for c in items],
                "animal_ids": sorted({c["animal_id"] for c in items}),
            })
        rows.sort(key=lambda row: (-row["cycles"], row["key"]))
        return rows

    @classmethod
    def summarize(cls, cycles: Iterable[dict[str, Any]]) -> dict[str, Any]:
        rows = list(cycles)
        closed = [c for c in rows if not str(c["status"]).startswith("ACTIVE_")]
        conceptions = [c for c in rows if c.get("pregnancy_confirmation_date")]
        calvings = [c for c in rows if c.get("outcome") == "CALVING"]
        losses = [
            c for c in rows
            if c.get("outcome") in {"PREGNANCY_LOST", "ABORTION", "STILLBIRTH"}
        ]
        herd_conception = cls._rate(len(conceptions), len(closed))

        by_animal = cls._group(rows, "animal_id")
        by_sire = cls._group(rows, "sire_code")
        by_semen_type = cls._group(rows, "semen_type")
        by_inseminator = cls._group(rows, "inseminator")

        signals: list[dict[str, Any]] = []
        for dimension, groups in (
            ("ANIMAL", by_animal),
            ("SIRE", by_sire),
            ("SEMEN_TYPE", by_semen_type),
            ("INSEMINATOR", by_inseminator),
        ):
            for group in groups:
                observed = group["documented_outcomes"]
                rate = group["conception_rate_percent"]
                if (
                    observed >= cls.MIN_SIGNAL_SAMPLE
                    and rate is not None
                    and herd_conception is not None
                    and rate <= herd_conception - cls.MATERIAL_RATE_GAP
                ):
                    signals.append({
                        "signal": "LOW_CONCEPTION_PATTERN",
                        "dimension": dimension,
                        "key": group["key"],
                        "sample_size": observed,
                        "observed_rate_percent": rate,
                        "herd_rate_percent": herd_conception,
                        "gap_percentage_points": round(herd_conception - rate, 2),
                        "cycle_ids": group["cycle_ids"],
                        "animal_ids": group["animal_ids"],
                        "explanation": (
                            f"{dimension.title()} {group['key']} has {observed} documented "
                            f"cycle outcomes with {rate}% conception versus {herd_conception}% "
                            "for the observed herd cycles."
                        ),
                    })

                conceptions_n = group["conceptions"]
                loss_rate = group["loss_rate_per_conception_percent"]
                herd_loss_rate = cls._rate(len(losses), len(conceptions))
                if (
                    conceptions_n >= cls.MIN_SIGNAL_SAMPLE
                    and loss_rate is not None
                    and herd_loss_rate is not None
                    and loss_rate >= herd_loss_rate + cls.MATERIAL_RATE_GAP
                ):
                    signals.append({
                        "signal": "HIGH_PREGNANCY_LOSS_PATTERN",
                        "dimension": dimension,
                        "key": group["key"],
                        "sample_size": conceptions_n,
                        "observed_rate_percent": loss_rate,
                        "herd_rate_percent": herd_loss_rate,
                        "gap_percentage_points": round(loss_rate - herd_loss_rate, 2),
                        "cycle_ids": group["cycle_ids"],
                        "animal_ids": group["animal_ids"],
                        "explanation": (
                            f"{dimension.title()} {group['key']} has {conceptions_n} confirmed "
                            f"conceptions with {loss_rate}% recorded pregnancy loss versus "
                            f"{herd_loss_rate}% across observed herd conceptions."
                        ),
                    })

        return {
            "data_status": "NO_DATA" if not rows else "LIVE_PERSISTED_DATA",
            "cycle_count": len(rows),
            "closed_cycle_count": len(closed),
            "active_cycle_count": len(rows) - len(closed),
            "documented_conceptions": len(conceptions),
            "calvings": len(calvings),
            "pregnancy_losses": len(losses),
            "herd_conception_rate_percent": herd_conception,
            "herd_loss_rate_per_conception_percent": cls._rate(len(losses), len(conceptions)),
            "by_animal": by_animal,
            "by_sire": by_sire,
            "by_semen_type": by_semen_type,
            "by_inseminator": by_inseminator,
            "signals": signals,
            "signal_policy": {
                "minimum_sample_size": cls.MIN_SIGNAL_SAMPLE,
                "material_rate_gap_percentage_points": cls.MATERIAL_RATE_GAP,
                "note": "Signals are evidence flags for management review, not causal diagnoses.",
            },
        }
