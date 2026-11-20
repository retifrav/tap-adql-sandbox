# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A desktop GUI ([Dear PyGui](https://pypi.org/project/dearpygui/)) for running ADQL queries against TAP services through PyVO, plus a SIMBAD ID lookup window through astroquery. It is published on PyPI as `tap-adql-sandbox`, and the console entry point is `tap_adql_sandbox.__main__:main`. There are no tests.

## Commands

**Before changing lint, type-check or build commands, read `.claude/notes/tooling.md`**: it holds the measurements behind the rules below.

- Lint: `ruff check`, run from the repo root. Its config is `[tool.ruff]` in `pyproject.toml`: `target-version = "py312"` plus ruff's own default rule set, which is deliberately not pinned, with only `BLE001` ignored (the GUI catches any exception from PyVO, astroquery or Dear PyGui to show it in the window). When an image bump brings a ruff with new default rules, fix the new findings instead of ignoring them or pinning the old set.
- Never run `ruff format`: the code isn't ruff-formatted, and it would rewrite most files.
- Type check: `ty check`, run from the repo root. Its config is `[tool.ty]` in `pyproject.toml`: `python-version = "3.12"`, and `allowed-unresolved-imports`, which lists a glob for every third-party module the code imports plus `setuptools` for `setup.py`. That is what lets it run in the container, where none of them is installed, so an import of a new dependency needs a glob there or ty fails with `unresolved-import`. mypy has been dropped (the `[mypy]` section in `setup.cfg` is gone); don't reintroduce it.
- Build: `uv build --out-dir <scratchpad>/dist`. `dist/` in the tree is gitignored and holds stale 0.8.1 artifacts. The README's documented routes are `pip install ./` and `python -m build`.
- Smoke-run in the container: `uv run --isolated --no-project --with <built .whl> tap-adql-sandbox --version` (or `--help`). All dependencies install on arm64 (verified; x86_64 untested), and every module is imported before argparse runs, so this also proves the imports work. It needs PyPI, which is sometimes unreachable from the container. The container has no display, but Xvfb and Mesa are installed (verified on x86_64), so the real GUI can run on a virtual one and save its frames to PNG. The recipe is in `.claude/notes/dearpygui.md`, and it includes the `-noreset` that Xvfb needs.
- `uv run --with .` also works, but setuptools leaves an in-tree `build/` behind. Delete it afterwards.

## Architecture

- `__main__.py` builds the entire UI imperatively inside `main()`: the menu bar, main window, save-file dialog, About window, theme bindings, handler registries and viewport. It also holds the query callbacks. `simbad.py` builds the SIMBAD window and its callback, `examples.py` is pure data, `theme.py` has the font and theme factories, `scaling.py` detects the display's content scale and has `scaled()`, `config.py` holds runtime settings, and `__init__.py` defines `applicationPath` and `settingsFile`.
- Widgets are addressed by **string tags**, not by references. Callbacks reach them with `dpg.get_value("errorMessage")`, `dpg.show_item("resultsGroup")` and so on, and theme bindings at the end of `main()` use the same tags. So renaming a tag means grepping both `__main__.py` and `simbad.py`. The SIMBAD window uses `…SimbadIDs`-suffixed tags. The `"cell-handler"` item handler registry (right-click copies a cell) is created in `main()` and shared by both results tables.
- Both lookup flows (`executeQuery`, `getSimbadIDs`) follow the same sequence:
  1. Hide previous results and errors, and show the loading indicator.
  2. Validate the input.
  3. Query.
  4. Delete the results table and rebuild it from scratch under its group parent.
  5. Restore the button.

  Every early `return` must restore the button and indicator state: `showLoading(False)` in the main window, a manual hide/show pair in `simbad.py`.
- `config` is mutable module state, overwritten from the CLI arguments in `main()` after import. Always use `from . import config` and read `config.debugMode` at call time. `from .config import debugMode` would freeze the default.
- HiDPI: Dear PyGui scales nothing on GNU/Linux, so the app does it itself, following Dear ImGui's own GLFW example. **Before changing the scaling, or when bumping Dear PyGui, read the HiDPI section of `.claude/notes/dearpygui.md`.**
  - `main()` sets `config.uiScale` before any UI is created. It comes from `--ui-scale`, or else from `scaling.getContentScale()`. That function returns `Xft.dpi / 96` on Linux, read through Dear PyGui's own bundled GLFW via `ctypes`, and 1 on other platforms, because macOS and Windows scale the window themselves.
  - Every size in pixels handed to Dear PyGui goes through `scaled()`: the font size, theme style values, the viewport size and minimum, widget `width`/`height`/`min_size`/`indent`, spacer heights, and pixel thresholds compared with item sizes (the 150 px per column check in `executeQuery`).
  - Not scaled: `-1` widths, table column weights, and the loading indicator's `radius`, which is measured in text line heights.
  - A Dear ImGui style size that the theme doesn't set stays at its unscaled default. When the UI starts relying on one, add it to the theme through `scaled()`, with its default value. That's why `CellPadding` is there.
- The query path is `pyvo.dal.TAPService(url).search(query)` → `results.to_table().to_pandas()`. The result goes into the module global `lastQueryResults`, which is what "Save results to pickle" writes. A guard refuses to render a result whose column count plus the `#` enumeration column (shown unless `--no-enum-column` or a single row, `addEnumerationColumn`) exceeds `config.dpgColumnsMax` (511), because Dear ImGui asserts `columns_count < IMGUI_TABLE_MAX_COLUMNS` (512) in `BeginTable` (issues #8, #14 were the 64-column limit of Dear PyGui 1.x).
- The SIMBAD lookup uses `Simbad.query_objectids`. The ID column is `ID` before astroquery 0.4.8 and `id` from 0.4.8 on, and both cases are handled deliberately.
- `examples.py` holds `tapServices`: service key → `name`, `url` and `examples` (a list of `{description, query}`). The Help → Examples submenus are generated from it in insertion order. The query prefilled at startup is picked **by position**, `tapServices["padc"]["examples"][5]`, so inserting or reordering PADC examples silently changes it.
- Fonts and icons are loaded relative to `applicationPath`, and they reach the wheel only through the `graft` lines in `MANIFEST.in` plus `include_package_data=True` in `setup.py`. A new resource directory needs its own `MANIFEST.in` line.
- Dear PyGui `>= 2.3` is required (`install_requires`), so there are no Dear PyGui version branches. **Before changing that minimum or the key handling, read `.claude/notes/dearpygui.md`**, which has the evidence behind these rules:
  - Key handling: use `dpg.mvKey_*` constants, never raw key numbers. Since 2.0 they are Dear ImGui `ImGuiKey` values (named keys start at 512), and Dear ImGui rejects anything else. `mvKey_LWin`/`mvKey_RWin` still hold 1.x values and are just as invalid. For modifiers, use `mvKey_ModCtrl`/`mvKey_ModSuper`/`mvKey_ModShift`/`mvKey_ModAlt`. On macOS Dear ImGui swaps Ctrl and Cmd, so there `mvKey_ModCtrl` is Cmd and `mvKey_ModSuper` is the physical Ctrl key.
  - The Cmd/Ctrl + R shortcut: a single key-press handler on `mvKey_R`, with `keyPressCallback` checking `dpg.is_key_down(dpg.mvKey_ModCtrl)`. Dear ImGui reports Cmd as Ctrl on macOS, so that one check is Cmd + R there and Ctrl + R elsewhere.
  - Pass `tag=`, never `id=`, which warns `id keyword renamed to tag`.
  - Don't add font range hints. Glyphs load on demand since 2.3, `add_font_range_hint` is a no-op, and its deprecation decorator rewrites the process-wide `warnings` filters.
  - `hint` does nothing on multiline inputs (Dear PyGui clears it).
  - `wrap=0` on a text wraps at the window edge.
  - Lowering the minimum would bring back version branches for all of the above, and Intel Macs would need one, since macOS x86_64 wheels stop at 2.1.1. Ask first.
- On exit Dear PyGui saves window layout to `settings.ini` inside the package directory (`settingsFile`, wired up through `init_file`). The file is gitignored.
- `--debug` turns on several things:
  - DEBUG logging with timestamps (all logging goes to stdout). Modules log through their own `logger: logging.Logger = logging.getLogger(__name__)`, never through `logging.debug()` and friends (ruff `LOG015`). The `logging.basicConfig` call in `main()` configures the root logger they propagate to, and its format has no `%(name)s`.
  - A `tabulate` dump of each result. It is a deliberate `print`, not logging.
  - Tracebacks to stderr.
  - A Dev menu.
  - A prefilled SIMBAD input.
- The README's "Known problems" section covers three dependency-side issues:
  - Installation fails on a Python version too new for Dear PyGui's wheels. It ships no sdist, and on 2026-11-20 its wheels stopped at 3.14.
  - astropy contacts remote hosts at startup.
  - PyVO raises `UnicodeDecodeError` on non-ASCII results (#19).

  Its Platforms section says which platforms Dear PyGui 2.3 has wheels for.

## Conventions

- Functions and variables use camelCase (`executeQuery`, `lastQueryResults`), and module-level variables carry type annotations.
- Long strings are adjacent string literals inside parentheses (implicit concatenation), one fragment per line, each ending with the space that separates it from the next. Plain and f-string fragments mix freely, and an argument that is only the string needs no extra parentheses. `str.join` is only for runtime sequences (`".".join(map(str, …))`, `", ".join(oids.colnames)`). A fixed tuple of fragments trips ruff's `FLY002`, and inside a list or tuple the concatenation needs its own parentheses (`ISC004`). Example queries put an explicit `\n` at the end of each line.
- Imports come in three groups in this order: `# standard libraries`, `# 3rd-party dependencies`, `# own stuff`. Each group starts with its header comment and a bare `#` line, and a blank line separates the groups. ruff's `I001` enforces the sorting within each group. The headers of the 3rd-party and own groups survive sorting only because each is attached to the first import of its group. So a new import that sorts above that one has to be written directly below the header, otherwise `ruff check --fix` puts it above the header. This was verified on stdin. The first group's header is safe either way, because it's the file's leading comment.
- Python 3.12 is the minimum, so 3.12 syntax is fine (PEP 695 `type` statements, PEP 701 f-strings, parenthesized context managers). It is declared in five places that change together: `python_requires` and the classifier in `setup.cfg`, the README's Dependencies list, `target-version` under `[tool.ruff]` and `python-version` under `[tool.ty.environment]` in `pyproject.toml`. Ask before raising it further.
- The version has a single source, `__version_info__` in `version.py`, which `setup.cfg` reads through `attr:`. A release bumps it and adds a `changelog.md` section: `## X.Y.Z`, then ``Released on `YYYY-MM-DD`.``, then bullets. The release commit is titled `Version X.Y.Z`. Commits about an issue start with `Closed #N:` or `For #N:`.
- `README.md` and `changelog.md` carry MarkdownTOC blocks (a Sublime Text plugin) between `<!-- MarkdownTOC -->` markers. When you add or rename a heading, update the block by hand in its existing format.
- The git remote uses an SSH URL, so fetch and push don't work from the container. The only branch is `master`.
