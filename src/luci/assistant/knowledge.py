"""What the assistant knows: LUCI itself, every program in it, and their upstream documentation.

Three sources, all turned into self-contained pieces for the search (rag.py):

* the hand-written pages below (the window, the inputs, environments, settings,
  the command line, common problems);
* pages generated from the registry at run time (every program, variant, input
  and option with its flag, default and help), so they are never out of date;
* the upstream documentation of each program (READMEs, docs, parameter lists
  of the installed versions), bundled in ``knowledge/programs/<key>.md``, plus
  LUCI's own README and docs when LUCI runs from its folder.

The page of the program on screen (and its layer) is always sent whole; the
rest only when the question touches it.
"""

from __future__ import annotations

import ast
from pathlib import Path
import re

from ..registry import ENV_BY_KEY, INPUT_LABELS, LAYERS, PROGRAMS, programs_in
from ..registry.model import COST_LABELS, MODE_LABELS

KNOWLEDGE_DIR = Path(__file__).resolve().parent / "knowledge"
# Upstream documentation files that cover several LUCI programs.
UPSTREAM = {"aqme_csearch": "aqme", "aqme_cmin": "aqme", "aqme_qdescp": "aqme"}
CHUNK = 2600

APP_MAP = """\
LUCI (Layered Unified Computational Interfaces) is a desktop application (PySide6) of a university research group in computational chemistry. It brings many cheminformatics programs together behind one window and one command line ("luci"), each program in its own isolated environment. It is used mostly on Windows laptops, also on Linux.

THE WINDOW
- Home page (when LUCI opens, and when the logo or the Home button is clicked): "Choose a layer", one card per layer listing its programs (coloured by state: green installed, blue update, red not for this system, dashed coming soon) and a search box to find a program by name (e.g. "AQME-CSEARCH"); clicking anywhere on a layer card opens the layer and clicking a program name opens it directly. Inside a layer or program, the "Home" button at the top of the sidebar goes back to this page.
- Left sidebar (once a layer is open): the LUCI logo (click = home) and the six LAYERS and the six LAYERS, named after what the user gets back: LUCI-STRUCT (3D structures), LUCI-THERMO (energies), LUCI-REACT (transition states), LUCI-FEAT (descriptors), LUCI-PRED (models and predictions), LUCI-DESIGN (next experiments). With the input filter on, each layer shows "N of M match".
- Top bar "What do you have?": amber toggles SMILES, 3D structures, QM outputs, Reactions, CSV / tables, and "Clear". They hide the programs that cannot start from what the user has.
- Layer landing page: title, one sentence, and a CARD per program: name, status pill, description, outlined input tags (and a purple "Iterative loop" tag for EDBO+, ScopeBO and BoReact), and the buttons Open, Install / Update, Uninstall. Status pills: "Installed" (green), "Not installed" (grey), "Update available" (a newer environment definition ships with this LUCI), "Coming soon" (code not public yet), and in red "Linux / WSL only" or "Not for this system" when the program cannot run on this computer.
- Program page (after Open): "Back", "Uninstall", orange "Run" and red-outlined "Stop" buttons at the top; title with the status pill; caption "<layer> · <description>"; banners: orange "X is not installed yet (size). LUCI installs it in its own environment" with an Install button, grey-outlined notes ("Needs Gaussian 16...", program notes), red "Cannot run on this computer". Then the FORM, built from the program's description:
  · "Input and output" section: "Input type" dropdown (when the program accepts several kinds of input), the "Input" field, input-specific options, and "Output directory" (empty = automatic: next to the input, or the last folder used for loop programs, or the default results folder).
  · "Method" section with a "Level" dropdown for programs with several variants (TS-tools: xTB, g-xTB, MLIP).
  · Option sections (Method, Core options, Constraints, Output...): one row per native flag, with a "?" button explaining it; rows marked "*" are required; placeholders starting "e.g." are examples, not values. Only options the user changes are sent; the program's own defaults apply otherwise. Some rows appear only for some inputs, variants or other choices.
  · "Advanced flags": free text with any other native flag of the program, written as on its command line (the "?" opens the program's documentation website).
  · "Command preview": the exact LUCI command that Run executes, with a "Copy command" button.
  · "Execution console" at the bottom: the live output of the run; "[LUCI]" lines are LUCI's own messages.
- Run: LUCI checks the input first (see STANDARD INPUTS), then runs the program in its environment and streams its output. Stop ends the run and everything it started (Windows: taskkill of the whole tree). Several programs can run at the same time on different pages.
- Menus: File > Save workflow... / Load workflow... (a JSON with the layer, program and every field; LUCI 0.1 workflows load too) / Exit. Tools > Environments... (every environment with install / update / uninstall) and Tools > Settings... Help > About LUCI.
- Tools > Settings: Gaussian 16 folder, ORCA folder, g-xTB executable (only Linux programs use them), Hugging Face token (UMA weights for ThermoMLIP and TS-tools MLIP), OpenAI API key (this assistant), Results folder (default for results), pixi executable (automatic otherwise), "Restricted network" (firewalls that block the conda/PyPI name mapping download).
- Installing: the Install button opens a window with the progress (expected download size, a heartbeat every 15 s because pixi prints nothing while it works) and a Stop button. An interrupted install leaves the program "Not installed" and the next install cleans it.
"""

STANDARD_INPUTS = """\
STANDARD INPUTS (the same in every program that starts from molecules or structures)
- Molecules (CSV): a CSV file with a header and the columns smiles and code_name (one molecule per row; any other column such as charge or mult is kept). code_name names every output file of that molecule in every program (ethanol -> ethanol_rdkit.sdf in CSEARCH), so results can be followed from layer to layer. LUCI writes the layout each program wants: AQME gets SMILES,code_name; ThermoMLIP gets id,smiles; thermoGNN, Auto-QChem and ScopeBO get smiles,code_name. The copy goes to <output>/.luci/inputs/.
- One SMILES: typed in, with an optional code_name (empty = "molecule"). For programs that only read files it is passed as a one-row CSV.
- Folder of 3D structures: LUCI always hands programs SDF files. SDF files are used as they are; XYZ, MOL, MOL2 and PDB are converted with Open Babel inside the program's own environment; Gaussian .gjf/.com inputs and Gaussian/ORCA .log/.out outputs are read by LUCI (last geometry, with the charge and multiplicity of that job) and converted too. Converted files go to <output>/input_sdf/ (cached: only changed files are converted again; LUCI never overwrites or deletes a file it did not create). Each SDF gets AQME's "Real charge" and "Mult" properties when the file states them; for XYZ files write "charge=1 mult=2" in the comment line. When two files share a name the SDF wins, then a finished calculation (.log/.out) over its input (.gjf). 2D drawings (ChemDraw exports: a MOL with a 2D header and all z = 0) are refused: give the SMILES and build 3D with AQME CSEARCH instead.
- Tables (ROBERT, EDBO+, ScopeBO, BoReact): CSV files only (not Excel).
- WHAT LUCI CHECKS (no chemistry library: LUCI does NOT check SMILES; the programs do): the CSV itself (Excel workbook saved as .csv, encoding, ";" separators from Spanish Excel, Excel's "sep=" line, unclosed quotes, rows with a wrong number of values), the columns (missing smiles/code_name, with the column to rename), empty cells, and the names (spaces become "_"; characters Windows forbids < > : " / \\ | ? *, reserved names CON, PRN, AUX, NUL, COM1..., trailing dots, names repeated even with different case are errors; accents, a leading "-" and very long names are warnings). Structure files: empty, unreadable, Z-matrix .gjf, not a Gaussian/ORCA output, unknown elements in XYZ, 2D drawings.
- In the window the check appears under the input as soon as it is chosen: a verdict ("40 molecules, 38 OK, 2 with errors"), "Problems only" toggle, a list (status, code_name, problem, line, SMILES; for folders: file and what LUCI does with it), the explanation of the selected row, and "Leave out the N with errors" (= --skip-invalid). "Check again" re-reads the file after editing it. Errors stop Run, with a dialog offering "Leave them out and run the rest".
- After a run, LUCI lists the molecules or files that produced no result ("No result for 1 of 4 inputs: X. Look for their names in CSEARCH_data.dat to see why"): usually a SMILES the program could not read.
- Paths with [ ] * ? confuse the programs (they read them as wildcards): LUCI refuses folders with them. ROBERT's inputs are copied to the output folder (ROBERT rejects paths with spaces); LUCI never overwrites a different file with the same name there.
"""

ENVIRONMENTS = """\
ENVIRONMENTS AND INSTALLATION
- Each program has its own pixi environment (AQME's three modules share one). Programs are never installed together, so one program's versions never break another. Each environment ships with a pixi.lock: everyone installs exactly the same versions (pixi install --frozen), nothing is solved on the user's computer.
- The user never needs pixi: LUCI uses the one on PATH or downloads a pinned copy into its own folder. LUCI's folder: %LOCALAPPDATA%\\LUCI on Windows, ~/.local/share/luci on Linux (LUCI_HOME changes it). Environments go to <LUCI folder>/envs/<key>.
- AQME 2.1 and ROBERT are installed from GitHub: Git must be installed on Windows (git-scm.com, default options). If git cannot reach GitHub, LUCI downloads a zip instead.
- Sizes: AQME ~2 GB, ROBERT ~1.5 GB, MolSimplify ~1.5 GB, thermoGNN ~3 GB, racerTS ~600 MB, Morfeus ~500 MB, DBSTEP and GoodVibes ~300 MB. Open Babel is in the AQME, Auto-QChem, MolSimplify, DBSTEP, racerTS, Morfeus and TS-tools environments (used to convert structures to SDF).
- "Update available": this LUCI version ships a newer environment definition; Update reinstalls it. Uninstall deletes only that environment (files and results are kept).
- Linux only: TS-tools, ThermoMLIP, and CREST inside AQME (on Windows, CSEARCH works with RDKit; CREST is Linux/WSL only). Coming soon (code not public yet): TS-tools g-xTB, TS-tools MLIP, BoReact.
- Typical install problems: no internet or a proxy (pixi cannot download; try "Restricted network" in Settings behind firewalls), Git missing (AQME, ROBERT), antivirus locking files (retry), very little disk space.
- LUCI itself is installed with: python -m pip install -e ".[gui]" in the LUCI folder, and started with luci-gui (or python -m luci --gui).
"""

COMMAND_LINE = """\
COMMAND LINE (the window runs exactly these commands; the Command preview shows them)
- luci <layer> --backend <program> [--variant V] [--molecules F.csv | --molecule SMILES --code-name N | --structures DIR] [--skip-invalid] [--output-dir D] [--dry-run] -- <native flags of the program>
- Everything after "--" goes to the program unchanged, with its own flag names (so its documentation applies as is). --dry-run prints the command without running.
- luci programs [--layer L] [--have smiles,structures,qm_output,reaction,table]; luci env list | install <program> | update <program> | uninstall <program> | path; luci check molecules.csv | folder (checks the CSV/names or the structure files without running).
- Examples: luci struct --backend aqme_csearch --molecules mols.csv -- --program rdkit --sample 25 ; luci feat --backend dbstep --structures ligands/ -- --sterimol --atom1 1 --atom2 2 ; luci struct --backend racerts --structures ts_guesses/ -- --task ts --reacting_atoms "2 3 4" ; luci feat --backend morfeus --structures conformers/ -- --descriptors "[sterimol,buried_volume]" --atom_1 1 --atom_2 2 ; luci thermo --backend goodvibes -- "outputs/*.log" -q --temp 353.15.
- LUCI 0.1 commands still work (luci --conf --aqme ..., luci gopt ..., luci --pred --robert ...).
- Exit codes: the program's own; 128+signal when it was stopped or crashed; LUCI says "crashed (killed by the system)" for segmentation faults (a bug or missing library in the program, not the input).
"""

ASSISTANT = """\
THE ASSISTANT (you)
- The round robot button at the bottom right of the window opens this chat; the small switch under it is CONTROL mode (green = on). The conversation is the same on every page.
- Control OFF: you explain, check and advise. Control ON: you can drive the window (open layers and programs, choose the input type, fill the input, the options, the advanced flags and the output folder, read files, press Run when asked, wait for a run to finish and chain the next program), and create text files where the user says (molecule CSVs, structure and QM inputs, merged result tables) with write_file. The assistant only writes data/input formats (.csv, .tsv, .txt, .smi, .xyz, .sdf, .mol, .mol2, .pdb, .gjf, .com, .inp, .json, .yaml, .dat, .md), never scripts, never inside LUCI's environments, and never replaces a file it did not write itself.
- Globe button (chat header): web search on/off. Microphone: dictation (the text stays in the box until sent). Reload button: new conversation.
- The OpenAI key is in Tools > Settings > OpenAI API key (or openai_key.txt in the LUCI folder). Errors about the key or credit are fixed there or at platform.openai.com.
"""

TROUBLESHOOTING = """\
COMMON PROBLEMS AND WHAT THEY MEAN
- "X is not installed yet": press Install (banner or card). "Update available": press Update.
- Run is greyed out: the program is not installed, or not available on this system, or a run is already going.
- "Missing information: fill in before running": required fields (marked *) are empty.
- "No result for N inputs" after AQME: the SMILES of those molecules could not be processed; look in CSEARCH_data.dat / CMIN_data.dat / QDESCP_data.dat in the output folder for lines starting with "x" next to their names. Typical SMILES mistakes: unclosed ring numbers, unbalanced parentheses, a pyrrole-type nitrogen written "n" instead of "[nH]", a 4-bonded N without [N+], copied characters from Word (en dash, non-breaking space), counter-ions left in, [C] without hydrogens (a radical).
- AQME CSEARCH outputs: <output>/CSEARCH/<code_name>_rdkit.sdf (or _crest.sdf); CMIN: <output>/CMIN/<name>.sdf plus All_confs/; QDESCP: descriptor CSV/JSON files and per-molecule folders. When the output folder is the input's own folder, results go to a CSEARCH/, CMIN/ or QDESCP/ subfolder.
- ROBERT: needs a CSV with the target column (y) and a names column; it never asks questions (LUCI closes its stdin), missing y/names stop it with an error.
- A run that "crashed (killed by the system)": a segmentation fault inside the program (seen with tblite/xTB in some systems), not the user's input.
- Windows: paths with accents and spaces work; [ ] in folder names do not. Results default to the input's folder.
- Restricted network: if installs fail downloading the conda/PyPI mapping, tick "Restricted network" in Settings.
"""


# ------------------------------------------------------------------ generated pages
def _option_line(option, style: str) -> str:
    flag = option.native_flag or option.key
    flag = flag if flag.startswith("-") else ("-" if style == "short" else "--") + flag
    parts = [f"- {option.label} [{option.kind}] -> native flag {flag}"]
    if option.group:
        parts.append(f"section '{'Input and output' if option.group == '@input' else option.group}'")
    if option.choices:
        choices = [c if isinstance(c, str) else f"{c[0]}={c[1]}" for c in option.choices]
        parts.append("choices: " + ", ".join(str(c) for c in choices))
    if option.default not in ("", None, (), []):
        parts.append(f"default shown: {option.default}")
    if option.placeholder:
        parts.append(f"placeholder: {option.placeholder}")
    if option.required:
        parts.append("REQUIRED")
    if option.flag_only:
        parts.append("switch (bare flag)")
    if option.multi_value:
        parts.append("several values")
    if option.visible_if:
        source, values = option.visible_if
        where = {"@input": "input type", "@variant": "method"}.get(source, f"option '{source}'")
        parts.append(f"shown only when {where} is {values}")
    text = "; ".join(parts) + "."
    if option.tooltip:
        text += f" {option.tooltip}"
    return text


def _runner_doc(name: str) -> str:
    path = Path(__file__).resolve().parents[1] / "runners" / f"{name}.py"
    try:
        return ast.get_docstring(ast.parse(path.read_text(encoding="utf-8"))) or ""
    except (OSError, SyntaxError):
        return ""


def program_page(spec) -> str:
    """Everything the registry says about one program, as the assistant reads it."""
    layer = next(l for l in LAYERS if l.key == spec.layer)
    lines = [f"PROGRAM {spec.name} (key {spec.key}) in {layer.title} ({layer.delivers})",
             f"What it does: {spec.description}"]
    inputs = ", ".join(INPUT_LABELS[k] for k in spec.tags.inputs) or "no input file (options only)"
    lines.append(f"Starts from: {inputs}. Mode: {MODE_LABELS[spec.tags.mode]}. Cost: "
                 + ", ".join(COST_LABELS[c] for c in spec.tags.cost) + ".")
    for variant in spec.variants:
        env = ENV_BY_KEY[variant.env]
        state = "available" if env.available else "NOT available yet"
        launch = variant.launch
        how = (" ".join(launch.command) if launch.kind != "runner" else f"LUCI runner {launch.runner}")
        lines.append(f"Variant '{variant.key}' ({variant.label}): environment '{env.key}' ({env.title}, "
                     f"{'/'.join(env.platforms)}, {env.size_hint or 'size n/a'}, {state}); runs {how}."
                     + (f" {variant.description}" if variant.description else "")
                     + (f" Needs: {'; '.join(variant.requires)}." if variant.requires else "")
                     + (f" Note: {env.note}" if env.note else ""))
    if spec.input_modes:
        lines.append("Input types (the 'Input type' dropdown):")
        for mode in spec.input_modes:
            kind = {"molecules": "LUCI molecule CSV", "smiles": "one typed SMILES",
                    "structures": "LUCI folder of structures"}.get(mode.kind, mode.dialog)
            flag = mode.flag or "positional"
            extra = f"; picks variant {mode.variant}" if mode.variant else ""
            lines.append(f"- '{mode.label}' (key {mode.key}, {kind}, native {flag}{extra}). {mode.help}")
    if spec.input_help:
        lines.append(f"Input help: {spec.input_help}")
    if spec.options:
        lines.append("Options (only changed ones are sent):")
        style = spec.variants[0].launch.flag_style
        lines += [_option_line(option, style) for option in spec.options]
    if spec.notes:
        lines.append(f"Notes: {spec.notes}")
    for variant in spec.variants:
        if variant.launch.runner:
            doc = _runner_doc(variant.launch.runner)
            if doc:
                lines.append(f"How LUCI runs it ({variant.launch.runner}): {doc}")
    if spec.docs_url:
        lines.append(f"Documentation: {spec.docs_url}")
    if spec.citation:
        lines.append(f"Cite: {spec.citation}")
    return "\n".join(lines)


def program_index() -> str:
    lines = ["ALL PROGRAMS IN LUCI (layer · key · name · what it does · starts from):"]
    for layer in LAYERS:
        for spec in programs_in(layer.key):
            inputs = ", ".join(INPUT_LABELS[k] for k in spec.tags.inputs) or "options only"
            available = all(ENV_BY_KEY[v.env].available for v in spec.variants)
            note = "" if available else " (some variants not available yet)"
            lines.append(f"- {layer.short_name} · {spec.key} · {spec.name} · {spec.description} · {inputs}{note}")
    return "\n".join(lines)


def layer_page(layer) -> str:
    names = ", ".join(p.name for p in programs_in(layer.key))
    return f"LAYER {layer.title}: {layer.description} Delivers: {layer.delivers}. Programs: {names}."


# ------------------------------------------------------------------ documents for the search
def _chunks(text: str, size: int = CHUNK) -> list[tuple[str, str]]:
    """Split a markdown document into (heading, text) pieces of about ``size`` characters."""
    sections = re.split(r"\n(?=#{1,3} )", text)
    pieces: list[tuple[str, str]] = []
    for section in sections:
        heading = section.strip().split("\n", 1)[0].lstrip("# ").strip()[:120]
        body = section.strip()
        while len(body) > size:
            cut = body.rfind("\n\n", 0, size)
            cut = cut if cut > size // 3 else size
            pieces.append((heading, body[:cut]))
            body = body[cut:].strip()
        if len(body) > 80:
            pieces.append((heading, body))
    return pieces


def documents() -> list[tuple[str, str, str, str]]:
    """(id, scope, title, text): scope is a program key, a layer key or 'app'."""
    docs = [("app_map", "app", "The LUCI window", APP_MAP),
            ("standard_inputs", "app", "Standard inputs", STANDARD_INPUTS),
            ("environments", "app", "Environments and installation", ENVIRONMENTS),
            ("command_line", "app", "Command line", COMMAND_LINE),
            ("troubleshooting", "app", "Common problems", TROUBLESHOOTING),
            ("assistant", "app", "The assistant", ASSISTANT)]
    for layer in LAYERS:
        docs.append((f"layer_{layer.key}", layer.key, layer.title, layer_page(layer)))
    for spec in PROGRAMS:
        docs.append((f"program_{spec.key}", spec.key, f"{spec.name} in LUCI", program_page(spec)))
    for path in sorted((KNOWLEDGE_DIR / "programs").glob("*.md")):
        key = path.stem
        scopes = [k for k, v in UPSTREAM.items() if v == key] or [key]
        text = path.read_text(encoding="utf-8")
        for number, (heading, body) in enumerate(_chunks(text)):
            docs.append((f"upstream_{key}_{number}", scopes[0], f"{key} documentation: {heading}", body))
    from .config import install_dir
    root = install_dir()
    if root is not None:
        for name in ("README.md", "docs/architecture.md", "docs/adding_a_program.md"):
            path = root / name
            if path.is_file():
                for number, (heading, body) in enumerate(_chunks(path.read_text(encoding="utf-8"))):
                    docs.append((f"luci_{path.stem}_{number}", "app", f"LUCI {path.stem}: {heading}", body))
    return docs


def scopes_for(program_key: str | None, layer_key: str | None) -> set[str]:
    """Scopes that belong to the screen: the program (and the other AQME modules), its layer."""
    scopes = {"app"}
    if layer_key:
        scopes.add(layer_key)
    if program_key:
        scopes.add(program_key)
        upstream = UPSTREAM.get(program_key)
        if upstream:
            scopes |= {k for k, v in UPSTREAM.items() if v == upstream}
    return scopes


def static_context(program_key: str | None, layer_key: str | None) -> str:
    """Sent with every question on this screen (identical each time, so OpenAI caches it)."""
    parts = [APP_MAP, STANDARD_INPUTS, ASSISTANT, program_index()]
    if layer_key:
        layer = next((l for l in LAYERS if l.key == layer_key), None)
        if layer is not None:
            parts.append(layer_page(layer))
            if not program_key:
                parts += [program_page(spec) for spec in programs_in(layer.key)]
    if program_key:
        spec = next((p for p in PROGRAMS if p.key == program_key), None)
        if spec is not None:
            parts.append("THE PROGRAM ON SCREEN (know it in depth):\n" + program_page(spec))
    return "\n\n".join(parts)
