debugMode: bool = False

tabulateFloatfmtPrecision: str = "g"

windowMinWidth: int = 900

# factor for every size in pixels (fonts, paddings, windows), set in `main()`
# from `--ui-scale` or from the content scale of the display (`scaling.py`)
uiScale: float = 1.0
uiScaleMin: float = 0.5
uiScaleMax: float = 4.0

noEnumerationColumn: bool = False

# Dear ImGui (which Dear PyGui is built on) asserts that a table has fewer
# than `IMGUI_TABLE_MAX_COLUMNS` (512) columns, and that counts the artificial
# enumeration column too:
# - https://github.com/ocornut/imgui/blob/v1.92.5/imgui_internal.h
# - https://github.com/ocornut/imgui/blob/v1.92.5/imgui_tables.cpp
dpgColumnsMax: int = 511
