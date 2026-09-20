"""The pre-release switch, and the single place it can be turned off.

The certified corpus serves only ``APPROVED`` items. The current consolidated
corpus contains 141 approved items, including the independently source-verified
non-clinical DairyOS how-to set and the veterinary-reviewed educational/triage
set. The Assistant is not a veterinarian and must not diagnose, prescribe, or
provide dosing.

So the gate is left alone and a separate, deliberate, single-valued switch is
provided instead. While ``PRE_RELEASE`` is true the index additionally serves
items that have passed implementation review, and every one of those items is
marked ``unreviewed`` so the distinction survives into the API response and
into whatever the operator sees.

This is a build-time constant rather than an environment variable on purpose.
An environment variable can be set on a customer's machine by accident, by a
support script, or by a well-meaning operator following a forum post. A
constant can only change by a commit, which is reviewable, and which the
certification test at AA-16 asserts against.

**Before certification this must be false.** ``tests/assistant/test_certification.py``
asserts exactly that, and is the gate that stops an unreviewed corpus shipping.
"""

from __future__ import annotations

# Set false before AA-16 certification. Nothing else in the package may
# override this at runtime.
PRE_RELEASE = False

# What a pre-release build additionally serves. Domain review is included
# because an item that has passed it is strictly better evidenced than one that
# has only passed implementation review; neither is approved, and both are
# flagged.
PRE_RELEASE_STATUSES: tuple[str, ...] = (
    "IMPLEMENTATION_REVIEW",
    "DOMAIN_REVIEW",
    "APPROVED",
)

# The reason, recorded here so that a reader of a pre-release build knows why
# it is one without having to find the decision in a chat log.
PRE_RELEASE_REASON = (
    "Closed 20 September 2026. Corpus v0.8.0-unified-approved contains 141 "
    "approved items. Animal-health content is educational and triage guidance "
    "only; diagnosis, prescribing, and dosing remain with a veterinarian. The "
    "switch is off and this build serves only approved knowledge."
)
