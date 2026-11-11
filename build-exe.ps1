param([switch]$SkipSetup)

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not $SkipSetup) {
    & (Join-Path $PSScriptRoot 'setup.ps1')
    if (-not $?) { throw 'Setup failed.' }
}
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Run setup.ps1 first.' }
& $python start.py --check
if ($LASTEXITCODE -ne 0) { throw 'Build prerequisites are missing. Run setup.ps1.' }
& $python -m pip --require-virtualenv install --cache-dir (Join-Path $PSScriptRoot '.tools\cache\pip') -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw 'Could not install the EXE build tools. Check internet access.' }
& $python -m PyInstaller --noconfirm --clean --distpath dist --workpath work\pyinstaller WordNest.spec
if ($LASTEXITCODE -ne 0) { throw 'EXE build failed.' }
# Run the actual packaged server with isolated data before declaring success.
$smokeRoot = Join-Path $PSScriptRoot ('work\exe-smoke-' + [guid]::NewGuid().ToString('N'))
$previousData = $env:WORDNEST_DATA
$env:WORDNEST_DATA = Join-Path $smokeRoot 'data'
try {
    $process = Start-Process -FilePath (Join-Path $PSScriptRoot 'dist\WordNest.exe') -ArgumentList '--smoke-test' -WindowStyle Hidden -PassThru
    if (-not $process.WaitForExit(60000)) { $process.Kill(); throw 'EXE smoke test timed out.' }
    if ($process.ExitCode -ne 0) { throw "EXE smoke test failed. See $smokeRoot\data\wordnest.log" }
} finally { $env:WORDNEST_DATA = $previousData }
Write-Host 'Ready: dist\WordNest.exe. Share only that file; the recipient needs no Python, Node.js or npm.'
