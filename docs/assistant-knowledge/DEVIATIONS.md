# Assistant knowledge: deviations from the brief

This file records every place where the delivered Assistant knowledge and
runtime depart from the brief, with the reason and what would close the gap.
An entry is an admission that a stated requirement is not met; nothing is
listed here to excuse it.

Revised 22 September 2026 for Assistant V2 (knowledge schema v3). Entries
D-002 and D-003 were rewritten because the V1 corpus they described was
retired; their history is kept in git.

## D-001. The Simulator is not taught

**Finding:** there is no Simulator in the promoted DairyOS source. The feature
is named in the brief, but no module, service, route or UI surface implements
it.

**Decision (operator, 2026-09-18):** omit Simulator knowledge and log the
deviation. Teaching behaviour that no code implements would be fabrication
carrying a citation.

**To close:** if a Simulator ships, author records anchored on its
implementation and remove this entry. Until then Simulator questions return
NOT_COVERED, which is accurate.

## D-002. General dairy knowledge is served before veterinary review

**Finding:** V2 serves 70 general dairy records with review status
`SOURCE_CURATED`. Each carries provenance to named authoritative sources in
`sources/registry.json` (Merck/MSD Veterinary Manual, university extension
services, NMC, WOAH and others), and the safety class of each record controls
how it may be used (EDUCATIONAL, TRIAGE, VET_ONLY). None has yet been signed by
a veterinarian.

**Decision:** serve them, because the V1 alternative (serve nothing general)
left operators with no dairy guidance at all, and because the pipeline never
lets these records diagnose, name a medicine or give a dose. The review status
travels with every evidence item so the UI can label it.

**Implementation:** `release.PRE_RELEASE` stays `False`; PENDING drafts are
never served. `SERVABLE_REVIEW_STATUSES` in `corpus/validation.py` lists what
may be served. `test_knowledge_governance.py` asserts that dairy records are
never marked `ENGINEERING_VERIFIED` and that each carries provenance.

**To close:** Dr Umair Shaffi reviews `veterinary-review-pack.html`
(regenerate with `python tools/build_review_pack.py`); approved records are set
to `VET_REVIEWED` with reviewer and date in their YAML source, then
`python tools/assistant_kb.py build`.

## D-003. The V1 veterinary sign-off does not transfer to V2

**Finding:** on 18 September 2026 Dr Umair Shaffi, DVM reviewed nineteen V1
clinical items. V2 replaced that corpus. Its dairy records are new text drawn
from cited sources, so the V1 approval does not cover them, and claiming it
would misstate the review.

**Decision:** no V2 record carries `VET_REVIEWED`. The V1 review is recorded
here and in git history only.

**To close:** as D-002.

## D-004. Elasticsearch is treated as an operational data route

**Finding:** `api/search.py` maintains a `dairyos-animals` Elasticsearch index on
loopback port 9200 containing animal records. The brief names the database but
not this index.

**Decision:** treated as named. `elasticsearch` is a forbidden import, and
ports 5432 and 9200 are refused by `model.assert_endpoint_allowed` before any
socket is opened. Both are asserted by `tests/assistant/test_boundary.py` and
`test_model_endpoint.py`.

## D-005. Retrieval is lexical (BM25F), not hybrid with embeddings

**Finding:** the brief sets hybrid retrieval as the direction. V2 ships a
field-weighted BM25 index with Roman-Urdu and shorthand phrase expansion,
spelling correction against the corpus vocabulary, collection and kind priors
from the intent classifier, and relation expansion. No embedding model is
shipped.

**Reason:** on the 605-question gold benchmark the lexical index reaches a
held-out Recall@5 of 0.967 in about 3 ms, with no second model to package,
pin and audit. An embedding model would have to beat that on the same split to
justify its footprint, and that comparison has not been run.

**To close:** evaluate a small local embedding model (for example
bge-small or multilingual-e5-small in GGUF) as a re-ranker on the test split,
and ship it only if recall on Roman-Urdu and paraphrase styles improves without
raising wrong-confident answers.

## D-006. Runtime profiles and GPU offload are not yet implemented

**Finding:** the bundled llama-server (b10456) is a CPU build and the bridge
passes only `-c 4096`. The certification workstation (i7-13700K, 64 GB,
RX 7900 XTX 24 GB) has not been measured, and the "2 cores" behaviour seen in
earlier runs was traced to the 2-vCPU cloud sandbox used for development, not
to DairyOS.

**Done:** the model client now separates connect (3 s), first-token (45 s),
stall (20 s) and total (120 s) limits, streams, and records TTFT and tokens/s;
the bridge's process-hang limit is 150 s. A model that misses a limit produces
the composed, grounded answer rather than no answer.

**To close:** see the handoff: a Vulkan llama.cpp build, hardware-aware
profiles (GPU, desktop CPU, low-spec CPU) selected by the bridge, llama-server
log capture, and a model comparison on the full benchmark.

## D-007. The Assistant screen still shows the V1 layout

**Finding:** the V2 service accepts conversation history and returns review
status and sources per evidence item, but `AIAssistant.tsx` and the API route
have not been updated to send history or display them.

**To close:** see the handoff (single mode, history, source and review labels,
follow-ups, model status). The top navigation is not to change.
