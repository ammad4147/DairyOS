"""The pre-release switch, and the single place it can be turned off.

The corpus is authored but not yet reviewed. Only ``APPROVED`` items are
servable, so a correctly configured Assistant built today would answer nothing
at all. That is the review gate doing its job, and weakening the gate itself
would be the wrong fix, because the gate is what makes an approved corpus mean
something.

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
PRE_RELEASE = True

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
    "Corpus v0.4.0 has passed implementation review against traced DairyOS "
    "source but has not had domain review. Operator decision of 2026-09-18: "
    "serve implementation-reviewed content during gates AA-6 to AA-12 so the "
    "subsystem can be built and tested, with every item flagged unreviewed, "
    "and require approval before AA-16 certification."
)
