$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Resolve-Path (Join-Path $scriptDir "..")
Set-Location $root

$venv = Join-Path $root ".venv"
if (!(Test-Path $venv)) {
  Write-Host "Creating virtualenv..."
  python -m venv $venv
}

$python = Join-Path $venv "Scripts\python.exe"
& $python -m pip install --upgrade pip
& $python -m pip install -r requirements.txt

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
  Write-Warning "ffmpeg not found. Audio utilities may fail."
  Write-Host "Install hints:"
  Write-Host "  winget install -e --id Gyan.FFmpeg"
  Write-Host "  choco install ffmpeg"
}

$ollamaUrl = "http://localhost:11434/api/tags"
function Test-Ollama {
  try {
    Invoke-RestMethod -Uri $ollamaUrl -TimeoutSec 2 | Out-Null
    return $true
  } catch {
    return $false
  }
}

if (-not (Test-Ollama)) {
  if (Get-Command ollama -ErrorAction SilentlyContinue) {
    Write-Host "Starting ollama serve..."
    Start-Process ollama "serve" -NoNewWindow
    Start-Sleep -Seconds 2
  } else {
    Write-Warning "Ollama not found. Install from https://ollama.com"
  }
}

if (Test-Ollama) {
  $tags = Invoke-RestMethod -Uri $ollamaUrl -TimeoutSec 3
  $names = @()
  if ($tags -and $tags.models) { $names = $tags.models | ForEach-Object { $_.name } }
  if ($names -notcontains "tinyllama:chat") {
    Write-Host "Pulling tinyllama:chat model..."
    & ollama pull tinyllama:chat
  }
} else {
  Write-Warning "Ollama server not reachable. Start with: ollama serve"
}

$whisperDir = Join-Path $root "models\whisper"
$hasWhisper = $false
if (Test-Path $whisperDir) {
  $files = Get-ChildItem -Path $whisperDir -Recurse -File -ErrorAction SilentlyContinue
  if ($files) { $hasWhisper = $true }
}
if (-not $hasWhisper) {
  Write-Host "Downloading faster-whisper model (small.en)..."
  & $python scripts\download_whisper_model.py --model small.en --output models\whisper
}

& $python app.py
