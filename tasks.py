"""Gate runner used locally (Windows) and in CI (Linux). Standard library only.

Commands: tools-check, build-sim, sim, py, verify, evidence --task <id>
"""

import argparse
import ast
import datetime
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WINDOWS = sys.platform == "win32"
BUILD = ROOT / "build"
THIRD_PARTY = {"pydantic", "pytest", "mcp", "verifieds"}
LOG = None

if WINDOWS:
    import os

    if not shutil.which("g++"):
        winget_pkg = Path(
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages")
        )
        for candidate in winget_pkg.glob("*WinLibs*/mingw64/bin"):
            if (candidate / "g++.exe").exists():
                os.environ["PATH"] = (
                    str(candidate) + os.path.pathsep + os.environ.get("PATH", "")
                )
                break


def emit(text):
    print(text, flush=True)
    if LOG is not None:
        LOG.write(text + "\n")
        LOG.flush()


def find_tool(name):
    found = shutil.which(name)
    if found:
        return found
    if WINDOWS and name == "cppcheck":
        for base in (r"C:\Program Files", r"C:\Program Files (x86)"):
            candidate = Path(base) / "Cppcheck" / "cppcheck.exe"
            if candidate.exists():
                return str(candidate)
    return None


def run(cmd):
    cmd = [str(part) for part in cmd]
    emit("$ " + " ".join(cmd))
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError as err:
        emit(f"cannot start {cmd[0]}: {err}")
        return 127
    assert proc.stdout is not None
    for line in proc.stdout:
        emit(line.rstrip("\n"))
    return proc.wait()


def python_m(*args):
    return [sys.executable, "-m", *args]


def tools_check():
    status = 0
    for name in ("cmake", "g++", "cppcheck"):
        path = find_tool(name)
        if path is None:
            emit(f"MISSING: {name}")
            status = 1
            continue
        code = run([path, "--version"])
        status = status or code
    emit(f"python {sys.version.split()[0]} on {sys.platform}")
    for module in ("ruff", "mypy", "vulture", "pytest"):
        status = status or run(python_m(module, "--version"))
    return status


def build_sim():
    cmake = find_tool("cmake")
    if cmake is None:
        emit("MISSING: cmake")
        return 1
    shutil.rmtree(BUILD, ignore_errors=True)
    sanitizers = "OFF" if WINDOWS else "ON"
    configure = [cmake]
    if WINDOWS:
        configure += ["-G", "MinGW Makefiles"]
    configure += ["-S", "sim", "-B", "build", "-DCMAKE_BUILD_TYPE=Debug"]
    configure.append(f"-DENABLE_SANITIZERS={sanitizers}")
    code = run(configure)
    return code or run([cmake, "--build", "build"])


def sim():
    status = build_sim()
    ctest = find_tool("ctest")
    cppcheck = find_tool("cppcheck")
    if ctest is None or cppcheck is None:
        emit("MISSING: ctest or cppcheck")
        return 1
    status = status or run([ctest, "--test-dir", "build", "--output-on-failure"])
    files = sorted((ROOT / "sim").glob("src/*.[hc]pp")) + sorted(
        (ROOT / "sim").glob("tests/*.cpp")
    )
    rel = [p.relative_to(ROOT).as_posix() for p in files]
    status = status or run(
        [cppcheck, "--enable=warning,style,unusedFunction", "--std=c++20"]
        + ["--error-exitcode=1", "--inline-suppr", "-I", "sim/src"]
        + ["--suppress=missingIncludeSystem", *rel]
    )
    return status


def check_imports():
    # Allowed imports for core modules, stdlib, third-party deps,
    # and Q0 test reference scheduler
    local = {p.stem for p in (ROOT / "tests").glob("*.py")} | {"tests"}
    allowed = set(sys.stdlib_module_names) | THIRD_PARTY | local
    bad = []
    for folder in ("verifieds", "tests"):
        for path in sorted((ROOT / folder).rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    names = [node.module or ""]
                else:
                    continue
                for name in names:
                    if name.split(".")[0] not in allowed:
                        bad.append(f"{path.relative_to(ROOT)}: {name}")
    for item in bad:
        emit(f"DISALLOWED IMPORT: {item}")
    return 1 if bad else 0


def py():
    steps = [
        ("ruff-check", lambda: run(python_m("ruff", "check", "."))),
        ("ruff-format", lambda: run(python_m("ruff", "format", "--check", "."))),
        ("mypy", lambda: run(python_m("mypy", "--strict", "verifieds"))),
        (
            "vulture",
            lambda: run(python_m("vulture", "verifieds", "--min-confidence=80")),
        ),
        ("schemas", lambda: run(python_m("verifieds.schemas.export", "--check"))),
        ("imports", check_imports),
        ("pytest", lambda: run(python_m("pytest"))),
    ]
    return run_steps(steps)


def run_steps(steps):
    results = []
    for name, step in steps:
        code = step()
        results.append((name, code))
        emit(f"STEP {name}: {'PASS' if code == 0 else 'FAIL'}")
    return 0 if all(code == 0 for _, code in results) else 1


def verify():
    return run_steps([("sim", sim), ("py", py)])


def git_output(*args):
    out = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    return out.stdout.strip()


def evidence(task):
    global LOG
    sha = git_output("rev-parse", "HEAD")
    dirty = git_output(
        "status", "--porcelain", "--", ".", ":(exclude).agent/state/evidence"
    )
    folder = ROOT / ".agent" / "state" / "evidence"
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    with (folder / f"{task}.log").open("w", encoding="utf-8", newline="\n") as fh:
        LOG = fh
        emit(f"task={task}")
        emit(f"sha={sha}")
        emit(f"date={stamp}")
        emit(f"platform={sys.platform}")
        emit(f"dirty={len(dirty.splitlines())}")
        code = tools_check() or verify()
        emit(f"exit={code}")
        LOG = None
    return code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=["tools-check", "build-sim", "sim", "py", "verify", "evidence"],
    )
    parser.add_argument("--task", default="manual")
    args = parser.parse_args()
    if args.command == "evidence":
        return evidence(args.task)
    table = {
        "tools-check": tools_check,
        "build-sim": build_sim,
        "sim": sim,
        "py": py,
        "verify": verify,
    }
    return table[args.command]()


if __name__ == "__main__":
    sys.exit(main())
