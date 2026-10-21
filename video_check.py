#!/usr/bin/env python3
"""Inspect video timestamps; numerical agreement is not visual approval."""
import argparse
import json
from pathlib import Path
import statistics
import subprocess


def probe(path, args, binary):
    return json.loads(subprocess.check_output([binary, '-v', 'error', *args, '-of', 'json', str(path)]))


def inspect(path, binary='ffprobe'):
    path = Path(path).expanduser().resolve(strict=True)
    data = probe(path, ['-show_streams', '-show_format'], binary)
    video = next((s for s in data['streams'] if s['codec_type'] == 'video'), None)
    if video is None:
        raise ValueError('Input has no video stream')
    frames = probe(path, ['-select_streams', 'v:0', '-show_frames', '-show_entries', 'frame=best_effort_timestamp_time'], binary)['frames']
    pts = [float(f['best_effort_timestamp_time']) for f in frames if 'best_effort_timestamp_time' in f]
    if len(pts) != len(frames) or len(pts) < 2:
        raise ValueError('At least two frames with valid timestamps are required')
    delta = [b-a for a, b in zip(pts, pts[1:])]
    med = statistics.median(delta)
    tolerance = max(0.0001, med * .005)
    duration = data.get('format', {}).get('duration')
    return {'path': str(path), 'width': video['width'], 'height': video['height'], 'frames': len(pts), 'pts': pts,
            'median_interval': med, 'constant_rate': med > 0 and all(abs(x-med) <= tolerance for x in delta),
            'strictly_increasing': all(x > 0 for x in delta), 'audio_streams': sum(s['codec_type'] == 'audio' for s in data['streams']),
            'duration': float(duration) if duration is not None else None,
            'rotation': [s['rotation'] for s in video.get('side_data_list', []) if 'rotation' in s]}


def compare(a, b):
    equal = len(a['pts']) == len(b['pts'])
    error = max(abs((x-a['pts'][0])-(y-b['pts'][0])) for x, y in zip(a['pts'], b['pts'])) if equal else None
    return {'same_frame_count': equal, 'same_dimensions': (a['width'], a['height']) == (b['width'], b['height']),
            'max_relative_pts_error_seconds': error,
            'timing_pass': equal and error <= .001 and a['strictly_increasing'] and b['strictly_increasing'],
            'visual_review': 'Not performed. Inspect visual content, contacts, occlusions, flicker and audio separately.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source')
    p.add_argument('--output-video')
    p.add_argument('--report', required=True, type=Path)
    p.add_argument('--ffprobe-bin', default='ffprobe')
    a = p.parse_args()
    report = a.report.expanduser()
    if report.exists():
        p.error('Report already exists; choose a new path')
    try:
        src = inspect(a.source, a.ffprobe_bin)
        result = {'source': src}
        if a.output_video:
            dst = inspect(a.output_video, a.ffprobe_bin)
            result.update(output=dst, checks=compare(src, dst))
        report.parent.mkdir(parents=True, exist_ok=True)
        with report.open('x', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        p.exit(1, str(exc) + '\n')
    print(json.dumps(result.get('checks', {k:v for k,v in src.items() if k != 'pts'}), indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
