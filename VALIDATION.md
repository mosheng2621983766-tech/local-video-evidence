# Validation — 0.1.0

Validated on 2026-10-21 on an Apple Silicon Mac. The wrapper scripts ran with Python 3.9; installed PySceneDetect 0.7.2 ran in its own Python 3.12 environment. FFmpeg 6.0 was available. No private source media was used.

| Check | Result |
|---|---|
| Generated 4-second, 25 fps red/blue video | 100 frames; cut at 2 seconds |
| Scene detection and representative frames | 2 scenes, 6 JPEG images, scene CSV, completed execution record |
| Local MLX Whisper using an existing whisper-small-mlx model | Completed; TXT, subtitle and JSON outputs produced |
| Synthetic spoken sentence | “This is a local video analysis test. The second scene starts after two seconds.” transcribed with “2” instead of “two” |
| One second of generated silence | Completed smoke test; not an accuracy benchmark |
| Compare a generated clip to itself | Timing passed, 25 frames |
| Compare against a shorter generated clip | Timing failed as expected |
| Attempt to overwrite a report | Refused; original report unchanged |
| Missing input | Refused before creating an output directory |

Run `python -m unittest -v test_tools` for the automated timestamp and input/protection checks. Scene and speech checks above were separate end-to-end runs. This is a limited functional validation, not a general speech accuracy or scene detection benchmark. Windows/Linux, long videos, unusual codecs and all languages have not been validated. Model files and dependencies must be installed separately.
