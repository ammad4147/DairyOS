<#
.SYNOPSIS
    Download and verify the DairyOS Assistant runtime: the local model and the
    llama.cpp server.

.DESCRIPTION
    The installed machine must need nothing external, so both artefacts are
    bundled into the package. They cannot live in git, because the model is
    1.28 GB and GitHub rejects files over 100 MB, so the build machine fetches
    them once and verifies them against pinned sha256 values.

    The pins are the point. They are the hashes of the exact artefacts that
    were benchmarked at six of six cases correct, 0.93 s mean latency and
    2,286 MB peak. A file that does not match a pin is not the file that was
    tested, and this script refuses it rather than shipping it.

    Re-running is cheap: an artefact already present and verified is skipped,
    and a partial download resumes rather than restarting.

.PARAMETER Force
    Re-download even if a verified artefact is already present.
#>
[CmdletBinding()]
param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$RepoRoot    = Split-Path -Parent $PSScriptRoot
$RuntimeRoot = Join-Path $RepoRoot "runtime\assistant"
$ModelDir    = Join-Path $RuntimeRoot "model"
$LlamaDir    = Join-Path $RuntimeRoot "llama"
$VulkanDir   = Join-Path $RuntimeRoot "llama-vulkan"
$WorkDir     = Join-Path $RuntimeRoot "_download"

$ModelPath   = Join-Path $ModelDir "Qwen3-1.7B-Q4_K_M.gguf"
$ServerPath  = Join-Path $LlamaDir "llama-server.exe"

# Pinned artefacts. Section 3 of the AA handoff.
$ModelUrl    = "https://huggingface.co/ggml-org/Qwen3-1.7B-GGUF/resolve/main/Qwen3-1.7B-Q4_K_M.gguf?download=true"
$ModelSha    = "D2387CA2DBFEE2FFABCE7120D3770DADCA0B293052BC2F0E138FDC940D9BC7B5"
$ModelBytes  = 1282439264

$ZipUrl      = "https://github.com/ggml-org/llama.cpp/releases/download/b10456/llama-b10456-bin-win-cpu-x64.zip"
$ServerSha   = "B3A37101C241635E5F6183FA88B1286B477FAAA4B573FB00EC484E0C6346B10F"
$VulkanZipUrl = "https://github.com/ggml-org/llama.cpp/releases/download/b10456/llama-b10456-bin-win-vulkan-x64.zip"
$VulkanZipSha = "60F3D31CC7C2FE62DE8F34F8D75FFD06655B4DE83BCC5AA6F08DF56BE42EBB91"
$VulkanServerSha = "B3A37101C241635E5F6183FA88B1286B477FAAA4B573FB00EC484E0C6346B10F"

function Test-Pinned {
    param([string]$Path, [string]$ExpectedSha, [long]$ExpectedBytes = 0)

    if (-not (Test-Path -LiteralPath $Path)) { return $false }
    if ($ExpectedBytes -gt 0) {
        $actualBytes = (Get-Item -LiteralPath $Path).Length
        if ($actualBytes -ne $ExpectedBytes) {
            Write-Host "  size mismatch: $actualBytes bytes, expected $ExpectedBytes"
            return $false
        }
    }
    $actualSha = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
    if ($actualSha -ne $ExpectedSha) {
        Write-Host "  sha256 mismatch: $actualSha"
        return $false
    }
    return $true
}

New-Item -ItemType Directory -Force -Path $ModelDir, $LlamaDir, $VulkanDir, $WorkDir | Out-Null

# -- model ------------------------------------------------------------------

if ((-not $Force) -and (Test-Pinned -Path $ModelPath -ExpectedSha $ModelSha -ExpectedBytes $ModelBytes)) {
    Write-Host "Model already present and verified."
} else {
    Write-Host "Downloading Qwen3-1.7B-Q4_K_M.gguf (1.28 GB)..."
    # curl.exe streams and resumes. Invoke-WebRequest on Windows PowerShell 5.1
    # buffers the whole body in memory, which is unreasonable at this size.
    & curl.exe -L -C - --fail --retry 3 -o $ModelPath $ModelUrl
    if ($LASTEXITCODE -ne 0) { throw "model download failed (curl exit $LASTEXITCODE)" }

    if (-not (Test-Pinned -Path $ModelPath -ExpectedSha $ModelSha -ExpectedBytes $ModelBytes)) {
        throw "Model failed verification against the pinned sha256. Refusing to ship an untested artefact."
    }
    Write-Host "Model verified."
}

# -- llama-server -----------------------------------------------------------

if ((-not $Force) -and (Test-Pinned -Path $ServerPath -ExpectedSha $ServerSha)) {
    Write-Host "llama-server already present and verified."
} else {
    $zipPath = Join-Path $WorkDir "llama-b10456-bin-win-cpu-x64.zip"
    Write-Host "Downloading llama.cpp b10456..."
    & curl.exe -L -C - --fail --retry 3 -o $zipPath $ZipUrl
    if ($LASTEXITCODE -ne 0) { throw "llama.cpp download failed (curl exit $LASTEXITCODE)" }

    $extractDir = Join-Path $WorkDir "b10456"
    if (Test-Path -LiteralPath $extractDir) { Remove-Item -Recurse -Force $extractDir }
    Expand-Archive -LiteralPath $zipPath -DestinationPath $extractDir -Force

    $found = Get-ChildItem -Path $extractDir -Recurse -Filter "llama-server.exe" | Select-Object -First 1
    if (-not $found) { throw "llama-server.exe not found in the downloaded archive" }

    # The server needs the DLLs shipped beside it, so the whole binary
    # directory is taken rather than the executable alone.
    Copy-Item -Path (Join-Path $found.DirectoryName "*") -Destination $LlamaDir -Recurse -Force

    if (-not (Test-Pinned -Path $ServerPath -ExpectedSha $ServerSha)) {
        throw "llama-server.exe failed verification against the pinned sha256. Refusing to ship an untested artefact."
    }
    Write-Host "llama-server verified."
}

# -- optional Vulkan llama-server ------------------------------------------

$VulkanServerPath = Join-Path $VulkanDir "llama-server.exe"
if ((-not $Force) -and (Test-Pinned -Path $VulkanServerPath -ExpectedSha $VulkanServerSha)) {
    Write-Host "Vulkan llama-server already present and verified."
} else {
    $vulkanZipPath = Join-Path $WorkDir "llama-b10456-bin-win-vulkan-x64.zip"
    Write-Host "Downloading llama.cpp b10456 Vulkan runtime..."
    & curl.exe -L -C - --fail --retry 3 -o $vulkanZipPath $VulkanZipUrl
    if ($LASTEXITCODE -ne 0) { throw "llama.cpp Vulkan download failed (curl exit $LASTEXITCODE)" }
    if (-not (Test-Pinned -Path $vulkanZipPath -ExpectedSha $VulkanZipSha)) {
        throw "Vulkan archive failed verification against the pinned sha256. Refusing to extract it."
    }

    $vulkanExtractDir = Join-Path $WorkDir "b10456-vulkan"
    if (Test-Path -LiteralPath $vulkanExtractDir) { Remove-Item -Recurse -Force $vulkanExtractDir }
    Expand-Archive -LiteralPath $vulkanZipPath -DestinationPath $vulkanExtractDir -Force

    $vulkanFound = Get-ChildItem -Path $vulkanExtractDir -Recurse -Filter "llama-server.exe" | Select-Object -First 1
    if (-not $vulkanFound) { throw "Vulkan llama-server.exe not found in the downloaded archive" }
    Copy-Item -Path (Join-Path $vulkanFound.DirectoryName "*") -Destination $VulkanDir -Recurse -Force

    if (-not (Test-Pinned -Path $VulkanServerPath -ExpectedSha $VulkanServerSha)) {
        throw "Vulkan llama-server.exe failed verification against the pinned sha256. Refusing to ship an untested artefact."
    }
    Write-Host "Vulkan llama-server verified."
}

Remove-Item -Recurse -Force $WorkDir -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "Assistant runtime ready:"
Write-Host "  $ModelPath"
Write-Host "  $ServerPath"
