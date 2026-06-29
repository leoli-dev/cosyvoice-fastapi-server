# CosyVoice TTS API 调用说明

当前服务已经切换成纯 FastAPI，唔再用 Gradio WebUI。

- 本机：`http://127.0.0.1:5055`
- 内网：`http://10.44.44.33:5055`
- Endpoint：`POST /v1/audio/speech`

## PowerShell 调用

```powershell
E:\AI\tts\cosyvoice-server\api-call-example.ps1 `
  -Text "你好，呢段声音係经由内网 API 生成。" `
  -Out "E:\AI\tts\cosyvoice-server\outputs\demo.wav"
```

输出 MP3：

```powershell
E:\AI\tts\cosyvoice-server\api-call-example.ps1 `
  -Text "你好，呢段声音会输出成 MP3。" `
  -Out "E:\AI\tts\cosyvoice-server\outputs\demo.mp3"
```

## HTTP JSON 调用

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
  -OutFile "E:\AI\tts\cosyvoice-server\outputs\api.wav"
```

返回 headers 会包含：

```text
X-Audio-Duration
X-TTS-Elapsed
X-TTS-RTF
```

## 请求字段

- `input`：要合成嘅文字
- `response_format`：`wav`、`mp3`、`flac`、`ogg`、`m4a`
- `mode`：默认 `自然语言控制`
- `instruct`：例如 `请用广东话表达，语气清晰、自然。`
- `prompt_wav`：服务器本地参考音频路径，可用于换音色
- `prompt_text`：`3s极速复刻` 模式下嘅参考音频文本
- `seed`：随机种子
- `speed`：语速

## 预热接口

服务默认不做长预热，避免 Start 之后等太久。你可以按应用里常见句子手动预热：

```powershell
$body = @{
  texts = @(
    "你好，这是短句预热。",
    "今日天气不错，我们测试一下语音服务器反应速度。",
    "请用自然的广东话讲出这一句话，看看延迟是否稳定。"
  )
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "http://127.0.0.1:5055/warmup" `
  -Method Post `
  -ContentType "application/json; charset=utf-8" `
  -Body $body
```

或者直接用脚本：

```powershell
E:\AI\tts\cosyvoice-server\warm-cosyvoice-tts.ps1
```

如果你想启动时阻塞预热：

```powershell
E:\AI\tts\cosyvoice-server\start-cosyvoice-tts.ps1 -Warmup
```

`-Fp16` 仍然保留，但这台 RTX 5070 + Windows 路径实测反而更慢，所以默认不用：

```powershell
E:\AI\tts\cosyvoice-server\start-cosyvoice-tts.ps1 -Fp16
```

## 已验证

```text
E:\AI\tts\cosyvoice-server\outputs\fastapi-test.wav
E:\AI\tts\cosyvoice-server\outputs\fastapi-test.mp3
```

当前优化后，默认自然语言控制模式在预热覆盖的常见句长上比较稳定：

```text
2.72 秒音频：约 3.4-3.6 秒
5.40 秒音频：约 6.1-6.6 秒
5.52 秒音频：约 6.1-6.3 秒
```

响应 headers 包含：

```text
X-Audio-Duration
X-TTS-Elapsed
X-TTS-RTF
X-TTS-Request-Count
```
