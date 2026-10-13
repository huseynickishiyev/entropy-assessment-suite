from pathlib import Path
import py_compile
import shutil
from datetime import datetime

root = Path.cwd()
gui = root / 'app' / 'gui.py'
readme = root / 'README.md'
if not gui.exists() or not readme.exists():
    raise SystemExit('Run from ip4_desktop directory.')
backup_dir = root / '.cleanup_backup' / datetime.now().strftime('%Y%m%d_%H%M%S')
backup_dir.mkdir(parents=True)
for src in (gui, readme):
    shutil.copy2(src, backup_dir / src.name)

source = gui.read_text(encoding='utf-8')
replacements = {
    "NIST reference + research health engine": "",
    "Research cutoffs — NOT NIST certified": "Health test parameters",
    "RCT + APT (research C engine)": "RCT + APT",
    "IP4 cross-platform Qt desktop interface.": "Desktop interface for entropy assessment.",
}
for old, new in replacements.items():
    source = source.replace(old, new)
# Remove subtitle widget only if it contains no other meaningful text.
# Exact subtitle line variant from v1.2 / subsequent edits.
source = '\n'.join(line for line in source.split('\n') if not ("vertical.addWidget(QLabel(" in line and "TÜBİTAK 1001" in line and ("124F362  |  " in line or "124F362  |" in line)))
compile(source, str(gui), 'exec')
gui.write_text(source, encoding='utf-8')

readme_text = '''# Entropy & Health Assessment

Desktop application for batch evaluation of entropy-source samples. The application runs NIST SP 800-90B IID and non-IID assessment executables and a separate C implementation of RCT/APT diagnostics.

## Current capabilities

- Load up to 200 `.bin` files per batch.
- Read 1-, 4-, and 8-bit symbols, stored as one byte per symbol or MSB-first packed data.
- Execute IID and non-IID NIST assessments and store complete output logs.
- Run the C RCT/APT diagnostics with configurable thresholds.
- Export per-file results and run settings as CSV and JSON.
- Keep SHA-256 hashes of the input files.

## macOS

```bash
./run_mac.sh
```

The launcher prepares the Python environment, checks native components and opens the Qt application. NIST source preparation may require Xcode Command Line Tools and Homebrew libraries on a developer machine.

## Linux

```bash
./run_linux.sh
```

## Windows

Run `run_windows.ps1` in a PowerShell environment with the required Python and C compiler tooling. Native NIST binaries must be available for Windows; automatic NIST preparation has not been verified on Windows.

## Using the application

1. Select `.bin` files and set the symbol width, storage format and number of samples.
2. Choose IID, non-IID and/or health tests.
3. Check the paths of the native test executables.
4. Run the batch and inspect individual outputs in the results panel.
5. Keep the generated results directory with the data provenance for reproducibility.

Input files are checked and converted to one-byte-per-symbol temporary data as required. They are not modified. For a batch, all files must share the selected width, encoding and sample count.

## Reproducible test data

```bash
python3 scripts/generate.py --out datasets/b1 --bits 1 --samples 1000000 --repeats 10
python3 scripts/generate.py --out datasets/b4 --bits 4 --samples 1000000 --repeats 10
python3 scripts/generate.py --out datasets/b8 --bits 8 --samples 1000000 --repeats 10
```

The generator is for deterministic experiments, not cryptographic random-number generation.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## Scope and limitations

An execution status of `ok` means the process completed, not that an IID assumption or entropy-source validation passed. Inspect NIST's statistical decisions separately. The C health thresholds are configurable research parameters and have not been validated as NIST SP 800-90B health-test cutoffs. Restart analysis, conditioning assessment, novel estimators, correlation-based selection and full cross-platform end-to-end verification remain outside this version. No NIST certification is claimed.

A release intended for users must bundle and validate platform-specific NIST executables and dependencies. Current launchers are developer entry points, not signed installers.
'''
readme.write_text(readme_text, encoding='utf-8')
ignore = root / '.gitignore'
with ignore.open('a', encoding='utf-8') as f:
    f.write('\n# Local setup and generated artifacts\n.cleanup_backup/\n*.bak\n*.log\n.env\n.env.*\nresults_*/\n')
print('Updated:', gui, readme, ignore)
print('Backup:', backup_dir)
