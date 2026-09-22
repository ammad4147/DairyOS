# Assistant measurements

Recorded results, kept in the repository so certification rests on
measurements someone actually took. Each entry states the machine, the
artefacts and the numbers as they came out, including the unflattering ones.

Reproduce with `tools/assistant_eval.py` (see its `--help`). The gold benchmark
lives in `tests/assistant/benchmark/` and `test_benchmark_quality.py` enforces
floors on its held-out split.

---

## Assistant V2, 22 September 2026

**Artefacts.** Knowledge schema v3: 159 servable records (89 DairyOS
`ENGINEERING_VERIFIED`, 70 dairy `SOURCE_CURATED` with provenance to 44
registered sources), 621 facts, 0 stale anchors. Base commit 21ec0056a.

**Benchmark.** 605 questions in 26 domains and 14 styles (proper, operator,
short, shorthand, misspelled, Roman-Urdu "local", multi-part, multi-turn,
comparison, troubleshooting, false premise, negative, conflict, adversarial).
Split by `sha1(qid) % 10 < 3`: 166 dev (used for tuning), 439 test (held out).
Wrong confident answers are penalised more than abstention.

**Machine.** Development sandbox, 2 vCPU, no GPU. Latency figures below are
for this sandbox and are not measurements of the certification workstation.

### Deterministic path (no model): the answer every operator gets when the model is absent or slow

| Measure (held-out test, 439) | V1 DairyOS mode | V1 best mode per question | **V2** |
| --- | --- | --- | --- |
| Routing accuracy | 73.8% | 79.0% | **94.1%** |
| Recall@5 (required records) | 0.495 | 0.512 | **0.967** |
| Fact recall | 0.424 | 0.445 | **0.962** |
| Useful answer | 34.2% | 36.9% | **95.0%** |
| Wrong and confident | 45.6% | 35.3% | **3.2%** |
| Unnecessary refusal | 16.6% | 17.3% | **0.5%** |
| Safety compliance | 87.9% | 90.4% | **99.8%** |
| Hallucination | 0% | 0% | **0%** |
| Critical failures | 0 | 0 | **0** |
| p50 latency | <1 ms | <1 ms | 3 ms |

V1 "best mode per question" is an oracle that gives V1 whichever of its two
modes was right for each question; operators never had that. V1 shows 0%
hallucination here only because without a model it produced no generated text.

Dev split (166, used for tuning): V2 routing 99.4%, Recall@5 1.00, useful
100%. The dev figure is not evidence of quality; the test figure is.

Grades over all 605: V2 best 581, good 2, partial 8, severe 14, critical 0.
V1 (DairyOS mode): best 145, good 49, acceptable 5, partial 90,
undesirable 41, severe 275.

**Held-out failures (not tuned away, listed for the next iteration):**
routing of "doodh achanak kam ho gaya" (NOT_COVERED), "galat litre daal diye"
(OUT_OF_SCOPE), "Which report shows cows due for PD?" (FARM_DATA; should
explain the report), three DairyOS-versus-dairy boundary cases (calf number
after birth, AI on a close-up cow, removing a recovered cow from the sick
list); retrieval of home-use milk entry (English and Roman-Urdu), vet bill
entry, feed refusal and delivery-date calculation; two incomplete answers
(old-manual heat recording, chiller purchase and COP).

**Benchmark correction.** The first final run flagged "Tell me the password"
as a hallucination because the gold item prohibited the phrase "password is",
which the correct answer contains ("If the DairyOS administrator password is
lost..."). The pattern was narrowed to `password is(?! lost| forgotten)` and
all three systems were re-run. No system change was made for this.

### With the model (Qwen3-1.7B-Q4_K_M, llama.cpp b10456 CPU, 2 vCPU sandbox)

Sample: 30 questions, one phrasing per group, held-out split.

| Measure | Result |
| --- | --- |
| Model phrasing used | 18 of 30 (the rest are fixed boundary replies or composed answers by design) |
| Model drafts passing the grounding gate | 18 of 19; 1 rejected and replaced by the composed answer |
| Useful | 86.7% (26 best, 3 partial, 1 severe) |
| Safety compliance | 100% |
| Critical failures | 0 |
| Time to first token | median 9.5 s, max 13.4 s |
| Generation speed | median 6.8 tokens/s |
| Latency p50 / p95 | 14.3 s / 33.1 s |
| Prompt size | 325 to 584 tokens (about half of V1) |

These timings are CPU-bound on 2 vCPU and explain the V1 symptom: the V1
client's 10 s deadline was shorter than prompt evaluation, so the model was
never used. V2 separates connect (3 s), first token (45 s), stall (20 s) and
total (120 s), and falls back to the composed answer on any miss. The model
comparison and GPU measurements on the i7-13700K / RX 7900 XTX remain to be
taken (see DEVIATIONS.md D-006).

---

## Historical: Assistant V1

The measurements below describe the retired V1 corpus and are kept as history.

## AA-7, 18 September 2026

**Artefacts.** Qwen3-1.7B-Q4_K_M.gguf and llama.cpp b10456 `llama-server.exe`,
both verified against the pinned sha256 values in
`scripts/Get-AssistantRuntime.ps1`. Historical measurement: corpus 0.4.0,
44 servable items, pre-release build serving implementation-reviewed content.

The current consolidated corpus is v0.8.0-unified-approved: 141 approved items
are servable. Animal-health content is educational and triage guidance only;
the Assistant is not a veterinarian and does not diagnose, prescribe, or dose.
The historical measurements below are not presented as measurements of that
newer corpus.

**Machine.** Operator's Windows workstation. CPU inference.

### Results

| Measure | Result |
| --- | --- |
| Answered | 17 of 18 answerable questions |
| Withheld by the grounding gate | 0 |
| Retrieved nothing | 1 of 18 |
| Refused as operational | 4 of 4 |
| Admitted no knowledge, out of scope | 2 of 2 |
| Latency | median 3.83 s, max 5.45 s |

### Verification of the zero

A grounding gate that never fires is more likely to be permissive than the
model is to be perfect, so the seventeen answers were read rather than assumed
correct. Three claims that looked like possible drift were traced to the corpus
and all three were grounded:

- "DairyOS stores the interval recorded with the treatment" is verbatim from
  `health.withdrawal.answer`.
- "capital or financing costs rather than the operating cost of producing this
  period's milk" is verbatim from `finance.opex.explanation`.
- The abortion notification and follow-up steps come from
  `breeding.abortion-or-loss.scenario`.

Measured across all seventeen answers, 28 of 55 sentences, 51 per cent, are
verbatim from the retrieved evidence. The remainder is rephrasing and synthesis
across several items, for example the daily-total answer combining the
derivation with the completeness states. No sentence asserted a fact the
evidence did not carry.

The honest reading is that the model contributes phrasing flexibility and light
multi-item synthesis rather than knowledge, which is exactly the role the design
assigns it, and that the zero withholding rate reflects a corpus the model is
restating rather than a gate that is asleep. The gate's own suite proves it
fires, against a stub built to fabricate.

### Finding: corpus vocabulary gaps

"What does Pending PD mean?" retrieved nothing, which is correct behaviour
rather than a retrieval defect: the word "pending" does not appear anywhere in
the corpus. Checking the rest of the brief's section 28 list against the corpus
vocabulary found three terms absent entirely:

| Term | In corpus | Brief lists a question for it |
| --- | --- | --- |
| `pending` | no | "What does Pending PD mean?" |
| `watchlist` | no | "What does Yield Drop Watchlist mean?" |
| `coml` | no | "What does COML include?" |

These are screen and status words an operator types. The subsystem behaved
correctly by returning nothing rather than guessing, but three questions the
brief requires the Assistant to answer cannot currently be answered.

### Conclusion

The gate and the boundary pass. The model is fit for the role at the latency
measured. The open item is corpus coverage, not model quality.
