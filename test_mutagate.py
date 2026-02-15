"""Tests for MutaGate mutation engine and diff parser."""
import pytest
from mutators import generate_mutants
from mutagate import parse_diff


def test_arithmetic_mutation_plus_to_minus():
    source = "result = a + b\n"
    mutants = generate_mutants(source)
    arith = [m for m in mutants if m.kind == 'arith']
    assert len(arith) >= 1
    assert ' - ' in arith[0].source
    assert arith[0].line == 1
    assert arith[0].description == '+ -> -'


def test_arithmetic_mutation_mul_to_div():
    source = "total = price * qty\n"
    mutants = generate_mutants(source)
    arith = [m for m in mutants if m.kind == 'arith']
    assert len(arith) >= 1
    assert ' / ' in arith[0].source


def test_comparison_gt_to_gte():
    source = "if amount > 0:\n    process()\n"
    mutants = generate_mutants(source)
    cmp_m = [m for m in mutants if m.kind == 'cmp']
    assert len(cmp_m) >= 1
    assert ' >= ' in cmp_m[0].source
    assert cmp_m[0].description == '> -> >='


def test_comparison_eq_to_neq():
    source = "if status == 'active':\n    run()\n"
    mutants = generate_mutants(source)
    cmp_m = [m for m in mutants if m.kind == 'cmp']
    assert len(cmp_m) >= 1
    assert any(' != ' in m.source for m in cmp_m)


def test_return_value_mutation():
    source = "def calc():\n    return 42\n"
    mutants = generate_mutants(source)
    ret = [m for m in mutants if m.kind == 'return']
    assert len(ret) == 1
    assert 'return None' in ret[0].source
    assert ret[0].line == 2


def test_condition_negation():
    source = "if is_valid:\n    approve()\n"
    mutants = generate_mutants(source)
    neg = [m for m in mutants if m.kind == 'negate']
    assert len(neg) == 1
    assert 'not (is_valid)' in neg[0].source


def test_changed_lines_filter():
    source = "a = x + y\nb = x - y\nc = x * y\n"
    mutants_all = generate_mutants(source)
    mutants_l2 = generate_mutants(source, changed_lines={2})
    assert len(mutants_all) >= 3
    assert all(m.line == 2 for m in mutants_l2)
    assert len(mutants_l2) >= 1


def test_parse_diff_extracts_changed_lines():
    diff = (
        "diff --git a/calc.py b/calc.py\n"
        "--- a/calc.py\n"
        "+++ b/calc.py\n"
        "@@ -1,3 +1,4 @@\n"
        " def add(a, b):\n"
        "-    return a - b\n"
        "+    return a + b\n"
        "+    # fixed\n"
    )
    result = parse_diff(diff)
    assert 'calc.py' in result
    assert 2 in result['calc.py']
    assert 3 in result['calc.py']
    assert 1 not in result['calc.py']


def test_parse_diff_multiple_files():
    diff = (
        "diff --git a/a.py b/a.py\n"
        "+++ b/a.py\n"
        "@@ -1,1 +1,2 @@\n"
        " x = 1\n"
        "+y = 2\n"
        "diff --git a/b.py b/b.py\n"
        "+++ b/b.py\n"
        "@@ -5,1 +5,2 @@\n"
        " z = 3\n"
        "+w = 4\n"
    )
    result = parse_diff(diff)
    assert 'a.py' in result and 'b.py' in result
    assert 2 in result['a.py']
    assert 6 in result['b.py']


def test_no_mutations_on_plain_assignment():
    source = "x = 42\n"
    mutants = generate_mutants(source)
    assert len(mutants) == 0


def test_elif_condition_negation():
    source = "if a:\n    pass\nelif b:\n    pass\n"
    mutants = generate_mutants(source)
    neg = [m for m in mutants if m.kind == 'negate']
    assert len(neg) == 2
    assert any('not (b)' in m.source for m in neg)
