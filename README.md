# CosyVoice FastAPI Server

A Windows PowerShell-based FastAPI wrapper for running CosyVoice TTS on a local
machine or LAN.

This repository contains the wrapper code and helper scripts only. It does not
include CosyVoice source code, model weights, Python environments, caches, logs,
or generated audio.

## Target Environment

- Windows 10/11
- PowerShell 7 or Windows PowerShell
- Python 3.10 recommended
- NVIDIA GPU with a working PyTorch/CUDA install recommended
- Git
- FFmpeg on `PATH` for non-WAV output formats

All examples use `<INSTALL_ROOT>` as a placeholder, for example:

```text
<INSTALL_ROOT>\cosyvoice-fastapi-server
```

Do not commit your personal install path, model weights, cache, or generated
audio.

## Setup

Clone this wrapper:

```powershell
cd <INSTALL_ROOT>
git clone https://github.com/leoli-dev/cosyvoice-fastapi-server.git
cd .\cosyvoice-fastapi-server
```

Run setup:

```powershell
.\setup.ps1
```

The setup script will:

- clone `https://github.com/FunAudioLLM/CosyVoice.git` into `.\CosyVoice`
- create `.\envs\cosyvoice`
- install wrapper and CosyVoice Python requirements
- download the default Fun-CosyVoice3 model into `.\models\Fun-CosyVoice3-0.5B`

If you already manage CosyVoice, Python, or model files yourself, use the skip
switches:

```powershell
.\setup.ps1 -SkipCosyVoiceClone
.\setup.ps1 -SkipPythonEnv
.\setup.ps1 -SkipModelDownload
```

## Start and Stop

Start the API server:

```powershell
.\start-cosyvoice-tts.ps1
```

Stop it:

```powershell
.\stop-cosyvoice-tts.ps1
```

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:5055/health
```

## API

Endpoint:

```text
POST /v1/audio/speech
```

PowerShell example:

```powershell
$body = @{
  input = "你好，呢个係纯 API TTS。"
  response_format = "wav"
  instruct = "请用广东话表达，语气清晰、自然。"
} | ConvertTo-Json

Invoke-WebRequest `
  -Uri "http://127.0.0.1:5055/v1/audio/speech" `
  -Method Post `
  -ContentType "application/json; charset=utf-8" `
  -Body $body `
  -OutFile ".\outputs\demo.wav"
```

Client script example:

```powershell
.\api-call-example.ps1 `
  -Text "你好，呢段声音係经由内网 API 生成。" `
  -Out ".\outputs\demo.wav"
```

## Request Fields

- `input`: text to synthesize.
- `response_format`: `wav`, `mp3`, `flac`, `ogg`, or `m4a`.
- `mode`: `自然语言控制`, `3s极速复刻`, or `跨语种复刻`.
- `instruct`: natural-language voice instruction.
- `prompt_wav`: server-local reference audio path.
- `prompt_text`: reference transcript for zero-shot mode.
- `seed`: random seed.
- `speed`: speech speed.

Response headers:

```text
X-Audio-Duration
X-TTS-Elapsed
X-TTS-RTF
X-TTS-Request-Count
```

## Warmup

The server does not run long warmup by default. To warm common sentence lengths:

```powershell
.\warm-cosyvoice-tts.ps1
```

To run blocking warmup during startup:

```powershell
.\start-cosyvoice-tts.ps1 -Warmup
```

## Third-Party Notice

This wrapper uses CosyVoice by FunAudioLLM and Fun-CosyVoice3 model artifacts,
but does not redistribute them. See [ATTRIBUTION.md](ATTRIBUTION.md).

The wrapper code and scripts in this repository are MIT licensed. Third-party
projects and model artifacts remain under their own licenses.
