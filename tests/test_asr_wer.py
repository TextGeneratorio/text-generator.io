#!/usr/bin/env python3
"""WER benchmark for ASR (Parakeet) inference server."""
import argparse
import json
import os
import re
import subprocess
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
TEST_AUDIO_DIR = os.path.join(PROJECT_DIR, '../voicetype/test_audio')
GROUND_TRUTH_PATH = os.path.join(TEST_AUDIO_DIR, 'ground_truth.json')
RESULTS_PATH = os.path.join(PROJECT_DIR, 'wer_results.json')
SERVER_URL = os.environ.get('ASR_SERVER_URL', 'http://localhost:9080')


def normalize(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s]', '', text)
    return ' '.join(text.split())


def wer(ref, hyp):
    r = normalize(ref).split()
    h = normalize(hyp).split()
    if not r:
        return 0.0 if not h else 1.0
    d = [[0] * (len(h) + 1) for _ in range(len(r) + 1)]
    for i in range(len(r) + 1):
        d[i][0] = i
    for j in range(len(h) + 1):
        d[0][j] = j
    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            sub = 0 if r[i - 1] == h[j - 1] else 1
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + sub)
    return d[len(r)][len(h)] / len(r)


def transcribe_file(audio_path, server_url=None, timeout=30, include_segments=True):
    url = server_url or SERVER_URL
    try:
        r = subprocess.run([
            'curl', '-s', '-X', 'POST', '--max-time', str(timeout),
            f'{url}/api/v1/audio-file-extraction',
            '-F', f'audio_file=@{audio_path}',
            '-F', 'translate_to_english=false',
            '-F', f'include_segments={str(include_segments).lower()}',
        ], capture_output=True, text=True, timeout=timeout + 5)
        data = json.loads(r.stdout)
        return data.get('text', '')
    except Exception as e:
        print(f"  error: {e}", file=sys.stderr)
        return ''


def run_benchmark(audio_dir=None, ground_truth_path=None, server_url=None, include_segments=True):
    audio_dir = audio_dir or TEST_AUDIO_DIR
    gt_path = ground_truth_path or os.path.join(audio_dir, 'ground_truth.json')

    if not os.path.exists(gt_path):
        print(f"ground truth not found: {gt_path}")
        return None

    gt = json.load(open(gt_path))
    results = {}

    for fname, ref_text in sorted(gt.items()):
        if not ref_text:
            continue
        fpath = os.path.join(audio_dir, fname)
        if not os.path.exists(fpath):
            continue

        t0 = time.time()
        hyp = transcribe_file(fpath, server_url=server_url, include_segments=include_segments)
        elapsed = time.time() - t0

        w = wer(ref_text, hyp) if hyp else None
        results[fname] = {
            'ref': ref_text,
            'hyp': hyp,
            'wer': w,
            'time': round(elapsed, 2),
        }
        status = f'WER={w:.3f}' if w is not None else 'FAIL'
        print(f"  {fname}: {status} ({elapsed:.1f}s)")

    succeeded = [r for r in results.values() if r['wer'] is not None]
    if succeeded:
        avg_wer = sum(r['wer'] for r in succeeded) / len(succeeded)
        avg_time = sum(r['time'] for r in succeeded) / len(succeeded)
        print(f"\n  {len(succeeded)}/{len(results)} succeeded, avg WER: {avg_wer:.3f}, avg time: {avg_time:.1f}s")
        results['_summary'] = {
            'avg_wer': round(avg_wer, 4),
            'avg_time': round(avg_time, 2),
            'succeeded': len(succeeded),
            'total': len(results) - 1,
        }

    return results


def main():
    parser = argparse.ArgumentParser(description='ASR WER benchmark')
    parser.add_argument('--audio-dir', help='directory with audio files')
    parser.add_argument('--ground-truth', help='path to ground_truth.json')
    parser.add_argument('--server', default=SERVER_URL, help='ASR server URL')
    parser.add_argument('--save', action='store_true', help='save results to wer_results.json')
    parser.add_argument('--fast', action='store_true', help='benchmark fast mode (skip segment extraction)')
    args = parser.parse_args()

    server = args.server

    print(f"=== ASR WER Benchmark ({server}) ===")
    results = run_benchmark(
        args.audio_dir,
        args.ground_truth,
        server_url=server,
        include_segments=not args.fast,
    )

    if results and args.save:
        entry = {
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'server': SERVER_URL,
            'results': results,
        }
        with open(RESULTS_PATH, 'w') as f:
            json.dump(entry, f, indent=2)
        print(f"  saved to {RESULTS_PATH}")


if __name__ == '__main__':
    main()
