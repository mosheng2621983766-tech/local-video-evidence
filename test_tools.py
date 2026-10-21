"""Integration checks using generated media only. Requires ffmpeg/ffprobe."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

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

    def test_invalid_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'result'
            r = subprocess.run([sys.executable, str(ROOT/'analyze.py'), 'scenes', str(Path(tmp)/'missing.mp4'), str(output)], capture_output=True)
            self.assertNotEqual(r.returncode, 0)
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
