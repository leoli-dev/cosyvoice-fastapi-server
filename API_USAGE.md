# API Usage

This project is intended to run on Windows through PowerShell.

Replace `<INSTALL_ROOT>` with the folder where you cloned this repository:

```text
<INSTALL_ROOT>\cosyvoice-fastapi-server
```

## Start

```powershell
cd <INSTALL_ROOT>\cosyvoice-fastapi-server
.\start-cosyvoice-tts.ps1
```

Default URLs:

```text
http://127.0.0.1:5055
http://<server-lan-ip>:5055
```

## Health

```powershell
Invoke-RestMethod http://127.0.0.1:5055/health
```

## Generate WAV

```powershell
$body = @{
  input = "你好，呢个係纯 API。"
  response_format = "wav"
  instruct = "请用广东话表达，语气清晰、自然。"
} | ConvertTo-Json

Invoke-WebRequest `
  -Uri "http://127.0.0.1:5055/v1/audio/speech" `
  -Method Post `
  -ContentType "application/json; charset=utf-8" `
  -Body $body `
  -OutFile ".\outputs\api.wav"
```

## Client Script

```powershell
.\api-call-example.ps1 `
  -Text "你好，呢段声音係经由内网 API 生成。" `
  -Out ".\outputs\demo.wav"
```

To call a server on another LAN machine:

```powershell
.\api-call-example.ps1 `
  -Server "http://<server-lan-ip>:5055" `
  -Text "你好，这是内网调用。" `
  -Out ".\outputs\lan-demo.wav"
```

## Request Fields

- `input`: text to synthesize.
- `response_format`: `wav`, `mp3`, `flac`, `ogg`, or `m4a`.
- `mode`: `自然语言控制`, `3s极速复刻`, or `跨语种复刻`.
- `instruct`: natural-language voice instruction.
- `prompt_wav`: server-local reference audio path for custom voice cloning.
- `prompt_text`: transcript for `3s极速复刻`.
- `seed`: random seed.
- `speed`: speech speed.

## Warmup

Manual warmup:

```powershell
.\warm-cosyvoice-tts.ps1
```

Custom warmup request:

```powershell
$body = @{
  texts = @(
    "你好，这是短句预热。",
    "今日天气不错，我们测试一下语音服务器反应速度。"
  )
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "http://127.0.0.1:5055/warmup" `
  -Method Post `
  -ContentType "application/json; charset=utf-8" `
  -Body $body
```

## Headers

```text
X-Audio-Duration
X-TTS-Elapsed
X-TTS-RTF
X-TTS-Request-Count
```
