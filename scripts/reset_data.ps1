$ErrorActionPreference = 'Continue'

Write-Host 'Stopping server on port 8000 (if running)...'
try {
  $conn = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction Stop | Select-Object -First 1
  if ($conn -and $conn.OwningProcess) {
    Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 400
  }
} catch {}

Write-Host 'Deleting SQLite DB and static uploads...'
Remove-Item -Force -ErrorAction SilentlyContinue "backend\aquaalert.db"
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue "backend\static\images\*"
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue "backend\static\qr\*"

Write-Host 'Done. Start the server again with:'
Write-Host '  uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000'
