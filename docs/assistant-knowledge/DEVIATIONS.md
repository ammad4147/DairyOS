# Assistant corpus: deviations from the project brief

This file records every place where the delivered Assistant knowledge corpus
departs from the project brief, together with the reason and the operator
decision that settled it. It exists so that a reviewer comparing the brief to
the corpus can tell a deliberate omission from an oversight without having to
reconstruct the reasoning from commit messages.

Nothing is added here to excuse a gap. An entry is an admission that a stated
requirement is not met, and each one names what would have to change for it to
be met.

## D-001. The Simulator is not taught

**Brief sections:** 7 and 26, which require the Assistant to explain the
DairyOS Simulator to operators.

**Finding:** there is no Simulator in the promoted DairyOS source. The feature
is named in the brief and referenced by the legacy training corpus, but no
module, service, route or UI surface implements it. This was confirmed by
searching the promoted tree rather than inferred from its absence in one place.

**Decision (operator, 2026-09-18):** omit Simulator knowledge entirely and log
the deviation.

**Reasoning:** the corpus rule is that every claim is traced to source. Writing
Simulator items from the brief's prose would mean the Assistant teaching
behaviour that no code implements, which is fabrication carrying a citation,
and it is precisely the failure the grounding gate exists to catch. An operator
acting on such an answer would look for a feature that is not there.

**To close:** if a Simulator ships, author items against its implementation and
remove this entry. Until then the Assistant returns no evidence for Simulator
questions and says it does not know, which is accurate.

## D-002. The corpus is served before domain review

**Brief sections:** the status schema, which makes `APPROVED` the only servable
status.

**Finding:** all 47 items have passed implementation review against traced
DairyOS source. None has passed domain review, because no qualified reviewer
has yet been appointed.

**Decision (operator, 2026-09-18):** run gates AA-6 to AA-12 as a pre-release
build that additionally serves implementation-reviewed content, with every item
flagged `unreviewed`, and require approval before AA-16 certification.

**Implementation:** `src/dairyos_assistant/release.py` holds a single build-time
constant, `PRE_RELEASE`. It is a constant rather than an environment variable so
that it cannot be set by accident on a customer machine, by a support script, or
by an operator following advice found online. The manifest default is unchanged
at `["APPROVED"]`.

**To close:** set `PRE_RELEASE = False` and run
`DAIRYOS_ASSISTANT_CERTIFY=1 pytest tests/assistant/test_certification.py`.
That module fails today, deliberately, and is the gate that stops an unreviewed
corpus shipping.

## D-003. Clinical content awaits a named veterinary reviewer

**Brief sections:** the requirement that approved items carry
`domain_reviewed_by`, and the requirement for evidence-backed veterinary,
vaccination and breeding knowledge.

**Finding:** the health, vaccination and breeding-science items make clinical
claims. The implementer is not competent to review them and neither is the
agent that authored them.

**Decision (operator, 2026-09-18):** a named veterinarian signs the clinical
items; the operator signs the DairyOS mechanics items, which are traced to
source and require no clinical judgement.

**Closed, 18 September 2026.** Dr Umair Shaffi, DVM reviewed the nineteen
clinical items in `veterinary-review-pack.html` and endorsed them. All nineteen
now carry his name and that date in `domain_reviewed_by` and
`domain_reviewed_at`, and are `APPROVED`.

**Consequence, and it is not a small one.** Approving the clinical items alone
made the corpus more dangerous rather than less. Retrieval serves the best
approved match, so with the twenty-five mechanics items still unapproved, "How
do I record milk for a session?" returned `breeding.dry-off` in a certified
build: a confident answer from the wrong item. A partly approved corpus is
worse than an unapproved one, because an unapproved one returns nothing.

The pre-release flag therefore stays on until the mechanics items are signed
too. This is recorded here because it is a trap anyone repeating this sequence
on a later corpus will walk into.

## D-004. Elasticsearch is treated as an operational data route

**Brief sections:** section 1, which enumerates the operational data the
Assistant must never reach, and does not mention the search index.

**Finding:** `api/search.py` maintains a `dairyos-animals` Elasticsearch index
on loopback port 9200. It contains animal records. The brief's prohibition
names the database but not this index, so a literal reading of the brief would
have left a second route to operational data uncovered.

**Decision:** treated as named. `elasticsearch` is in the forbidden import list,
9200 is in the forbidden port list, and both are asserted by
`tests/assistant/test_boundary.py`.

**Note:** this is a deviation in the direction of more restriction than the
brief requires, recorded here so that the boundary certification can be audited
against what was actually enforced rather than against what was written down.
