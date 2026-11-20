# Tooling measurements

Evidence behind the Commands rules in `CLAUDE.md`. Measured in the arm64 (macOS host) container: the 2026-11-19 baseline, then the mypy → ty switch and the move to ruff's default rules on 2026-11-20.

## ruff

- Config lives in `[tool.ruff]` in `pyproject.toml` since 2026-11-20; before that there was none at all (no `ruff.toml`, no `[tool.ruff]`, no `~/.config/ruff`, no `RUFF_*` variables). `ruff check --show-settings` confirms `Settings path: "/workspace/pyproject.toml"` and `linter.unresolved_target_version = 3.12`.
- ruff infers the target only from `[project].requires-python`, and this project keeps its metadata in `setup.cfg` with no `[project]` table, so `target-version` has to be explicit; without it ruff assumes its own default.
- The gitignored `.ruff_cache/` once held only a `0.14.11` directory, presumably the ruff behind commit `039dc3e` ("Fixes from ruff"). Back then the project was checked with the classic default set `E4,E7,E9,F`.
- ruff 0.17's default rule set is far broader than the classic one (by prefix: PYI 47, UP 42, F 40, RUF 36, PLE 33, B 29, SIM 21, PLW 20, FURB 17, C 17, PLR 13, plus smaller groups such as LOG, FLY, I, ISC, BLE). It also *drops* most classic pycodestyle rules: E401, E402, E701–E703, E711–E714, E721, E731, E741–E743 and E999 are no longer default; only E722 and E902 remain. The code passed the classic set before the switch, so nothing was lost in practice. `extend-select = ["E4", "E7", "E9"]` would bring them back.
- Before the switch, ruff 0.17.6 at `--target-version py312` reported 69 findings with its default rules: `FLY002` ×23, `LOG015` ×17, `BLE001` ×7, `UP006` ×7, `UP034` ×4, `I001` ×4, `UP035` ×2, `ISC004` ×2, `PLR2044` ×1, `PLW0602` ×1, `SIM117` ×1. The `UP034`/`ISC004` hits in `examples.py` were real slips: four `"".join((…))` calls whose tuple was in fact one implicitly concatenated string, and two tuples with a missing comma. Both produced the right string only because the separator was `""`.
- `BLE001` is the one ignored rule: all seven sites catch whatever PyVO, astroquery or Dear PyGui raises and show it in the window, and there is no narrower type to catch.
- `I001` and the comment-headed import groups (tested on stdin): ruff attaches comment lines to the import directly below them. So the headers survive sorting when the groups are ordered stdlib → 3rd-party → own with a blank line between them. The original order (3rd-party first, no blank lines) was scrambled by `--fix`. A new import that sorts above the first import of a later group lands *above* that group's header after `--fix`; the first group's header stays put, because it is the file's leading comment. Multi-line `from` imports with a trailing comma stay vertical; short ones without one get collapsed onto a single line.
- After the fixes, `ruff check` from the repo root → `All checks passed!`. It checks `setup.py`, `pyproject.toml` and the seven package modules.
- `ruff format --check` → 6 files would be reformatted, 4 already formatted (2026-11-19). Formatting was not part of the switch.

## Type checkers

- mypy (history): `uvx mypy src/tap_adql_sandbox` (mypy 2.4.1) passed on 2026-11-19 with `[mypy] ignore_missing_imports = true` in `setup.cfg`. Its gitignored `.mypy_cache/` (107 MB, entries for 3.9, 3.11, 3.13 and 3.14) was deleted on 2026-11-20. mypy 2.4.1 rejects anything below 3.10 as a target. With default settings it skipped the bodies of unannotated functions (`getGlobalFont`, `simbadWindow`, …). On 2026-11-20, with PyPI unreachable, `uvx --offline mypy` could not run at all, because mypy was not in uv's cache.
- ty 0.0.107 replaced it. ty is in the image, so it needs no download, and it checks unannotated bodies too. Like ruff, it infers the Python version only from `[project].requires-python`, hence the explicit `[tool.ty.environment] python-version`. `ty check -v` logs `Python version: Python 3.12`.
- Without config, `ty check src` → 10 `import-not-found` diagnostics for `dearpygui`, `pyvo`, `astroquery`, `pandas` and `tabulate`, because the container has none of them installed. `packaging` resolves from Debian's `/usr/lib/python3/dist-packages`. `ty check` from the root additionally fails on `setuptools` in `setup.py`.
- `[tool.ty.analysis] allowed-unresolved-imports` with one `"<module>.**"` glob per dependency (`**` also matches the top-level module itself) plus `setuptools.**` → `All checks passed!`. `replace-imports-with-any` gives the same result. `allowed-unresolved-imports` was chosen because it only suppresses the diagnostic: where the dependencies *are* installed, ty uses their real types.
- Against a real environment (`uv run --isolated --no-project --python 3.12 --with dearpygui --with pyvo --with astroquery --with pandas --with tabulate --with packaging` → `ty check --python <sys.prefix>`, which got Dear PyGui 2.3.1, PyVO 1.10.0, astroquery 0.4.11, pandas 3.1.1 and packaging 26.3) → `All checks passed!` as well.
- `--config 'rules.all="error"'` adds only 4 `unsound-assignment` diagnostics (`Any`/`Unknown` assigned to `str`/`Path` from `dpg.get_value` and `app_data[…]`), which aren't worth enabling.

## Python floor

- Raised to 3.12 on 2026-11-20 (`python_requires`, classifier, README, ruff `target-version`, ty `python-version`). Before that, the metadata declared 3.6, but the `user_data: tuple[str, str]` annotation on `preFillExample` (PEP 585, evaluated at definition time) already needed 3.9.
- The built wheel's `METADATA` carries `Requires-Python: >=3.12` and `Classifier: Programming Language :: Python :: 3.12`. The smoke-run works on 3.13 (system) and 3.12, and on 3.11 uv refuses to resolve it (`does not satisfy Python>=3.12`).

## Build and run

- `uv build --out-dir <dir>` → `tap_adql_sandbox-0.8.2.tar.gz` and `tap_adql_sandbox-0.8.2-py3-none-any.whl`. The wheel has 16 entries, including `fonts/JetBrainsMono-Thin.ttf` and both `.ico` files. `uv build` leaves no `build/` directory in the tree.
- The sdist contains only `LICENSE`, `MANIFEST.in`, `PKG-INFO`, `README.md`, `pyproject.toml`, `setup.cfg`, `setup.py` and `src/`. `changelog.md`, `CLAUDE.md` and `.claude/` don't ship.
- `uv run --isolated --no-project --with <wheel> tap-adql-sandbox --version` installed 35 packages (Dear PyGui ships an aarch64 Linux wheel) and printed `tap-adql-sandbox 0.8.2`.
- `uv run --isolated --no-project --with . tap-adql-sandbox --help` works too, but it created an in-tree `build/` (`build/lib`, `build/bdist.linux-aarch64`) that had to be deleted by hand.
- No `DISPLAY` is set in the container, and the GUI was not launched.
