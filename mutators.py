"""MutaGate mutation engine — AST-guided source mutations."""
import ast
import re
from dataclasses import dataclass, field
from typing import List, Optional, Set


@dataclass
class Mutant:
    file: str
    line: int
    kind: str
    description: str
    source: str


ARITH_SWAPS = [(' + ', ' - '), (' - ', ' + '), (' * ', ' / '), (' / ', ' * ')]
CMP_SWAPS = [
    (' >= ', ' > '), (' <= ', ' < '),
    (' > ', ' >= '), (' < ', ' <= '),
    (' == ', ' != '), (' != ', ' == '),
]


def _swap_line(src_lines: list, ln: int, old: str, new: str) -> str:
    lines = src_lines.copy()
    lines[ln - 1] = lines[ln - 1].replace(old, new, 1)
    return '\n'.join(lines)


def generate_mutants(
    source: str,
    filepath: str = "<input>",
    changed_lines: Optional[Set[int]] = None,
) -> List[Mutant]:
    """Scan Python source via AST, yield mutants for mutable nodes."""
    tree = ast.parse(source)
    src_lines = source.split('\n')
    mutants: List[Mutant] = []
    seen: set = set()

    for node in ast.walk(tree):
        if not hasattr(node, 'lineno'):
            continue
        ln = node.lineno
        if changed_lines is not None and ln not in changed_lines:
            continue
        if ln < 1 or ln > len(src_lines):
            continue
        line = src_lines[ln - 1]

        # Arithmetic mutations
        if isinstance(node, ast.BinOp):
            for old, new in ARITH_SWAPS:
                key = (ln, 'arith', old)
                if old in line and key not in seen:
                    seen.add(key)
                    mutants.append(Mutant(filepath, ln, 'arith',
                        f"{old.strip()} -> {new.strip()}",
                        _swap_line(src_lines, ln, old, new)))

        # Comparison mutations
        if isinstance(node, ast.Compare):
            for old, new in CMP_SWAPS:
                key = (ln, 'cmp', old)
                if old in line and key not in seen:
                    seen.add(key)
                    mutants.append(Mutant(filepath, ln, 'cmp',
                        f"{old.strip()} -> {new.strip()}",
                        _swap_line(src_lines, ln, old, new)))

        # Return value mutation
        if isinstance(node, ast.Return) and node.value is not None:
            key = (ln, 'return')
            if key not in seen:
                seen.add(key)
                lines = src_lines.copy()
                indent = len(line) - len(line.lstrip())
                lines[ln - 1] = ' ' * indent + 'return None'
                mutants.append(Mutant(filepath, ln, 'return',
                    'return -> None', '\n'.join(lines)))

        # Condition negation
        if isinstance(node, ast.If):
            key = (ln, 'negate')
            if key not in seen:
                match = re.match(r'^(\s*(?:el)?if\s+)(.*):(.*)$', line)
                if match:
                    seen.add(key)
                    pre, cond, post = match.groups()
                    lines = src_lines.copy()
                    lines[ln - 1] = f"{pre}not ({cond}):{post}"
                    mutants.append(Mutant(filepath, ln, 'negate',
                        'condition negated', '\n'.join(lines)))

    return mutants
