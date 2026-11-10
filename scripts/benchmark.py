"""Run the same fixed local experiment as the Hermes Watt Desktop button."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dashboard.plugin_api import WORKLOADS, checked_answers, run_experiment

# Kept for consumers of the original classification checker.
ITEMS = [{**item, 'expected': item['expected']['category']} for item in WORKLOADS['tickets']['items']]


def check_answers(answers, expected=ITEMS):
    return checked_answers(answers, [{**item, 'expected': {'category': item['expected']}} for item in expected])


def run(args):
    root = Path(args.output).resolve()
    root.mkdir(parents=True, exist_ok=True)
    report = run_experiment(root, endpoint=args.endpoint, model=args.model,
                            workload=args.workload, repetitions=args.repetitions,
                            progress=lambda **state: print(json.dumps(state), flush=True))
    pending = root / 'comparison.pending.json'
    pending.write_text(json.dumps(report, indent=2, allow_nan=False), encoding='utf-8')
    pending.replace(root / 'comparison.json')
    print('Result:', report['verdict'], 'Observed reduction:', report['observed_reduction_percent'], flush=True)
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--endpoint', default='http://127.0.0.1:18082/v1')
    p.add_argument('--model', default='Qwen3-1.7B-Q8_0')
    p.add_argument('--output', required=True)
    p.add_argument('--workload', choices=list(WORKLOADS), default='tickets')
    p.add_argument('--repetitions', type=int, choices=range(3, 11), default=5)
    p.add_argument('--consent', action='store_true', required=True, help='Allow synthetic local model calls and system-wide CPU/GPU estimates for this experiment')
    run(p.parse_args())
