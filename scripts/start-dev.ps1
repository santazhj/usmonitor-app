$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$python = Join-Path $root ".venv\Scripts\python.exe"
if (!(Test-Path $python)) {
  $bundled = "C:\Users\user\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
  if (Test-Path $bundled) {
    & $bundled -m venv .venv
  } else {
    python -m venv .venv
  }
}

& $python -m pip install -r requirements.txt
& $python -m app.cli init-db
& $python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
