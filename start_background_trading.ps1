# Elliott Wave Persistent Trading - PowerShell Background Job
# This script runs the trading system as a background job

Write-Host "========================================" -ForegroundColor Green
Write-Host "Elliott Wave Persistent Trading Setup" -ForegroundColor Green  
Write-Host "========================================" -ForegroundColor Green

# Change to trading directory
Set-Location "C:\Users\Administrator\Documents\Elliott-Wave-VPS-Trader"

# Define the script block for background execution
$tradingScript = {
    Set-Location "C:\Users\Administrator\Documents\Elliott-Wave-VPS-Trader"
    & "venv\Scripts\activate"
    python start_multi_asset_trading.py
}

# Start as background job
$job = Start-Job -ScriptBlock $tradingScript -Name "ElliottWaveTrading"

Write-Host "✅ Elliott Wave Trading started as background job!" -ForegroundColor Green
Write-Host "Job ID: $($job.Id)" -ForegroundColor Yellow
Write-Host ""
Write-Host "📋 Management Commands:" -ForegroundColor Cyan
Write-Host "  Check Status: Get-Job -Name 'ElliottWaveTrading'" -ForegroundColor White
Write-Host "  View Output:  Receive-Job -Name 'ElliottWaveTrading'" -ForegroundColor White  
Write-Host "  Stop Trading: Stop-Job -Name 'ElliottWaveTrading'" -ForegroundColor White
Write-Host "  Remove Job:   Remove-Job -Name 'ElliottWaveTrading'" -ForegroundColor White
Write-Host ""
Write-Host "🌊 Trading will continue even if you disconnect!" -ForegroundColor Green

# Show current status
Get-Job -Name "ElliottWaveTrading"