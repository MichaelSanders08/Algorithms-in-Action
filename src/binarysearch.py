"""Compatibility entry point for the original prototype."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from algorithms_in_action.core import run as run_algorithm

def binarySearch(values=None, target=7):
    return run_algorithm('binary-search', [2, 4, 7, 11, 19] if values is None else values, target=target).output

def run():
    print(binarySearch())

if __name__ == '__main__':
    run()
