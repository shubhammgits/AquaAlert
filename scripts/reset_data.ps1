$ErrorActionPreference = 'Continue'

Write-Host 'Stopping server on port 8000 (if running)...'
try {
  $conn = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction Stop | Select-Object -First 1
  if ($conn -and $conn.OwningProcess) {
    Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 400
  }
} catch {}

Write-Host 'Deleting generated images and QR codes...'
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue "backend\static\images\*"
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue "backend\static\qr\*"

Write-Host 'Done. Start the server again with:'
Write-Host '  Set-Location ''C:\Users\shubh\Desktop\aquaalert''; .\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000'
Write-Host ''
Write-Host 'If you want to clear MongoDB too, drop the collections in your database (users, reports, validations, counters).'
