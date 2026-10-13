$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path .venv)) { py -3 -m venv .venv; if ($LASTEXITCODE -ne 0) { throw 'Python venv creation failed' } }
$Python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
& $Python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
# Requires an installed C compiler: MSVC cl.exe (Developer PowerShell) or GCC on PATH.
if (Get-Command cl.exe -ErrorAction SilentlyContinue) {
    & cl.exe /nologo /O2 /W4 /Fe:engine\ip4_health.exe engine\health.c
} elseif (Get-Command gcc.exe -ErrorAction SilentlyContinue) {
    & gcc.exe -O2 -std=c11 -Wall -Wextra engine\health.c -lm -o engine\ip4_health.exe
} else { throw 'Install Visual Studio Build Tools (C++) or GCC and add it to PATH' }
if ($LASTEXITCODE -ne 0) { throw 'C engine compilation failed' }
& $Python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Tests failed' }
& $Python app\gui.py
if ($LASTEXITCODE -ne 0) { throw 'GUI exited with an error' }
