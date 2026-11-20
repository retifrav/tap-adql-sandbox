# Dear PyGui measurements

Evidence behind the Dear PyGui rules in `CLAUDE.md`, gathered on 2026-11-20 from the 2.3.0/2.3.1 wheels (`dearpygui/dearpygui.py`), the C++ sources at the `v2.3.0`/`v2.3.1` tags on GitHub, Dear ImGui's sources at the bundled versions, and headless runs of Dear PyGui 2.3.0 and 2.3.1 in the arm64 container.

## Decision

- On 2026-11-20 the user chose `dearpygui >= 2.3` over `>= 2.0` and over keeping `>= 1.5.0`. That gives one code path, with no `packaging` import and no version checks, at the cost of Intel Macs.
- With Python ≥ 3.12 the oldest installable Dear PyGui was already 1.10.1, the first release with `cp312` wheels. Dear PyGui publishes wheels only, never an sdist.

## Versions and platforms

- Bundled Dear ImGui, read from the `thirdparty/imgui` submodule at each tag: v2.0.0, v2.1.0 and v2.2.0 have 1.91.0; v2.3.0 and v2.3.1 have 1.92.5.
- Wheel platforms per release:
  - 1.11.1 to 2.1.1: `macosx_10_6_x86_64`, `macosx_13_0_arm64`, `manylinux1_x86_64`, `win_amd64`.
  - 2.2: macOS x86_64 dropped.
  - 2.3 and 2.3.1: `manylinux2014_aarch64` added.

  So 2.3 is the first release that can be imported in the arm64 container, and Intel Macs end at 2.1.1. None of the macOS arm64 wheels (`macosx_13_0`) install below macOS 13.
- The latest release, 2.3.1, has wheels for `cp38`–`cp314`, none for 3.15.
- `dearpygui.__version__` is `'2.3'` for 2.3.0 (no patch digit); `packaging` compares it as equal to `2.3.0`.

## Deprecations

- Scanned with `ast` over the 2.3.1 wrapper: functions whose docstring starts with `(deprecated` and keywords documented as `(deprecated)`, cross-checked against every `dpg.<name>(…, kw=…)` and `dpg.<name>` in the package. Two hits, both fixed:
  - `add_font_range_hint`: `@deprecated("This call is a no-op because character ranges are now automatic")`, with a body of `pass` in 2.3.0 and 2.3.1. In 2.2 it was an ordinary function.
  - `file_dialog(id=…)`: `warnings.warn('id keyword renamed to tag', DeprecationWarning, 2)`.
- Dear PyGui's `deprecated` decorator calls `warnings.simplefilter('always', DeprecationWarning)` before warning and `simplefilter('default', DeprecationWarning)` after. So it prints regardless of Python's default filters, and it leaves process-wide filters changed for every later `DeprecationWarning`.
- Every other function and constant the app uses exists in 2.3.0 and 2.3.1. `mvThemeCol_TabActive`/`TabUnfocused`/`TabUnfocusedActive` are aliases of `TabSelected`/`TabDimmed`/`TabDimmedSelected` (36/38/39). The new names are absent from the v2.0.0 wrapper. The app has no tab bars, so these theme entries have no visible effect.

## Keys

- Values in 2.3.1: `mvKey_LControl` = 527 (`ImGuiKey_LeftCtrl`), `mvKey_RControl` = 531, `mvKey_R` = 563, `mvKey_A` = 546, `mvKey_ModCtrl` = 4096 (`ImGuiMod_Ctrl`), `mvKey_ModSuper` = 32768.
- `mvKey_LWin`/`mvKey_RWin` are 343/347 on non-Windows and 0x5B/0x5C on Windows. These are the old GLFW and VK codes, hard-coded in `src/mvContext.cpp` (the `#if defined (_WIN32)` block around lines 383–421 at v2.3.1).
- `mvKey_ModCtrl` exists since v2.0.0; the v1.10.0 and v1.11.0 wrappers don't have it.
- `mvKeyPressHandler::draw` (`src/mvGlobalHandlers.cpp`) calls `ImGui::IsKeyPressed(_key)` with the registered number unchanged. `ImGui::GetKeyData` (imgui.cpp 1.92.5) asserts `IsNamedKey(key)` ("Support for user key indices was dropped in favor of ImGuiKey") and indexes `KeysData[key - ImGuiKey_NamedKey_BEGIN]`.
- So the raw codes the app used to register (341, 343, 345, 347 and 17) can't work on 2.x. The app doesn't abort on the first frame, which suggests the assert is compiled out, so those reads land outside the array.
- `is_key_down` calls `ImGui::IsKeyDown(key)`, and `GetKeyData` maps `ImGuiMod_*` flags to their keys, so modifier constants are valid arguments.
- Dear ImGui's changelog for 1.90.7 says: "on macOS X, Cmd and Ctrl keys are now automatically swapped by io.AddKeyEvent()". In 1.92.5, `io.ConfigMacOSXBehaviors` defaults to true under `__APPLE__`. Every 2.x release bundles ImGui ≥ 1.91.0.
- Not verified here (no display): that Cmd+R actually triggers on the user's Mac.

## Tables

- `IMGUI_TABLE_MAX_COLUMNS` is 512 in both 1.91.0 and 1.92.5. `BeginTableEx` asserts `columns_count > 0 && columns_count < IMGUI_TABLE_MAX_COLUMNS`, so the maximum is 511, including the app's `#` column.
- Headless: before the guard was changed, `HEAD` built tables of 512 and 600 columns without complaint, because tables only reach ImGui when drawn. The new guard refuses 511+`#` and 600, and allows 510+`#`, 511 with `--no-enum-column`, and 511 with a single row (no `#` column).

## Text and input

- `add_text`/`set_value` on a text item convert any value with `str()` (2.3.1): ints, floats, numpy scalars, `bytes` (`"b'x'"`), `None` (`'None'`), `numpy.ma.masked` (`'--'`) and exceptions (their message).
- `wrap` (`src/mvBasicWidgets.cpp`, 2.3.0 and 2.3.1): `0` → `ImGui::PushTextWrapPos(0)`, which wraps at the window edge; `> 0` → wraps `wrap` pixels from the item's start; `-1` (the default) → no wrapping. Dear PyGui issue #1275 ("Add TextWrapped") is still open, but doesn't affect `wrap=0`.
- Multiline input: `if (config.multiline) config.hint.clear();` before drawing, so `hint` never shows there. Issue #1519 ("Hint argument of add_input_text doesn't work with multiline") was closed as completed on 2023-01-04 by exactly this.

## Headless harness

- `main()` builds the whole UI without a display if `dpg.create_viewport` is patched to raise. All items, handler registries, the font and the themes then exist and can be inspected with `get_item_configuration`, and `executeQuery()` can be driven with a fake `pyvo.dal.TAPService` whose `search()` returns an object with `__len__` and `to_table().to_pandas()`.
- On 2.3.0 and 2.3.1 the current tree gives no warnings (recorded with `simplefilter("always")`), both error texts have `wrap == 0`, `dialogSaveFile` exists, and there is exactly one key-press handler, with `key == mvKey_R`.
- `HEAD` before this change fails those checks: both deprecation warnings, five raw-code handlers, fixed wrap widths.
