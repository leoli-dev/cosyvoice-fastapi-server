$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$PidFile = Join-Path $Root "run\cosyvoice-tts.pid"

if (-not (Test-Path -LiteralPath $PidFile)) {
  Write-Host "CosyVoice TTS API is not running: PID file not found."
  exit 0
}

$PidText = (Get-Content -LiteralPath $PidFile -Raw).Trim()
if ($PidText) {
  $Process = Get-Process -Id ([int]$PidText) -ErrorAction SilentlyContinue
  if ($Process) {
    Stop-Process -Id $Process.Id -Force
    Write-Host "CosyVoice TTS API stopped. PID: $PidText"
  } else {
    Write-Host "CosyVoice TTS API process was already stopped. PID: $PidText"
  }
}

Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue
