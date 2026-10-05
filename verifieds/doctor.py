import json
import os
import shutil
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any

from verifieds.proposer.client import OllamaConfig


if sys.platform == "win32" and not shutil.which("g++"):
    winget_pkg = Path(os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages"))
    for _cand in winget_pkg.glob("*WinLibs*/mingw64/bin"):
        if (_cand / "g++.exe").exists():
            os.environ["PATH"] = (
                str(_cand) + os.path.pathsep + os.environ.get("PATH", "")
            )
            break


def run_doctor() -> int:
    all_passed = True

    # 1. g++ present
    gxx_path = shutil.which("g++")
    if gxx_path:
        print("[PASS] g++ is present")
    else:
        print("[FAIL] g++ is missing from PATH")
        all_passed = False

    # 2. workspace root exists and is writable
    env_ws = os.environ.get("VERIFIEDS_WORKSPACE")
    ws_root = Path(env_ws).resolve() if env_ws else Path.cwd().resolve()

    if ws_root.exists() and os.access(ws_root, os.W_OK):
        print(f"[PASS] Workspace root exists and is writable: {ws_root}")
    else:
        print(f"[FAIL] Workspace root does not exist or is not writable: {ws_root}")
        all_passed = False

    # 3. Ollama reachable & 4. model present
    cfg = OllamaConfig()
    url = cfg.base_url.rstrip("/")
    tags_url = f"{url}/api/tags"

    ollama_reachable = False
    model_found = False

    try:
        req = urllib.request.Request(tags_url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                ollama_reachable = True
                data: dict[str, Any] = json.loads(resp.read().decode("utf-8"))
                models = data.get("models", [])
                cfg_model = cfg.model
                for m in models:
                    name = m.get("name", "")
                    if name == cfg_model or name.startswith(f"{cfg_model}:"):
                        model_found = True
                        break
    except Exception:
        ollama_reachable = False

    if ollama_reachable:
        print(f"[PASS] Ollama reachable at {cfg.base_url}")
    else:
        print(f"[FAIL] Ollama not reachable at {cfg.base_url}")
        all_passed = False

    if model_found:
        print(f"[PASS] Configured model '{cfg.model}' present in Ollama")
    else:
        print(f"[FAIL] Configured model '{cfg.model}' not found in Ollama /api/tags")
        all_passed = False

    return 0 if all_passed else 1


def main() -> None:
    sys.exit(run_doctor())


if __name__ == "__main__":
    main()
