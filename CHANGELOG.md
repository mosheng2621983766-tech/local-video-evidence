# Changelog

## 0.2.0 — 2026-10-22

- Add opt-in `--strict` comparison with exit code 3 on timing or dimension mismatch, preserving default behavior.
- Report missing ffprobe and corrupt media with actionable errors; reject missing and non-finite timestamps.
- Save external tool output to `tool.log` and record execution start/end timestamps, including failed runs.
- Expand regression coverage to seven tests and rerun local scene/speech smoke checks.

## 0.1.0 — 2026-10-21

First public version, adapted from a personal video workflow with Codex assistance.

- Configurable tool and model paths instead of machine-specific locations.
- Scene detection with representative frames and CSV output.
- Offline MLX Whisper transcription with an explicitly supplied local model.
- Video timestamp inspection and source/output comparison.
- Non-overwriting outputs and execution records.
- MIT license, setup instructions, synthetic example and validation notes.
