param(
  [string]$Text = "你好，我係本地 TTS API。",
  [string]$Out = "",
  [string]$Server = "http://127.0.0.1:5055",
  [ValidateSet("自然语言控制", "3s极速复刻", "跨语种复刻")]
  [string]$Mode = "自然语言控制",
  [string]$Instruct = "请用广东话表达，语气清晰、自然。",
  [string]$PromptWav = "",
  [string]$PromptText = "",
  [int]$Seed = 0,
  [double]$Speed = 1.0
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$EnvRoot = Join-Path $Root "envs\cosyvoice"
$Python = Join-Path $EnvRoot "python.exe"
if (-not (Test-Path -LiteralPath $Python)) {
  $Python = Join-Path $EnvRoot "Scripts\python.exe"
}
if (-not (Test-Path -LiteralPath $Python)) {
  throw "Python environment not found. Run setup.ps1 first, or create envs\cosyvoice."
}
$Example = Join-Path $Root "api-call-example.py"

if (-not $Out) {
  $Out = Join-Path $Root "outputs\api-output.wav"
}

$env:PYTHONIOENCODING = "utf-8"

$Args = @(
  $Example,
  "--server", $Server,
  "--text", $Text,
  "--out", $Out,
  "--mode", $Mode,
  "--instruct", $Instruct,
  "--prompt-text", $PromptText,
  "--seed", $Seed,
  "--speed", $Speed
)

if ($PromptWav) {
  $Args += @("--prompt-wav", $PromptWav)
}

& $Python @Args
