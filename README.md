# Algorithms in Action

**Understand the mechanism. Then use the tool.**

A small workbench for curious people: supply your data, follow each decision, and compare how much work two approaches do. Six algorithms, an interactive terminal menu, scriptable JSON, and no runtime dependencies.

## Start here

Python 3.10 or newer. From this directory:

```sh
python -m algorithms_in_action
```

Press Enter for examples, enter your own numbers or graph, and read the trace. `q` exits. To install a command available outside this directory:

```sh
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install .
algorithms list
```

## Three-minute demo

```sh
# First 7 is index 2; watch the interval shrink.
python -m algorithms_in_action run binary-search --values '2,4,7,7,11,19' --target 7 --trace
# A sorted prefix emerges from a mixed list.
python -m algorithms_in_action run insertion-sort --values '19,4,7,2,11,7' --trace
# The direct route is not always the cheapest route.
python -m algorithms_in_action run dijkstra --graph examples/routes.json --start studio --end park --trace
# Same input, different work. Try --order sorted next.
python -m algorithms_in_action compare --size 500 --seed 8
```

Use `--json` with `run` or `compare` for machine-readable output. Add `--trace` to include steps in JSON. `--trace-limit 50` bounds detail without stopping the calculation.

## Mechanisms and assumptions

| Algorithm | Demonstrates | Core time | Working space, excluding trace |
| --- | --- | --- | --- |
| Linear search | Inspect in order; return first match | O(n) | O(n) input copy |
| Binary search | Eliminate half of a sorted interval | O(log n) | O(n) input copy |
| Insertion sort | Grow a sorted prefix | O(n²), best O(n) | O(n) input copy |
| Merge sort | Divide, then merge sorted runs | O(n log n) | O(n) |
| Breadth-first search | Queue finds shortest paths by edge count | O(V + E) | O(V + E) graph copy |
| Dijkstra | Priority queue finds least-cost paths | O((V + E) log V) | O(V + E) |

Binary search checks ascending order first; this adds O(n). Inputs are copied, not changed. Optional traces cost additional storage: 200 steps by default, maximum 5,000; snapshots show up to 80 values. Results are complete even when the trace is truncated. A search comparison means one inspected element, a sorting comparison means one order decision, and a graph comparison means one inspected edge. Timing includes Python validation and bookkeeping; `compare` is an illustration, not a rigorous benchmark. Comparison inputs are limited to 5,000 values.

## Graph input

Graphs are directed. Add reverse edges explicitly for an undirected graph. Destination-only nodes are included automatically. BFS uses adjacency arrays:

```json
{"studio":["library","cinema"],"library":["park"],"cinema":["park"],"park":[]}
```

Dijkstra uses neighbor-to-weight objects (see `examples/routes.json`). It accepts finite nonnegative weights including zero. Unknown start/end nodes and negative weights produce clear errors. Unreachable distances and paths are `null` in JSON. Without `--end`, traversal still returns every distance.

## Python API

```python
from algorithms_in_action import run
result = run('merge-sort', [8, 3, 5])
assert result.output == [3, 5, 8]
print(result.steps)
```

Search results use zero-based indexes and `-1` when absent. Both searches return the first duplicate. Nonfinite numbers and booleans are rejected. The original `python src/binarysearch.py` entry point still works, now returning a computed result.

## Verify

```sh
python -m unittest discover -s tests -v
```

Tests compare randomized sorts against Python; cover duplicate/missing search targets, cycles, disconnected graphs, zero-weight relaxation, malformed inputs, bounded traces, and CLI results. CI checks Python 3.10, 3.12, and 3.13.

MIT licensed. Built by Michael Sanders.

## Browser learning lab

Run `python3 -m algorithms_in_action lab` and open **http://127.0.0.1:4176/**. The lab calls the same Python implementations as the CLI. Choose an algorithm, enter your own values or directed graph, and run it. Step forward/back, scrub, rewind or play the recorded trace at three speeds. Array bars and directed graph highlights show changing state; exact state, final output, operation counts and JSON export remain available.

The lab accepts at most 80 values, 24 total graph nodes and 120 edges, with 500 recorded steps. It binds only to loopback, rejects foreign origins/hosts and serves an explicit asset allowlist. No account, dependencies, remote processing, saved input or credentials. Use `--port 4177` to choose another local port. The CLI retains its larger input limits.
