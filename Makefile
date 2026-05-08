# Shortcuts that avoid uv run <console_script> sync/rebuild churn (maturin).
.PHONY: regen-doc-screenshot
regen-doc-screenshot:
	uv run --no-sync python scripts/dev_tt3de_screenshot.py -o source/_static/screenshots/triple_panel.svg --width 132 --height 28
