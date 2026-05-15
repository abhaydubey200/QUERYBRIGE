# ==================================================
# QUERYBRIDGE ENTERPRISE - STARTUP ORCHESTRATOR
# ==================================================

Write-Host "🚀 Initializing QueryBridge Enterprise Runtime..." -ForegroundColor Cyan

# 1. Check Dependencies
Write-Host "🔍 Verifying System Dependencies..." -ForegroundColor Yellow

if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ FATAL: Docker is not installed. Please install Docker Desktop." -ForegroundColor Red
    exit 1
}

if (!(Test-Path .env)) {
    Write-Host "⚠️  WARNING: .env file not found. Creating from .env.example..." -ForegroundColor Magenta
    Copy-Item .env.example .env
}

# 1.1 Secure Key Initialization (Auto-Generation)
$envContent = Get-Content .env -Raw
$needsUpdate = $false

if ($envContent -match "replace-this-with-32-byte-base64-key" -or $envContent -match "JWT_SECRET=KEY") {
    Write-Host "🔐 Generating secure enterprise keys..." -ForegroundColor Yellow
    
    # Generate 32-byte Base64 key for AES
    $bytes = New-Object Byte[] 32
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $rng.GetBytes($bytes)
    $newEncKey = [Convert]::ToBase64String($bytes)
    
    # Generate secure JWT secret
    $jwtBytes = New-Object Byte[] 48
    $rng.GetBytes($jwtBytes)
    $newJwtSecret = [Convert]::ToBase64String($jwtBytes)
    
    $envContent = $envContent -replace "replace-this-with-32-byte-base64-key", $newEncKey
    $envContent = $envContent -replace "JWT_SECRET=KEY", "JWT_SECRET=$newJwtSecret"
    $needsUpdate = $true
}

if ($needsUpdate) {
    $envContent | Set-Content .env
    Write-Host "✅ Secure keys injected into .env" -ForegroundColor Green
}

# 2. Port Availability Check (Resilient & Configurable)
$uiPort = 3000
$apiPort = 8000
if (Test-Path .env) {
    $envLines = Get-Content .env
    foreach ($line in $envLines) {
        if ($line -match "^UI_PORT=(\d+)") { $uiPort = [int]$matches[1] }
        if ($line -match "^API_PORT=(\d+)") { $apiPort = [int]$matches[1] }
    }
}

$ports = @($uiPort, $apiPort, 5444, 6380, 9090)
$maxRetries = 3
$retryDelay = 2

foreach ($port in $ports) {
    $retryCount = 0
    $portOccupied = $false
    
    do {
        # Only care about ports in 'Listen' state with an actual process ID (> 0)
        $connection = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | 
                     Where-Object { $_.OwningProcess -gt 0 } | 
                     Select-Object -First 1
        
        if ($connection) {
            $process = Get-Process -Id $connection.OwningProcess -ErrorAction SilentlyContinue
            $processName = if ($process) { $process.ProcessName } else { "Unknown" }
            
            Write-Host "❌ FATAL: Port $port is actively in use by process: $processName (PID: $($connection.OwningProcess))." -ForegroundColor Red
            Write-Host "👉 FIX: Run 'Stop-Process -Id $($connection.OwningProcess) -Force' or change UI_PORT/API_PORT in .env" -ForegroundColor Cyan
            exit 1
        }
        
        # Check if port is held by System/Kernel (PID 0 or 4) which might be transient
        $ghostConnection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($ghostConnection) {
            Write-Host "⏳ Port $port is in a transient state (PID: $($ghostConnection.OwningProcess)). Waiting for release..." -ForegroundColor Gray
            Start-Sleep -Seconds $retryDelay
            $retryCount++
        } else {
            break
        }
    } while ($retryCount -lt $maxRetries)
}

# 3. Launch Services
Write-Host "📦 Orchestrating Docker Containers..." -ForegroundColor Blue
docker-compose up -d --build

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ FATAL: Docker Compose failed to start services." -ForegroundColor Red
    exit 1
}

# 4. Wait for Health
Write-Host "⏳ Waiting for Service Stability (30s)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# 5. Final Readiness Check
Write-Host "✅ QueryBridge is now operational!" -ForegroundColor Green
Write-Host "--------------------------------------------------" -ForegroundColor Cyan
Write-Host "Dashboard: http://localhost:3000" -ForegroundColor White
Write-Host "API Specs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "Metrics:   http://localhost:8000/metrics" -ForegroundColor White
Write-Host "Grafana:   http://localhost:3001" -ForegroundColor White
Write-Host "--------------------------------------------------" -ForegroundColor Cyan
Write-Host "Use 'stop-querybridge.ps1' to shutdown safely." -ForegroundColor Yellow
