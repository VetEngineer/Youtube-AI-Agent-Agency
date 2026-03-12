# Release Notes - 2026-03-12

## Scope

- Branch: `main`
- Push commit: `9cd901d86250667e8200bd3aea602cf11dbddaa7`
- Release window: 2026-03-12 13:46 KST

## Included Commits

- `49a146d` `docs: sync runtime project map and guides`
- `9cd901d` `fix: harden queue runtime and test teardown`

## Delivered Changes

### Documentation

- Added a current-state project map covering workspace structure, API surface, DB schema, auth model, and request flow.
- Synced runtime and operator docs to the actual UV workspace layout:
  - `docs/MANUAL.md`
  - `docs/QUEUES.md`
  - `docs/MONITORING.md`
  - `docs/LOGGING.md`
  - `packages/README.md`

### Runtime Fixes

- Made RAG channel cleanup safe when `chromadb` is not installed.
- Updated production compose to match the current runtime:
  - added Redis service
  - corrected worker entrypoint
  - mounted `channels` and `output`
  - aligned Redis environment variables with the application config

### Test Stability

- Removed fallback-worker side effects from queue tests by mocking background execution where scheduling alone is under test.
- Explicitly disposed async SQLite engines in fixtures to eliminate `aiosqlite` thread shutdown warnings.

## Validation

- `uv run pytest packages/api/tests/test_rag.py -q`
- `uv run pytest packages/api/tests/test_worker.py -q`
- `make test`
- `docker compose -f infra/docker-compose.prod.yml config`

Result:

- `454 passed, 3 skipped`
- no test warnings
- production compose file resolves successfully

## GitHub Actions Status

Latest push workflow:

- Workflow: `CI`
- Run: `22986976374`
- URL: [CI run 22986976374](https://github.com/VetEngineer/Youtube-AI-Agent-Agency/actions/runs/22986976374)
- Conclusion: `failure`

Observed failure:

- `Lint` failed at step `Install uv`
- `Test` failed at step `Install uv`
- `Docker Build` was skipped because upstream jobs failed

Root cause:

- `.github/workflows/ci.yml` configures `astral-sh/setup-uv@v4` with `cache-dependency-glob: **/uv.lock`
- this repository stores `uv.lock` at the workspace root
- the current glob did not match the root lockfile in GitHub Actions, so the action aborted before dependency installation

Recommended follow-up:

- change the cache dependency glob to `uv.lock`
- or provide both root and nested forms explicitly if nested lockfiles are expected later

## Vercel Status

Checked with the authenticated `vetengineer` Vercel account.

Findings:

- no Vercel project matching `Youtube-AI-Agent-Agency` exists in the accessible scope `vetengineers-projects`
- no deployment was found for commit `9cd901d86250667e8200bd3aea602cf11dbddaa7`
- no GitHub deployment objects exist for this repository push
- no Vercel check runs or commit statuses were attached to the pushed commit

Interpretation:

- this repository is not currently wired to an active Vercel project in the authenticated scope
- the push to `main` did not trigger a Vercel deployment

## Review

- Codex (PM) review requested via implementation handoff summary before merge/push completion tracking
