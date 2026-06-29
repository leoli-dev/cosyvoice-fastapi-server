param(
  [string]$CosyVoiceRepo = "https://github.com/FunAudioLLM/CosyVoice.git",
  [string]$ModelRepo = "FunAudioLLM/Fun-CosyVoice3-0.5B-2512",
  [string]$ModelDir = "",
  [switch]$SkipCosyVoiceClone,
  [switch]$SkipPythonEnv,
  [switch]$SkipModelDownload
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$EnvDir = Join-Path $Root "envs\cosyvoice"
$Python = Join-Path $EnvDir "Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) {
  $Python = Join-Path $EnvDir "python.exe"
}
if (-not $ModelDir) {
  $ModelDir = Join-Path $Root "models\Fun-CosyVoice3-0.5B"
}

New-Item -ItemType Directory -Path (Join-Path $Root "models"),(Join-Path $Root "outputs"),(Join-Path $Root "cache"),(Join-Path $Root "tmp") -Force | Out-Null

if (-not $SkipCosyVoiceClone) {
  $cosyVoicePath = Join-Path $Root "CosyVoice"
  if (Test-Path -LiteralPath $cosyVoicePath) {
    Write-Host "CosyVoice already exists: $cosyVoicePath"
  } else {
    git clone $CosyVoiceRepo $cosyVoicePath
  }
}

if (-not $SkipPythonEnv) {
  if (-not (Test-Path -LiteralPath $EnvDir)) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
      py -3.10 -m venv $EnvDir
    } else {
      python -m venv $EnvDir
    }
  }
  if (-not (Test-Path -LiteralPath $Python)) {
    throw "Python venv was created, but python.exe was not found in $EnvDir"
  }
  & $Python -m pip install --upgrade pip
  & $Python -m pip install -r (Join-Path $Root "requirements.txt")

  $cosyReq = Join-Path $Root "CosyVoice\requirements.txt"
  if (Test-Path -LiteralPath $cosyReq) {
    & $Python -m pip install -r $cosyReq
  }
}

if (-not $SkipModelDownload) {
  if (-not (Test-Path -LiteralPath $Python)) {
    throw "Python environment not found. Run setup without -SkipPythonEnv first, or create envs\cosyvoice manually."
  }
  $downloadScript = @"
from pathlib import Path
model_dir = Path(r"$ModelDir")
model_dir.mkdir(parents=True, exist_ok=True)
try:
    from modelscope import snapshot_download
    snapshot_download("$ModelRepo", local_dir=str(model_dir))
except Exception:
    from huggingface_hub import snapshot_download
    snapshot_download("$ModelRepo", local_dir=str(model_dir), local_dir_use_symlinks=False)
"@
  $downloadScript | & $Python -
}

Write-Host "Setup complete."
Write-Host "CosyVoice path: $(Join-Path $Root 'CosyVoice')"
Write-Host "Model path: $ModelDir"
Write-Host "Start: $(Join-Path $Root 'start-cosyvoice-tts.ps1')"
