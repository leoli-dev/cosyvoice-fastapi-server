param(
  [string]$HostName = "0.0.0.0",
  [int]$Port = 5055,
  [switch]$NoWarmup,
  [switch]$Warmup,
  [switch]$Fp16,
  [switch]$AccessLog
)

$ErrorActionPreference = "Stop"
$Root = "E:\AI\tts\cosyvoice-server"
$RunDir = Join-Path $Root "run"
$PidFile = Join-Path $RunDir "cosyvoice-tts.pid"
$OutLog = Join-Path $RunDir "cosyvoice-tts.out.log"
$ErrLog = Join-Path $RunDir "cosyvoice-tts.err.log"
$Python = Join-Path $Root "envs\cosyvoice\python.exe"
$EnvRoot = Join-Path $Root "envs\cosyvoice"
$ApiServer = Join-Path $Root "homelab_tts_api.py"
$ModelDir = Join-Path $Root "models\Fun-CosyVoice3-0.5B"
$WorkDir = $Root

New-Item -ItemType Directory -Path $RunDir -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $Root "cache\hf"),(Join-Path $Root "cache\modelscope"),(Join-Path $Root "tmp") -Force | Out-Null

if (Test-Path -LiteralPath $PidFile) {
  $ExistingPid = (Get-Content -LiteralPath $PidFile -Raw).Trim()
  if ($ExistingPid -and (Get-Process -Id ([int]$ExistingPid) -ErrorAction SilentlyContinue)) {
    Write-Host "CosyVoice TTS already running. PID: $ExistingPid"
    exit 0
  }
}

$env:HF_HOME = Join-Path $Root "cache\hf"
$env:HUGGINGFACE_HUB_CACHE = Join-Path $Root "cache\hf\hub"
$env:MODELSCOPE_CACHE = Join-Path $Root "cache\modelscope"
$env:TEMP = Join-Path $Root "tmp"
$env:TMP = $env:TEMP
$env:GRADIO_TEMP_DIR = Join-Path $Root "tmp\gradio"
$env:COSYVOICE_DEFAULT_PROMPT_WAV = Join-Path $Root "CosyVoice\asset\zero_shot_prompt.wav"
$env:COSYVOICE_DEFAULT_PROMPT_TEXT = "You are a helpful assistant.<|endofprompt|>希望你以后能够做的比我还好呦。"
$env:ORT_LOG_SEVERITY_LEVEL = "3"
$env:PYTHONUNBUFFERED = "1"
$env:PATH = @(
  $EnvRoot,
  (Join-Path $EnvRoot "Library\mingw-w64\bin"),
  (Join-Path $EnvRoot "Library\usr\bin"),
  (Join-Path $EnvRoot "Library\bin"),
  (Join-Path $EnvRoot "Scripts"),
  (Join-Path $EnvRoot "bin"),
  $env:PATH
) -join ";"

$WarmupArg = if ($Warmup -and -not $NoWarmup) { " --warmup" } else { "" }
$Fp16Arg = if ($Fp16) { " --fp16" } else { "" }
$AccessLogArg = if ($AccessLog) { " --access-log" } else { "" }
$Args = "`"$ApiServer`" --host `"$HostName`" --port $Port --model_dir `"$ModelDir`"$WarmupArg$Fp16Arg$AccessLogArg"
$Process = Start-Process `
  -FilePath $Python `
  -ArgumentList $Args `
  -WorkingDirectory $WorkDir `
  -RedirectStandardOutput $OutLog `
  -RedirectStandardError $ErrLog `
  -WindowStyle Hidden `
  -PassThru

try {
  $Process.PriorityClass = "AboveNormal"
} catch {
}

$Process.Id | Set-Content -LiteralPath $PidFile -Encoding ASCII
Write-Host "CosyVoice TTS API started. PID: $($Process.Id)"
Write-Host "Local API: http://127.0.0.1:$Port/v1/audio/speech"
Write-Host "LAN API: http://<server-lan-ip>:$Port/v1/audio/speech"
Write-Host "Output log: $OutLog"
Write-Host "Error log: $ErrLog"
