"""Settings of the LUCI assistant (OpenAI, model Luna).

The key is looked up, in this order, so a whole group can share one:

1. the ``LUCI_OPENAI_API_KEY`` or ``OPENAI_API_KEY`` environment variable;
2. Tools > Settings > "OpenAI API key" (saved in the LUCI folder's settings.json);
3. a file ``openai_key.txt`` in the LUCI installation folder (next to README.md);
4. a file ``openai_key.txt`` in the LUCI data folder (``luci env path``);
5. the key packed into the executable when it was built (``packaging/build_exe.bat``
   copies ``openai_key.txt`` to ``assistant/bundled_key.txt``; never committed).

The file holds the key alone, or a line ``OPENAI_API_KEY = sk-...``. It is read
again before every question, so changing it needs no restart.
"""

from __future__ import annotations

import os
from pathlib import Path
import re

# --- Models ---------------------------------------------------------------
MODEL = "gpt-6-luna"                         # always Luna for the chat
MODEL_TRANSCRIPTION = "gpt-transcribe"       # audio -> text (Luna does not take audio)
MODEL_TRANSCRIPTION_FALLBACK = "gpt-4o-mini-transcribe"
MODEL_EMBEDDINGS = "text-embedding-3-small"

# Web search (globe button of the chat). "low" = fewer pages read = fewer tokens.
WEB_SEARCH_TOOL = {"type": "web_search", "search_context_size": "low"}

# --- Token budget ---------------------------------------------------------
REASONING_EFFORT = "low"
MAX_OUTPUT_TOKENS = 2400
MEMORY_TURNS = 5                   # earlier question/answer pairs sent again
MAX_TURN_CHARS = 2000              # each earlier message is cut to this
MAX_TOOL_ROUNDS = 48               # chained tool calls per question (a whole chain of programs)
RAG_CHUNKS = 6                     # documentation pieces retrieved per question
RAG_BUDGET = 9000                  # characters of retrieved documentation
MAX_TOOL_CHARS = 8000              # cut of what a tool returns

MAX_AUDIO_SECONDS = 120
KEY_FILE = "openai_key.txt"
BUNDLED_KEY_FILE = "bundled_key.txt"   # put here only while building the executable
KEY_NAME = "OPENAI_API_KEY"


def cache_dir() -> Path:
    from ..settings import luci_home
    folder = luci_home() / "assistant"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def install_dir() -> Path | None:
    """The LUCI installation folder (the one with pyproject.toml), if LUCI runs from it."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if _is_luci_folder(parent):
            return parent
    # Installed with "pip install ." (not -e): pip remembers the folder it came from.
    try:
        import json
        from importlib.metadata import distribution
        from urllib.parse import unquote, urlparse
        url = json.loads(distribution("luci").read_text("direct_url.json") or "{}").get("url", "")
        if url.startswith("file:"):
            path = unquote(urlparse(url).path)
            if len(path) > 2 and path[0] == "/" and path[2] == ":":  # /C:/Users/... on Windows
                path = path[1:]
            if _is_luci_folder(Path(path)):
                return Path(path)
    except Exception:
        pass
    # Started from the LUCI folder (or below it).
    cwd = Path.cwd()
    for parent in (cwd, *cwd.parents):
        if _is_luci_folder(parent):
            return parent
    return None


def _is_luci_folder(path: Path) -> bool:
    return (path / "pyproject.toml").is_file() and (path / "src" / "luci").is_dir()


def key_files() -> list[Path]:
    from ..settings import luci_home
    files = []
    root = install_dir()
    if root is not None:
        files.append(root / KEY_FILE)
    files.append(luci_home() / KEY_FILE)
    files.append(Path(__file__).resolve().parent / BUNDLED_KEY_FILE)
    return files


def _key_from_file(path: Path) -> str:
    """The OpenAI key in a text file: an 'OPENAI_API_KEY = ...' line (also 'export', ':' or
    lower case), or else a line holding only a key that starts with 'sk-'."""
    try:
        raw = path.read_bytes()
    except OSError:
        return ""
    for encoding in ("utf-16", "utf-8-sig", "latin-1") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") \
            else ("utf-8-sig", "latin-1"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        return ""
    lines = [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]
    for line in lines:
        match = re.match(rf"(?:export\s+)?{KEY_NAME}\s*[=:]\s*(\S+)", line, re.IGNORECASE)
        if match:
            return match.group(1).strip().strip("\"'")
    for line in lines:
        value = line.strip().strip("\"'")
        if value.startswith("sk-") and " " not in value:
            return value
    return ""


def read_key() -> tuple[str | None, str | None]:
    """(key, error). Read on every question so a new key works without restarting."""
    for name in ("LUCI_OPENAI_API_KEY", KEY_NAME):
        if os.environ.get(name, "").strip():
            return os.environ[name].strip(), None
    try:
        from ..settings import Settings
        saved = Settings.load().openai_api_key.strip()
    except Exception:
        saved = ""
    if saved:
        return saved, None
    for path in key_files():
        key = _key_from_file(path)
        if key:
            return key, None
    places = " or ".join(str(p) for p in key_files()[:-1])
    return None, ("There is no OpenAI key yet. Paste it in Tools > Settings > OpenAI API key, or save it "
                  f"in {places}.")
