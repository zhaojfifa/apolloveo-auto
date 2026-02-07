$files = Get-ChildItem -Recurse -Filter "main.py" -Path "gateway" | Select-Object -ExpandProperty FullName
Write-Host "main.py files found:"
$files | ForEach-Object { Write-Host " - $_" }

if ($files.Count -gt 2) {
  Write-Error "Too many main.py entrypoints under gateway/. Keep only gateway/main.py and gateway/app/main.py (wrapper)."
  exit 1
}

$wrapper = "gateway\\main.py"
if (Test-Path $wrapper) {
  $content = Get-Content $wrapper -Raw
  if ($content -match "FastAPI\\(") {
    Write-Error "gateway/main.py must be a wrapper only (no FastAPI construction)."
    exit 1
  }
  if ($content -notmatch "from\\s+gateway\\.app\\.main\\s+import\\s+app") {
    Write-Error "gateway/main.py must re-export: from gateway.app.main import app"
    exit 1
  }
}

Write-Host "OK: entrypoint contract satisfied."
