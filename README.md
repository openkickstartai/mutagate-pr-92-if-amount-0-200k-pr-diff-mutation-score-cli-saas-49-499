# MutaGate — PR-Scoped Mutation Testing Quality Gate

> Your 92% line coverage is a lie. `if amount > 0` was never tested with negatives.
> MutaGate injects mutations into your PR diff and proves whether your tests actually verify anything.

## The Problem

Line coverage measures **execution**, not **verification**. A test that calls `transfer(100)` and never asserts the result gives you coverage — but catches nothing. MutaGate flips `>` to `>=`, swaps `+` to `-`, negates conditions, and checks: **do your tests notice?**

## 🚀 Quick Start

```bash
pip install click pytest

# Mutate specific files, run tests, gate at 80%
python mutagate.py app/payment.py --test-dir tests --threshold 80

# PR mode: only mutate git diff lines
python mutagate.py --diff --threshold 75
```

## Mutation Operators

| Operator | Example | Catches |
|----------|---------|--------|
| Arithmetic flip | `a + b` → `a - b` | Missing calculation assertions |
| Boundary shift | `x > 0` → `x >= 0` | Off-by-one blind spots |
| Condition negate | `if valid:` → `if not (valid):` | Untested branches |
| Return tamper | `return total` → `return None` | Unchecked return values |

## 📊 Why Pay — Coverage vs Mutation Score

| Metric | Coverage | Mutation Score |
|--------|----------|---------------|
| Measures | Lines executed | Logic verified |
| `transfer(100)` with no assert | ✅ 100% | ❌ 0% |
| Catches `>` vs `>=` bugs | ❌ No | ✅ Yes |
| Prevents $200K incidents | ❌ No | ✅ Yes |

## 💰 Pricing

| | Free | Pro $49/mo | Enterprise $499/mo |
|---|---|---|---|
| CLI mutation testing | ✅ | ✅ | ✅ |
| 4 mutation operators | ✅ | ✅ | ✅ |
| PR-scoped diff mode | ✅ | ✅ | ✅ |
| Repos | 1 | Unlimited | Unlimited |
| GitHub/GitLab CI integration | ❌ | ✅ | ✅ |
| PR comment with survived mutants | ❌ | ✅ | ✅ |
| Mutation score trend dashboard | ❌ | ✅ | ✅ |
| Slack alerts on gate failure | ❌ | ✅ | ✅ |
| SARIF/PDF compliance reports | ❌ | ❌ | ✅ |
| SSO + audit trail | ❌ | ❌ | ✅ |
| Self-hosted deployment | ❌ | ❌ | ✅ |
| Priority support + SLA | ❌ | ❌ | ✅ |

**ROI**: One boundary bug in payment logic costs $50K-$200K. MutaGate costs $49/mo.

## License

BSL 1.1 — Free for small teams, commercial license required for >10 devs.
