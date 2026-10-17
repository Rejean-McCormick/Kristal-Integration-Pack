#!/usr/bin/env python3
"""Read-only local C3 preflight; delegates entirely to the collection owner's checker.

This command does NOT qualify the scientific truth, obtain C1/C2 authorization,
publish to GitHub, activate a Kristal, or modify any canonical data.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import subprocess
import sys


def check(collection: Path, mode: str = 'scan', timeout: int = 60) -> tuple[int, str]:
    root = collection.expanduser().resolve()
    owner_checker = root / 'tools' / 'c3_collection.py'
    if not owner_checker.is_file():
        return 3, 'NOT_EVALUATED: collection owner C3 checker is unavailable. No qualification can be claimed.'
    if mode not in {'scan', 'validate-index'}:
        raise ValueError('Read-only mode must be scan or validate-index')
    try:
        result = subprocess.run(
            [sys.executable, str(owner_checker), '--repo', str(root), mode],
            cwd=root, text=True, capture_output=True, encoding='utf-8', errors='replace',
            shell=False, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return 124, f'BLOCKED: C3 checker exceeded {timeout} seconds.'
    output = '\n'.join(x.strip() for x in (result.stdout, result.stderr) if x.strip())
    # This is a structural C3 result only; no C1/C2 grants are inferred.
    header = ('C3_LOCAL_STRUCTURE_PASS (C1/C2 and remote publication NOT verified)' if result.returncode == 0
              else 'C3_BLOCKED (no remote publication or authorization inferred)')
    return result.returncode, header + '\n' + output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--collection', required=True, type=Path, help='Extracted local collection checkout')
    parser.add_argument('--mode', default='scan', choices=('scan', 'validate-index'))
    args = parser.parse_args(argv)
    code, report = check(args.collection, args.mode)
    print(report)
    return code


if __name__ == '__main__':
    raise SystemExit(main())
