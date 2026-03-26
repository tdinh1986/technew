#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== TechNew Build + Start ==="

# ── Prerequisites ──────────────────────────────────────────────────────────────

if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found. Install Python 3.9+ and retry."
    exit 1
fi
if ! command -v node &>/dev/null || ! command -v npm &>/dev/null; then
    echo "ERROR: node/npm not found. Install Node.js 18+ and retry."
    exit 1
fi

# ── Backend setup ──────────────────────────────────────────────────────────────

echo ""
echo "[backend] Setting up..."
cd backend

if [ ! -d ".venv" ]; then
    echo "[backend] Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate

echo "[backend] Installing dependencies..."
pip install -r requirements.txt --quiet

if [ ! -f ".env" ]; then
    echo "[backend] Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "  !! ACTION REQUIRED: Edit backend/.env and set ANTHROPIC_API_KEY"
    echo "  !!   then re-run ./start.sh"
    echo ""
    exit 1
fi

if grep -q "your-anthropic-api-key-here" .env 2>/dev/null; then
    echo ""
    echo "  !! WARNING: ANTHROPIC_API_KEY in backend/.env still has the placeholder value."
    echo "  !!   Summarization will fail. Edit backend/.env before fetching articles."
    echo ""
fi

echo "[backend] Running database migrations..."
alembic upgrade head

cd ..

# ── Frontend setup ─────────────────────────────────────────────────────────────

echo ""
echo "[frontend] Setting up..."
cd frontend

if [ ! -f ".env.local" ]; then
    echo "[frontend] Creating .env.local from .env.local.example..."
    cp .env.local.example .env.local
fi

echo "[frontend] Installing dependencies..."
npm install --silent

cd ..

# ── Start servers ──────────────────────────────────────────────────────────────

echo ""
echo "=== Starting servers ==="

cd backend
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

cleanup() {
    echo ""
    echo "Shutting down..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

echo ""
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop."

wait $BACKEND_PID $FRONTEND_PID
