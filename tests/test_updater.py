"""Updates: version check, download with checksum, safe unpacking, the swap script."""

import hashlib
import http.server
import io
import json
import threading
import zipfile
from pathlib import Path

import pytest

from luci import updater


def _zip_bytes(files: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    return buffer.getvalue()


GOOD = _zip_bytes({"LUCI/LUCI.exe": b"MZ1", "LUCI/luci-cli.exe": b"MZ2", "LUCI/_internal/lib.dll": b"x"})


@pytest.fixture
def server(tmp_path, monkeypatch):
    monkeypatch.setenv("LUCI_HOME", str(tmp_path / "home"))
    routes: dict[str, tuple[int, bytes]] = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            code, body = routes.get(self.path, (404, b""))
            self.send_response(code)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    httpd = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{httpd.server_port}"
    routes["/latest/download/version.json"] = (200, json.dumps({
        "version": "9.9.9", "sha256": hashlib.sha256(GOOD).hexdigest(), "size": len(GOOD),
        "file": "http://evil.example/x.zip", "notes": "News"}).encode())
    routes["/download/v9.9.9/LUCI_windows.zip"] = (200, GOOD)
    yield base, routes
    httpd.shutdown()


def test_versions():
    assert updater.is_newer("0.3.1", "0.3.0")
    assert updater.is_newer("v1.0.0", "0.9.9")
    assert not updater.is_newer("0.3.0", "0.3.0")
    assert not updater.is_newer("0.2.9", "0.3.0")
    assert not updater.is_newer("abc", "0.3.0")


def test_check_newer_and_url_is_built_locally(server):
    base, _ = server
    info = updater.check(f"{base}/latest/download/version.json", "0.3.0", base)
    assert info.version == "9.9.9" and info.notes == "News"
    assert info.url == f"{base}/download/v9.9.9/LUCI_windows.zip"   # the manifest's "file" is ignored


def test_check_up_to_date(server):
    base, _ = server
    assert updater.check(f"{base}/latest/download/version.json", "9.9.9", base) is None


@pytest.mark.parametrize("manifest", [b"not json", b"{}", json.dumps({"version": "1.0.0", "sha256": "zz", "size": 5}).encode(),
                                      json.dumps({"version": "x", "sha256": "0" * 64, "size": 5}).encode()])
def test_check_invalid_manifest(server, manifest):
    base, routes = server
    routes["/latest/download/version.json"] = (200, manifest)
    with pytest.raises(updater.UpdateError):
        updater.check(f"{base}/latest/download/version.json", "0.3.0", base)


def test_check_no_release_or_offline(server):
    base, routes = server
    routes.pop("/latest/download/version.json")
    with pytest.raises(updater.UpdateError):
        updater.check(f"{base}/latest/download/version.json", "0.3.0", base)
    with pytest.raises(updater.UpdateError):
        updater.check("http://127.0.0.1:9/version.json", "0.3.0", base)


def _info(base, data=GOOD, **over):
    values = dict(version="9.9.9", sha256=hashlib.sha256(data).hexdigest(), size=len(data), notes="",
                  url=f"{base}/download/v9.9.9/LUCI_windows.zip")
    values.update(over)
    return updater.Update(**values)


def test_download_ok(server, tmp_path):
    base, _ = server
    seen = []
    root = updater.download(_info(base), lambda a, b, t: seen.append(t), tmp_path / "w")
    assert (root / "LUCI.exe").read_bytes() == b"MZ1" and (root / "_internal").is_dir()
    assert "Downloading..." in seen and not (tmp_path / "w" / "LUCI_windows.zip").exists()


def test_download_wrong_hash_or_size(server, tmp_path):
    base, _ = server
    with pytest.raises(updater.UpdateError, match="checksum"):
        updater.download(_info(base, sha256="0" * 64), None, tmp_path / "w")
    with pytest.raises(updater.UpdateError, match="size"):
        updater.download(_info(base, size=len(GOOD) + 1), None, tmp_path / "w")


def test_download_404(server, tmp_path):
    base, _ = server
    with pytest.raises(updater.UpdateError, match="404"):
        updater.download(_info(base, url=f"{base}/nope.zip"), None, tmp_path / "w")


def test_download_rejects_path_traversal(server, tmp_path):
    base, routes = server
    evil = _zip_bytes({"../evil.txt": b"x", "LUCI/LUCI.exe": b"MZ"})
    routes["/download/v9.9.9/LUCI_windows.zip"] = (200, evil)
    with pytest.raises(updater.UpdateError, match="unsafe"):
        updater.download(_info(base, evil), None, tmp_path / "w")
    assert not (tmp_path / "evil.txt").exists()


def test_download_rejects_incomplete_zip(server, tmp_path):
    base, routes = server
    partial = _zip_bytes({"LUCI/LUCI.exe": b"MZ"})
    routes["/download/v9.9.9/LUCI_windows.zip"] = (200, partial)
    with pytest.raises(updater.UpdateError, match="does not contain"):
        updater.download(_info(base, partial), None, tmp_path / "w")


def test_swap_script_order_and_paths():
    text = updater.swap_script(Path("C:/w/new/LUCI"), Path("C:/Apps/LUCI"), Path("C:/Apps/LUCI/LUCI.exe"),
                               Path("C:/w"), Path("C:/h/update.log"))
    assert "\r\n" in text
    assert text.index("_internal") < text.index("/E /XD _internal")      # libraries before executables
    assert text.index("robocopy") < text.index("start")
    assert 'del "%~f0"' in text and "PYINSTALLER_RESET_ENVIRONMENT=1" in text


def test_can_update_not_frozen():
    ok, why = updater.can_update()
    assert not ok and "source" in why


# ---------------------------------------------------------------- helper (new LUCI.exe)
def _make_install(base: Path, exe: bytes, lib: bytes, extra: dict | None = None) -> Path:
    base.mkdir(parents=True)
    (base / "LUCI.exe").write_bytes(exe)
    (base / "luci-cli.exe").write_bytes(exe)
    (base / "_internal").mkdir()
    (base / "_internal" / "lib.dll").write_bytes(lib)
    for name, data in (extra or {}).items():
        (base / "_internal" / name).write_bytes(data)
    return base


def test_swap_files_replaces_everything(tmp_path):
    install = _make_install(tmp_path / "app", b"old", b"oldlib", {"gone.dll": b"x"})
    source = _make_install(tmp_path / "new", b"new", b"newlib")
    updater.swap_files(source, install)
    assert (install / "LUCI.exe").read_bytes() == b"new" and (install / "luci-cli.exe").read_bytes() == b"new"
    assert (install / "_internal" / "lib.dll").read_bytes() == b"newlib"
    assert not (install / "_internal" / "gone.dll").exists()          # files removed by the update go away
    assert not (install / "_internal.old").exists() and not list(install.glob("*.new"))


def test_swap_files_failure_keeps_old_version(tmp_path, monkeypatch):
    install = _make_install(tmp_path / "app", b"old", b"oldlib")
    source = _make_install(tmp_path / "new", b"new", b"newlib")
    real_copy = updater.shutil.copy2

    def broken(src, dst, *a, **k):
        if str(dst).endswith("luci-cli.exe.new"):
            raise PermissionError("locked")
        return real_copy(src, dst, *a, **k)

    monkeypatch.setattr(updater.shutil, "copy2", broken)
    monkeypatch.setattr(updater.time, "sleep", lambda _s: None)
    with pytest.raises(OSError):
        updater.swap_files(source, install)
    assert (install / "LUCI.exe").read_bytes() == b"old"
    assert (install / "_internal" / "lib.dll").read_bytes() == b"oldlib"
    assert not list(install.glob("*.new")) and not (install / "_internal.old").exists()


def test_helper_main_installs_and_logs(tmp_path, monkeypatch):
    install = _make_install(tmp_path / "app", b"old", b"oldlib")
    source = _make_install(tmp_path / "new", b"new", b"newlib")
    log = tmp_path / "update.log"
    (install / "LUCI").write_bytes(b"x")      # the name the helper reopens on Linux (LUCI.exe on Windows)
    monkeypatch.setattr(updater.sys, "executable", str(source / "LUCI.exe"))
    started = []
    monkeypatch.setattr(updater, "_spawn", lambda argv, cwd, flags, env: started.append(argv))
    code = updater.helper_main(["LUCI.exe", "--apply-update", "--install", str(install), "--pid", "0",
                                "--log", str(log)])
    assert code == 0 and (install / "LUCI.exe").read_bytes() == b"new"
    assert started and "update installed" in log.read_text(encoding="utf-8")
    started.clear()
    updater.helper_main(["LUCI.exe", "--apply-update", "--install", str(install), "--pid", "0",
                         "--log", str(log), "--no-restart"])
    assert started == []                                               # "install when I close LUCI"


def test_supports_helper(tmp_path):
    root = _make_install(tmp_path / "new", b"x", b"y")
    assert not updater.supports_helper(root)
    (root / "_internal" / "luci").mkdir()
    (root / "_internal" / "luci" / updater.HELPER_MARKER).write_text("x")
    assert updater.supports_helper(root)
