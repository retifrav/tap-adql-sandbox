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
- Verified by the user on their Mac on 2026-11-20: Cmd+R triggers the query. It can't be checked in the container, which has no macOS.

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

## HiDPI

Gathered on 2026-11-20 from the v2.3.1 sources, the `cp313` `manylinux1_x86_64` wheel, Dear ImGui at the bundled commit `3912b3d` (1.92.5), and Xvfb runs in the x86_64 container on the Arch host. It was not verified on the user's real 4K Arch desktop, and the session type there (X11, or Wayland with XWayland) is unknown.

### What Dear PyGui does

- Linux (`src/mvViewport_linux.cpp`): the GLFW window is created at the requested size in physical pixels, and no scale-related hint is set. Nothing in `src/` calls `glfwGet*ContentScale` or `ScaleAllSizes`, and nothing sets `FontScaleDpi`. Hence the tiny UI on a 4K display. Upstream issue #1081 ("Support High DPI") has been open since 2021.
- The only scale Dear PyGui has is `set_global_font_scale`, which `Render()` (`src/mvContext.cpp`) copies into `style.FontScaleMain` every frame.
- macOS (`src/mvViewport_apple.mm`): `glfwWindowHint(GLFW_COCOA_RETINA_FRAMEBUFFER, GLFW_FALSE)`, so the framebuffer is in points and macOS upscales it. That's why the size is right on a Retina Mac. GLFW reports a content scale of 2 there, so the app must not apply it on macOS.
- Windows (`src/mvViewport_win32.cpp`): there is no DPI-awareness call, so presumably Windows bitmap-scales the window (the right size, but blurry). Not checked on a Windows host.
- The bundled GLFW's `glfwGetVersionString()` reports `3.3.7 X11 GLX EGL OSMesa clock_gettime evdev`. It is X11 only, with no Wayland backend, so on a Wayland session it runs through XWayland. What it then sees depends on how the compositor scales XWayland clients.
- `_dearpygui.so` exports 133 `glfw*` symbols (`nm -D --defined-only`), including `glfwInit`, `glfwTerminate`, `glfwGetPrimaryMonitor` and `glfwGetMonitorContentScale`. GLFW is linked statically, and only `libX11.so.6` appears in `ldd`. The aarch64 and macOS wheels were not checked.

### Dear ImGui's recipe

- In 1.92.5, `examples/example_glfw_opengl3/main.cpp` computes `main_scale = ImGui_ImplGlfw_GetContentScaleForMonitor(glfwGetPrimaryMonitor())`, creates the window at `1280 * main_scale` by `800 * main_scale`, then calls `style.ScaleAllSizes(main_scale)` and sets `style.FontScaleDpi = main_scale`.
- `ImGui_ImplGlfw_GetContentScaleForMonitor` returns 1 on Apple, Emscripten, Android and Wayland, and `glfwGetMonitorContentScale()` everywhere else.
- In GLFW 3.3 on X11 that value is `Xft.dpi / 96`, read from the root window's `RESOURCE_MANAGER` with `XrmGetResource("Xft.dpi", "Xft.Dpi")`. It is the same for every monitor, and an unset `Xft.dpi` counts as 96.

### What the app does

- `getContentScale()` follows that recipe on Linux, through `ctypes.CDLL(_dearpygui.__file__)`. Dear PyGui calls `glfwInit()` only in `show_viewport()`, so the app runs `glfwInit` → `glfwGetPrimaryMonitor` → `glfwGetMonitorContentScale` → `glfwTerminate` before any of that.
- Measured under Xvfb:

  | `RESOURCE_MANAGER` | scale |
  |---|---|
  | `Xft.dpi: 192` | 2.0 |
  | `Xft.dpi: 144` | 1.5 |
  | `*dpi: 120` | 1.25 (the wildcard matches) |
  | unset | 1.0 |
  | `Xft.dpi: 0` | 0.0, which is why the range check exists |

  A second `glfwInit` after `glfwTerminate` works. Without a display `glfwInit` returns 0.
- `ScaleAllSizes` in 1.92.5 scales about 35 fields. The theme sets these through `scaled()`:
  - `WindowPadding`, `FramePadding`, `ItemSpacing`, `ItemInnerSpacing`, `GrabMinSize` and `ScrollbarSize`.
  - The rounding values, which are 0.
  - `CellPadding`, added only to be scaled, at Dear ImGui's default (4, 2). Dear PyGui doesn't change Dear ImGui's default style sizes.

  The rest stay at their unscaled defaults (`IndentSpacing` 21, `WindowMinSize` 32, `SeparatorTextPadding`, the tab sizes and so on), and nothing in this UI visibly uses them. Border sizes aren't scaled by Dear ImGui either.
- The font is scaled through the size passed to `add_font`, so `get_global_font_scale()` stays 1.0 (measured). Dear ImGui 1.92 rasterizes glyphs at the final size, and at 2× the text is sharp.
- Results:
  - Scale 1 (`Xft.dpi` unset, or `--ui-scale 1`): the main-window and SIMBAD-window frames are byte-identical to the frames from before the change.
  - `Xft.dpi: 192`: a 2400×1800 viewport. The main window, the SIMBAD window, a results table and the About window all keep the 1× proportions.
  - `Xft.dpi: 144`: 1800×1350.
  - `--ui-scale 1.25`: 1500×1125.
  - `--ui-scale 0`, `nan` and `5` are refused by the range check, and `abc` by argparse.
- Window sizes saved in `settings.ini` are physical pixels from whatever scale the previous run used. Not checked: what a saved size below the newly scaled `min_size` looks like.

### Risks to recheck on a Dear PyGui bump

- If Dear PyGui adds its own Linux DPI handling, or bundles a GLFW 3.4+ with Wayland (where the content scale is the output scale and sizes are already logical), the app would scale twice. Check `glfwGetVersionString()` and `mvViewport_linux.cpp` first.
- Some setups scale XWayland clients in the compositor while also advertising an `Xft.dpi` above 96. They get double scaling, and `--ui-scale 1` is the way out.

### Running the GUI on Xvfb

- Start the server with `Xvfb :99 -screen 0 3840x2160x24 -nolisten tcp -noreset`, run in the background, and kill it by PID afterwards. **`-noreset` is required**: without it the server resets when its last client disconnects, which drops `RESOURCE_MANAGER`. A property set by one process is then gone for the next, and every probe reads 1.0.
- The image has no `xrdb`, so set the property through libX11 with `ctypes`:

  ```python
  x = ctypes.CDLL("libX11.so.6")
  # set restype/argtypes: XOpenDisplay -> c_void_p, XDefaultRootWindow/XInternAtom -> c_ulong
  d = x.XOpenDisplay(None)
  atom = x.XInternAtom(d, b"RESOURCE_MANAGER", 0)
  x.XChangeProperty(d, x.XDefaultRootWindow(d), atom, 31, 8, 0, data, len(data))  # XA_STRING, format 8, PropModeReplace
  x.XCloseDisplay(d)
  ```

  `XDeleteProperty` removes the property again, and `XResourceManagerString` reads it back.
- The harness:
  - Wrap `dpg.setup_dearpygui` (`main()` looks it up at call time) to add `dpg.set_frame_callback(N, …)` calls. These save frames with `dpg.output_frame_buffer(file=…png)`, show windows with `dpg.show_item("window_simbadIDs")` and so on, and end with `dpg.stop_dearpygui()`.
  - Point `tap_adql_sandbox.__main__.settingsFile` outside the tree, because the tree has a real, gitignored `settings.ini`.
  - Replace `pyvo.dal.TAPService` with a fake whose `search()` returns an object with `__len__` and `to_table().to_pandas()`. Calling `app.executeQuery()` from a frame callback then fills a results table without any network access.
- Mesa renders GLX in Xvfb without complaint. The venv was `uv venv --python /usr/bin/python3` plus the Dear PyGui wheel, `pyvo`, `astroquery`, `pandas` and `tabulate`, and the app ran from `PYTHONPATH=/workspace/src`.
