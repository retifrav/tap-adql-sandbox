debugMode: bool = False

tabulateFloatfmtPrecision: str = "g"

windowMinWidth: int = 900

noEnumerationColumn: bool = False

# Dear ImGui (which Dear PyGui is built on) asserts that a table has
# fewer than `IMGUI_TABLE_MAX_COLUMNS` (512) columns, and that counts
# the artificial enumeration column too:
# - https://github.com/ocornut/imgui/blob/v1.92.5/imgui_internal.h
# - https://github.com/ocornut/imgui/blob/v1.92.5/imgui_tables.cpp
dpgColumnsMax: int = 511
