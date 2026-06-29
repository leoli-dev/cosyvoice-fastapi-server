from __future__ import annotations

import argparse
import io
import logging
import os
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Literal

import librosa
import numpy as np
import soundfile as sf
import torch
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field


ROOT_DIR = Path(__file__).resolve().parent
COSYVOICE_DIR = ROOT_DIR / "CosyVoice"
sys.path.insert(0, str(COSYVOICE_DIR))
sys.path.insert(0, str(COSYVOICE_DIR / "third_party" / "Matcha-TTS"))

from cosyvoice.cli.cosyvoice import AutoModel  # noqa: E402
import cosyvoice.cli.frontend as cosyvoice_frontend  # noqa: E402
from cosyvoice.utils.common import set_all_random_seed  # noqa: E402


DEFAULT_PROMPT_WAV = os.environ.get(
    "COSYVOICE_DEFAULT_PROMPT_WAV",
    str(COSYVOICE_DIR / "asset" / "zero_shot_prompt.wav"),
)
DEFAULT_PROMPT_TEXT = os.environ.get(
    "COSYVOICE_DEFAULT_PROMPT_TEXT",
    "You are a helpful assistant.<|endofprompt|>希望你以后能够做的比我还好呦。",
)
DEFAULT_INSTRUCT = "请用广东话表达，语气清晰、自然。"

app = FastAPI(title="Homelab CosyVoice TTS API", version="1.0")
model_lock = threading.Lock()
cosyvoice = None
model_dir = None
request_count = 0


class SpeechRequest(BaseModel):
    input: str = Field(..., description="Text to synthesize")
    voice: str | None = Field(default=None, description="Reserved for OpenAI-compatible clients")
    response_format: Literal["wav", "mp3", "flac", "ogg", "m4a"] = "wav"
    speed: float = 1.0
    seed: int = 0
    mode: Literal["自然语言控制", "3s极速复刻", "跨语种复刻"] = "自然语言控制"
    instruct: str = DEFAULT_INSTRUCT
    prompt_wav: str | None = None
    prompt_text: str = ""


def ensure_endofprompt(text: str | None) -> str:
    text = (text or "").strip()
    if "<|endofprompt|>" in text:
        return text
    if not text.lower().startswith("you are a helpful assistant."):
        text = "You are a helpful assistant. " + text
    return text + "<|endofprompt|>"


def compatible_load_wav(wav, target_sr, min_sr=16000):
    if isinstance(wav, torch.Tensor):
        return wav
    audio, sample_rate = sf.read(str(wav), dtype="float32", always_2d=True)
    audio = audio.mean(axis=1)
    if sample_rate != target_sr:
        if sample_rate < min_sr:
            raise ValueError(f"wav sample rate {sample_rate} must be greater than {min_sr}")
        audio = librosa.resample(audio, orig_sr=sample_rate, target_sr=target_sr)
    return torch.from_numpy(audio).unsqueeze(0)


def audio_to_bytes(audio: np.ndarray, sample_rate: int, response_format: str) -> bytes:
    audio = np.asarray(audio, dtype=np.float32)
    if response_format == "wav":
        buffer = io.BytesIO()
        sf.write(buffer, audio, sample_rate, format="WAV", subtype="PCM_16")
        return buffer.getvalue()

    wav_path = None
    out_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as wav_file:
            wav_path = wav_file.name
        with tempfile.NamedTemporaryFile(suffix=f".{response_format}", delete=False) as out_file:
            out_path = out_file.name
        sf.write(wav_path, audio, sample_rate, format="WAV", subtype="PCM_16")
        subprocess.run(
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", wav_path, out_path],
            check=True,
        )
        return Path(out_path).read_bytes()
    finally:
        for path in (wav_path, out_path):
            if path:
                try:
                    os.remove(path)
                except OSError:
                    pass


def synthesize(req: SpeechRequest) -> tuple[bytes, float, float]:
    if not req.input.strip():
        raise HTTPException(status_code=400, detail="input is empty")

    prompt_wav = req.prompt_wav
    prompt_text = req.prompt_text
    instruct = req.instruct or DEFAULT_INSTRUCT
    is_cosyvoice3 = cosyvoice.__class__.__name__ == "CosyVoice3"

    if is_cosyvoice3 and req.mode == "自然语言控制" and not prompt_wav:
        prompt_wav = DEFAULT_PROMPT_WAV
    if is_cosyvoice3 and req.mode == "3s极速复刻" and not prompt_wav:
        prompt_wav = DEFAULT_PROMPT_WAV
    if is_cosyvoice3 and req.mode == "3s极速复刻" and not prompt_text:
        prompt_text = DEFAULT_PROMPT_TEXT

    if prompt_wav and not Path(prompt_wav).exists():
        raise HTTPException(status_code=400, detail=f"prompt_wav not found: {prompt_wav}")

    set_all_random_seed(req.seed)
    chunks: list[np.ndarray] = []
    start = time.perf_counter()

    with model_lock:
        if req.mode == "自然语言控制":
            if is_cosyvoice3:
                instruct = ensure_endofprompt(instruct)
                iterator = cosyvoice.inference_instruct2(req.input, instruct, prompt_wav, stream=False, speed=req.speed)
            else:
                iterator = cosyvoice.inference_instruct(req.input, "", instruct, stream=False, speed=req.speed)
        elif req.mode == "3s极速复刻":
            if is_cosyvoice3:
                prompt_text = ensure_endofprompt(prompt_text)
            iterator = cosyvoice.inference_zero_shot(req.input, prompt_text, prompt_wav, stream=False, speed=req.speed)
        else:
            tts_text = ensure_endofprompt(req.input) if is_cosyvoice3 else req.input
            iterator = cosyvoice.inference_cross_lingual(tts_text, prompt_wav, stream=False, speed=req.speed)

        for item in iterator:
            chunks.append(item["tts_speech"].detach().cpu().numpy().flatten())

    if not chunks:
        raise HTTPException(status_code=500, detail="model returned no audio")

    audio = np.concatenate(chunks)
    duration = len(audio) / float(cosyvoice.sample_rate)
    elapsed = time.perf_counter() - start
    return audio_to_bytes(audio, cosyvoice.sample_rate, req.response_format), duration, elapsed


@app.get("/health")
def health():
    return {
        "ok": True,
        "model": str(model_dir),
        "model_type": cosyvoice.__class__.__name__ if cosyvoice else None,
        "sample_rate": cosyvoice.sample_rate if cosyvoice else None,
        "cuda": torch.cuda.is_available(),
        "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
    }


@app.post("/v1/audio/speech")
def speech(req: SpeechRequest):
    global request_count
    request_count += 1
    try:
        data, duration, elapsed = synthesize(req)
    except HTTPException:
        raise
    except Exception as exc:
        logging.exception("TTS request failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    rtf = elapsed / duration if duration else 0.0
    media_type = {
        "wav": "audio/wav",
        "mp3": "audio/mpeg",
        "flac": "audio/flac",
        "ogg": "audio/ogg",
        "m4a": "audio/mp4",
    }[req.response_format]
    return Response(
        content=data,
        media_type=media_type,
        headers={
            "X-Audio-Duration": f"{duration:.3f}",
            "X-TTS-Elapsed": f"{elapsed:.3f}",
            "X-TTS-RTF": f"{rtf:.3f}",
            "X-TTS-Request-Count": str(request_count),
        },
    )


@app.post("/tts")
def tts(req: SpeechRequest):
    return speech(req)


@app.post("/warmup")
def warmup_endpoint(req: dict | None = None):
    texts = None
    if isinstance(req, dict):
        texts = req.get("texts")
    return {"ok": True, "results": warmup(texts)}


def warmup(texts: list[str] | None = None) -> list[dict[str, float | int | str | bool]]:
    warmup_texts = texts or ["预热。"]
    results: list[dict[str, float | int | str | bool]] = []
    for text in warmup_texts:
        try:
            start = time.perf_counter()
            req = SpeechRequest(input=text, response_format="wav")
            _, duration, elapsed = synthesize(req)
            wall = time.perf_counter() - start
            results.append({"ok": True, "text_len": len(text), "audio_duration": duration, "elapsed": elapsed, "wall": wall})
            print(
                f"Warmup ok: text_len={len(text)} audio={duration:.2f}s elapsed={elapsed:.2f}s wall={wall:.2f}s",
                flush=True,
            )
        except Exception as exc:
            results.append({"ok": False, "text_len": len(text), "error": str(exc)})
            print(f"warmup failed: {exc}", flush=True)
    return results


def main() -> None:
    global cosyvoice, model_dir

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5055)
    parser.add_argument("--model_dir", default=str(ROOT_DIR / "models" / "Fun-CosyVoice3-0.5B"))
    parser.add_argument("--fp16", action="store_true")
    parser.add_argument("--warmup", action="store_true")
    parser.add_argument("--access-log", action="store_true")
    args = parser.parse_args()

    cosyvoice_frontend.load_wav = compatible_load_wav
    model_dir = Path(args.model_dir)
    cosyvoice = AutoModel(model_dir=str(model_dir), fp16=args.fp16)
    print(f"Loaded {cosyvoice.__class__.__name__} from {model_dir}", flush=True)
    print(f"FP16: {args.fp16}", flush=True)
    print(f"CUDA: {torch.cuda.is_available()} {torch.cuda.get_device_name(0) if torch.cuda.is_available() else ''}", flush=True)

    if args.warmup:
        warmup()

    import uvicorn

    uvicorn.run(app, host=args.host, port=args.port, log_level="info", access_log=args.access_log)


if __name__ == "__main__":
    main()
