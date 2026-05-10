# Changelog

## [1.0.0](https://github.com/fanff/tt3de/compare/v0.1.2...v1.0.0) (2026-05-10)


### ⚠ BREAKING CHANGES

* materials.ComboMaterialPy and MaterialBufferPy.add_combo_material are removed. Compose multiple materials by issuing per-channel writes from the calling code instead.

### Features

* add dev command to regenerate TTSL opcodes ([6d52d20](https://github.com/fanff/tt3de/commit/6d52d20c3284ca1078549deb971265251fb0120a))
* add dev command to regenerate TTSL opcodes ([e48d902](https://github.com/fanff/tt3de/commit/e48d9027c90f48ac283e0a5475d3fb6a48dacd76))
* add tt_FragDepth pixel builtin and ShaderPy bridge ([c24d171](https://github.com/fanff/tt3de/commit/c24d17169bfa4a188c989b9cbbd664958375b4b0))
* adding a demo file ([f19501d](https://github.com/fanff/tt3de/commit/f19501da51b0a6704d84e2204f7397dc0acfb8f7))
* adding demo ([d2e3875](https://github.com/fanff/tt3de/commit/d2e38752fd23d731c5c12aac916e7c24d0b46caf))
* Adding far and near plane ([657913f](https://github.com/fanff/tt3de/commit/657913fa66b120074e27db07a01afe7150c90af9))
* adding proper shader material ([9cde10a](https://github.com/fanff/tt3de/commit/9cde10af11f9fc888ca93f91874328e122d7dd5d))
* adding proper texture mapping ([4af3d66](https://github.com/fanff/tt3de/commit/4af3d66ccd1cd8bbfd1b192ba04492ab4a48e24a))
* adding shader compiler demo ([bfe54dd](https://github.com/fanff/tt3de/commit/bfe54dd050af35b38efe1a5c9c4467c867cef62a))
* align drawbuffer layers and document agent workflow ([d42aadb](https://github.com/fanff/tt3de/commit/d42aadbcf21aa3a82383e311e1d462aca5ba3946))
* align drawbuffer layers and document agent workflow ([6e48cc6](https://github.com/fanff/tt3de/commit/6e48cc6ccd1e0eff9f079cb0e3050475bafa6146))
* **demos:** TTSL texture cube demos and prefab cube UVs ([d552dbf](https://github.com/fanff/tt3de/commit/d552dbfe71403d06323de9e29ef659fa12c3c253))
* **docs:** enhance Mermaid diagram support and update documentation build instructions ([ad8a59c](https://github.com/fanff/tt3de/commit/ad8a59c0b3ee14c8bb78a71b3d65e4ab2942e638))
* fix compiler ([3e43178](https://github.com/fanff/tt3de/commit/3e43178ba60dd4938e0096b1d5a8df5dd932c91c))
* fix compiler ([91a1eb4](https://github.com/fanff/tt3de/commit/91a1eb44ca50a84dca37432d134ec575e2e87ce5))
* fixing compile warnings ([5348972](https://github.com/fanff/tt3de/commit/534897251795c4f75d154db4eac58cabbbc1c7f0))
* fixing compile warnings ([8eade78](https://github.com/fanff/tt3de/commit/8eade7829b8fcd88441ba58e6676b963a0c0d8b5))
* fixing compiler bugs ([e924446](https://github.com/fanff/tt3de/commit/e924446edc60e43a241ff881f3735a4b328210f1))
* fixing compiler bugs ([224ab69](https://github.com/fanff/tt3de/commit/224ab695989498578df571900c1bafbc9d31789f))
* fixing many bugs ([9ccdc5d](https://github.com/fanff/tt3de/commit/9ccdc5df0fe17eab13708bca0014e5cbd8f65d7a))
* fixing some tests ([368987e](https://github.com/fanff/tt3de/commit/368987e37a058e1ca3c728976f479785062c1606))
* fixing the square demo and proper shader material code ([9be6164](https://github.com/fanff/tt3de/commit/9be6164d3f55b2cf0124dbead137c7658ab1c9e3))
* material shading benchmark scripts and Rich KPI terminal report ([35895c4](https://github.com/fanff/tt3de/commit/35895c43055caddd49adabb21f14a811e9b5deef))
* remove ComboMaterial and move material docs to low_level_api ([7bf6c9a](https://github.com/fanff/tt3de/commit/7bf6c9af600ebaad2495d2205543d4c5de29ff25))
* simplify shader ([76bdf87](https://github.com/fanff/tt3de/commit/76bdf8776d05a5d688746e65b9838bcfe02ede1b))
* TTSL engine builtins and shader material bridge ([d0e3eed](https://github.com/fanff/tt3de/commit/d0e3eedf313339a8f7f196f968fd7bb3c16563a8))
* **ttsl:** floor, ceil, fract, mod ops and fog glyph demo ([4cdfcad](https://github.com/fanff/tt3de/commit/4cdfcad925dfd249f75c9e29898721fc023fc699))
* **ttsl:** migrate built-ins to tt_* naming and document pipeline ([b228542](https://github.com/fanff/tt3de/commit/b228542a68427a73a1700efc2f1e065aaa5be9d6))
* **ttsl:** migrate built-ins to tt_* naming and document pipeline ([e7e5429](https://github.com/fanff/tt3de/commit/e7e542988581e54a9b6db301e171d4a424d5e012))
* **ttsl:** plumb tt_LineCoord and tt_PointCoord into ShaderMaterial ([366d1f8](https://github.com/fanff/tt3de/commit/366d1f820e9e842407839eea59e450ecb2bef40a))
* updating demo compiler ([f591316](https://github.com/fanff/tt3de/commit/f59131649a695753e8f7f6a1e9a916b057e7deb7))
* updating the generation scroipt ([55d82db](https://github.com/fanff/tt3de/commit/55d82dbbb05c6628fc14225e87f6d60107b3c3db))
* updating to_textual_benchmark ([e0592aa](https://github.com/fanff/tt3de/commit/e0592aa2aa82112315475eab8782d86b0e4dcf85))


### Bug Fixes

* correct triangle clipping, texture sampling, and doc-tests ([850f35b](https://github.com/fanff/tt3de/commit/850f35bcee2b78601e510963ad66b61857e5e120))
* correct triangle clipping, texture sampling, and doc-tests ([0fc6846](https://github.com/fanff/tt3de/commit/0fc6846525249b0218695eb397a9df29ab09eb39))
* **drawbuffer:** correct to_textual_2 segment cache and glyph palette tests ([1246ef2](https://github.com/fanff/tt3de/commit/1246ef28f0bdda593a2032a18703059e6214c038))
* resolve all Rust compilation warnings ([25e9b88](https://github.com/fanff/tt3de/commit/25e9b881086acc29b9912d03bfd1276214849f01))
* resolve all Rust compilation warnings ([2d2820e](https://github.com/fanff/tt3de/commit/2d2820e2d91b1b7fa1bd9246247295db0f54ffa1))
* **ttsl:** pin JMP_IF_FALSE fall-through in bytecode layout ([dcecfbb](https://github.com/fanff/tt3de/commit/dcecfbb617fa4a002cbfe886e8b16196cdc9b71f))
* **ttsl:** seed every LOAD_CONST register for duplicate literals ([c1d53c8](https://github.com/fanff/tt3de/commit/c1d53c89135a565fe3a66380375c360b7d15ef73))


### Performance Improvements

* **drawbuffer:** speed up to_textual_2 and segment cache ([24ea07a](https://github.com/fanff/tt3de/commit/24ea07a77baab905f698bb6eaf14f697fd6e1167))
* reuse TTSL TLS registers and row-chunk parallel shading ([fb26f92](https://github.com/fanff/tt3de/commit/fb26f9283e823c724b72010fbfb62c963a4456c4))


### Documentation

* drop cairosvg; use SVG for Sphinx and dev screenshots ([570bd28](https://github.com/fanff/tt3de/commit/570bd28dbe03f99305973eb0fa2578d7ef03be4a))
* drop cairosvg; use SVG for Sphinx and dev screenshots ([d4865e3](https://github.com/fanff/tt3de/commit/d4865e3e768e3f2d184579411287feff1e7c61b0))
* **ttsl:** remove Mermaid pipeline docs integration ([81dac93](https://github.com/fanff/tt3de/commit/81dac936307bd044e7eeb3bdc57131f59324feb8))
* **ttsl:** remove Mermaid pipeline docs integration ([57bd3c2](https://github.com/fanff/tt3de/commit/57bd3c292bf5e00fde74f16a68c114078929fea2))

## [0.1.2](https://github.com/fanff/tt3de/compare/v0.1.1...v0.1.2) (2026-05-08)


### Bug Fixes

* actually, maybe just on master branch push is fine ([2287a10](https://github.com/fanff/tt3de/commit/2287a100f09b2a66a6d9c16b83cffeea12211f4b))
* adding documentation build ([0834bf3](https://github.com/fanff/tt3de/commit/0834bf30df58ce953c089e11c3159f9484686786))

## [0.1.1](https://github.com/fanff/tt3de/compare/v0.1.0...v0.1.1) (2025-12-17)


### Bug Fixes

* wire release ([249a571](https://github.com/fanff/tt3de/commit/249a5719f04340921160ae8b8beec288103664f2))
