#!/usr/bin/env bash
# Build LUCI on macOS or Linux (the Windows twin is build_exe.bat).
# Result: dist/LUCI/ (Linux) or dist/LUCI.app (macOS), plus dist/LUCI_linux.tar.gz or dist/LUCI_macos.zip.
# It builds in a clean virtual environment (build/exe-venv) so nothing else installed gets in.
set -euo pipefail
cd "$(dirname "$0")/.."

PY="${LUCI_PYTHON:-python3}"
echo "[1/4] Making a clean Python environment (build/exe-venv)..."
"$PY" -m venv build/exe-venv
VPY="$PWD/build/exe-venv/bin/python"
"$VPY" -m pip install --upgrade --quiet pip
"$VPY" -m pip install --upgrade --quiet -e ".[gui]" pyinstaller

echo "[2/4] Packing the OpenAI key of the assistant (if there is one)..."
"$VPY" packaging/bundle_key.py || true
trap 'rm -f src/luci/assistant/bundled_key.txt' EXIT

echo "[3/4] Building (a few minutes)..."
rm -rf dist/LUCI dist/LUCI.app
"$VPY" -m PyInstaller --noconfirm --clean packaging/luci.spec

echo "[4/4] Packing the download..."
if [ "$(uname)" = "Darwin" ]; then
  ditto -c -k --sequesterRsrc --keepParent dist/LUCI.app dist/LUCI_macos.zip
  echo "Done: dist/LUCI_macos.zip (unzip it and open LUCI.app; the first time: right-click > Open)."
else
  tar -czf dist/LUCI_linux.tar.gz -C dist LUCI
  echo "Done: dist/LUCI_linux.tar.gz (tar xzf it and run LUCI/LUCI)."
fi
