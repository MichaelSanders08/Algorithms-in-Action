"""Interactive terminal front end and stable JSON for scripts."""
import argparse
import json
from pathlib import Path
import random
import sys
from time import perf_counter_ns
from .core import ALGORITHMS, run


def parse_values(text):
    try:
        values = json.loads(text) if text.strip().startswith('[') else [float(v) for v in text.replace(',', ' ').split()]
    except (ValueError, TypeError) as error:
        raise ValueError('Enter numbers separated by spaces/commas, or a JSON array.') from error
    if not isinstance(values, list):
        raise ValueError('Values must be an array.')
    return values


def display(result, as_json=False, trace=False):
    if as_json:
        print(json.dumps(result.to_dict(), indent=2, allow_nan=False))
        return
    meta = ALGORITHMS[result.algorithm]
    print(f"\n{result.algorithm.upper()}  ·  {meta['time']}\n{meta['idea']}")
    if trace:
        for step in result.steps:
            state = {k: v for k, v in step.items() if k not in ('step', 'explanation')}
            print(f"  {step['step']:>3}. {step['explanation']} {json.dumps(state)}")
        if result.trace_truncated:
            print('  … Trace limit reached; the computation still completed.')
    print('Result:', json.dumps(result.output, ensure_ascii=False, allow_nan=False))
    if meta['kind'] == 'search':
        print('Indexes are zero-based; -1 means the target was not found.')
    print('Work:', ', '.join(f'{key}={value}' for key, value in result.metrics.items()))


def menu():
    names = list(ALGORITHMS)
    while True:
        print('\nALGORITHMS IN ACTION\nUnderstand the mechanism. Then use the tool.\n')
        for index, name in enumerate(names, 1):
            print(f"  {index}. {name:18} {ALGORITHMS[name]['idea']}")
        choice = input('\nChoose 1–6, or q to quit: ').strip()
        if choice.lower() in {'q', 'quit', 'exit'}:
            return 0
        try:
            if choice not in {str(i) for i in range(1, 7)}:
                raise ValueError('Choose a number from 1 to 6.')
            name = names[int(choice) - 1]
            kind = ALGORITHMS[name]['kind']
            if kind == 'graph':
                sample = {'studio': {'library': 2, 'cinema': 5}, 'library': {'cinema': 1}, 'cinema': {}, 'island': {}} if name == 'dijkstra' else {'studio': ['library', 'cinema'], 'library': ['park'], 'cinema': ['park'], 'park': []}
                print('Example graph:', json.dumps(sample))
                raw = input('Graph JSON (Enter for example): ').strip()
                graph = json.loads(raw) if raw else sample
                start = input('Start node [studio]: ').strip() or 'studio'
                end = input('Destination (optional): ').strip() or None
                result = run(name, graph=graph, start=start, end=end)
            else:
                default = '2, 4, 7, 7, 11, 19' if kind == 'search' else '19, 4, 7, 2, 11, 7'
                values = parse_values(input(f'Numbers [{default}]: ').strip() or default)
                target = float(input('Target [7]: ').strip() or '7') if kind == 'search' else None
                result = run(name, values, target=target)
            display(result, trace=True)
        except (ValueError, TypeError) as error:
            print(f'Input error: {error}')


def main(argv=None):
    parser = argparse.ArgumentParser(description='Run, trace, and compare algorithms. No dependencies or accounts.')
    sub = parser.add_subparsers(dest='command')
    sub.add_parser('list', help='Show algorithms and complexity')
    command = sub.add_parser('run', help='Run on your own data')
    command.add_argument('algorithm', choices=list(ALGORITHMS))
    command.add_argument('--values', help='Numbers, such as "8,3,5" or "[8,3,5]"')
    command.add_argument('--target', type=float)
    command.add_argument('--graph', type=Path, help='Adjacency JSON file')
    command.add_argument('--start')
    command.add_argument('--end')
    command.add_argument('--trace', action='store_true')
    command.add_argument('--trace-limit', type=int, default=200)
    command.add_argument('--json', action='store_true')
    benchmark = sub.add_parser('compare', help='Compare sorts on identical deterministic input')
    benchmark.add_argument('--size', type=int, default=100)
    benchmark.add_argument('--seed', type=int, default=8)
    benchmark.add_argument('--order', choices=['random', 'sorted', 'reversed'], default='random')
    benchmark.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.command is None:
            return menu()
        if args.command == 'list':
            for name, meta in ALGORITHMS.items():
                print(f"{name:18} {meta['time']:24} {meta['idea']}")
            print('\nComplexity excludes validation and trace storage. Binary search validates order in O(n).')
        elif args.command == 'run':
            graph = json.loads(args.graph.read_text()) if args.graph else None
            values = parse_values(args.values) if args.values is not None else None
            result = run(args.algorithm, values, target=args.target, graph=graph, start=args.start, end=args.end, trace_limit=args.trace_limit if args.trace else 0)
            display(result, args.json, args.trace)
        else:
            if not 0 <= args.size <= 5000:
                raise ValueError('Comparison size must be between 0 and 5000.')
            rng = random.Random(args.seed)
            values = [rng.randrange(max(1, args.size * 10)) for _ in range(args.size)]
            if args.order != 'random':
                values.sort(reverse=args.order == 'reversed')
            rows = []
            for name in ('insertion-sort', 'merge-sort'):
                start = perf_counter_ns()
                result = run(name, values, trace_limit=0)
                elapsed = (perf_counter_ns() - start) / 1_000_000
                rows.append({'algorithm': name, 'size': args.size, 'seed': args.seed, 'order': args.order, **result.metrics, 'milliseconds': round(elapsed, 3), 'correct': result.output == sorted(values)})
            if args.json:
                print(json.dumps(rows, indent=2))
            else:
                print('Same input, different mechanisms. Timing is illustrative, not a rigorous benchmark.\n')
                for row in rows:
                    print(f"{row['algorithm']:18} comparisons={row['comparisons']:<8} writes={row['writes']:<8} {row['milliseconds']:.3f} ms")
        return 0
    except (ValueError, TypeError, OSError, OverflowError) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 2
    except (KeyboardInterrupt, EOFError):
        print('\nGoodbye.')
        return 0

if __name__ == '__main__':
    raise SystemExit(main())
