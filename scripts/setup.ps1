# DbToolsApp Setup Script for Windows
# Run this script from the project root directory

param(
    [switch]$SkipBackend,
    [switch]$SkipFrontend
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "=== DbToolsApp Setup ===" -ForegroundColor Cyan
Write-Host "Project Root: $ProjectRoot" -ForegroundColor Gray

# Check prerequisites
Write-Host "`nChecking prerequisites..." -ForegroundColor Yellow

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Check Node
try {
    $nodeVersion = node --version 2>&1
    Write-Host "  Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "  Node.js not found. Please install Node.js 18+" -ForegroundColor Red
    exit 1
}

# Backend Setup
if (-not $SkipBackend) {
    Write-Host "`n=== Setting up Backend ===" -ForegroundColor Cyan
    $backendPath = Join-Path $ProjectRoot "backend"

    # Create virtual environment if it doesn't exist
    $venvPath = Join-Path $backendPath "venv"
    if (-not (Test-Path $venvPath)) {
        Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
        python -m venv $venvPath
    } else {
        Write-Host "Virtual environment already exists" -ForegroundColor Gray
    }

    # Activate and install dependencies
    Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
    $pipPath = Join-Path $venvPath "Scripts\pip"
    & $pipPath install -r (Join-Path $backendPath "requirements-dev.txt") --quiet
    Write-Host "Backend dependencies installed" -ForegroundColor Green
}

# Frontend Setup
if (-not $SkipFrontend) {
    Write-Host "`n=== Setting up Frontend ===" -ForegroundColor Cyan
    $frontendPath = Join-Path $ProjectRoot "frontend"

    Write-Host "Installing npm dependencies..." -ForegroundColor Yellow
    Push-Location $frontendPath
    npm install --silent
    Pop-Location
    Write-Host "Frontend dependencies installed" -ForegroundColor Green
}

# Create .env file if it doesn't exist
$envFile = Join-Path $ProjectRoot ".env"
$envExample = Join-Path $ProjectRoot ".env.example"
if (-not (Test-Path $envFile) -and (Test-Path $envExample)) {
    Write-Host "`nCreating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item $envExample $envFile
    Write-Host ".env file created - please update with your settings" -ForegroundColor Green
}

Write-Host "`n=== Setup Complete ===" -ForegroundColor Cyan
Write-Host "`nTo start development:" -ForegroundColor Yellow
Write-Host "  Backend:  cd backend && venv\Scripts\activate && python run.py" -ForegroundColor White
Write-Host "  Frontend: cd frontend && npm run dev" -ForegroundColor White
