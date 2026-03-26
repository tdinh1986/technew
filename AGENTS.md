# Repository Guidelines

## Project Structure & Module Organization
`backend/` contains the FastAPI service, scheduler, Alembic migrations, and pytest suite. Main API routes live in `backend/api/`, persistence models in `backend/models/`, fetch/summarize logic in `backend/fetcher/` and `backend/summarizer/`, and tests in `backend/tests/`.

`frontend/` contains the Next.js 14 app. Route files live under `frontend/app/`, shared UI in `frontend/components/`, API and type helpers in `frontend/lib/`, and Vitest tests in `frontend/tests/`.

Use the canonical files such as `backend/main.py` and `frontend/next.config.mjs`; several duplicate `* 2.*` files exist and should not be extended unless you are intentionally cleaning them up.

## Build, Test, and Development Commands
- `./start.sh`: bootstraps both apps, runs backend migrations, and starts the backend on `:8000` and frontend on `:3000`.
- `cd backend && source .venv/bin/activate && alembic upgrade head`: apply database migrations.
- `cd backend && pytest`: run the backend test suite.
- `cd backend && ruff check . && ruff format .`: lint and format Python code.
- `cd frontend && npm run dev`: start the Next.js app locally.
- `cd frontend && npm test`: run Vitest component tests.
- `cd frontend && npm run lint`: run ESLint with Next.js rules.
- `cd frontend && npm run build`: verify the production build.

## Coding Style & Naming Conventions
Python follows Ruff defaults: 4-space indentation, type hints on public code, snake_case for modules/functions, and concise docstrings only where they add value. Keep FastAPI route modules focused by domain.

Frontend code uses TypeScript, 2-space indentation, semicolons, and double quotes. Name React components in PascalCase (`DigestReport.tsx`), helpers in camelCase, and test files as `ComponentName.test.tsx`.

## Testing Guidelines
Backend tests use `pytest` and `fastapi.testclient`; place new tests in `backend/tests/test_<feature>.py`. Frontend tests use `vitest` with Testing Library and `jsdom`; colocate by feature under `frontend/tests/components/` when testing UI.

Cover new API routes, fetch/summarize flows, and user-visible component states. Run the relevant suite before opening a PR, then run both full test commands for cross-stack changes.

## Commit & Pull Request Guidelines
Recent commits are short, imperative, and focused, for example `create start.sh` or `adjust fetch`. Keep commit subjects under about 72 characters and split unrelated backend/frontend work into separate commits when practical.

Pull requests should describe the user-facing change, list validation steps, and link the relevant spec or issue. Include screenshots or short recordings for frontend changes and call out any new env vars, migrations, or background job behavior.
