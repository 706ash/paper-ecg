param(
  [string]$OneFileTarget = "target_onefile"
)

$ErrorActionPreference = "Stop"

function Require-File([string]$Path, [string]$Hint) {
  if (-not (Test-Path -LiteralPath $Path)) {
    Write-Error "Missing: $Path`n$Hint"
    exit 1
  }
}

# Run from repo root (paper-ecg/)
$repoRoot = (Get-Location).Path

# fbs on Windows (PyInstaller) needs the VC++ 2012 x64 runtime DLL present.
if (-not (Test-Path -LiteralPath "C:\Windows\System32\msvcr110.dll")) {
  Write-Error "Missing C:\Windows\System32\msvcr110.dll (VC++ 2012 x64 runtime). Install 'Visual C++ Redistributable for Visual Studio 2012 Update 4 (x64)', then rerun."
  exit 1
}

# Windows 10/11 store the UCRT downlevel DLLs in this directory; fbs looks for them on PATH.
$ucrtDownlevel = "C:\Windows\System32\downlevel"
if (Test-Path -LiteralPath $ucrtDownlevel) {
  if ($env:PATH -notlike "*$ucrtDownlevel*") {
    $env:PATH = "$ucrtDownlevel;$env:PATH"
  }
}

$python = Join-Path $repoRoot ".env\Scripts\python.exe"
$fbs    = Join-Path $repoRoot ".env\Scripts\fbs.exe"

Require-File $python "Activate your venv or create it: `py -3.6 -m venv .env` then `pip install -r requirements.txt`."
Require-File $fbs    "Install fbs into the venv: `.env\\Scripts\\python -m pip install fbs==0.9.0`."

# Step 1: run the normal freeze once. This generates fbs' runtime hook under target/PyInstaller/.
& $fbs freeze

$runtimeHook = Join-Path $repoRoot "target\PyInstaller\fbs_pyinstaller_hook.py"
Require-File $runtimeHook "fbs freeze should have created this file. If it didn't, check the freeze output for earlier errors."

$pyinstaller = Join-Path $repoRoot ".env\Scripts\pyinstaller.exe"
Require-File $pyinstaller "PyInstaller should be installed as part of fbs. Try: `.env\\Scripts\\python -m pip install pyinstaller`."

$iconPath = Join-Path $repoRoot "src\main\icons\Icon.ico"
$mainPy   = Join-Path $repoRoot "src\main\python\Main.py"
$hooksDir = Join-Path $repoRoot ".env\Lib\site-packages\fbs\freeze\hooks"

Require-File $iconPath "Missing app icon."
Require-File $mainPy "Missing main entrypoint."
Require-File $hooksDir "fbs hooks dir not found; ensure fbs is installed in this venv."

$distPath = Join-Path $repoRoot $OneFileTarget
$specPath = Join-Path $distPath "PyInstaller"
$workPath = $specPath

New-Item -ItemType Directory -Force -Path $distPath | Out-Null
New-Item -ItemType Directory -Force -Path $specPath | Out-Null

# Step 2: build a single-file exe. This reuses the fbs runtime hook so resources/plugins are found at runtime.
& $pyinstaller `
  --name "Paper ECG" `
  --onefile `
  --noupx `
  --log-level ERROR `
  --noconfirm `
  --windowed `
  --icon $iconPath `
  --distpath $distPath `
  --specpath $specPath `
  --workpath $workPath `
  --additional-hooks-dir $hooksDir `
  --runtime-hook $runtimeHook `
  $mainPy

Write-Host "Built onefile exe at: $(Join-Path $distPath 'Paper ECG.exe')"
