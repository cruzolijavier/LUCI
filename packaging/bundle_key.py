"""Copy the OpenAI key LUCI uses on this computer into the executable being built.

Looks where the assistant looks (OPENAI_API_KEY, Tools > Settings, openai_key.txt) and
writes src/luci/assistant/bundled_key.txt, which build_exe.bat deletes after the build.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
target = ROOT / "src" / "luci" / "assistant" / "bundled_key.txt"
target.unlink(missing_ok=True)

from luci.assistant.config import read_key  # noqa: E402

key, _error = read_key()
if key:
    target.write_text(f"OPENAI_API_KEY = {key}\n", encoding="utf-8")
    print(f"OpenAI key packed into the executable ({key[:7]}...).")
else:
    print("WARNING: no OpenAI key found (Tools > Settings or openai_key.txt in the LUCI folder).\n"
          "         The executable will work, but its assistant will ask each user for a key.")
