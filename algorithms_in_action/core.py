"""Pure implementations, explicit assumptions, bounded explanatory traces."""
from collections import deque
from dataclasses import asdict, dataclass, field
import heapq
import math
from numbers import Real

ALGORITHMS = {
    'linear-search': {'kind': 'search', 'time': 'O(n)', 'idea': 'Inspect each value until the first match.'},
    'binary-search': {'kind': 'search', 'time': 'O(log n)', 'idea': 'Halve a sorted interval; return the first duplicate.'},
    'insertion-sort': {'kind': 'sort', 'time': 'O(n²), best O(n)', 'idea': 'Grow a sorted prefix, moving one value into place.'},
    'merge-sort': {'kind': 'sort', 'time': 'O(n log n)', 'idea': 'Split, sort each half, then merge in order.'},
    'bfs': {'kind': 'graph', 'time': 'O(V + E)', 'idea': 'A queue explores the nearest unweighted neighbors first.'},
    'dijkstra': {'kind': 'graph', 'time': 'O((V + E) log V)', 'idea': 'Expand the cheapest known route; weights must be nonnegative.'},
}

@dataclass
class Result:
    algorithm: str
    output: object = None
    metrics: dict = field(default_factory=lambda: {'comparisons': 0, 'writes': 0, 'visited': 0})
    steps: list = field(default_factory=list)
    trace_truncated: bool = False
    trace_limit: int = field(default=200, repr=False)

    def note(self, explanation, **state):
        if not self.trace_limit:
            return
        if len(self.steps) < self.trace_limit:
            self.steps.append({'step': len(self.steps) + 1, 'explanation': explanation, **state})
        else:
            self.trace_truncated = True

    def to_dict(self):
        data = asdict(self)
        del data['trace_limit']
        return data


def number(value):
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
        raise ValueError('Use finite numbers, not booleans, NaN, or infinity.')
    return value


def graph_nodes(graph, weighted):
    if not isinstance(graph, dict) or not graph or any(not isinstance(n, str) or not n for n in graph):
        raise ValueError('The graph must be a nonempty object with nonempty string node names.')
    result = {node: {} if weighted else [] for node in graph}
    for node, edges in graph.items():
        if weighted:
            if not isinstance(edges, dict):
                raise ValueError('Dijkstra needs neighbor-to-weight objects, such as {"A": {"B": 2}}.')
            pairs = edges.items()
        else:
            if not isinstance(edges, list):
                raise ValueError('BFS needs neighbor arrays, such as {"A": ["B"]}.')
            pairs = ((neighbor, 1) for neighbor in edges)
        for neighbor, weight in pairs:
            if not isinstance(neighbor, str) or not neighbor:
                raise ValueError('Every neighbor must have a nonempty string name.')
            if weighted and number(weight) < 0:
                raise ValueError('Dijkstra cannot use negative weights.')
            result.setdefault(neighbor, {} if weighted else [])
            if weighted:
                result[node][neighbor] = weight
            elif neighbor not in result[node]:
                result[node].append(neighbor)
    return result


def run(algorithm, values=None, *, target=None, graph=None, start=None, end=None, trace_limit=200):
    if algorithm not in ALGORITHMS:
        raise ValueError(f'Unknown algorithm: {algorithm}')
    if not isinstance(trace_limit, int) or not 0 <= trace_limit <= 5000:
        raise ValueError('Trace limit must be an integer from 0 to 5000.')
    result = Result(algorithm, trace_limit=trace_limit)
    kind = ALGORITHMS[algorithm]['kind']
    if kind == 'graph':
        return _graph(result, graph, start, end)
    if values is None or not isinstance(values, (list, tuple)):
        raise ValueError('Provide a list of numbers.')
    data = [number(v) for v in values]
    if kind == 'search':
        number(target)
        if algorithm == 'linear-search':
            result.output = -1
            for i, value in enumerate(data):
                result.metrics['comparisons'] += 1
                result.note('Compare this value with the target.', index=i, value=value, target=target)
                if value == target:
                    result.output = i
                    break
        else:
            if any(data[i] > data[i + 1] for i in range(len(data) - 1)):
                raise ValueError('Binary search requires ascending input. Sort it explicitly; indexes refer to the supplied array.')
            left, right, found = 0, len(data) - 1, -1
            while left <= right:
                middle = (left + right) // 2
                result.metrics['comparisons'] += 1
                result.note('Compare the midpoint; retain the half that may contain the first match.', left=left, right=right, middle=middle, value=data[middle])
                if data[middle] >= target:
                    if data[middle] == target:
                        found = middle
                    right = middle - 1
                else:
                    left = middle + 1
            result.output = found
    elif algorithm == 'insertion-sort':
        for i in range(1, len(data)):
            value, j = data[i], i - 1
            while j >= 0:
                result.metrics['comparisons'] += 1
                if data[j] <= value:
                    break
                data[j + 1] = data[j]
                result.metrics['writes'] += 1
                j -= 1
            data[j + 1] = value
            result.metrics['writes'] += 1
            result.note(f'Insert {value} into the sorted prefix.', inserted_at=j + 1, sorted_through=i, values=data[:80], values_omitted=max(0, len(data) - 80))
        result.output = data
    else:
        def merge(items, offset=0):
            if len(items) <= 1:
                return items
            middle = len(items) // 2
            left, right = merge(items[:middle], offset), merge(items[middle:], offset + middle)
            merged, i, j = [], 0, 0
            while i < len(left) and j < len(right):
                result.metrics['comparisons'] += 1
                if left[i] <= right[j]:
                    merged.append(left[i]); i += 1
                else:
                    merged.append(right[j]); j += 1
            merged.extend(left[i:]); merged.extend(right[j:])
            result.metrics['writes'] += len(merged)
            result.note('Merge two sorted runs, taking the smaller head each time.', start=offset, length=len(merged), values=merged[:80], values_omitted=max(0, len(merged) - 80))
            return merged
        result.output = merge(data)
    return result


def _graph(result, raw, start, end):
    weighted = result.algorithm == 'dijkstra'
    graph = graph_nodes(raw, weighted)
    if start not in graph or (end is not None and end not in graph):
        raise ValueError('Start and destination must be nodes in the graph.')
    distances = {node: math.inf for node in graph}
    distances[start] = 0
    parents, order = {}, []
    if weighted:
        frontier = [(0, start)]
        while frontier:
            distance, node = heapq.heappop(frontier)
            if distance != distances[node]:
                continue
            order.append(node)
            result.note('Expand the node with the smallest known cost.', node=node, distance=distance)
            for neighbor, weight in graph[node].items():
                result.metrics['comparisons'] += 1
                candidate = distance + weight
                if not math.isfinite(candidate):
                    raise ValueError('A path cost exceeds the finite numeric range.')
                if candidate < distances[neighbor]:
                    distances[neighbor], parents[neighbor] = candidate, node
                    heapq.heappush(frontier, (candidate, neighbor))
                    result.note('A cheaper route replaces the previous estimate.', from_node=node, to=neighbor, distance=candidate)
    else:
        frontier = deque([start])
        while frontier:
            node = frontier.popleft()
            order.append(node)
            result.note('Take the next node from the front of the queue.', node=node, distance=distances[node])
            for neighbor in graph[node]:
                result.metrics['comparisons'] += 1
                if math.isinf(distances[neighbor]):
                    distances[neighbor], parents[neighbor] = distances[node] + 1, node
                    frontier.append(neighbor)
    result.metrics['visited'] = len(order)
    path = None
    if end is not None and not math.isinf(distances[end]):
        path = [end]
        while path[-1] != start:
            path.append(parents[path[-1]])
        path.reverse()
    result.output = {'order': order, 'distances': {n: None if math.isinf(d) else d for n, d in distances.items()}, 'path': path}
    return result
