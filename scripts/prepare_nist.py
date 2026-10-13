#!/usr/bin/env python3
"""Find and prepare upstream SP800-90B entropy assessment, without patching it."""
import argparse
import glob
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
NAME = 'SP800-90B_EntropyAssessment'
REPO = 'https://github.com/usnistgov/SP800-90B_EntropyAssessment.git'


def run(cmd, **kwargs):
    print('> ' + ' '.join(map(str, cmd)), flush=True)
    subprocess.run(list(map(str, cmd)), check=True, **kwargs)


def locate():
    hints = [os.environ.get('IP4_NIST_DIR'), ROOT.parent / NAME, Path.home() / 'Desktop' / NAME,
             ROOT / 'vendor' / NAME]
    for hint in hints:
        if not hint: continue
        p = Path(hint).expanduser()
        cpp = p if p.name == 'cpp' else p / 'cpp'
        if (cpp / 'Makefile').exists(): return cpp.resolve()
    return None


def brew_prefix(formula):
    p = subprocess.run(['brew', '--prefix', formula], capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else ''




def prepare_macos(cpp, install_deps):
    import os

    compiler = subprocess.check_output(
        ["xcrun", "--find", "clang++"],
        text=True
    ).strip()

    sdk = subprocess.check_output(
        ["xcrun", "--sdk", "macosx", "--show-sdk-path"],
        text=True
    ).strip()

    formulas = [
        "jsoncpp",
        "openssl@3",
        "bzip2",
        "libdivsufsort",
        "libomp",
    ]

    prefixes = {}

    for formula in formulas:
        prefix = Path(brew_prefix(formula))

        if not prefix.exists():
            if not install_deps:
                raise RuntimeError(
                    f"Missing dependency: {formula}"
                )

            run(["brew", "install", formula])

        prefixes[formula] = Path(brew_prefix(formula))

    includes = [
        "-I" + str(prefixes[f] / "include")
        for f in formulas
    ]

    includes.append(
        "-I" + str(
            prefixes["jsoncpp"] / "include" / "jsoncpp"
        )
    )

    libdirs = [
        str(prefixes[f] / "lib")
        for f in formulas
    ]

    flags = " ".join([
        "-std=c++11",
        "-O2",
        "-Xpreprocessor -fopenmp",
        "-isysroot " + sdk,
        *includes,
    ])

    libflags = " ".join(
        ["-L" + d for d in libdirs]
        + ["-Wl,-rpath," + d for d in libdirs]
    )

    libflags += (
        " -lbz2 -lpthread"
        " -ldivsufsort -ldivsufsort64"
    )

    print("Using Apple Clang:", compiler, flush=True)
    print("Using SDK:", sdk, flush=True)

    # Remove incomplete build products.
    for name in ("ea_iid", "ea_non_iid"):
        target = Path(cpp) / name

        if target.exists():
            target.unlink()

    for target in ("iid", "non_iid"):
        print("Building NIST:", target, flush=True)

        run([
            "make",
            "ARCH=arm",
            "CXX=" + compiler,
            "CXXFLAGS=" + flags,
            "LIB=" + libflags,
            "SHARED_LIB=-ljsoncpp -lcrypto -lomp",
            target,
        ], cwd=cpp)

    for name in ("ea_iid", "ea_non_iid"):
        executable = Path(cpp) / name

        if not executable.is_file():
            raise RuntimeError(
                f"NIST executable was not created: {name}"
            )

        print("Built:", executable, flush=True)

    print("NIST setup completed successfully.", flush=True)

def prepare_linux(cpp):
    if not shutil.which('g++') or not shutil.which('make'):
        raise RuntimeError('Linux compilation needs make, g++, libjsoncpp-dev, libssl-dev, libbz2-dev, libdivsufsort-dev, libgomp1.')
    for target in ('iid','non_iid'):
        run(['make','ARCH=arm',target],cwd=cpp)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--install-deps', action='store_true', help='Automatically install missing Homebrew libraries on macOS')
    args=p.parse_args()
    cpp=locate()
    if cpp is None:
        dest=ROOT/'vendor'/NAME
        if not shutil.which('git'): raise RuntimeError('Git is needed for first-time NIST download')
        dest.parent.mkdir(parents=True,exist_ok=True)
        run(['git','clone','--depth','1',REPO,dest])
        cpp=dest/'cpp'
    ext='.exe' if os.name=='nt' else ''
    if all((cpp/(n+ext)).is_file() for n in ('ea_iid','ea_non_iid')):
        print('NIST executables found; no rebuild needed: '+str(cpp))
    elif sys.platform == 'darwin': prepare_macos(cpp,args.install_deps)
    elif sys.platform.startswith('linux'): prepare_linux(cpp)
    else:
        raise RuntimeError('Windows release must bundle prebuilt NIST binaries. Upstream POSIX build cannot be assumed to compile with MSVC; prepare them in release CI.')
    for n in ('ea_iid','ea_non_iid'):
        exe=cpp/(n+ext)
        if not exe.is_file(): raise RuntimeError('Build finished without expected executable: '+str(exe))
    config=ROOT/'.nist_location'
    config.write_text(str(cpp.resolve()),encoding='utf-8')
    print('Ready: '+str(cpp))

if __name__=='__main__':
    try: main()
    except (RuntimeError,subprocess.CalledProcessError) as exc:
        print('NIST setup failed: '+str(exc),file=sys.stderr)
        sys.exit(1)
