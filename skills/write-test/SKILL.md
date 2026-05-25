---
name: write-test
description: >
  Generate a test in the target repo's existing framework and style. Used by
  fix-from-issue and implement-feature.
license: Apache-2.0
allowed-tools: [read, write, detect-conventions, codebase-grep]
metadata:
  author: repo-surgeon
  version: 1.0.0
  category: testing
  risk_tier: low
---

## Instructions

1. Detect the test framework via `detect-conventions` (or look it up in `memory/repos/<TARGET_REPO>/conventions.md`).
   - Common frameworks: pytest (Python), jest/vitest (JS/TS), go test (Go), cargo test (Rust), JUnit (Java), RSpec (Ruby).
2. Find similar existing tests via `codebase-grep` — use them as templates. Match:
   - Directory layout (where tests live)
   - File naming convention (`*.test.ts`, `test_*.py`, `*_spec.rb`, etc.)
   - Test structure (`describe/it`, `test_*`, `it/should`, etc.)
   - Assertion style (`expect(x).toBe(y)`, `assert x == y`, etc.)
   - Setup/teardown patterns (fixtures, mocks)
3. Write the test:
   - Descriptive name referencing the issue or feature
   - Arrange-Act-Assert structure
   - Minimal — test one thing per test function
   - Use existing fixtures and helpers; do not invent new ones
4. Use `write` to create the test file (or `edit` to append to an existing one).

## Output Format

```json
{
  "test_file": "path/to/test/file",
  "test_function": "test_or_describe_name",
  "framework": "pytest|jest|...",
  "lines_added": int,
  "fixtures_used": ["fixture_name"]
}
```

## Examples

**Bug fix test (pytest)**:
```python
def test_cart_total_handles_decimal_prices_issue_142():
    cart = Cart()
    cart.add_item(Item(price=Decimal("3.99")))
    cart.add_item(Item(price=Decimal("1.50")))
    assert cart.total() == Decimal("5.49")  # was returning 5.4 due to float rounding
```

**Feature test (jest)**:
```javascript
describe('discount calculator', () => {
  it('applies percentage discount before tax', () => {
    const result = applyDiscount({subtotal: 100, discount: 0.1, taxRate: 0.08});
    expect(result.total).toBe(97.2);  // (100 * 0.9) * 1.08
  });
});
```

## Notes

- NEVER use snapshot testing for new tests — too easy to commit wrong snapshots.
- NEVER mock things the test is supposed to validate.
- If the framework supports it, use parametrized tests for edge cases.
