#!/usr/bin/env python3
"""MutaGate CLI — PR-scoped mutation testing quality gate."""
import os
import re
import subprocess
import sys

import click

from mutators import generate_mutants


def parse_diff(diff_text: str) -> dict:
    """Parse unified diff into {filepath: set(line_numbers)} for added/changed lines."""
    result: dict = {}
    current_file = None
    line_no = 0
    for raw in diff_text.split('\n'):
        if raw.startswith('+++ b/'):
            current_file = raw[6:]
            result.setdefault(current_file, set())
        elif raw.startswith('@@'):
            m = re.search(r'\+(\d+)', raw)
            if m:
                line_no = int(m.group(1)) - 1
        elif current_file and raw.startswith('+') and not raw.startswith('+++'):
            line_no += 1
            result[current_file].add(line_no)
        elif current_file and not raw.startswith('-'):
            line_no += 1
    return result


def find_test_files(source_path: str, test_dir: str = 'tests') -> list:
    """Find test files that import the module under mutation."""
    module = os.path.splitext(os.path.basename(source_path))[0]
    hits = []
    if os.path.isdir(test_dir):
        for f in os.listdir(test_dir):
            if f.startswith('test_') and f.endswith('.py'):
                path = os.path.join(test_dir, f)
                if module in open(path).read():
                    hits.append(path)
    return hits if hits else ([test_dir] if os.path.isdir(test_dir) else [])


def run_mutant(source_path: str, mutated_source: str, test_files: list) -> bool:
    """Swap source with mutant, run tests, restore. Returns True if mutant was killed."""
    original = open(source_path).read()
    try:
        with open(source_path, 'w') as f:
            f.write(mutated_source)
        cmd = [sys.executable, '-m', 'pytest', '-x', '-q', '--tb=no', '--no-header'] + test_files
        proc = subprocess.run(cmd, capture_output=True, timeout=30)
        return proc.returncode != 0
    except subprocess.TimeoutExpired:
        return True
    finally:
        with open(source_path, 'w') as f:
            f.write(original)


@click.command()
@click.argument('files', nargs=-1)
@click.option('--threshold', '-t', default=80, help='Min mutation score % to pass gate')
@click.option('--diff/--no-diff', default=False, help='Only mutate lines in git diff')
@click.option('--test-dir', default='tests', help='Test directory path')
@click.option('--dry-run', is_flag=True, help='List mutations without running tests')
def main(files, threshold, diff, test_dir, dry_run):
    """MutaGate: mutation testing quality gate for your PRs."""
    changed = {}
    if diff:
        proc = subprocess.run(['git', 'diff', 'HEAD~1'], capture_output=True, text=True)
        changed = parse_diff(proc.stdout)
        if not files:
            files = tuple(f for f in changed if f.endswith('.py'))
    if not files:
        click.secho('No files to mutate. Pass file paths or use --diff.', fg='yellow')
        return
    total = killed = 0
    for fpath in files:
        if not os.path.exists(fpath):
            click.secho(f'Skip {fpath}: not found', fg='yellow')
            continue
        source = open(fpath).read()
        lines = changed.get(fpath) if diff else None
        mutants = generate_mutants(source, fpath, lines)
        click.secho(f'\n{fpath}: {len(mutants)} mutant(s)', bold=True)
        if dry_run:
            for m in mutants:
                click.echo(f'  L{m.line} [{m.kind}] {m.description}')
            total += len(mutants)
            continue
        tests = find_test_files(fpath, test_dir)
        for m in mutants:
            total += 1
            is_killed = run_mutant(fpath, m.source, tests)
            killed += is_killed
            sym, color = ('KILLED', 'green') if is_killed else ('SURVIVED', 'red')
            click.secho(f'  L{m.line} [{m.kind}] {m.description} — {sym}', fg=color)
    click.echo(f'\n{"="*50}')
    if total == 0:
        click.secho('No mutations generated.', fg='yellow')
        return
    score = round(killed / total * 100, 1) if not dry_run else 0.0
    if dry_run:
        click.secho(f'Dry run: {total} mutations found. Run without --dry-run to test.', fg='cyan')
        return
    fg = 'green' if score >= threshold else 'red'
    click.secho(f'Mutation Score: {score}% ({killed}/{total} killed)', fg=fg, bold=True)
    click.echo(f'Threshold:      {threshold}%')
    if score < threshold:
        click.secho(f'GATE FAILED — score {score}% < {threshold}%', fg='red', bold=True)
        sys.exit(1)
    else:
        click.secho('GATE PASSED', fg='green', bold=True)


if __name__ == '__main__':
    main()
