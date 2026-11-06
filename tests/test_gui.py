"""Build every screen offscreen and drive the forms like a user would."""

import json
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
QtWidgets = pytest.importorskip("PySide6.QtWidgets")

from luci.commands import preview_command  # noqa: E402
from luci.registry import LAYERS, PROGRAMS, programs_in  # noqa: E402


@pytest.fixture(scope="module")
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture
def window(app, luci_home):
    from luci.gui.app import MainWindow
    win = MainWindow()
    win.resize(1280, 800)
    win.show()
    app.processEvents()
    yield win
    win.close()


def test_every_program_has_a_page(window):
    for row, layer in enumerate(LAYERS):
        window.layer_list.setCurrentRow(row)
        workspace = window.current_workspace()
        assert set(workspace.pages) == {p.key for p in programs_in(layer.key)}
        for key, page in workspace.pages.items():
            workspace.select_package(key)
            command = page.command()
            assert command[3:6] == [layer.key, "--backend", key]
            assert "--" in command
            assert preview_command(command).startswith(f"luci {layer.key} --backend {key}")


def test_form_values_reach_the_command(window, tmp_path):
    window.layer_list.setCurrentRow(3)  # FEAT
    workspace = window.current_workspace()
    workspace.select_package("dbstep")
    form = workspace.current_form()
    folder = tmp_path / "ligands"
    folder.mkdir()
    form.input_widgets["structures"].edit.setText(str(folder))
    form.widgets["sterimol"].setChecked(True)
    form.widgets["atom1"].setText("2")
    command = form.command()
    native = command[command.index("--") + 1:]
    assert native == ["--sterimol", "--atom1", "2"]
    assert command[command.index("--structures") + 1] == str(folder)
    # The output folder follows the input automatically.
    assert command[command.index("--output-dir") + 1] == str(folder.resolve())


def test_variant_visibility_and_required(window):
    window.layer_list.setCurrentRow(2)  # REACT
    workspace = window.current_workspace()
    workspace.select_package("ts_tools")
    form = workspace.current_form()
    page = workspace.current_package()
    assert form.widgets["solvent"].isVisibleTo(form)
    form.variant_combo.setCurrentIndex(2)  # MLIP
    assert not form.widgets["solvent"].isVisibleTo(form)
    assert page.pill.text() == "Coming soon" and not page.run_button.isEnabled()
    assert "--variant" in form.command() and "mlip" in form.command()
    assert form.missing_required() == ["Reaction list (.txt)"]


def test_input_mode_selects_variant(window):
    window.layer_list.setCurrentRow(1)  # THERMO
    workspace = window.current_workspace()
    workspace.select_package("thermomlip")
    form = workspace.current_form()
    assert form.variant_combo is None
    assert form.current_variant().key == "batch"
    form.input_combo.setCurrentIndex(1)
    assert form.current_variant().key == "single"
    assert form.widgets["results_file"].isVisibleTo(form)
    assert set(form.missing_required()) >= {"One SMILES", "Dataset name", "Results CSV"}
    smiles = form.input_widgets["smiles"].checked
    smiles.edit.setText("CCO")
    smiles.name_edit.setText("ethanol")
    command = form.command()
    assert command[command.index("--molecule"):command.index("--molecule") + 4] == [
        "--molecule", "CCO", "--code-name", "ethanol"]


def test_filter_hides_programs(window):
    window.filter_bar.buttons["reaction"].setChecked(True)
    landing = window.workspaces["react"].landing
    assert all(card.isVisibleTo(landing) for card in landing.cards)
    thermo = window.workspaces["thermo"].landing
    assert not any(card.isVisibleTo(thermo) for card in thermo.cards)
    assert window.nav_items[1].caption.text() == "0 of 3 match"
    window.filter_bar.clear()
    assert all(card.isVisibleTo(thermo) for card in thermo.cards)


def test_workflow_roundtrip_and_legacy(window, tmp_path, monkeypatch):
    window.layer_list.setCurrentRow(0)
    workspace = window.current_workspace()
    workspace.select_package("aqme_csearch")
    form = workspace.current_form()
    form.input_combo.setCurrentIndex(1)
    form.input_widgets["smiles"].edit.setText("CCO")
    form.input_widgets["smiles"].checked.name_edit.setText("ethanol")
    form.widgets["sample"].setText("7")
    saved = tmp_path / "wf.json"
    monkeypatch.setattr(QtWidgets.QFileDialog, "getSaveFileName", lambda *a, **k: (str(saved), ""))
    window.save_workflow()
    form.reset()
    assert form.widgets["sample"].text() == ""
    window.load_workflow(str(saved))
    assert form.widgets["sample"].text() == "7" and form.input_value() == "CCO"
    assert form.code_name() == "ethanol"
    # A LUCI 0.1 file: four modules and "backend".
    legacy = tmp_path / "old.json"
    legacy.write_text(json.dumps({"module": "gopt", "state": {"backend": "aqme_cmin", "form": {}}}))
    window.load_workflow(str(legacy))
    assert window.current_workspace().spec.key == "struct"
    assert window.current_workspace().package_key == "aqme_cmin"


def test_states_follow_installation(window, luci_home):
    from conftest import fake_install
    fake_install(luci_home, "dbstep")
    window.refresh_all()
    card = next(c for c in window.workspaces["feat"].landing.cards if c.spec.key == "dbstep")
    assert card.pill.text() == "Installed" and not card.install_button.isVisible()
    page = window.workspaces["feat"].pages["dbstep"]
    assert page.run_button.isEnabled()


@pytest.mark.parametrize("size", [(1920, 1080), (1366, 768), (1024, 700), (760, 520)])
def test_no_horizontal_overflow(window, app, size):
    """Nothing may need a horizontal scrollbar at common laptop sizes."""
    window.resize(*size)
    app.processEvents()
    for row, layer in enumerate(LAYERS):
        window.layer_list.setCurrentRow(row)
        workspace = window.current_workspace()
        workspace.go_home()
        app.processEvents()
        landing_scroll = workspace.stack.widget(0)
        assert not landing_scroll.horizontalScrollBar().isVisible(), (size, layer.key)
        for key in workspace.pages:
            workspace.select_package(key)
            app.processEvents()
            scroll = workspace.pages[key].findChild(QtWidgets.QScrollArea)
            assert not scroll.horizontalScrollBar().isVisible(), (size, key)


def test_legacy_workflow_with_package_backend(window, tmp_path):
    legacy = tmp_path / "old.json"
    legacy.write_text(json.dumps({"module": "gopt", "state": {"backend": "aqme", "form": {}}}))
    window.load_workflow(str(legacy))
    assert window.current_workspace().package_key == "aqme_cmin"
    odd = tmp_path / "odd.json"
    odd.write_text(json.dumps({"layer": "struct", "state": {
        "program": "aqme_csearch", "form": {"inputs": {"smi": 5}, "destination": None,
                                            "values": {"sample": 7}, "advanced": None}}}))
    window.load_workflow(str(odd))
    form = window.current_workspace().current_form()
    # The old "smi" input (and its "name" option) became the standard typed SMILES.
    assert form.mode_key() == "smiles" or form.input_widgets["smiles"].edit.text() == "5"
    assert form.input_widgets["smiles"].edit.text() == "5" and form.widgets["sample"].text() == "7"


def test_last_output_folder_is_reused(window, tmp_path):
    window.layer_list.setCurrentRow(5)  # DESIGN
    workspace = window.current_workspace()
    workspace.select_package("edboplus")
    form = workspace.current_form()
    form.input_combo.setCurrentIndex(1)  # new scope, no input file
    form.destination.setText(str(tmp_path / "campaign"))
    form.remember_output()
    form.destination.setText("")
    assert form.output_dir() == str(tmp_path / "campaign")


def test_hidden_rows_stay_hidden_after_show_and_expand(window, app):
    window.layer_list.setCurrentRow(1)  # THERMO
    workspace = window.current_workspace()
    workspace.select_package("thermomlip")
    app.processEvents()
    form = workspace.current_form()
    assert form.current_variant().key == "batch"
    field = form.widgets["results_file"]
    assert not field.isVisibleTo(form)
    section = form.sections["@input"]
    section.collapse()
    section.expand()
    app.processEvents()
    assert not field.isVisibleTo(form)
    # Its row title must be hidden too, not left as an orphan label.
    layout, row, _ = form.rows["results_file"]
    assert not layout.isRowVisible(row)
    form.input_combo.setCurrentIndex(1)
    assert field.isVisibleTo(form) and layout.isRowVisible(row)


def test_semicolon_csv_columns(window, tmp_path):
    window.layer_list.setCurrentRow(4)  # PRED
    workspace = window.current_workspace()
    workspace.select_package("robert")
    form = workspace.current_form()
    csv_path = tmp_path / "es.csv"
    csv_path.write_text("code_name;x1;yield\nm1;0,5;3\n")
    form.input_widgets["csv_name"].edit.setText(str(csv_path))
    items = [form.widgets["y"].itemText(i) for i in range(form.widgets["y"].count())]
    assert items[1:] == ["code_name", "x1", "yield"]


def test_uninstall_from_card_and_page(window, luci_home, monkeypatch):
    from conftest import fake_install
    from luci.gui import dialogs
    fake_install(luci_home, "dbstep")
    window.refresh_all()
    card = next(c for c in window.workspaces["feat"].landing.cards if c.spec.key == "dbstep")
    page = window.workspaces["feat"].pages["dbstep"]
    assert not card.uninstall_button.isHidden() and not page.uninstall_button.isHidden()
    # Confirmed uninstall runs "luci env remove dbstep".
    ran = []

    class FakeDialog:
        def __init__(self, title, argv, parent):
            ran.append(argv)
            from luci.envs.manager import EnvManager
            EnvManager(luci_home).remove("dbstep")
            self.exit_code = 0

        def exec(self):
            return 0

    monkeypatch.setattr(dialogs, "ProcessDialog", FakeDialog)
    monkeypatch.setattr(dialogs.QMessageBox, "question", lambda *a, **k: dialogs.QMessageBox.Yes)
    window.uninstall_program("dbstep")
    assert ran and ran[0][-3:] == ["env", "remove", "dbstep"]
    assert card.uninstall_button.isHidden() and page.uninstall_button.isHidden()
    assert page.pill.text() == "Not installed"


def test_uninstall_can_be_cancelled(window, luci_home, monkeypatch):
    from conftest import fake_install
    from luci.gui import dialogs
    fake_install(luci_home, "dbstep")
    monkeypatch.setattr(dialogs.QMessageBox, "question", lambda *a, **k: dialogs.QMessageBox.No)
    window.uninstall_program("dbstep")
    from luci.envs.manager import EnvManager
    assert EnvManager(luci_home).is_installed("dbstep")


# ------------------------------------------------------------------ standard inputs
def _csearch(window):
    window.layer_list.setCurrentRow(0)
    workspace = window.current_workspace()
    workspace.select_package("aqme_csearch")
    return workspace.current_package(), workspace.current_form()


def test_molecule_csv_is_checked_in_the_panel(window, tmp_path):
    page, form = _csearch(window)
    csv = tmp_path / "mols.csv"
    csv.write_text("code_name;smiles\nethanol;CCO\na/b;c1ccnc1\nbad name;C1CC\nempty;\n",
                   encoding="utf-8")
    checked = form.input_widgets["molecules"].checked
    checked.edit.setText(str(csv))
    checked.wait()
    panel = checked.panel
    text = panel.summary.text()
    assert "4 molecules" in text and "2 with errors" in text and "1 with warnings" in text
    assert panel.summary.property("kind") == "error"
    rows = [panel.list.topLevelItem(i).text(1) for i in range(panel.list.topLevelItemCount())]
    assert rows == ["a/b", "empty", "bad name"]  # problems only, errors first
    assert checked.problems() == (2, 4, "")
    # The preview follows the check, and leaving the bad ones out reaches the command.
    assert not panel.skip.isHidden()
    panel.skip.setChecked(True)
    assert "--skip-invalid" in form.command() and "--skip-invalid" in form.preview.toPlainText()
    panel.only_problems.setChecked(False)
    assert panel.list.topLevelItemCount() == 4
    # A new file never inherits the choice.
    good = tmp_path / "good.csv"
    good.write_text("code_name,smiles\na,CCO\n")
    checked.edit.setText(str(good))
    checked.wait()
    assert "--skip-invalid" not in form.preview.toPlainText()


def test_missing_columns_and_paths_are_explained(window, tmp_path):
    page, form = _csearch(window)
    csv = tmp_path / "mols.csv"
    csv.write_text("Name,SMILES string\nA,CCO\n", encoding="utf-8")
    checked = form.input_widgets["molecules"].checked
    checked.edit.setText(str(csv))
    checked.wait()
    assert "code_name" in checked.panel.summary.text()
    assert checked.problems()[2]
    checked.edit.setText(str(tmp_path))
    checked.wait()
    assert "is a folder" in checked.problems()[2]
    checked.edit.setText(str(tmp_path / "nope.csv"))
    checked.wait()
    assert "does not exist" in checked.problems()[2]


def test_typed_smiles_only_checks_the_name(window):
    page, form = _csearch(window)
    form.input_combo.setCurrentIndex(1)
    checked = form.input_widgets["smiles"].checked
    checked.edit.setText("C1CC")  # not LUCI's business: the program checks SMILES
    checked.wait()
    assert checked.problems() == (0, 0, "")
    checked.name_edit.setText("a/b")
    checked.wait()
    assert "cannot be used in file names" in checked.problems()[2]
    assert not checked.note.isHidden()


def test_structures_folder_is_listed(window, tmp_path):
    window.layer_list.setCurrentRow(0)
    workspace = window.current_workspace()
    workspace.select_package("aqme_cmin")
    form = workspace.current_form()
    (tmp_path / "w.xyz").write_text("3\ncharge=0\nO 0 0 0\nH 0.96 0 0\nH -0.24 0.93 0\n")
    (tmp_path / "broken.log").write_text("not a calculation")
    checked = form.input_widgets["structures"].checked
    checked.edit.setText(str(tmp_path))
    checked.wait()
    assert "2 files" in checked.panel.summary.text() and "Open Babel" in checked.panel.summary.text()
    assert checked.problems() == (1, 2, "")


def test_run_refuses_an_unusable_input(window, monkeypatch, luci_home, tmp_path):
    from conftest import fake_install
    fake_install(luci_home, "aqme")
    page, form = _csearch(window)
    page.refresh_status()
    form.input_widgets["molecules"].checked.edit.setText(str(tmp_path / "missing.csv"))
    shown = []
    monkeypatch.setattr(QtWidgets.QMessageBox, "warning", lambda *a, **k: shown.append(a[1]))
    page.run()  # straight away: the pending check must still run first
    assert shown == ["The input cannot be used"] and page.process is None


@pytest.mark.parametrize("size", [(1366, 768), (760, 520)])
def test_checked_inputs_fit_small_windows(window, app, tmp_path, size):
    """The check panel (list, drawing, explanation) must not need a horizontal scrollbar."""
    window.resize(*size)
    page, form = _csearch(window)
    csv = tmp_path / "mols.csv"
    csv.write_text("code_name,smiles\npyrrole,c1ccnc1\na/b," + "CC(=O)Oc1ccccc1C(=O)O" * 10 + "\n")
    checked = form.input_widgets["molecules"].checked
    checked.edit.setText(str(csv))
    checked.check()
    checked.wait()
    for _ in range(3):
        app.processEvents()
    scroll = page.findChild(QtWidgets.QScrollArea)
    assert not scroll.horizontalScrollBar().isVisible()
    detail = checked.panel.detail
    assert detail.height() >= detail.heightForWidth(detail.width()) - 2
    form.input_combo.setCurrentIndex(1)
    smiles = form.input_widgets["smiles"].checked
    smiles.edit.setText("CC(C)(C)" * 40)  # a very long SMILES must not widen the form
    smiles.name_edit.setText("long name")
    smiles.wait()
    for _ in range(3):
        app.processEvents()
    assert not scroll.horizontalScrollBar().isVisible()
