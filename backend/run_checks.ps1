$ErrorActionPreference = "Stop"
$Python = Join-Path $PSScriptRoot "venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "Backend virtual environment not found. From backend run: python -m venv venv"
}

Write-Host "[1/5] Checking Python dependencies..." -ForegroundColor Cyan
& $Python -c "import fastapi, uvicorn, pandas, numpy; print('Dependencies OK')"

Write-Host "[2/5] Building compact official-data dataset..." -ForegroundColor Cyan
& $Python -m services.compact_market_data

Write-Host "[3/5] Running sector-demand descriptive analysis..." -ForegroundColor Cyan
& $Python -m services.sector_demand_engine

Write-Host "[4/5] Running automated tests..." -ForegroundColor Cyan
& $Python -m unittest discover -s tests -v

Write-Host "[5/5] Checking FastAPI imports and route registration..." -ForegroundColor Cyan
& $Python -c "import main; print('FastAPI app loaded. Registered routes:', len(main.app.routes))"

Write-Host "All checks completed. Start the server with: .\venv\Scripts\python.exe -m uvicorn main:app --reload" -ForegroundColor Green
