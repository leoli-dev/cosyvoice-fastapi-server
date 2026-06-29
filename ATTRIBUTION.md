# Attribution and Third-Party Notices

This repository contains a small FastAPI wrapper and Windows helper scripts for
running a local CosyVoice TTS service. It does not vendor third-party model
weights, the CosyVoice source tree, Python environments, generated audio, or
cache files.

## CosyVoice

- Project: FunAudioLLM / CosyVoice
- Repository: https://github.com/FunAudioLLM/CosyVoice
- License: Apache License 2.0
- Role in this project: the local TTS engine imported by `homelab_tts_api.py`.

Users must install or clone CosyVoice separately into `CosyVoice/`, or adjust
the paths in the startup scripts.

## Fun-CosyVoice3 model

- Model family: Fun-CosyVoice3 / CosyVoice3
- Hugging Face: https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512
- ModelScope: https://www.modelscope.cn/models/FunAudioLLM/Fun-CosyVoice3-0.5B-2512
- Model card license field observed locally: `apache-2.0`
- Role in this project: default model directory expected by the server.

Users must download model weights separately into `models/Fun-CosyVoice3-0.5B`
or pass another `--model_dir`.

## Other runtime dependencies

This service also relies on Python packages and tools commonly used by
CosyVoice, such as:

- FastAPI / Uvicorn for the HTTP API.
- PyTorch for model execution.
- librosa and soundfile for audio loading/encoding.
- WeTextProcessing / wetext when CosyVoice falls back to that text frontend.
- FFmpeg for non-WAV output formats such as mp3, flac, ogg, and m4a.

Each dependency remains governed by its own license. Check the installed package
metadata and upstream repositories before redistribution or commercial use.

## This wrapper

Files written for this wrapper, including `homelab_tts_api.py`, PowerShell
scripts, and documentation in this repository, are licensed under the MIT
License in `LICENSE`.

