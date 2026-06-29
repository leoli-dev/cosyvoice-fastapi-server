param(
  [string]$Server = "http://127.0.0.1:5055"
)

$ErrorActionPreference = "Stop"

$body = @{
  texts = @(
    "你好。",
    "听得见，测试完全没问题。",
    "你再试一次看看？",
    "今天过得怎么样呀？",
    "可能是网络有点延迟，我这边马上就好。",
    "我们随便聊几句，测试一下反应速度。",
    "请用自然的广东话讲出这一句话，看看延迟是否稳定。"
  )
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri ($Server.TrimEnd("/") + "/warmup") `
  -Method Post `
  -ContentType "application/json; charset=utf-8" `
  -Body $body
