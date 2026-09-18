# Assistant measurements

Recorded results from `tools/assistant_bench.py`. Kept in the repository
because AA-16 certification has to rest on measurements someone actually took,
not on a recollection that the Assistant seemed to work.

Each entry states the machine, the artefacts, and the numbers as they came out,
including the ones that are unflattering.

---

## AA-7, 18 September 2026

**Artefacts.** Qwen3-1.7B-Q4_K_M.gguf and llama.cpp b10456 `llama-server.exe`,
both verified against the pinned sha256 values in
`scripts/Get-AssistantRuntime.ps1`. Corpus 0.4.0, 44 servable items, pre-release
build serving implementation-reviewed content.

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
