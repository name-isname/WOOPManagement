# Dev helper: start backend (uvicorn via uv) and frontend (Vite) on Windows PowerShell
# Usage:
#   - Double-click dev.ps1 (if allowed) or run in PowerShell:  ./dev.ps1
#   - Optional: set execution policy for current user once:  Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

$ErrorActionPreference = 'Stop'

# Resolve folders
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $Root 'backend'
$FrontDir   = Join-Path $Root 'my-front'

# Simple TCP probe (PS5.1 friendly)
function Test-Port($HostName, $Port){
  try {
    $tcp = New-Object System.Net.Sockets.TcpClient
    $iar = $tcp.BeginConnect($HostName, [int]$Port, $null, $null)
    $ok  = $iar.AsyncWaitHandle.WaitOne(500)
    if($ok){ $tcp.EndConnect($iar) }
    $tcp.Close()
    return [bool]$ok
  } catch { return $false }
}

function Wait-Health($Url, $TimeoutSec){
  $sw = [Diagnostics.Stopwatch]::StartNew()
  while($sw.Elapsed.TotalSeconds -lt $TimeoutSec){
    try { $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3; if($r.StatusCode -ge 200 -and $r.StatusCode -lt 300){ return $true } } catch {}
    Start-Sleep -Milliseconds 600
  }
  return $false
}

Write-Host "Starting backend (127.0.0.1:8000) and frontend (5173)..." -ForegroundColor Cyan

# 1) Start backend if not listening
if(-not (Test-Port 127.0.0.1 8000)){
  if(-not (Test-Path $BackendDir)){ throw "Backend folder not found: $BackendDir" }

  # Prefer uv to manage env, but run uvicorn module explicitly
  $uvCmd = "cd `"$BackendDir`"; uv run --python 3.12 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"
  # Fallback to direct Python if uv is missing or fails
  $fallbackCmd = "cd `"$BackendDir`"; python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"

  $hasUv = $false
  try { $null = Get-Command uv -ErrorAction Stop; $hasUv = $true } catch { $hasUv = $false }

  if($hasUv){
    Write-Host "Starting backend via uv (uvicorn module)..." -ForegroundColor DarkGray
    Start-Process -FilePath powershell.exe -ArgumentList '-NoProfile','-Command', $uvCmd -WindowStyle Minimized | Out-Null
    Start-Sleep -Seconds 2
    # If port still not open shortly after, fallback
    if(-not (Test-Port 127.0.0.1 8000)){
      Write-Host "uv start did not open port, falling back to 'python -m uvicorn'" -ForegroundColor Yellow
      Start-Process -FilePath powershell.exe -ArgumentList '-NoProfile','-Command', $fallbackCmd -WindowStyle Minimized | Out-Null
    }
  } else {
    Write-Host "uv not found, fallback to 'python -m uvicorn'" -ForegroundColor Yellow
    Start-Process -FilePath powershell.exe -ArgumentList '-NoProfile','-Command', $fallbackCmd -WindowStyle Minimized | Out-Null
  }
} else {
  Write-Host "Backend already listening on 8000" -ForegroundColor DarkGray
}

# Wait until health is OK (max ~20s). If still not OK, try fallback once more.
if(Wait-Health 'http://127.0.0.1:8000/health' 20){
  Write-Host 'Backend is up [OK]' -ForegroundColor Green
} else {
  Write-Host 'Backend is not responding on /health, attempting python fallback...' -ForegroundColor Yellow
  $fallbackCmd = "cd `"$BackendDir`"; python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"
  Start-Process -FilePath powershell.exe -ArgumentList '-NoProfile','-Command', $fallbackCmd -WindowStyle Minimized | Out-Null
  if(Wait-Health 'http://127.0.0.1:8000/health' 12){
    Write-Host 'Backend is up after fallback [OK]' -ForegroundColor Green
  } else {
    Write-Host 'Backend is not responding on /health (still continuing).' -ForegroundColor Yellow
  }
}

# 2) Start frontend (always ensure VITE_API_BASE)
if(-not (Test-Port 127.0.0.1 5173)){
  if(-not (Test-Path $FrontDir)){ throw "Frontend folder not found: $FrontDir" }
  $frontCmd = "$env:VITE_API_BASE='http://127.0.0.1:8000'; cd `"$FrontDir`"; npm run dev -- --port 5173 --strictPort"
  Start-Process -FilePath powershell.exe -ArgumentList '-NoProfile','-Command', $frontCmd -WindowStyle Minimized | Out-Null
} else {
  Write-Host "Frontend already listening on 5173" -ForegroundColor DarkGray
}

Start-Sleep -Seconds 2
try { Start-Process 'http://localhost:5173/' | Out-Null } catch {}

Write-Host 'All set. Frontend: http://localhost:5173  | Backend: http://127.0.0.1:8000' -ForegroundColor Cyan
