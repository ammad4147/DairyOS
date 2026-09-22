"""Release gate for the knowledge the Assistant serves.

V2 serves only records whose review status is in
``corpus.validation.SERVABLE_REVIEW_STATUSES`` and which are not STALE:

* ``ENGINEERING_VERIFIED`` DairyOS capability records, verified against hashed
  source anchors (a source change makes them STALE and fails the build);
* ``SOURCE_CURATED`` general dairy records, curated from cited authoritative
  sources and labelled in the UI as not yet reviewed by the farm's veterinarian;
* ``VET_REVIEWED`` / ``OWNER_CONFIRMED`` records once a named reviewer signs off.

``PRE_RELEASE`` remains as the single, reviewable switch that would widen this
to ``PENDING`` drafts. It must stay false; ``tests/assistant/test_benchmark_quality.py``
asserts it.
"""

from __future__ import annotations

PRE_RELEASE = False
PRE_RELEASE_STATUSES: tuple[str, ...] = ("PENDING",)
PRE_RELEASE_REASON = (
    "Assistant V2: serves engineering-verified DairyOS knowledge and source-curated dairy knowledge "
    "(labelled pending veterinary review). Diagnosis, prescribing and dosing remain with the veterinarian."
)
