# Guard Report — программу-оптимизации-windows-11

Generated: 2026-08-19T14:14:02.166Z

| Step | Status | Detail |
|------|--------|--------|
| lint | SKIP | no lint script in package.json |
| type | FAIL | Command failed: npm exec tsc --noEmit
npm warn Unknown cli config "--noEmit". This will stop working in the next major version of npm.
 |
| test | SKIP | no test script in package.json |
| drift | PASS | no capabilities in specs |
| yagni | SKIP | no existing .ts sources to build a baseline from |
| economy | PASS | cache 278.0 KB of 100.0 MB (703 entries) — within budget; ≈ 1463963 tok saved across 830 compress op(s) |
| security | PASS | no obvious issues |
| policy | PASS | no .orion/policy.json — no project gates to enforce |
| verifiability | WARN | oracles: none · verifiability level 0 · tests weak/missing — low verifiability: treat this PASS as lower-confidence (human review advised) |

**Overall: FAIL**

> ⚠️ lower-confidence PASS: this repo has weak/no verification oracles — treat as human-review needed.
