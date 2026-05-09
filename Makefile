# Shortcuts that avoid uv sync/rebuild churn (maturin) via explicit python paths.
.PHONY: regen-doc-screenshot gen-opcodes
regen-doc-screenshot:
	uv run --no-sync python scripts/dev_tt3de_screenshot.py -o source/_static/screenshots/triple_panel.svg --width 200 --height 56

gen-opcodes:
	bash scripts/gen_opcodes.sh
