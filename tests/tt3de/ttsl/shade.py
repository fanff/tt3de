# -*- coding: utf-8 -*-
"""Test helper: run a compiled TTSL shader through ShaderPy (Cranelift)."""

from tt3de.tt3de import materials
from tt3de.ttsl.compiler import RegisterSettings


def shade(regs, ssa_json: str | None = None, bytecode: bytes = b""):
    """Execute SSA via ``ShaderPy`` against seeded registers.

    ``regs`` is either a ``RegisterSettings`` (uses ``ssa_json()``) or the six
    bank dicts from ``get_register_list()`` plus an explicit ``ssa_json``.
    """
    if ssa_json is None:
        if not isinstance(regs, RegisterSettings):
            raise TypeError("ssa_json is required unless regs is RegisterSettings")
        seed = regs.get_register_list()
        ssa_json = regs.ssa_json()
    else:
        seed = list(regs)
    shader = materials.ShaderPy(
        bytecode,
        register_seed=seed,
        ssa_json=ssa_json,
        default_glyph=None,
    )
    return shader.run_seeded()
