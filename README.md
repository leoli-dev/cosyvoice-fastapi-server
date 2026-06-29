# CosyVoice FastAPI Server

A small self-hosted FastAPI wrapper around CosyVoice3 for LAN TTS calls.

This repository contains only the API wrapper, client examples, and Windows
PowerShell helper scripts. It does not include CosyVoice source code, model
weights, Python environments, caches, or generated audio files.

## Features

- OpenAI-style `POST /v1/audio/speech` endpoint.
- Health check endpoint at `GET /health`.
- WAV output by default, with optional mp3/flac/ogg/m4a conversion through
  FFmpeg.
- CosyVoice3 natural-language control mode by default.
- Optional zero-shot and cross-lingual modes exposed through request fields.
- Windows start/stop/warmup scripts.

## Repository Layout

```text
homelab_tts_api.py          FastAPI server
start-cosyvoice-tts.ps1     Start server on Windows
stop-cosyvoice-tts.ps1      Stop server on Windows
warm-cosyvoice-tts.ps1      Optional warmup request script
api-call-example.py         Python client example
api-call-example.ps1        PowerShell client wrapper
API_USAGE.md                API examples
ATTRIBUTION.md              Third-party notices
```

## Required External Files

Expected local layout after setup:

```text
CosyVoice/                              # cloned separately
models/Fun-CosyVoice3-0.5B/             # downloaded separately
envs/cosyvoice/                         # local Python environment
```

The default PowerShell scripts assume the repository is located at:

```text
E:\AI\tts\cosyvoice-server
```

If you install elsewhere, edit `$Root` in the `.ps1` scripts.

## Third-Party Attribution

This wrapper depends on:

- CosyVoice by FunAudioLLM: https://github.com/FunAudioLLM/CosyVoice
- Fun-CosyVoice3 model weights from Hugging Face or ModelScope.
- PyTorch, FastAPI, Uvicorn, librosa, soundfile, and FFmpeg.

See [ATTRIBUTION.md](ATTRIBUTION.md) for license and source notes. The wrapper
code in this repository is MIT licensed; CosyVoice and model artifacts remain
under their own licenses.

## API

Start the service:

```powershell
E:\AI\tts\cosyvoice-server\start-cosyvoice-tts.ps1
```

Stop the service:

```powershell
E:\AI\tts\cosyvoice-server\stop-cosyvoice-tts.ps1
```

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:5055/health
```

Generate speech:

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

Or use the included client:

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

The server does not run long warmup by default, so it becomes ready faster.
You can manually warm common sentence lengths:

```powershell
.\warm-cosyvoice-tts.ps1
```

Or start with blocking warmup:

```powershell
.\start-cosyvoice-tts.ps1 -Warmup
```

## Notes

- The model is intentionally protected by a single `model_lock`; concurrent
  requests are serialized because this local CosyVoice path is not proven safe
  for parallel inference on one GPU.
- Non-WAV formats require `ffmpeg` on `PATH`.
- The first request after process start may be slower due to model and CUDA
  lazy initialization.
