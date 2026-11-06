"""What the assistant sees on the LUCI window, and what it can do there.

* ``state()``  short summary of the screen (sent with every question)
* ``detail()`` everything visible on the screen (tool view_screen)
* actions      fill the form, open programs, run (only with CONTROL on)

The window knows nothing about the assistant: this module reads its widgets.
"""

from __future__ import annotations

from pathlib import Path

from ..registry import INPUT_LABELS, LAYERS, PROGRAM_BY_KEY, layer as find_layer
from .tools import Tool, Wait, boolean, enum, integer, s, strings

MAX_CONSOLE = 4000


def _alive(widget) -> bool:
    try:
        widget.objectName()
        return True
    except RuntimeError:
        return False


def _columns_of(widget) -> list[str]:
    """Columns offered by a MultiColumnSelector (empty until a CSV is loaded)."""
    model = widget.model()
    columns = []
    for row in range(model.rowCount()):
        item = model.item(row)
        if item is not None and item.isEnabled():
            columns.append(item.text())
    return columns


def _choice_pairs(choices):
    return [c if isinstance(c, tuple) else (c, c) for c in choices]


class LuciScreen:
    """The main window, as the assistant sees it."""

    def __init__(self, window):
        self.w = window

    # ------------------------------------------------------------------ where
    def layer(self):
        return LAYERS[self.w.stack.currentIndex()]

    def workspace(self):
        return self.w.current_workspace()

    def page(self):
        return self.workspace().current_package()

    def form(self):
        page = self.page()
        return page.form if page is not None else None

    def program_key(self) -> str | None:
        form = self.form()
        return form.package.key if form is not None else None

    def ready(self) -> bool:
        form = self.form()
        checked = form.standard_input() if form is not None else None
        return checked is None or not checked.is_checking()

    # ------------------------------------------------------------------ reading
    def state(self) -> str:
        if getattr(self.w, "is_home", lambda: False)():
            return ("Home page 'Choose a layer': one card per layer (click it to open) with its programs, plus a search box; "
                    "the sidebar and the input filter appear once a layer is open. Layers: "
                    + "; ".join(f"{l.title} ({l.delivers})" for l in LAYERS) + ".")
        layer = self.layer()
        page = self.page()
        filters = sorted(self.w.filter_bar.selected())
        filter_text = f" Filter 'What do you have?': {', '.join(INPUT_LABELS[k] for k in filters)}." if filters else ""
        if page is None:
            cards = []
            for card in self.workspace().landing.cards:
                if card.isVisibleTo(self.workspace().landing):
                    cards.append(f"{card.spec.name} [{card.pill.text()}]")
            return f"Layer {layer.title} landing page. Program cards: {'; '.join(cards) or 'none shown'}.{filter_text}"
        form = page.form
        spec = form.package
        parts = [f"Program page {spec.name} (key {spec.key}) in {layer.title}. Status: {page.pill.text()}."]
        if page.banner.isVisibleTo(page):
            parts.append(f"Banner: {self._plain(page.banner.label.text())}")
        if form.variant_combo is not None or len(spec.variants) > 1:
            parts.append(f"Method/variant: {form.current_variant().label}.")
        mode = form.current_mode()
        if mode is not None:
            value = form.input_value()
            parts.append(f"Input type: {mode.label}. Input: {value or '(empty)'}"
                         + (f", code_name: {form.code_name()}" if form.code_name() else "") + ".")
            check = self._check_summary(form)
            if check:
                parts.append(f"Input check: {check}")
        changed = form.values()
        if changed:
            shown = ", ".join(f"{self._label(spec, k)}={v}" for k, v in changed.items())
            parts.append(f"Options sent to the program: {shown}.")
        missing = form.missing_required()
        if missing:
            parts.append(f"Required and empty: {', '.join(missing)}.")
        advanced = form.advanced.toPlainText().strip()
        if advanced:
            parts.append(f"Advanced flags: {advanced}.")
        parts.append(f"Output folder: {form.output_dir() or '(automatic)'}.")
        if page.is_running():
            parts.append("A run is IN PROGRESS.")
        tail = self._console_tail(page, 6)
        if tail:
            parts.append("Last console lines: " + " | ".join(tail))
        return " ".join(parts) + filter_text

    def detail(self):
        page = self.page()
        if page is None:
            return {"screen": self.state(), "layers": [l.title for l in LAYERS]}
        form = page.form
        spec = form.package
        rows = []
        for option in spec.options:
            if option.key not in form.widgets:
                continue
            visible = form._visible(option)
            row = {"key": option.key, "label": option.label, "kind": option.kind,
                   "value": form._raw_value(option.key), "visible": visible}
            if option.required:
                row["required"] = True
            widget = form.widgets[option.key]
            if option.kind == "choice":
                row["choices"] = [v for _, v in _choice_pairs(option.choices)]
            elif option.kind == "columns":
                row["choices"] = [widget.itemData(i) for i in range(1, widget.count())] or "load the input CSV first"
            elif option.kind == "multi_columns":
                row["choices"] = _columns_of(widget) or "load the input CSV first"
            elif option.kind == "multi_choice":
                row["choices"] = list(widget.boxes)
            rows.append(row)
        result = {"screen": self.state()}
        checked = form.standard_input()
        if checked is not None and checked.result is not None:
            result["input_problems"] = self._problems(checked)
        if page.requirements.isVisibleTo(page):
            result["notes_banner"] = self._plain(page.requirements.label.text())
        result.update({
            "input_types": [{"key": m.key, "label": m.label, "kind": m.kind or m.dialog} for m in spec.input_modes],
            "options": rows,
            "command_preview": form.preview.toPlainText(),
            # Last, and short: a long console must not push the rest out of the answer.
            "console_tail": self._console_tail(page, 20),
        })
        return result

    def console(self, lines: int = 80):
        page = self.page()
        if page is None:
            return {"error": "No program page is open."}
        return {"program": page.form.package.name, "running": page.is_running(),
                "console": self._console_tail(page, lines)}

    @staticmethod
    def _plain(html_text: str) -> str:
        import re
        return re.sub(r"<[^>]+>", "", html_text).replace("&nbsp;", " ").strip()

    @staticmethod
    def _label(spec, key):
        option = spec.option(key)
        return option.label if option else key

    @staticmethod
    def _console_tail(page, lines):
        text = page.console.toPlainText()
        rows = [row for row in text.splitlines() if row.strip()]
        tail = rows[-lines:]
        joined = "\n".join(tail)
        return joined[-MAX_CONSOLE:].splitlines() if len(joined) > MAX_CONSOLE else tail

    def _check_summary(self, form) -> str:
        checked = form.standard_input()
        if checked is None:
            return ""
        if checked.is_checking():
            return "being checked..."
        bad, total, fatal = checked.problems()
        if fatal:
            return f"cannot be used: {fatal}"
        if not total:
            return ""
        skip = " ('Leave out the N with errors' is ticked)" if checked.skip_invalid() else ""
        return f"{total} entries, {bad} with errors{skip}."

    @staticmethod
    def _problems(checked, limit=25):
        rows = []
        result = checked.result
        records = getattr(result, "records", None) or getattr(result, "files", None) or []
        for item in records:
            issues = [i for i in item.issues if i.level in ("error", "warning")]
            if not issues:
                continue
            name = getattr(item, "code_name", None) or getattr(getattr(item, "source", None), "name", "?")
            where = getattr(item, "line", "")
            rows.append({"entry": name, "line": where,
                         "problems": [f"{i.level}: {i.text()}" for i in issues]})
            if len(rows) >= limit:
                break
        for issue in getattr(result, "issues", []):
            if issue.level != "info":
                rows.insert(0, {"entry": "(whole input)", "problems": [f"{issue.level}: {issue.text()}"]})
        return rows

    # ------------------------------------------------------------------ actions
    def open_layer(self, layer: str):
        try:
            spec = find_layer(layer)
        except KeyError:
            return {"error": f"Unknown layer '{layer}'. Layers: {', '.join(l.key for l in LAYERS)}."}
        if hasattr(self.w, "leave_home"):
            self.w.leave_home()
        self.w.layer_list.setCurrentRow([l.key for l in LAYERS].index(spec.key))
        self.workspace().go_home()
        return self.state()

    def open_program(self, program: str):
        spec = PROGRAM_BY_KEY.get(program)
        if spec is None:
            from ..registry import program as find_program
            wanted = str(program).strip().lower()
            try:
                spec = find_program(wanted)
            except KeyError:
                matches = [p for p in PROGRAM_BY_KEY.values()
                           if wanted in p.key.lower() or wanted in p.name.lower().replace(" ", "")
                           or wanted in p.name.lower()]
                spec = matches[0] if len(matches) == 1 else None
        if spec is None:
            return {"error": f"Unknown program '{program}'. Keys: {', '.join(PROGRAM_BY_KEY)}."}
        if hasattr(self.w, "leave_home"):
            self.w.leave_home()
        self.w.layer_list.setCurrentRow([l.key for l in LAYERS].index(spec.layer))
        self.workspace().select_package(spec.key)
        return self.state()

    def back_to_layer(self):
        self.workspace().go_home()
        return self.state()

    def set_filter(self, inputs: list | None = None):
        wanted = set(inputs or [])
        unknown = wanted - set(self.w.filter_bar.buttons)
        if unknown:
            return {"error": f"Unknown input kinds {sorted(unknown)}. Use {sorted(self.w.filter_bar.buttons)}."}
        for key, button in self.w.filter_bar.buttons.items():
            button.setChecked(key in wanted)
        return self.state()

    def _require_form(self, program=None):
        if program and program != self.program_key():
            opened = self.open_program(program)
            if isinstance(opened, dict):
                return None, opened
        form = self.form()
        if form is None:
            return None, {"error": "No program page is open: open a program first (open_program)."}
        return form, None

    def set_input(self, value: str = "", input_type: str | None = None, code_name: str | None = None,
                  program: str | None = None):
        form, error = self._require_form(program)
        if error:
            return error
        spec = form.package
        if input_type:
            modes = spec.input_modes
            match = next((i for i, m in enumerate(modes)
                          if input_type.lower() in (m.key.lower(), m.label.lower(), (m.kind or "").lower())), None)
            if match is None:
                return {"error": f"{spec.name} has no input type '{input_type}'. Types: "
                                 + ", ".join(f"{m.key} ({m.label})" for m in modes)}
            if form.input_combo is not None:
                form.input_combo.setCurrentIndex(match)
        mode = form.current_mode()
        if mode is None:
            return {"error": f"{spec.name} takes no input file: fill its options instead."}
        panel = form.input_widgets[mode.key]
        if value is not None:
            if mode.dialog in ("file", "directory") and value:
                path = Path(value).expanduser()
                if mode.dialog == "file" and not path.is_file():
                    return {"error": f"{value} is not a file on this computer."}
                if mode.dialog == "directory" and not path.is_dir():
                    return {"error": f"{value} is not a folder on this computer."}
            if mode.dialog in ("file", "directory") and value:
                value = str(Path(value).expanduser().resolve())
            panel.edit.setText(value)
        checked = getattr(panel, "checked", None)
        if code_name is not None and checked is not None and hasattr(checked, "name_edit"):
            checked.name_edit.setText(code_name)
        if checked is not None:
            checked.check()
            return Wait(lambda: not checked.is_checking(), self.state, 120)
        return self.state()

    def set_options(self, options: list, program: str | None = None):
        form, error = self._require_form(program)
        if error:
            return error
        spec = form.package
        report = []
        for item in options or []:
            key = str(item.get("option", "")).strip()
            value = item.get("value", "")
            option = spec.option(key) or next((o for o in spec.options if o.label.lower() == key.lower()), None)
            if option is None:
                report.append({"option": key, "error": "No such option; use view_screen to see the keys, or put "
                                                       "the native flag in set_advanced_flags."})
                continue
            message = self._set_widget(form, option, value)
            row = {"option": option.key, "set": form._raw_value(option.key)}
            if message:
                row["error"] = message
            elif not form._visible(option):
                row["warning"] = "Set, but hidden now (it only applies to another input type, method or choice)."
            report.append(row)
        form.update_preview()
        return {"results": report, "screen": self.state()}

    @staticmethod
    def _set_widget(form, option, value) -> str:
        widget = form.widgets[option.key]
        kind = option.kind
        text = "" if value is None else str(value)
        if kind == "bool":
            on = text.strip().lower() in ("true", "1", "yes", "on", "si", "sí")
            widget.setChecked(on)
            return ""
        if kind in ("choice", "columns"):
            if not text:
                widget.setCurrentIndex(0)
                return ""
            index = widget.findData(text)
            if index < 0:
                for i in range(widget.count()):
                    if widget.itemText(i).strip().lower() == text.strip().lower() or \
                            str(widget.itemData(i)).lower() == text.strip().lower():
                        index = i
                        break
            if index < 0:
                choices = [str(widget.itemData(i)) for i in range(widget.count()) if widget.itemData(i)]
                return f"'{text}' is not a choice. Choices: {', '.join(choices) or '(load the CSV first)'}."
            widget.setCurrentIndex(index)
            return ""
        if kind == "multi_columns":
            wanted = value if isinstance(value, list) else [v.strip() for v in text.strip("[]").split(",") if v.strip()]
            available = _columns_of(widget)
            unknown = [v for v in wanted if v not in available]
            if unknown:
                return (f"Unknown columns {unknown}; the input CSV has: {available}." if available else
                        "Load the input CSV first: the columns come from its header.")
            widget.set_values(wanted)
            return ""
        if kind == "multi_choice":
            wanted = value if isinstance(value, list) else [v.strip() for v in text.strip("[]").split(",") if v.strip()]
            unknown = [v for v in wanted if v not in widget.boxes]
            for name, box in widget.boxes.items():
                box.setChecked(name in wanted)
            return f"Unknown values {unknown}; valid: {list(widget.boxes)}." if unknown else ""
        widget.setText(text)
        return ""

    def set_variant(self, variant: str, program: str | None = None):
        form, error = self._require_form(program)
        if error:
            return error
        if form.variant_combo is None:
            return {"error": f"{form.package.name} has no method selector (the input type picks it, if any)."}
        index = form.variant_combo.findData(variant)
        if index < 0:
            wanted = str(variant).strip().lower()
            for i in range(form.variant_combo.count()):
                label = form.variant_combo.itemText(i).lower()
                if str(form.variant_combo.itemData(i)).lower() == wanted or label == wanted or label.startswith(wanted):
                    index = i
                    break
        if index < 0:
            keys = [form.variant_combo.itemData(i) for i in range(form.variant_combo.count())]
            return {"error": f"Unknown method '{variant}'. Methods: {keys}."}
        form.variant_combo.setCurrentIndex(index)
        return self.state()

    def set_advanced_flags(self, flags: str, append: bool = False, program: str | None = None):
        form, error = self._require_form(program)
        if error:
            return error
        current = form.advanced.toPlainText().strip()
        form.advanced.setPlainText(f"{current} {flags}".strip() if append and current else flags)
        return {"command_preview": form.preview.toPlainText()}

    def set_output_folder(self, folder: str = "", program: str | None = None):
        form, error = self._require_form(program)
        if error:
            return error
        if form.destination is None:
            return {"error": f"{form.package.name} has no output folder field."}
        form.destination.setText(folder)
        return {"output_folder": form.output_dir(), "command_preview": form.preview.toPlainText()}

    def leave_out_invalid(self, leave_out: bool = True):
        form, error = self._require_form()
        if error:
            return error
        checked = form.standard_input()
        if checked is None or checked.panel.skip.isHidden():
            return {"error": "There is nothing to leave out: the input has no entries with errors."}
        checked.set_skip_invalid(leave_out)
        form.update_preview()
        return self.state()

    def reset_form(self, program: str | None = None):
        form, error = self._require_form(program)
        if error:
            return error
        form.reset()
        return self.state()

    def run(self, program: str | None = None):
        form, error = self._require_form(program)
        if error:
            return error
        page = self.page()
        if page.is_running():
            return {"error": "This program is already running."}
        if not page.run_button.isEnabled():
            return {"error": f"Run is not possible now: {page.pill.text()}. "
                             + self._plain(page.banner.label.text())}
        missing = form.missing_required()
        if missing:
            return {"error": "Required fields are empty: " + ", ".join(missing)}
        checked = form.standard_input()
        if checked is not None:
            checked.check()  # the file may have changed since it was last read
            checked.wait(30000)
            bad, total, fatal = checked.problems()
            if fatal:
                return {"error": f"The input cannot be used: {fatal}"}
            if bad and not checked.skip_invalid():
                return {"error": f"{bad} of {total} entries have errors. Fix them, or ask the user whether "
                                 "to leave them out (leave_out_invalid) before running."}
        page.run()
        if not page.is_running():
            return {"error": "LUCI did not start the run; read the console or ask the user what the window shows."}
        return {"started": True, "command": form.preview.toPlainText(), "note": "Follow it with read_console."}

    def _page_of(self, program: str | None):
        """The page of ``program`` (any layer), or the page on screen."""
        if program:
            for workspace in self.w.workspaces.values():
                if program in workspace.pages:
                    return workspace.pages[program]
            return None
        return self.page()

    def wait_for_run(self, program: str | None = None, minutes: float = 10):
        """Wait until a run ends (at most ``minutes``), then report how it ended and where the results are."""
        import time
        page = self._page_of(program)
        if page is None:
            return {"error": "No program page is open." if not program else f"Unknown program '{program}'."}
        if not page.is_running():
            return self._run_report(page, waited=0)
        minutes = max(0.5, min(float(minutes or 10), 30))
        start = time.monotonic()
        limit = start + minutes * 60

        def ready():
            return not page.is_running() or time.monotonic() > limit

        def result():
            report = self._run_report(page, waited=round(time.monotonic() - start))
            if page.is_running():
                report["still_running"] = True
                report["note"] = ("The run is still going. Tell the user, or call wait_for_run again if they "
                                  "asked you to carry on with the next steps.")
            return report
        return Wait(ready, result, seconds=minutes * 60 + 30)

    def _run_report(self, page, waited):
        import re
        tail = self._console_tail(page, 40)
        text = "\n".join(tail)
        folders = re.findall(r"\[LUCI\] Output folder: (.+)", page.console.toPlainText())
        codes = re.findall(r"finished with exit code (-?\d+)", text)
        report = {"program": page.form.package.name, "running": page.is_running(), "waited_seconds": waited,
                  "exit_code": int(codes[-1]) if codes else None,
                  "output_folder": folders[-1].strip() if folders else page.form.output_dir(),
                  "console_tail": tail}
        if report["exit_code"] not in (None, 0):
            report["note"] = "The run failed: read the console tail and the program's logs before going on."
        return report

    def stop(self):
        page = self.page()
        if page is None or not page.is_running():
            return {"error": "Nothing is running on this page."}
        page.stop()
        return {"stopping": True}

    def install(self, program: str | None = None):
        form, error = self._require_form(program)
        if error:
            return error
        page = self.page()
        if page.pill.property("state") not in ("missing", "update"):
            return {"error": f"Nothing to install: {page.pill.text()}."}
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, page.install)
        return {"installing": True, "note": "The installation window is open; it can take several minutes."}

    def save_workflow(self, path: str):
        import json
        from .. import __version__
        target = Path(path).expanduser()
        if not target.is_absolute():
            return {"error": "Give a full path (for example C:\\Users\\me\\Documents\\csearch.json)."}
        if target.suffix.lower() != ".json":
            return {"error": "A workflow is saved as a .json file."}
        if target.exists():
            try:
                existing = json.loads(target.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                existing = None
            if not (isinstance(existing, dict) and ("luci" in existing or "module" in existing)):
                return {"error": f"{target} exists and is not a LUCI workflow; it is left alone."}
        target.write_text(json.dumps({"luci": __version__, "layer": self.layer().key,
                                      "state": self.workspace().save_state()}, indent=2), encoding="utf-8")
        return {"saved": str(target.resolve())}

    def load_workflow(self, path: str):
        import json
        target = Path(path).expanduser()
        if not target.is_file():
            return {"error": f"{path} does not exist."}
        try:
            data = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            return {"error": f"{target.name} is not a LUCI workflow ({exc})."}
        if not (isinstance(data, dict) and isinstance(data.get("state"), dict)
                and (data.get("layer") or data.get("module"))):
            return {"error": f"{target.name} is not a LUCI workflow (it needs 'layer' and 'state')."}
        self.w.load_workflow(str(target))
        return self.state()


def screen_tools(session) -> list[Tool]:
    """Tools that read or drive the window. ``session.screen`` is the LuciScreen."""
    sc = lambda: session.screen  # noqa: E731
    program = s("Program key (optional): opens that program first if another one is on screen.")
    layers = [l.key for l in LAYERS]
    return [
        Tool("view_screen", "Everything visible now: the program, its input and the problems LUCI found in it, "
             "every option with its key, kind, value, choices and whether it is shown, the command preview and "
             "the console. Use it before filling a form and whenever the user asks about 'this'.",
             {}, (), lambda: sc().detail(), thread="ui", label="Looking at the screen..."),
        Tool("read_console", "The last lines of the program's console (a run's output and LUCI's [LUCI] messages).",
             {"lines": integer("How many lines (80 by default).")}, (), lambda lines=80: sc().console(lines),
             thread="ui", label="Reading the console..."),
        Tool("open_layer", "Show a layer's landing page with its program cards.",
             {"layer": enum(layers, "Layer.")}, ("layer",), lambda layer: sc().open_layer(layer),
             thread="ui", control=True, label="Opening the layer..."),
        Tool("open_program", "Open a program's page.", {"program": enum(sorted(PROGRAM_BY_KEY), "Program key.")},
             ("program",), lambda program: sc().open_program(program), thread="ui", control=True,
             label="Opening the program..."),
        Tool("back_to_layer", "Go back from the program page to its layer's cards.", {}, (),
             lambda: sc().back_to_layer(), thread="ui", control=True, label="Going back..."),
        Tool("set_input_filter", "Set the 'What do you have?' filter (empty list clears it).",
             {"inputs": strings("Input kinds: smiles, structures, qm_output, reaction, table.")}, (),
             lambda inputs=None: sc().set_filter(inputs), thread="ui", control=True, label="Filtering..."),
        Tool("set_input", "Choose the input type and fill the input: a CSV or file path, a folder, or a SMILES "
             "(with code_name). Waits for LUCI's check and returns it.",
             {"value": s("Path of the file or folder, or the SMILES. Empty string clears it."),
              "input_type": s("Input type key or label (molecules, smiles, structures, or the program's own)."),
              "code_name": s("code_name for a typed SMILES."), "program": program},
             ("value",), lambda **k: sc().set_input(**k), thread="ui", control=True, label="Filling the input..."),
        Tool("set_options", "Fill option fields of the form by key (or label). Values are text: 'true'/'false' "
             "for switches, the choice value for dropdowns, '' to clear.",
             {"options": {"type": "array", "description": "Options to set.",
                          "items": {"type": "object", "additionalProperties": False, "required": ["option", "value"],
                                    "properties": {"option": s("Option key or label."), "value": s("Value.")}}},
              "program": program},
             ("options",), lambda **k: sc().set_options(**k), thread="ui", control=True, label="Filling the form..."),
        Tool("set_method", "Choose the method/variant (programs with a 'Level' selector, e.g. TS-tools xtb/gxtb/mlip).",
             {"variant": s("Variant key."), "program": program}, ("variant",), lambda **k: sc().set_variant(**k),
             thread="ui", control=True, label="Choosing the method..."),
        Tool("set_advanced_flags", "Write native flags of the program in 'Advanced flags' (for options with no field).",
             {"flags": s("Flags as on the program's command line."), "append": boolean("Add to what is there."),
              "program": program}, ("flags",), lambda **k: sc().set_advanced_flags(**k), thread="ui", control=True,
             label="Writing advanced flags..."),
        Tool("set_output_folder", "Set the output folder ('' = automatic: next to the input).",
             {"folder": s("Folder path."), "program": program}, ("folder",), lambda **k: sc().set_output_folder(**k),
             thread="ui", control=True, label="Setting the output folder..."),
        Tool("leave_out_invalid", "Tick or untick 'Leave out the N with errors' (only when the user agreed).",
             {"leave_out": boolean("True to leave the bad entries out.")}, ("leave_out",),
             lambda leave_out: sc().leave_out_invalid(leave_out), thread="ui", control=True, label="Updating..."),
        Tool("reset_form", "Clear every field of the program's form.", {"program": program}, (),
             lambda **k: sc().reset_form(**k), thread="ui", control=True, label="Clearing the form..."),
        Tool("run_program", "Press Run (only when the user asked to run). Refuses when inputs have errors or "
             "required fields are empty.", {"program": program}, (), lambda **k: sc().run(**k), thread="ui",
             control=True, label="Starting the run..."),
        Tool("wait_for_run", "Wait until a run ends (up to the given minutes) and get its exit code, its output "
             "folder and the end of the console. Use it after run_program when the user asked you to run several "
             "programs one after another, before preparing the next step.",
             {"program": s("Program key of the run (optional: the page on screen)."),
              "minutes": {"type": "number", "description": "Longest wait, 0.5 to 30 minutes (10 by default)."}},
             (), lambda **k: sc().wait_for_run(**k), thread="ui", label="Waiting for the run to finish..."),
        Tool("stop_program", "Press Stop on the current program.", {}, (), lambda: sc().stop(), thread="ui",
             control=True, label="Stopping..."),
        Tool("install_program", "Open the installation of the program's environment (only when asked: it downloads "
             "hundreds of MB).", {"program": program}, (), lambda **k: sc().install(**k), thread="ui", control=True,
             label="Installing..."),
        Tool("save_workflow", "Save the current form as a workflow JSON file.", {"path": s("File path (.json).")},
             ("path",), lambda path: sc().save_workflow(path), thread="ui", control=True, label="Saving..."),
        Tool("load_workflow", "Load a workflow JSON file into the window.", {"path": s("File path.")}, ("path",),
             lambda path: sc().load_workflow(path), thread="ui", control=True, label="Loading..."),
    ]
