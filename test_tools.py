"""Integration checks using generated media only. Requires ffmpeg/ffprobe."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import analyze
import video_check

ROOT = Path(__file__).resolve().parent


class ToolsTest(unittest.TestCase):
    def test_timing_and_protection(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            clip = d / 'sample.mp4'
            subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=red:s=160x120:r=25:d=1', '-c:v', 'mpeg4', str(clip)], check=True)
            report = d / 'report.json'
            cmd = [sys.executable, str(ROOT / 'video_check.py'), str(clip), '--output-video', str(clip), '--report', str(report)]
            subprocess.run(cmd, check=True, capture_output=True)
            result = json.loads(report.read_text())
            self.assertEqual(result['source']['frames'], 25)
            self.assertTrue(result['checks']['timing_pass'])
            before = report.read_bytes()
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            self.assertEqual(before, report.read_bytes())
            shorter = d / 'short.mp4'
            subprocess.run(['ffmpeg', '-v', 'error', '-i', str(clip), '-t', '0.5', '-c:v', 'mpeg4', str(shorter)], check=True)
            cmd[cmd.index('--output-video')+1] = str(shorter)
            cmd[-1] = str(d / 'different.json')
            subprocess.run(cmd, check=True, capture_output=True)
            self.assertFalse(json.loads((d/'different.json').read_text())['checks']['timing_pass'])

    def test_strict_exit_codes_and_dimensions(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            for name, size in [('a', '160x120'), ('b', '320x240')]:
                subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i',
                                'color=red:s=' + size + ':r=25:d=1', '-c:v', 'mpeg4', str(d/(name+'.mp4'))], check=True)
            base = [sys.executable, str(ROOT/'video_check.py'), str(d/'a.mp4'), '--output-video']
            for label, target, strict, expected in [('equal', 'a', True, 0), ('changed', 'b', True, 3), ('legacy', 'b', False, 0)]:
                report = d/(label+'.json')
                cmd = base + [str(d/(target+'.mp4')), '--report', str(report)] + (['--strict'] if strict else [])
                self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, expected)
                data = json.loads(report.read_text())
                self.assertTrue(data['checks']['timing_pass'])
                self.assertEqual(data['checks']['same_dimensions'], target == 'a')
            result = subprocess.run([sys.executable, str(ROOT/'video_check.py'), str(d/'a.mp4'), '--strict', '--report', str(d/'invalid.json')], capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertFalse((d/'invalid.json').exists())

    def test_corrupt_media_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            bad = d/'bad.mp4'
            bad.write_text('not a video')
            r = subprocess.run([sys.executable, str(ROOT/'video_check.py'), str(bad), '--report', str(d/'report.json')], capture_output=True, text=True)
            self.assertEqual(r.returncode, 1)
            self.assertIn('ffprobe could not read', r.stderr)
            self.assertNotIn('Traceback', r.stderr)
            self.assertFalse((d/'report.json').exists())

    def test_missing_probe_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp)/'input.mp4'
            source.touch()
            with self.assertRaisesRegex(ValueError, 'ffprobe was not found'):
                video_check.inspect(source, str(Path(tmp)/'missing-ffprobe'))

    def test_missing_or_nonfinite_timestamps(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp)/'input.mp4'
            source.touch()
            metadata = {'streams': [{'codec_type': 'video', 'width': 10, 'height': 10}]}
            for frames in [{}, {'frames': [{}, {}]}, {'frames': [{'best_effort_timestamp_time': '0'}, {'best_effort_timestamp_time': 'nan'}]}]:
                with patch('video_check.probe', side_effect=[metadata, frames]):
                    with self.assertRaises(ValueError):
                        video_check.inspect(source)

    def test_failed_analysis_keeps_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            source = d/'input.mp4'
            source.touch()
            out = d/'output'
            def failed_tool(command, **kwargs):
                kwargs['stdout'].write('decoder failed\n')
                return subprocess.CompletedProcess(command, 7)
            argv = ['analyze.py', 'scenes', str(source), str(out)]
            with patch.object(sys, 'argv', argv), patch('analyze.shutil.which', return_value='scenedetect'), patch('analyze.subprocess.run', side_effect=failed_tool):
                self.assertEqual(analyze.main(), 7)
            manifest = json.loads((out/'execution.json').read_text())
            self.assertEqual(manifest['status'], 'failed')
            self.assertEqual(manifest['returncode'], 7)
            self.assertIn('finished_at', manifest)
            self.assertEqual((out/'tool.log').read_text(), 'decoder failed\n')
            before = (out/'execution.json').read_bytes()
            with patch.object(sys, 'argv', argv), self.assertRaises(SystemExit):
                analyze.main()
            self.assertEqual((out/'execution.json').read_bytes(), before)

    def test_invalid_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'result'
            r = subprocess.run([sys.executable, str(ROOT/'analyze.py'), 'scenes', str(Path(tmp)/'missing.mp4'), str(output)], capture_output=True)
            self.assertNotEqual(r.returncode, 0)
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
