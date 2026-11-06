"""Isolated environments for LUCI's programs, managed with pixi.

Each environment has its own ``manifests/<key>/pixi.toml`` shipped with LUCI.
On install it is copied to ``<LUCI home>/envs/<key>/``, the program's source
is fetched there when it is not on a package index, and ``pixi install``
builds the environment next to it. LUCI never imports a program: it runs it
with ``pixi run`` in a separate process.

Group users never see pixi: if it is not on PATH, LUCI downloads a pinned
pixi binary into its home folder. Developers with pixi installed use theirs.
Both use the same manifests.
"""

from .manager import EnvManager, EnvStatus, PIXI_VERSION

__all__ = ["EnvManager", "EnvStatus", "PIXI_VERSION"]
