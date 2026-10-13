# Entropy & Health Assessment

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
