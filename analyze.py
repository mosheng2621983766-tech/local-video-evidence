#!/usr/bin/env python3
"""Local scene detection and offline speech transcription. Python 3.9+."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['scenes', 'speech'])
    p.add_argument('input', type=Path)
    p.add_argument('output', type=Path, help='New output directory; never overwritten')
    p.add_argument('--language', default='zh', help='Speech language, or auto')
    p.add_argument('--model-dir', type=Path, help='Existing local MLX Whisper model directory')
    p.add_argument('--min-scene-len', default='0.2s')
    p.add_argument('--scenedetect-bin', default='scenedetect')
    p.add_argument('--whisper-bin', default='mlx_whisper')
    a = p.parse_args()
    source = a.input.expanduser().resolve()
    out = a.output.expanduser().resolve()
    if not source.is_file():
        p.error('Input must be an existing local file')
    if out.exists():
        p.error('Output already exists; choose a new directory')
    binary = a.scenedetect_bin if a.mode == 'scenes' else a.whisper_bin
    executable = shutil.which(binary)
    if not executable:
        p.error('Executable not found: ' + binary)
    env = dict(os.environ)
    if a.mode == 'scenes':
        cmd = [executable, '-i', str(source), '-o', str(out), '-d', '1', '-fs', '0', '-m', a.min_scene_len,
               'detect-adaptive', 'list-scenes', 'save-images']
    else:
        if a.model_dir is None:
            p.error('Speech requires --model-dir; models are never downloaded automatically')
        model = a.model_dir.expanduser().resolve()
        if not (model / 'config.json').is_file() or not any((model / f).is_file() for f in ('weights.npz', 'weights.safetensors')):
            p.error('Model directory must contain config.json and MLX Whisper weights')
        env.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', HF_HUB_DISABLE_TELEMETRY='1')
        cmd = [executable, str(source), '--model', str(model), '--output-dir', str(out), '--output-format', 'all',
               '--word-timestamps', 'True', '--task', 'transcribe', '--condition-on-previous-text', 'False', '--verbose', 'False']
        if a.language != 'auto':
            cmd += ['--language', a.language]
    out.mkdir(parents=True, exist_ok=False)
    manifest = {'input': str(source), 'mode': a.mode, 'command': cmd, 'status': 'running', 'speech_offline': a.mode == 'speech'}
    record = out / 'execution.json'
    def save():
        record.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    save()
    try:
        r = subprocess.run(cmd, env=env, check=False)
        manifest.update(status='complete' if r.returncode == 0 else 'failed', returncode=r.returncode)
    except (OSError, KeyboardInterrupt) as exc:
        manifest.update(status='failed', error=str(exc), returncode=130 if isinstance(exc, KeyboardInterrupt) else 1)
    save()
    return manifest['returncode']


if __name__ == '__main__':
    raise SystemExit(main())
