# ==================================================
# QUERYBRIDGE ENTERPRISE - SHUTDOWN ORCHESTRATOR
# ==================================================

Write-Host "🛑 Initiating Graceful Shutdown..." -ForegroundColor Yellow

docker-compose down

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ QueryBridge services stopped successfully." -ForegroundColor Green
    Write-Host "Metadata and backups have been preserved in volumes." -ForegroundColor Cyan
} else {
    Write-Host "❌ Error occurred during shutdown." -ForegroundColor Red
}
