"""The LUCI assistant: its knowledge, its key, what it sees and the tool loop (with a fake model)."""

import json
import os
import time
import types

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
QtWidgets = pytest.importorskip("PySide6.QtWidgets")

from luci.assistant import config, knowledge  # noqa: E402
from luci.assistant.rag import Knowledge  # noqa: E402
from luci.registry import PROGRAMS  # noqa: E402


@pytest.fixture(scope="module")
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture
def window(app, luci_home):
    from luci.gui.app import MainWindow
    win = MainWindow()
    win.resize(1366, 768)
    win.show()
    app.processEvents()
    yield win
    win.close()


def test_knowledge_covers_every_program():
    docs = knowledge.documents()
    ids = {d[0] for d in docs}
    for spec in PROGRAMS:
        assert f"program_{spec.key}" in ids
    upstream = {d[1] for d in docs if d[0].startswith("upstream_")}
    assert {"aqme_csearch", "robert", "dbstep", "goodvibes", "thermognn"} <= upstream
    context = knowledge.static_context("aqme_csearch", "struct")
    assert "THE PROGRAM ON SCREEN" in context and "--sample" in context and "ALL PROGRAMS IN LUCI" in context


def test_offline_search_finds_upstream_documentation():
    rag = Knowledge()
    rag._embeddings_ok = False
    found = rag.search("quasi-harmonic temperature", knowledge.scopes_for("goodvibes", "thermo"), set())
    assert found and any("goodvibes" in title for title, _ in found)


def test_key_sources(luci_home, monkeypatch, tmp_path):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LUCI_OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(config, "install_dir", lambda: tmp_path)
    key, error = config.read_key()
    assert key is None and "Settings" in error
    (tmp_path / "openai_key.txt").write_text("# my key\nOPENAI_API_KEY = sk-file\n")
    assert config.read_key() == ("sk-file", None)
    from luci.settings import Settings
    settings = Settings.load()
    settings.openai_api_key = "sk-settings"
    settings.save()
    assert config.read_key() == ("sk-settings", None)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env")
    assert config.read_key() == ("sk-env", None)


def _call(name, args, cid):
    return types.SimpleNamespace(type="function_call", name=name, arguments=json.dumps(args), call_id=cid)


def _converse(app, window, monkeypatch, script, text, control=True):
    from luci.assistant import client
    session = window._assistant.panel.session
    session.knowledge._embeddings_ok = False
    seen = []

    def respond(instructions, items, tools, previous_id=None):
        seen.append({"instructions": instructions, "items": items, "tools": [t.get("name") for t in tools]})
        step = script.pop(0)
        if isinstance(step, str):
            return types.SimpleNamespace(output=[], output_text=step, id="last", status="completed")
        return types.SimpleNamespace(output=step, output_text="", id=f"r{len(script)}", status="completed")
    monkeypatch.setattr(client, "respond", respond)
    session.set_control(control)
    assert session.send(text)
    limit = time.time() + 30
    while session.busy and time.time() < limit:
        app.processEvents()
        time.sleep(0.01)
    return session, seen


def test_assistant_fills_a_form(app, window, monkeypatch, tmp_path):
    csv = tmp_path / "mols.csv"
    csv.write_text("code_name,smiles\nethanol,CCO\n")
    script = [[_call("open_program", {"program": "aqme_csearch"}, "a")],
              [_call("set_input", {"value": str(csv), "input_type": "molecules"}, "b")],
              [_call("set_options", {"options": [{"option": "sample", "value": "10"},
                                                 {"option": "program", "value": "crest"}]}, "c")],
              "Listo."]
    session, seen = _converse(app, window, monkeypatch, script, "Rellena CSEARCH con mi CSV")
    assert session.messages[-1] == {"role": "assistant", "text": "Listo."}
    command = window.current_workspace().current_form().command()
    assert command[command.index("--molecules") + 1] == str(csv)
    assert command[-4:] == ["--program", "crest", "--sample", "10"]
    # The screen goes with the question; the tool outputs go back to the model.
    assert "On screen now" in seen[0]["items"][-2]["content"]
    outputs = [item for step in seen[1:] for item in step["items"]]
    assert all(item["type"] == "function_call_output" for item in outputs)


def test_control_off_refuses_actions(app, window, monkeypatch):
    script = [[_call("open_program", {"program": "dbstep"}, "a")], "Explained."]
    session, seen = _converse(app, window, monkeypatch, script, "Open DBSTEP", control=False)
    assert "open_program" not in seen[0]["tools"] and "view_screen" in seen[0]["tools"]
    assert "Control mode is OFF" in seen[1]["items"][0]["output"]
    assert window.current_workspace().current_package() is None


def test_errors_are_explained(app, window, monkeypatch):
    from luci.assistant import client

    def fail(*_a, **_k):
        raise client.AssistantError("There is no OpenAI key yet.")
    monkeypatch.setattr(client, "respond", fail)
    session = window._assistant.panel.session
    session.knowledge._embeddings_ok = False
    session.send("hola")
    limit = time.time() + 10
    while session.busy and time.time() < limit:
        app.processEvents()
        time.sleep(0.01)
    assert session.messages[-1]["role"] == "system" and "OpenAI key" in session.messages[-1]["text"]


def test_view_screen_lists_options_and_problems(app, window, tmp_path):
    csv = tmp_path / "m.csv"
    csv.write_text("code_name,smiles\na/b,CCO\n")
    screen = window._assistant.panel.session.screen
    screen.open_program("aqme_csearch")
    result = screen.set_input(str(csv), "molecules")
    checked = window.current_workspace().current_form().standard_input()
    checked.wait()
    detail = screen.detail()
    assert any(row["key"] == "sample" for row in detail["options"])
    assert detail["input_problems"][0]["entry"] == "a/b"
    assert "1 with errors" in screen.state()
    assert screen.run()["error"]  # not installed


def test_key_file_formats(tmp_path):
    from luci.assistant.config import _key_from_file
    path = tmp_path / "k.txt"
    for content, expected in [("HF_TOKEN=hf_x\nOPENAI_API_KEY=sk-c\n", "sk-c"), ("export OPENAI_API_KEY=sk-a", "sk-a"),
                              ("openai_api_key: sk-b", "sk-b"), ("sk-proj-bare\n", "sk-proj-bare"), ("hf_only", "")]:
        path.write_text(content)
        assert _key_from_file(path) == expected
    path.write_text("OPENAI_API_KEY = sk-u16", encoding="utf-16")
    assert _key_from_file(path) == "sk-u16"


def test_secrets_never_reach_the_model(luci_home, tmp_path):
    from luci.assistant.data_tools import find_in_file, read_file
    from luci.settings import Settings
    settings = Settings.load()
    settings.openai_api_key = "sk-SECRET1234567"
    settings.save()
    assert "error" in read_file(str(Settings.path()))
    log = tmp_path / "run.log"
    log.write_text("token sk-SECRET1234567 here\nline two\n")
    assert "sk-SECRET" not in str(read_file(str(log))) and "[hidden]" in read_file(str(log))["text"]
    assert "sk-SECRET" not in str(find_in_file(str(log), "token"))


def test_odd_tool_arguments_never_block_the_chat(app, window, monkeypatch):
    bad = types.SimpleNamespace(type="function_call", name="view_screen", arguments="[]", call_id="x")
    session, seen = _converse(app, window, monkeypatch, [[bad], "ok"], "hola")
    assert not session.busy and session.messages[-1]["text"] == "ok"


def test_assistant_writes_an_input_and_loads_it(app, window, monkeypatch, tmp_path):
    target = tmp_path / "project" / "inputs" / "mols.csv"
    script = [[_call("write_file", {"path": str(target),
                                    "content": "smiles,code_name\nCCO,ethanol\nc1ccccc1O,phenol"}, "a")],
              [_call("open_program", {"program": "aqme_csearch"}, "b")],
              [_call("set_input", {"value": str(target), "input_type": "molecules"}, "c")],
              "Hecho."]
    session, seen = _converse(app, window, monkeypatch, script, "Crea un CSV con etanol y fenol y cárgalo")
    assert "write_file" in seen[0]["tools"] and "wait_for_run" in seen[0]["tools"]
    assert target.read_text() == "smiles,code_name\nCCO,ethanol\nc1ccccc1O,phenol\n"
    report = json.loads(seen[1]["items"][0]["output"])
    assert report["written"] == str(target.resolve()) and "molecule_csv_check" in report
    command = window.current_workspace().current_form().command()
    assert command[command.index("--molecules") + 1] == str(target)


def test_write_file_never_replaces_user_files(luci_home, tmp_path):
    from luci.assistant.data_tools import write_file
    session = types.SimpleNamespace(written_files=set())
    mine = tmp_path / "user.csv"
    mine.write_text("precious\n")
    assert "already exists" in write_file(session, str(mine), "x")["error"]
    assert "never replaced" in write_file(session, str(mine), "x", overwrite=True)["error"]
    assert mine.read_text() == "precious\n"
    new = tmp_path / "new.xyz"
    assert "consistent" in write_file(session, str(new), "1\nH\nH 0 0 0")["xyz_check"]
    assert write_file(session, str(new), "2\nH2\nH 0 0 0\nH 0 0 0.74", overwrite=True)["xyz_check"].startswith("1")
    assert "says 3 atoms" in write_file(session, str(tmp_path / "bad.xyz"), "3\nx\nH 0 0 0")["xyz_check"]
    assert "not programs" in write_file(session, str(tmp_path / "run.bat"), "del *")["error"]
    assert "full path" in write_file(session, "relative.csv", "a")["error"]
    assert "reserved" in write_file(session, str(tmp_path / "openai_key.txt"), "sk-x")["error"]
    assert "environments" in write_file(session, str(luci_home / "envs" / "aqme" / "a.csv"), "a")["error"]
    gjf = write_file(session, str(tmp_path / "h2.gjf"), "# hf\n\nH2\n\n0 1\nH 0 0 0\nH 0 0 0.74")
    assert (tmp_path / "h2.gjf").read_text().endswith("0.74\n\n") and "error" not in gjf


def test_wait_for_run_reports_a_finished_run(app, window, tmp_path):
    screen = window._assistant.panel.session.screen
    window.open_program("dbstep")
    page = window.current_workspace().current_package()
    page.console.appendPlainText("[LUCI] Output folder: C:/data/dbstep_out\nDBSTEP finished\n"
                                 "[LUCI] Workflow finished with exit code 0.")
    report = screen.wait_for_run("dbstep")
    assert report["exit_code"] == 0 and report["output_folder"] == "C:/data/dbstep_out" and not report["running"]
