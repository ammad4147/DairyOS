#requires -Version 7.0
[CmdletBinding()]
param([string]$Repo = 'D:\DairyOS',[Parameter(Mandatory=$true)][string]$ExpectedSha)
$ErrorActionPreference = 'Stop'
Set-Location $Repo
Write-Host '=== DairyOS REMEDIATION SYNC GATE ==='
git fetch origin
if ($LASTEXITCODE -ne 0) { throw 'git fetch origin failed.' }
$Remote = (git rev-parse origin/main).Trim()
Write-Host "Expected remediation SHA : $ExpectedSha"
Write-Host "origin/main SHA           : $Remote"
if ($Remote -ne $ExpectedSha) { throw 'origin/main is not the expected remediation SHA. STOP.' }
$Status = @(git status --porcelain)
if ($Status.Count -gt 0) { $Status | ForEach-Object { Write-Host $_ }; throw 'Worktree is not clean. Preserve/stash local work explicitly; no reset was performed.' }
$Head = (git rev-parse HEAD).Trim()
$Base = (git merge-base HEAD origin/main).Trim()
if ($Head -ne $Base -and $Head -ne $Remote) { throw 'Local HEAD contains commits not represented by origin/main. STOP; no reset performed.' }
git merge --ff-only origin/main
if ($LASTEXITCODE -ne 0) { throw 'Fast-forward failed. STOP.' }
$Head = (git rev-parse HEAD).Trim()
if ($Head -ne $ExpectedSha) { throw 'HEAD mismatch after fast-forward.' }
Write-Host 'SYNC GATE: PASS'
Write-Host "HEAD: $Head"