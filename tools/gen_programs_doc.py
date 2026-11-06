"""Regenerate docs/programs.md from the registry (run after adding a program)."""

from pathlib import Path

from luci.registry import (
    COST_LABELS, ENV_BY_KEY, INPUT_LABELS, LAYERS, MODE_LABELS, PLATFORM_LABELS, program_platforms,
    programs_in,
)

ROOT = Path(__file__).resolve().parents[1]


def main():
    lines = ["# Programs in LUCI", "",
             "Generated from `src/luci/registry` by `tools/gen_programs_doc.py`. Do not edit by hand.",
             ""]
    for layer in LAYERS:
        lines += [f"## {layer.title}: {layer.delivers}", "", layer.description, "",
                  "| Program | Key | Inputs | Cost | Mode | Platforms | Environment | Status |",
                  "|---|---|---|---|---|---|---|---|"]
        for spec in programs_in(layer.key):
            envs = []
            status = []
            for variant in spec.variants:
                env = ENV_BY_KEY[variant.env]
                label = env.key if len(spec.variants) == 1 else f"{variant.label}: {env.key}"
                envs.append(label)
                state = "tested on Linux" if env.available else "not public yet"
                if env.available and not env.tested:
                    state = "untested"
                status.append(state if len(spec.variants) == 1 else f"{variant.label}: {state}")
            inputs = ", ".join(INPUT_LABELS[i] for i in spec.tags.inputs) or "none"
            cost = ", ".join(COST_LABELS[c] for c in spec.tags.cost)
            platforms = ", ".join(PLATFORM_LABELS[p] for p in program_platforms(spec))
            lines.append(f"| [{spec.name}]({spec.docs_url}) | `{spec.key}` | {inputs} | {cost} | "
                         f"{MODE_LABELS[spec.tags.mode]} | {platforms} | {'; '.join(envs)} | "
                         f"{'; '.join(status)} |")
        lines.append("")
    lines += ["## Environments", "", "| Key | Title | Platforms | Source | Notes |", "|---|---|---|---|---|"]
    for env in ENV_BY_KEY.values():
        source = f"{env.source.repo} (`{env.source.branch}`)" if env.source else "package index"
        lines.append(f"| `{env.key}` | {env.title} | {', '.join(env.platforms)} | {source} | {env.note} |")
    (ROOT / "docs" / "programs.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("docs/programs.md written")


if __name__ == "__main__":
    main()
