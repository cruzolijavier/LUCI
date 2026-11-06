#!/bin/sh
# Solve every environment manifest for all its platforms with the real conda<->PyPI
# mapping (as on a user's machine). Usage: tools/lock_check.sh [env ...]
# MAPPING=<local compressed_mapping.json> uses a local copy of the mapping.
set -u
ROOT=$(cd "$(dirname "$0")/.." && pwd)
WORK=${WORK:-/tmp/luci_lock_check}
mkdir -p "$WORK"
ENVS=${*:-$(ls "$ROOT/src/luci/envs/manifests")}
status=0
for env in $ENVS; do
  mkdir -p "$WORK/$env"
  cp "$ROOT/src/luci/envs/manifests/$env/pixi.toml" "$WORK/$env/pixi.toml"
  if [ -n "${MAPPING:-}" ]; then
    # Point every channel of the manifest at the local mapping file.
    python3 - "$WORK/$env/pixi.toml" "$MAPPING" <<'PY'
import re, sys
path, mapping = sys.argv[1], sys.argv[2]
text = open(path).read()
channels = re.findall(r'"([^"]+)"', re.search(r'^channels = \[(.*)\]$', text, re.M).group(1))
entry = ", ".join(f'"{c}" = {{ location = "{mapping}", mapping-mode = "replace" }}' for c in channels)
text = text.replace("[workspace]\n", "[workspace]\nconda-pypi-map = { " + entry + " }\n", 1)
open(path, "w").write(text)
PY
  fi
  rm -f "$WORK/$env/pixi.lock"
  if pixi lock --manifest-path "$WORK/$env/pixi.toml" > "$WORK/$env.log" 2>&1; then
    echo "OK    $env"
  else
    echo "FAIL  $env  (see $WORK/$env.log)"; status=1
  fi
done
exit $status
