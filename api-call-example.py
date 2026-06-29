from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Call the local CosyVoice API and save an audio file.")
    parser.add_argument("--server", default="http://127.0.0.1:5055", help="CosyVoice API base URL")
    parser.add_argument("--text", required=True, help="Text to synthesize")
    parser.add_argument("--out", default="outputs/api-output.wav", help="Output audio path")
    parser.add_argument("--mode", default="自然语言控制", choices=["自然语言控制", "3s极速复刻", "跨语种复刻"], help="Inference mode")
    parser.add_argument("--instruct", default="请用广东话表达，语气清晰、自然。", help="Natural-language voice instruction")
    parser.add_argument("--prompt-wav", default=None, help="Server-local reference voice WAV/MP3 path")
    parser.add_argument("--prompt-text", default="", help="Transcript of prompt-wav; required for 3s极速复刻")
    parser.add_argument("--seed", type=int, default=0, help="Inference seed")
    parser.add_argument("--speed", type=float, default=1.0, help="Speech speed, usually 0.5-2.0")
    args = parser.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    response_format = out_path.suffix.lower().lstrip(".") or "wav"

    payload = {
        "input": args.text,
        "response_format": response_format,
        "mode": args.mode,
        "instruct": args.instruct,
        "prompt_wav": args.prompt_wav,
        "prompt_text": args.prompt_text,
        "seed": args.seed,
        "speed": args.speed,
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        args.server.rstrip("/") + "/v1/audio/speech",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=300) as response:
        out_path.write_bytes(response.read())
        print(str(out_path))
        print("duration", response.headers.get("X-Audio-Duration"))
        print("elapsed", response.headers.get("X-TTS-Elapsed"))
        print("rtf", response.headers.get("X-TTS-RTF"))


if __name__ == "__main__":
    main()
