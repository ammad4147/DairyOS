# DairyOS AI Assistant V2 Certification Report

Date: 2026-09-22  
Status: **CONDITIONALLY CLEARED FOR INSTALLATION TESTING — GPU and installed acceptance remain open**

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
| Assistant package | PASS | `dist/DairyOS-Assistant-Release/DairyOS-Assistant.dairyassistant`; rebuilt from the approval commit |
| Veterinary review | PASS | 70 dairy records approved by Dr Umair Shaffi on 2026-09-22 and rebuilt as `VET_REVIEWED` |
| Desktop bundle | PASS | Rebuilt from the approval commit; embedded Assistant package and private PostgreSQL runtime validated |
| Windows installer compile | PASS | Inno Setup 7.1.0; `DairyOS-Windows-Installer.exe` and release manifest produced |
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

Dr Umair Shaffi approved the clinical responses in the review packet. All 70
dairy records are now marked `VET_REVIEWED` with reviewer and approval date;
the 89 DairyOS engineering records remain `ENGINEERING_VERIFIED`.

### Packaged installer acceptance

The desktop bundle and installer are now rebuilt from the approval commit using
Inno Setup 7.1.0. Installed-runtime acceptance is still pending: install on the
certification workstation and one low-spec PC, then complete first-start,
second-start, 30-question, model-absent, slow-model, and farm-data refusal
acceptance.

## Clearance decision

The implementation, veterinary review, source regression, package build, and
installer compile are complete. It is not certified as an installed DairyOS
release until GPU offload evidence and installed-runtime acceptance are recorded.
