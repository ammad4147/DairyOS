# DairyOS AI Assistant V2 Certification Report

Date: 2026-09-22  
Status: **CONDITIONALLY CLEARED — installed accelerator path passed; portability remains capability-driven**

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
| Runtime artifact verification | PASS | Qwen3-1.7B-Q4_K_M, llama.cpp b10456 CPU runtime, and optional Vulkan runtime matched pinned hashes |
| Assistant package | PASS | `dist/DairyOS-Assistant-Release/DairyOS-Assistant.dairyassistant`; rebuilt from the approval commit |
| Veterinary review | PASS | 70 dairy records approved by Dr Umair Shaffi on 2026-09-22 and rebuilt as `VET_REVIEWED` |
| Desktop bundle | PASS | Rebuilt from the approval commit; embedded Assistant package and private PostgreSQL runtime validated |
| Windows installer compile | PASS | Inno Setup 7.1.0; `DairyOS-Windows-Installer.exe` and release manifest produced |
| Installed acceptance | PASS | Installer exit 0; installed release and Assistant manifests cross-checked; two startup checks passed |
| Runtime profiles | PASS on installed workstation; hardware-neutral by design | Capability probe selected Vulkan; CPU fallback retained; `assistant-llama.log` capture added |

## Open gates

### GPU/runtime profiling

The workstation exposes an AMD Radeon RX 7900 XTX and an i7-13700KF. The
installed package contains separately pinned CPU and Vulkan runtimes. The
runtime probe selected Vulkan because the installed binary enumerated
`Vulkan0`; model-start logs show the model using `Vulkan0` and layers assigned
to that device. This is evidence for the installed machine only. DairyOS does
not bind to this GPU model: it selects any supported enumerated accelerator
and falls back to CPU when none is usable.

### Veterinary review

Dr Umair Shaffi approved the clinical responses in the review packet. All 70
dairy records are now marked `VET_REVIEWED` with reviewer and approval date;
the 89 DairyOS engineering records remain `ENGINEERING_VERIFIED`.

### Packaged installer acceptance

The desktop bundle and installer were rebuilt using Inno Setup 7.1.0 and
installed successfully. The installed release manifest records the release and
Assistant package commits, while the Assistant package records the corpus
generation commit explicitly. Two installed startup checks passed and the
installed Assistant status reported 70 `VET_REVIEWED` records and no
operational-data access. A second low-spec PC and the full 30-question UI
script remain additional deployment coverage, not performed on this machine.

## Clearance decision

The implementation, veterinary review, source regression, package build,
installer compile, and workstation installed acceptance are complete. The
installed accelerator path is verified on this workstation; cross-hardware
performance certification remains a deployment-coverage activity rather than
a DairyOS correctness gate.
