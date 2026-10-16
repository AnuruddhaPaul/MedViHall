"""
Driver: runs Stage 3 (stage3_layer2_judge.py) one model at a time for every
model not yet in medvihall_outputs/stage3_metrics_by_model.json, saving that
model's SMHR/CHR summary (via compute_model_metrics.py) before moving to the
next model. Each stage3_layer2_judge.py invocation is itself resume-safe, so
this driver is safe to re-run after any interruption -- it just re-enters
wherever it left off (mid-model or at the next model boundary).
"""
import json
import subprocess
import sys
from pathlib import Path

ALL_MODELS = [
    'llava_med', 'qwen3vl', 'qwen25vl', 'gemma3', 'idefics3', 'qwen2vl',
    'qwen35', 'llava16', 'huatuogpt', 'chexagent', 'internvl3', 'minicpm',
]
SUMMARY_FILE = Path('medvihall_outputs/stage3_metrics_by_model.json')
PYTHON = sys.executable


def already_scored():
    if not SUMMARY_FILE.exists():
        return set()
    return set(json.loads(SUMMARY_FILE.read_text(encoding='utf-8')).keys())


def main():
    done = already_scored()
    todo = [m for m in ALL_MODELS if m not in done]
    print(f'Models already scored: {sorted(done)}')
    print(f'Models remaining: {todo}')

    for model in todo:
        print(f'\n{"="*70}\n[driver] Starting Stage 3 for model={model}\n{"="*70}')
        r = subprocess.run([PYTHON, 'stage3_layer2_judge.py', '--model', model])
        if r.returncode != 0:
            print(f'[driver] stage3_layer2_judge.py exited with code {r.returncode} for {model} -- stopping driver.')
            sys.exit(r.returncode)

        print(f'[driver] Judging complete for {model}. Computing + saving metrics ...')
        r = subprocess.run([PYTHON, 'compute_model_metrics.py', model])
        if r.returncode != 0:
            print(f'[driver] compute_model_metrics.py exited with code {r.returncode} for {model} -- stopping driver.')
            sys.exit(r.returncode)

    print('\n[driver] All models scored. Stage 3 fully complete.')


if __name__ == '__main__':
    main()
