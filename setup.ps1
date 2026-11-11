param([string]$NpmCliPath)

# ASCII is intentional: this file also runs in Windows PowerShell 5.1.
$ErrorActionPreference = 'Stop'
$ProjectRoot = $PSScriptRoot
$ToolsRoot = Join-Path $ProjectRoot '.tools'
$VenvPython = Join-Path $ProjectRoot '.venv\Scripts\python.exe'

function Test-PythonRuntime([string]$Executable) {
    if (-not $Executable -or -not (Test-Path -LiteralPath $Executable -PathType Leaf)) { return $false }
    if ($Executable -like '*\WindowsApps\*') { return $false }
    try {
        & $Executable -I -c 'import sys, sqlite3, venv, ensurepip; sys.exit(0 if (3,12) <= sys.version_info[:2] < (3,14) else 1)' 2>$null | Out-Null
        return $LASTEXITCODE -eq 0
    } catch { return $false }
}

function Test-NodeRuntime([string]$Executable) {
    if (-not $Executable -or -not (Test-Path -LiteralPath $Executable -PathType Leaf)) { return $false }
    try {
        & $Executable -e 'const [major,minor]=process.versions.node.split(/[.]/).map(Number);process.exit(major>22||(major===22&&minor>=12)?0:1)' 2>$null | Out-Null
        return $LASTEXITCODE -eq 0
    } catch { return $false }
}

function Receive-SetupFile([string]$Url, [string]$Destination) {
    Write-Host "Downloading: $Url"
    try {
        Invoke-WebRequest -UseBasicParsing -Uri $Url -OutFile $Destination -TimeoutSec 120
    } catch {
        throw "Download failed: $Url. Check internet access and rerun setup.ps1. $($_.Exception.Message)"
    }
}

function Get-WindowsArchitecture {
    $architecture = $env:PROCESSOR_ARCHITEW6432
    if (-not $architecture) { $architecture = $env:PROCESSOR_ARCHITECTURE }
    switch ($architecture) {
        'AMD64' { return 'x64' }
        'ARM64' { return 'arm64' }
        'x86' { return 'x86' }
        default { throw "Unsupported Windows architecture: $architecture" }
    }
}

function Install-LocalPython {
    $architecture = Get-WindowsArchitecture
    $package = switch ($architecture) { 'x64' { 'python' } 'arm64' { 'pythonarm64' } 'x86' { 'pythonx86' } }
    # The CPython NuGet distribution is a full local runtime with venv/ensurepip.
    # It is extracted, without installing an MSI, modifying the registry or PATH.
    $version = '3.13.12'
    $destination = Join-Path $ToolsRoot "$package-$version"
    $executable = Join-Path $destination 'tools\python.exe'
    if (Test-PythonRuntime $executable) { return $executable }
    New-Item -ItemType Directory -Path $ToolsRoot -Force | Out-Null
    $staging = Join-Path $ToolsRoot ('download-python-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $staging | Out-Null
    $archive = Join-Path $staging 'python.zip'
    Receive-SetupFile "https://api.nuget.org/v3-flatcontainer/$package/$version/$package.$version.nupkg" $archive
    $expanded = Join-Path $staging 'expanded'
    Expand-Archive -LiteralPath $archive -DestinationPath $expanded
    $downloadedPython = Join-Path $expanded 'tools\python.exe'
    if (-not (Test-PythonRuntime $downloadedPython)) { throw 'Downloaded Python could not run. Check Windows compatibility and rerun setup.' }
    if (Test-Path -LiteralPath $destination) {
        # Preserve an incomplete installation instead of deleting user files.
        Move-Item -LiteralPath $destination -Destination ($destination + '.incomplete-' + [guid]::NewGuid().ToString('N'))
    }
    Move-Item -LiteralPath $expanded -Destination $destination
    return $executable
}

function Find-PythonRuntime {
    if (Test-PythonRuntime $VenvPython) { return $VenvPython }
    foreach ($package in @('python', 'pythonarm64', 'pythonx86')) {
        $candidate = Join-Path $ToolsRoot "$package-3.13.12\tools\python.exe"
        if (Test-PythonRuntime $candidate) { return $candidate }
    }
    foreach ($name in @('python.exe', 'python3.exe')) {
        $command = Get-Command $name -ErrorAction SilentlyContinue
        if ($command -and (Test-PythonRuntime $command.Source)) { return $command.Source }
    }
    $launcher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($launcher) {
        foreach ($version in @('-3.13', '-3.12')) {
            try {
                $candidate = & $launcher.Source $version -I -c 'import sys; print(sys.executable)' 2>$null
                if ($LASTEXITCODE -eq 0 -and $candidate -and (Test-PythonRuntime ([string]$candidate))) { return [string]$candidate }
            } catch { }
        }
    }
    Write-Host 'Compatible Python not found. Installing a local copy in .tools.'
    return Install-LocalPython
}

function Install-LocalNode {
    $architecture = Get-WindowsArchitecture
    New-Item -ItemType Directory -Path $ToolsRoot -Force | Out-Null
    $staging = Join-Path $ToolsRoot ('download-node-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $staging | Out-Null
    $manifest = Join-Path $staging 'SHASUMS256.txt'
    Receive-SetupFile 'https://nodejs.org/dist/latest-v22.x/SHASUMS256.txt' $manifest
    $pattern = '^([a-fA-F0-9]{64})\s+(node-v22\.[0-9]+\.[0-9]+-win-' + $architecture + '\.zip)$'
    $entry = @(Get-Content -LiteralPath $manifest | Where-Object { $_ -match $pattern })
    if ($entry.Count -ne 1 -or $entry[0] -notmatch $pattern) { throw 'Cannot find the Windows Node.js archive in the official manifest.' }
    $checksum = $Matches[1]
    $filename = $Matches[2]
    $archive = Join-Path $staging $filename
    Receive-SetupFile "https://nodejs.org/dist/latest-v22.x/$filename" $archive
    if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ne $checksum) { throw 'Node.js download checksum mismatch. Rerun setup.' }
    $expanded = Join-Path $staging 'expanded'
    Expand-Archive -LiteralPath $archive -DestinationPath $expanded
    $folderName = [IO.Path]::GetFileNameWithoutExtension($filename)
    $source = Join-Path $expanded $folderName
    $destination = Join-Path $ToolsRoot $folderName
    if (-not (Test-NodeRuntime (Join-Path $source 'node.exe')) -or -not (Test-Path (Join-Path $source 'node_modules\npm\bin\npm-cli.js'))) {
        throw 'Downloaded Node.js or npm could not be verified.'
    }
    if (Test-Path -LiteralPath $destination) {
        Move-Item -LiteralPath $destination -Destination ($destination + '.incomplete-' + [guid]::NewGuid().ToString('N'))
    }
    Move-Item -LiteralPath $source -Destination $destination
    return $destination
}

function Find-NodeTools([string]$ExplicitNpmCli) {
    if ($ExplicitNpmCli -and -not (Test-Path -LiteralPath $ExplicitNpmCli -PathType Leaf)) { throw 'NpmCliPath must point to npm-cli.js.' }
    $folders = @()
    if (Test-Path -LiteralPath $ToolsRoot) {
        $folders += @(Get-ChildItem -LiteralPath $ToolsRoot -Directory -Filter 'node-v*-win-*' | Sort-Object LastWriteTime -Descending | ForEach-Object { $_.FullName })
    }
    $command = Get-Command node.exe -ErrorAction SilentlyContinue
    if ($command) { $folders += Split-Path $command.Source }
    $folders += @(
        (Join-Path $env:ProgramFiles 'nodejs'),
        (Join-Path $env:LOCALAPPDATA 'Programs\nodejs'),
        (Join-Path $env:LOCALAPPDATA 'qwen-code\qwen-code\node')
    )
    foreach ($folder in $folders) {
        $executable = Join-Path $folder 'node.exe'
        $cli = if ($ExplicitNpmCli) { (Resolve-Path -LiteralPath $ExplicitNpmCli).Path } else { Join-Path $folder 'node_modules\npm\bin\npm-cli.js' }
        if ((Test-NodeRuntime $executable) -and (Test-Path -LiteralPath $cli -PathType Leaf)) {
            return @{ Node = $executable; Npm = $cli }
        }
    }
    Write-Host 'Compatible Node.js with npm not found. Installing a local copy in .tools.'
    $folder = Install-LocalNode
    $cli = if ($ExplicitNpmCli) { (Resolve-Path -LiteralPath $ExplicitNpmCli).Path } else { Join-Path $folder 'node_modules\npm\bin\npm-cli.js' }
    return @{ Node = (Join-Path $folder 'node.exe'); Npm = $cli }
}

function Invoke-WordNestSetup {
    Set-Location -LiteralPath $ProjectRoot
    [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
    New-Item -ItemType Directory -Path $ToolsRoot -Force | Out-Null
    $python = Find-PythonRuntime
    if ($python -ne $VenvPython) {
        if (Test-Path -LiteralPath (Join-Path $ProjectRoot '.venv')) {
            $oldEnvironment = Join-Path $ProjectRoot ('.venv.incomplete-' + [guid]::NewGuid().ToString('N'))
            Move-Item -LiteralPath (Join-Path $ProjectRoot '.venv') -Destination $oldEnvironment
            Write-Host "Preserved incompatible environment: $oldEnvironment"
        }
        Write-Host 'Creating .venv...'
        & $python -I -m venv (Join-Path $ProjectRoot '.venv')
        if ($LASTEXITCODE -ne 0) { throw 'Cannot create Python environment. Rerun setup.' }
    }
    & $VenvPython -I -c 'import sys; sys.exit(0 if sys.prefix != sys.base_prefix else 1)'
    if ($LASTEXITCODE -ne 0) { throw 'Refusing to install packages outside a virtual environment.' }
    & $VenvPython -I -m ensurepip --upgrade
    if ($LASTEXITCODE -ne 0) { throw 'Cannot prepare pip inside .venv.' }
    Write-Host 'Installing Python dependencies in .venv...'
    & $VenvPython -I -m pip --isolated --require-virtualenv install --cache-dir (Join-Path $ToolsRoot 'cache\pip') -r (Join-Path $ProjectRoot 'requirements.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed. Check internet access and rerun setup.' }
    $nodeTools = Find-NodeTools $NpmCliPath
    # PATH changes affect this process only, so npm build scripts can find node.
    $previousPath = $env:PATH
    $previousNodeEnv = $env:NODE_ENV
    $env:PATH = (Split-Path $nodeTools.Node) + ';' + $env:PATH
    $env:NODE_ENV = 'development'
    Push-Location -LiteralPath (Join-Path $ProjectRoot 'frontend')
    try {
        $installCommand = if (Test-Path -LiteralPath 'package-lock.json') { 'ci' } else { 'install' }
        Write-Host 'Installing frontend dependencies in frontend/node_modules...'
        & $nodeTools.Node $nodeTools.Npm $installCommand --include=dev --cache (Join-Path $ToolsRoot 'cache\npm') --no-audit --no-fund
        if ($LASTEXITCODE -ne 0) { throw 'npm installation failed. Check registry.npmjs.org access and rerun setup.' }
        & $nodeTools.Node $nodeTools.Npm run build
        if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed. Read the error above.' }
    } finally {
        Pop-Location
        $env:PATH = $previousPath
        $env:NODE_ENV = $previousNodeEnv
    }
    & $VenvPython (Join-Path $ProjectRoot 'start.py') --check
    if ($LASTEXITCODE -ne 0) { throw 'Installation verification failed.' }
    Write-Host 'Ready. Double-click start.cmd or run: .\.venv\Scripts\python.exe start.py'
}

# Dot-sourcing loads functions for offline tests without installing anything.
if ($MyInvocation.InvocationName -ne '.') { Invoke-WordNestSetup }
