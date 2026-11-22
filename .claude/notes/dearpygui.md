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

## Text layout

Measured on 2026-11-21 with Dear PyGui 2.3.1 on Xvfb (x86_64), with `get_item_rect_min`/`get_item_rect_max` of every text and button in the Donation and About windows, at `--ui-scale 1` and `2`. Numbers are y pixels at scale 1 (scale 2 doubles them exactly). The window content starts at y = 43 (title bar plus `getWindowTheme`'s 4 px `WindowPadding.y`).

- A standalone text behaves as if it were aligned to the frame padding (`AlignTextToFramePadding`): its rect starts `FramePadding.y` (6) below the cursor, and its line ends `FramePadding.y` below the text. About's three-line first paragraph is 49–121 (lines at 49, 73, 97), and the next text, "Version", starts at 133: 6 of padding plus 6 of `ItemSpacing.y`. So two separate text items are 30 px apart, but the lines of one multiline text are 24 px apart.
- In a horizontal group, a text before a button with the default `FramePadding` is level with the button's label: the address button is 108–144, so its label starts at 114, and `XLM:` is 114–138. With `FramePadding.y` = 0 on the button alone, the button was 138–162 (so its label at 138) while `XLM:` stayed 6 below the line top, at 144: the address sat 6 px too high.
- `getInlineTheme()` (`FramePadding` and `ItemSpacing` both 0) bound to a vertical group holding a `styleFramePadding[1]` spacer, a horizontal group (text, hyperlink, text) and a second text gives lines at 49–73 and 73–97. That is exactly About's first paragraph. At scale 2 both are 95, 143, 191.
- An item theme bound to a group is still in effect when the group ends: with `ItemSpacing` 0 on a horizontal group, the next item started right at its bottom. That's why the spacer and the second line have to be inside the themed group, and why the paragraph is followed directly by the next item, with no spacing.
- Leading and trailing spaces count in a text's width. With `ItemSpacing.x` = 0, `"… via "`, the hyperlink and `" or …"` touch exactly (375 → 375, 539 → 539), and the gaps look like ordinary spaces.
- The compact wallet list (measured 2026-11-22, scale 1, window at (20, 20)): before it, the rows were 42 px apart, a 36 px button (24 of text plus 6 of `FramePadding.y` on each side) and 6 of `ItemSpacing.y`, against the 24 px lines of the paragraph above. `getCompactListTheme()` on a group around the rows, with `ItemSpacing.y` 0 and `FramePadding.y` p for the texts and the buttons alike, gives a pitch of 24 + 2p: 36, 30, 28 and 24 for p = 6, 3, 2 and 0. At every p the texts stay level with the button labels (at p = 3: the button at 126–156, `XLM:` at 129–153). The user wanted the list a bit more compact, and p = 3 was chosen. At p = 0 the rows are exactly the paragraph's 24 px lines, and the hover boxes of the addresses touch the text. The group-end effect above holds here too: without a spacer the "Signed variant" button started right at the BTC button's bottom (198 → 198). A plain `add_spacer()` after the group restores the 6 px gap (186 → 192), since it is drawn outside the theme. At scale 2 every distance doubles exactly (rows 60 px apart, that gap 12).
- Not tried: `wrap=0` on the text after the hyperlink. Dear ImGui would start the continuation lines at that text's own x, not at the window's left edge, so it can't make the paragraph wrap by itself.

## Fonts

Checked on 2026-11-22 against the 2.3.1 wheel (`dearpygui.py`, the x86_64 `_dearpygui.so`) and the JetBrains Mono 2.225 and 2.304 release zips from GitHub, and measured on Xvfb (x86_64) at `--ui-scale 1` and `2`.

### History

- Until 2026-11-22 the only font was `JetBrainsMono-Thin.ttf`, byte-identical (SHA-256 `e53e5021…c982`) to the one in the 2.225 release (January 2021). The currency names first became bold with that release's Bold, next to the Thin.
- The same day the user switched the UI font to Regular and asked for the latest release, 2.304 (January 2023, still the latest on GitHub), with Thin deleted from `fonts/`.
- **Decision**: after looking at all the text in the application in Regular (SHA-256 `a0bf60ef…d138f`), the user found it too bold everywhere and went back to Thin, keeping 2.304. Thin is the preferred UI weight, and Regular is rejected.
- Shipped now: `JetBrainsMono-Thin.ttf` (270112 bytes, SHA-256 `0756e8e8…ae1b702`) and `JetBrainsMono-Bold.ttf` (277828 bytes, `5590990c…79dcb`), both from `fonts/ttf/` in `JetBrainsMono-2.304.zip`. They are about 100 KB bigger than the 2.225 files because 2.304 has 1743 glyphs against 1213. The 2.225 Thin was committed with mode `100755` in 2022; the 2.304 one replaced it as `100644`, like the icons and the Bold.

### Metrics

- Every weight in 2.225 and 2.304 has 1000 units per em, `hhea` and `OS/2` typo ascent/descent/line gap 1020/−300/0, win ascent/descent 1020/300, and every glyph advance 600, with one exception: in Thin 2.304 U+FF5D (FULLWIDTH RIGHT CURLY BRACKET, glyph `uniFF5D`) has 599, which the UI never shows. So weights and these two releases are interchangeable for layout: same columns, line height and baseline.
- Switching Thin 2.225 → Regular 2.304 (with Bold 2.225 → 2.304) left the rect of every item identical in the main window (4 items), the Donation window (24) and the About window (11), at scale 1 and at scale 2. So did switching back from Regular 2.304 to Thin 2.304.

### Bold text

- Dear PyGui has no bold style or font flag. `add_font(file, size, …)` takes only `pixel_snapH`/`pixel_snapV` besides the usual item keywords, and `_dearpygui.so` has Dear ImGui's stb_truetype loader (`ImFontAtlasGetFontLoaderForStbTruetype`, `stbtt_*`) and no FreeType, so there is no synthetic bold either: Dear ImGui's `ImGuiFreeTypeLoaderFlags_Bold` exists only in the FreeType loader. A bold text is therefore a second font file bound to the item with `bind_item_font`.
- Splitting `"- XLM:"` into `"- "`, bold `"XLM"` and `":"` in a `horizontal_spacing=0` group: at scale 1 every rect is identical to the single text (`- XLM:` 15–81, the address button 89–720, both rows). At scale 2 the button moves 1 px right (174 → 175), because each text rounds its own fractional width (about 21.8 px per column there) instead of the whole string's: `"- "` 27–71, `"XLM"` 71–137, `":"` 137–159, against 27–158 before. Nothing lines up with that button, so the pixel was accepted. Measured with the Thin and Bold of 2.225; the metrics above make it hold for 2.304 too, and the switch moved nothing.

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

## Syntax highlighting

Researched on 2026-11-21 for the ADQL query input (`queryTextID` in `__main__.py`) from the installed 2.3.1 wheel (`dearpygui.py`, the x86_64 `_dearpygui.so`), Dear ImGui's `imgui_widgets.cpp` at `v1.92.5` (`InputTextEx`) and Dear PyGui's GitHub issues. Nothing was prototyped.

### Decision

- The user deferred it until Dear PyGui has a code editor widget, and declined both workarounds below for now.
- When it is done, the user wants it switchable two ways: a `--no-syntax-highlighting` CLI flag for the startup state, like `--no-enum-column`, and a checkbox menu item at runtime. The choice isn't persisted, because the app has no settings file (`settings.ini` is only Dear PyGui's window layout).

### Nothing ready-made

- In 2.3.1 the only `dearpygui.py` matches for editor, highlight and syntax are the node editor, the style editor, the color editor, plot-series highlighting and `readonly`'s text selection. `nm -D` on `_dearpygui.so` finds no `TextEditor` or `LanguageDefinition` symbols. `add_input_text` has a single text color.
- Upstream: #1194 ("Add JSON syntax highlighting as optional parameter for add_input_text") was opened and closed on 2021-08-20 with "This will be handled with the text editing widget!", which points to #173 ("Text Editing Widget", opened 2020-09-05). #173 was closed on 2022-09-24 with "Closing as this will likely be pushed to DPG 2". 2.3.1 has no such widget, and a May 2025 question in #173 is unanswered.
- The Dear ImGui addon is ImGuiColorTextEdit (BalazsJako, no longer maintained by its author; the maintained fork is `goossens/ImGuiColorTextEdit`, which tracks Dear ImGui 1.92.x). It has an SQL language definition. It is C++, and its only Python bindings are in imgui_bundle (pthom), a different framework, so using them means rewriting the UI. The other route is a C++ contribution to Dear PyGui.
- No Python package adds one: `dearpygui-ext` (2.1.1) and `DearPyGui_Extend` (movable groups, file browser, layout) have no editor.

### What Dear PyGui exposes

- No caret position or selection of an input: nothing in the wrapper takes or returns one.
- A multiline input scrolls inside a child window it creates itself (`BeginChildEx`). That child isn't a Dear PyGui item, so `get_x_scroll`/`get_y_scroll` can't reach it.
- Exposed: `mvThemeCol_InputTextCursor` and `no_horizontal_scroll`. Not exposed: Dear ImGui 1.92's `ImGuiInputTextFlags_WordWrap` (there is no `word_wrap` keyword).

### Overlay workaround (not built)

The idea: make the input's `Text` and `FrameBg` colors transparent through an item theme, and draw the background and colored text beneath it at the input's position. The `InputTextEx` facts it relies on:

- Multiline pushes `ImGuiCol_ChildBg` = `FrameBg` and draws into its child window, which renders above the parent window's draw list. So the overlay has to go *under* the input, not over it.
- The text starts at the frame's min corner plus `FramePadding`, and each line is `g.FontSize` tall. Text uses `ImGuiCol_Text`, but the caret uses `ImGuiCol_InputTextCursor`, so it stays visible over transparent text. Selection rects are drawn before the text.
- With `ImGuiInputTextFlags_NoHorizontalScroll`, every caret follow sets `state->Scroll.x = 0.0f`. Without it, the box scrolls in quarter-width chunks. An inactive input draws with zero horizontal scroll (the `//draw_scroll.x = state->Scroll.x; // Preserve scroll when inactive?` line is commented out).
- Vertical scroll is clamped to `max(text height + 2 × FramePadding.y − inner height, 0)`, so it is 0 while the text fits.

Since the scroll can't be read, the overlay is only right while the whole query fits without scrolling: about 12 lines × 80 columns at scale 1 in the default 1200 px window (the box is `scaled(300)` tall, and 24 px JetBrains Mono is about 14.4 px per column). Outside that, the box would fall back to plain text. The 92-column NASA example "Most recent value of a planets parameter" doesn't fit at that width.

- Open risk: after a query shrinks back to fitting, the horizontal scroll can stay non-zero until the next caret move with the flag set.
- Rejected variant: growing the input to its content inside a scrolling child window. The outer window doesn't follow the caret, and the caret position can't be read to scroll it.

### Other options considered

- A colored read-only view shown in place of the input while it isn't focused, swapped for the input on click. It is robust and works at any size, but shows no colors while typing, and the caret can't be put where the click landed.
- A custom editor built from drawlist primitives and key handlers. Rejected: too much to reimplement (caret, selection, clipboard, undo, IME).
- Untested idea for the tokenizer: a small regex lexer for ADQL 2.1 (the SQL keywords plus `TOP`, `CONTAINS`, `POINT`, `CIRCLE` and so on) rather than Pygments' `SqlLexer`, which would be a new dependency. Whether Pygments knows ADQL's functions wasn't checked.

### On a Dear PyGui bump

Check the wrapper for a text or code editor item (`rg -i editor dearpygui.py`, minus the node, style and color editors) and the state of #173.

## Loading indicator

Checked on 2026-11-22 against Dear PyGui's sources at `v2.3.1` (`src/mvLoadingIndicator.h`/`.cpp`, `src/mvLoadingIndicatorCustom.cpp`, `src/dearpygui.cpp`, the viewport and graphics backends) and the 2.3.1 wheel, and measured on Xvfb (x86_64) at `--ui-scale 1` and `2`.

### Styles

- `mvLoadingIndicator::Style` is `Style_OldDottedCircle = 0`, `Style_OldRing = 1`, `Style_DottedCircle = 2`, `Style_Ring = 3`. At runtime `dpg.mvLoadInd_DottedCircle` is 2 and `dpg.mvLoadInd_Ring` is 3 (registered in `src/dearpygui.cpp`). `_dearpygui.pyi` says 0 for both, which is wrong. The `style` keyword defaults to 0, the old dotted circle.
- Upstream commit `99058f35` (2026-01-04, in 2.3.0): "Old indicator rendering is kept at style=1 for compatibility; new corrected rendering can be selected with style=mvLoadInd_Ring". The app's `style=1` dates from Dear PyGui 1.x (commit `1428135`), where 1 simply meant the ring, so after the bump to 2.3 it silently stayed on the old drawing.
- `Style_OldRing` is `LoadingIndicatorCircle2`, posted in ocornut/imgui#1901. It rotates at `8t` rad/s, and its tail offset is `start = abs((int)(sin(1.8t) * 25))` thirtieths of a turn. The cast moves the tail in 12° steps. `abs` puts a V-shaped kink where `sin` crosses 0, which is the end of every ~1.75 s cycle, where the arc is longest: there the tail's speed flips from −1.4 to +17.4 rad/s between two frames. That was the jerk the user saw. It takes no `speed`, which is why `# speed=2` was commented out.
- `Style_Ring` is `LoadingIndicatorRing`, upstream's "corrected version": `t = Time * speed` and `start = 0.5 (1 − sin 3t) * 25` as a float, so the tail's speed, 8 − 7.85 cos 3t rad/s at `speed=1`, varies smoothly between 0.15 and 15.9 rad/s. Upstream's comment on it: "does not have visual artifacts (jitter of the ring tail when it slows down)".

### Geometry

`L` is the text line height, 24 px at scale 1.

- Old ring: the circle is centred `0.38·radius·L` right of the item's x and `FramePadding.y + 0.38·radius·L` below its y. The stroke is `0.12·thickness·radius·L` wide (the `if (t > t * 0.4f) t = t * 0.4f` clamp always applies), and the outer diameter is `0.88·radius·L` at `thickness=1`. So the ring overhangs its item rect by `0.06·radius·L` on the left and at the top.
- New ring: the box is `radius·L` square and starts at the item's x and `FramePadding.y` below the cursor (`AlignTextToFramePadding`). The ring touches the box on all sides, with a stroke of `thickness·radius·L/8`.
- Keeping the outline therefore means `radius` × 0.88, `thickness` ≈ 0.96 × old radius / new radius, and an `indent` smaller by `0.06·radius·L`. Chosen: main window 2.0 → 1.75, SIMBAD window 1.5 → 1.3, `thickness=1.1` for both, `indent` `scaled(7)` → `scaled(4)` and `scaled(5)`.
- Measured as the union of the ring's pixels (green exceeding red and blue by more than half the maximum) over ~2.5 s of frames. The SIMBAD window was placed at `(600, 100)` × scale by the harness:

  | ring box, x × y | old (`style=1`) | new |
  |---|---|---|
  | main, scale 1 | 16–58 × 401–443 | 16–58 × 404–446 |
  | SIMBAD, scale 1 | 617–649 × 196–228 | 617–648 × 198–229 |
  | main, scale 2 | 32–117 × 802–887 | 32–116 × 808–892 |
  | SIMBAD, scale 2 | 1234–1297 × 392–455 | 1234–1296 × 396–458 |

  Size and horizontal position match within 1 px. The new ring sits lower by the old one's top overhang: 3 px at scale 1 and 6 at scale 2 for the main window. There is no knob for that: the indicator has no vertical offset, and only an item theme with a smaller `FramePadding.y` would lift it. Nothing lines up with the ring vertically, so it was left. The main window's item rect ends at y = 446 in both versions, so what follows doesn't move.

### Rendering cost

- Dear PyGui renders every frame unconditionally. Each `render_dearpygui_frame()` calls `glfwPollEvents` (`mvViewport_linux.cpp`, `mvViewport_apple.mm`; `PeekMessage` in `mvViewport_win32.cpp`) and redraws the whole UI. Only an iconified window waits (`glfwWaitEvents`), and on macOS an occluded one sleeps 32 ms per frame. The pace is vsync: on Linux `present()` calls `glfwSwapInterval(vsync ? 1 : 0)`, on macOS it sets Metal's `displaySyncEnabled`. `create_viewport`'s `vsync` defaults to true, and the app doesn't pass it.
- Measured on Xvfb, where Mesa's llvmpipe makes rendering CPU time in the app's own process. Each state ran for 5 s, in two rounds, at scale 1, with the main and SIMBAD windows open. Xvfb has no vblank, so vsync doesn't throttle there: the app ran at ~440 fps on ~10.7 cores. CPU per frame:

  | state | app | Xvfb |
  |---|---|---|
  | idle (buttons shown) | 24.18 ms | 0.31–0.32 ms |
  | old ring spinning | 24.13 ms | 0.32 ms |
  | new ring spinning | 24.14–24.16 ms | 0.32 ms |

  So the indicator costs less than the noise. The GPU load the user saw is the continuous redraw at the display's refresh rate, which is the same whether or not a query runs. Replacing the spinner with anything else, static text included, would save nothing.

### Power saving (not built)

On 2026-11-22 the user chose to fix the style only and decide about power saving separately, and then asked for the frame rate cap below rather than this. What is known:

- `configure_app(wait_for_input=True)` swaps `glfwPollEvents` for `glfwWaitEvents` (`WaitMessage` on Windows), so an idle window would cost nothing.
- Nothing in Dear PyGui's 104 `src/*.cpp`/`.h`/`.mm` files at `v2.3.1` calls `glfwPostEmptyEvent`, `PostMessage` or `PostThreadMessage`, so there is no way to wake a waiting loop from Python.
  - `split_frame()` waits for a frame to end, so it would block while the loop waits.
  - Setting the flag back to false from the callback thread doesn't wake a loop that is already waiting either.
  - So everything the callback thread changes would stay unpainted until the next mouse or keyboard event: the indicator, the results, the error texts, and the `[copied]` and cell-highlight reverts after `sleep(1)`.
- A working version would need its own wake-up, and would render continuously while anything animates (a query, a SIMBAD lookup, a revert) and wait otherwise.
  - Linux: `glfwPostEmptyEvent`, which GLFW allows from any thread, through `ctypes` on the GLFW bundled in `_dearpygui.so`, as `scaling.py` already does for the content scale. It is exported by the x86_64 wheel; the aarch64 and macOS wheels were not checked.
  - Windows: `PostThreadMessageW` to the main thread, because that backend doesn't use GLFW.
### Frame rate cap (built)

Later on 2026-11-22 the user asked for a cap instead, at 30 fps, which Claude also recommended.

- Why 30:
  - It divides 60, 120 and 240 Hz evenly, so with vsync every frame lands on the same number of refreshes. At 144 Hz frames alternate between 4 and 5 refreshes (27.8 and 34.7 ms), which is visible only as slight judder of the spinner.
  - It halves the redraws at 60 Hz and quarters them at 120 Hz.
  - The cost is up to one frame period (33 ms) of extra input latency, and choppier scrolling and window dragging.
  - Dear ImGui's key repeat (`KeyRepeatRate` 0.05 s, 20 Hz) is slower than 30 fps, so no repeats are lost. The spinner (`g.Time`), the caret blink and double-click detection are time-based, so they keep their speed.
- `start_dearpygui()` in the 2.3.1 wrapper is only `is_viewport_ok()` and then `while is_dearpygui_running(): render_dearpygui_frame()`. `runRenderLoop()` in `__main__.py` is that loop with a sleep until the next frame is due, and it skips `is_viewport_ok()` because `main()` has just shown the viewport.
  - Frames are due at fixed intervals, so frame time doesn't add to the interval. After a late frame the schedule restarts instead of bursting.
  - vsync stays on, so a frame never presents faster than the display, and there is no tearing.
  - `time.sleep` releases the GIL, which leaves the callback thread more of it.
- Measured on Xvfb, scale 1, 5 s per state, idle and spinning alike, two rounds:
  - The frame rate holds at 30.0 (`get_frame_count` over wall time; Dear ImGui's `get_frame_rate()` reads 29–30). The same at scale 2.
  - A fake query in `executeQuery()` that sleeps 2 s in `search()` got 60 frames during the query. The results table then appeared (3 rows), the button came back, and the exit callback still wrote `settings.ini`.
- CPU time under llvmpipe is not a proxy for the GPU saving:
  - With its default 16 raster threads, uncapped ~440 fps took ~1070 % CPU and the 30 fps cap ~410 %. The 16 `llvmpipe-N` threads were ~24 % each at the cap, and the Python main thread 6.5 %. No Dear PyGui thread busy-loops.
  - With `LP_NUM_THREADS=0`, so that rendering happens in the main thread, uncapped is 57 fps on one core at 16.8 ms per frame, and capped is 30 fps at 69 % at ~23 ms per frame. Per-frame CPU grows once the CPU idles between frames (presumably frequency scaling).
  - So the saving on a real GPU has to be checked on a real display.

### On a Dear PyGui bump

Check that `Style_Old*` and the `mvLoadInd_*` values are unchanged (`src/mvLoadingIndicator.h`, `src/dearpygui.cpp`). Rerun the outline comparison if `LoadingIndicatorRing` changed. Check that `start_dearpygui()` in `dearpygui.py` is still just the bare loop that `runRenderLoop()` copies. Look for a wake-up, a frame-rate limit or a redraw-on-demand mode in the viewport backends.
