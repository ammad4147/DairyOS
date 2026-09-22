# DairyOS AI Assistant V2 Certification Report

Date: 2026-09-22  
Status: **NOT CERTIFIED — evidence assembled; external gates remain open**

## Scope

This report separates source, isolated regression, package, hardware, veterinary,
and installed-runtime evidence. A green source test or package manifest is not
treated as installed-runtime acceptance.

## Evidence completed

| Area | Result | Evidence |
|---|---|---|
| Knowledge build | PASS | 159 records, 159 servable, 621 facts, 0 stale, 0 errors |
| Assistant benchmark | PASS against configured floors | 439 held-out questions; 94.08% routing, 96.7% Recall@5, 94.99% useful, 99.77% safety, 0 critical failures |
| Full backend regression | PASS | 3,476 passed, 2 skipped; disposable PostgreSQL cluster on a dynamic loopback port |
| Frontend type check | PASS | `npm run typecheck` |
| Runtime artifact verification | PASS | Qwen3-1.7B-Q4_K_M and llama.cpp b10456 CPU runtime matched pinned hashes |
| Assistant package | PASS | `dist/DairyOS-Assistant-Release/DairyOS-Assistant.dairyassistant`; source commit `860b5d79` |
| Runtime profiles | IMPLEMENTED, not hardware-certified | GPU/Desktop CPU/Low-spec CPU selection and `assistant-llama.log` capture added |

## Open gates

### GPU/runtime profiling

The workstation exposes an AMD Radeon RX 7900 XTX and an i7-13700KF. The
checked-in runtime is CPU-only; no Vulkan server artifact is present. Therefore
GPU offload, VRAM use, TTFT, throughput, and model comparison are **not
certified**. A pinned Vulkan build must be supplied, then verified by the
llama-server device list, an `offloaded N/N layers to GPU` log entry, and a
live GPU/VRAM observation during an answer.

### Veterinary review

The 70 dairy records remain `SOURCE_CURATED`. The review pack exists at
`veterinary-review-pack.html`, but no veterinarian verdict, reviewer identity,
or review date was supplied. No record was changed to `VET_REVIEWED`, and no
veterinary approval is claimed.

### Packaged installer acceptance

The existing desktop bundle manifest points to source commit
`21ec0056af1f7d6222e2aa3770a23e2178061b62`, while the current Assistant package
was built from `860b5d79`. Inno Setup (`ISCC.exe`) is unavailable. The installer
must be rebuilt from a clean matching source/build, then installed on the
certification workstation and one low-spec PC with first-start, second-start,
30-question, model-absent, slow-model, and farm-data refusal acceptance.

## Clearance decision

The implementation is suitable for continued engineering evaluation and the
Assistant package is reproducibly built. It is not cleared as an installed
DairyOS release until the three open gates above are completed and evidenced.
