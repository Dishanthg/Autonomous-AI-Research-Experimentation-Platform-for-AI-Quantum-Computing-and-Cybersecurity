# Dependency Vulnerability Audit

Real `pip-audit`/`npm audit` run, not an estimate. Performed while adding
rate limiting - the pip-audit run surfaced enough real, fixable CVEs in already-pinned
dependencies to justify fixing them in the same pass rather than leaving
`pip-audit` wired into CI against a known-red baseline.

## Backend (`pip-audit -r backend/requirements.txt`)

**Before:** 38 known vulnerabilities across 6 packages (`pyjwt`,
`cryptography`, `qiskit`, `python-dotenv`, `python-multipart`,
`starlette`).

**Action taken**, in two passes:

1. Low-risk patch/minor bumps, verified against the full 118-test suite
   after each: `pyjwt` 2.10.1→2.13.0, `python-dotenv` 1.0.1→1.2.2,
   `python-multipart` 0.0.20→0.0.31, `cryptography` 44.0.0→50.0.1, `qiskit`
   1.3.1→1.4.2.
2. `starlette` 0.41.3 had CVEs whose fixes required jumping to Starlette
   1.x - not installable directly, because `fastapi==0.115.6` pins
   `starlette<0.42.0,>=0.40.0` (there is no patched version inside that
   range) and the installed `prometheus-fastapi-instrumentator==7.0.0`
   pins `starlette<1.0.0`. Fixing this required bumping **both** packages
   together: `fastapi` 0.115.6→0.141.1 (`starlette>=0.46.0`, no upper
   bound) and `prometheus-fastapi-instrumentator` 7.0.0→8.1.0
   (`starlette>=1.0.0,<2.0.0`) - the two ranges overlap at `starlette==1.6.0`,
   which was installed and is what's now pinned.

**A real regression was caught and fixed by the test suite during this
upgrade**, not just avoided by luck: with `starlette==1.6.0` installed,
`slowapi==0.1.10` (the library originally used for rate limiting, added in
this same session) silently stopped enforcing limits - every request
returned 200 instead of 429 on `test_rate_limit_returns_429_once_exceeded`.
slowapi has had no release since 0.1.10 and doesn't declare a Starlette
upper bound, so pip installed it against an incompatible Starlette without
any warning. Rather than pin Starlette back down (reintroducing the CVEs
above) or add a slowapi upper-bound workaround, `app/core/rate_limit.py`
was rewritten as a small ASGI middleware built directly on the
framework-agnostic `limits` library (which slowapi itself wraps) - no
Starlette-version coupling at all, verified by the same test passing again
unmodified in behavior (only the implementation underneath changed).

**After:** `pip-audit -r backend/requirements.txt` → `No known
vulnerabilities found`. Full 118-test suite passes; `frontend`
`npx tsc -b` and `vite build` both pass unchanged.

## Frontend (`npm audit`)

**Before:** 4 vulnerabilities (3 moderate, 1 high) in `esbuild`/`vite` and
`react-router`/`react-router-dom`.

**Action taken:** `vite` 5.4.11→8.2.2, `@vitejs/plugin-react` 4.3.4→5.0.0
(required peer bump for Vite 8), `react-router-dom` 6.28.0→7.18.3. All
three are major-version bumps; verified safe for this app specifically
because it only uses React Router's plain declarative API
(`BrowserRouter`, `Routes`, `Route`, `Navigate`, `NavLink`, `Link`,
`useParams`, `useNavigate` - `grep -rn "react-router-dom" frontend/src`),
which React Router v7 keeps as a compatible mode; confirmed by a clean
`npx tsc -b` and a real `vite build` producing the same three-file bundle
shape as before.

**After:** `npm audit` → `found 0 vulnerabilities`.

## CI enforcement

`.github/workflows/ci.yml` now runs `pip-audit -r requirements.txt` in the
backend job and `npm audit --audit-level=high` in the frontend job, so a
newly-introduced or newly-disclosed vulnerability fails CI rather than
sitting undetected - this audit's "before" state is exactly what CI would
now catch and block.

## What this does not cover

- Transitive dependencies not captured by `pip-audit`'s vulnerability
  database at the time of this run - it queries a live feed (PyPA's
  Advisory Database), so this is a point-in-time result, not a permanent
  guarantee. Re-run `pip-audit -r backend/requirements.txt` periodically.
- `liboqs`/`oqs-python` (PQC) - not installed in this environment at all
  (see `FINAL_RESEARCH_AUDIT.md`), so it has no entry here either way.
- Docker base images (`sandbox/images/`) - not scanned by this pass; a
  container-image scanner (e.g. `trivy`) would be the appropriate follow-up
  for those, tracked as a future addition alongside Docker sandbox
  end-to-end verification (blocked on ADR-008).
