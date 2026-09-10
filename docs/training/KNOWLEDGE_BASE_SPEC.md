# DairyOS Assistant Knowledge Base

This directory is the source of truth for the DairyOS Assistant. The assistant
must not be built from unreviewed or invented content.

## Content contract

Every knowledge item must include:

- `id`, `domain`, `capability`, `title`, and `status`
- one canonical question plus alternative operator phrasings
- a concise answer and an expanded explanation
- role-specific guidance where the answer differs by responsibility
- preconditions, step-by-step actions, expected result, and next action
- persisted facts, derived calculations, projections, and audit effects
- normal path, exception paths, correction/recovery, and safety warnings
- related knowledge-item IDs for cross-linking
- implementation anchors: screen/component, API route, service/model, and test
- source authority and reviewer/date metadata

## Review states

- `INVENTORY`: capability identified but content not yet written
- `DRAFT`: content written, implementation anchors still being checked
- `IMPLEMENTATION_REVIEW`: content checked against current source and tests
- `DOMAIN_REVIEW`: operational/accounting/veterinary wording awaiting review
- `APPROVED`: safe for simulator and assistant consumption
- `DEPRECATED`: retained for history but must not be served as current guidance

## Safety rules

1. The knowledge base must never be used to infer a write permission.
2. Health-check guidance must remain explicitly read-only.
3. Reset guidance must identify the exact confirmation, maintenance handoff,
   verified recovery point, zero-state check, and failure rollback.
4. A live-data answer must identify its data date and source authority.
5. If implementation and documentation disagree, the item is blocked from
   `APPROVED` status until the discrepancy is resolved.
6. Assistant answers must remain grounded in approved knowledge and must never
   infer write permission or silently act on live DairyOS data.

## Required answer perspectives

Where applicable, each item is written from the operator, supervisor,
finance, veterinary/health, technical, training, and troubleshooting
perspectives. A perspective may be marked `NOT_APPLICABLE`, but may not be
silently omitted.

## Completion gate

The assistant UI may begin only when the capability catalog is complete, every
item is cross-linked, all implementation anchors have been validated against
the current repository, domain review is complete, and the coverage checks
pass.
